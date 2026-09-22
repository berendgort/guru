"""Build structured session advice from a forecast + rider profile."""

from __future__ import annotations

from guru.models.advice import AdviceReport
from guru.models.forecast import Forecast, ForecastHour, Spot
from guru.models.profile import Level, RiderProfile, Sport
from guru.rider import voice
from guru.rider.advice_gates import apply_long_drive_gate, apply_spot_note
from guru.rider.advice_windows import collapse_windows, overall_verdict, summary_line
from guru.rider.shore import classify_shore, sectors_for_spot
from guru.rider.sizing import (
    hour_verdict,
    ideal_kite_m2,
    pick_owned_kite,
    pick_owned_wetsuit,
    recommend_wetsuit,
    sizing_rule_text,
    wind_quality,
)

__all__ = ("advise_forecast", "drive_km_from_home")


def drive_km_from_home(profile: RiderProfile, spot: Spot) -> float | None:
    from guru.search.near import haversine_km

    if (
        profile.home_lat is None
        or profile.home_lon is None
        or spot.lat is None
        or spot.lon is None
    ):
        return None
    return haversine_km(profile.home_lat, profile.home_lon, spot.lat, spot.lon)


def advise_forecast(
    forecast: Forecast,
    profile: RiderProfile,
    *,
    max_windows: int = 6,
    drive_km: float | None = None,
    sst_c: float | None = None,
    wave_by_hour: dict[int, tuple[float | None, float | None]] | None = None,
) -> AdviceReport:
    """Score rideable windows on the top-model forecast."""
    missing = profile.missing_fields()
    if missing:
        return AdviceReport(
            verdict="incomplete",
            sport=profile.sport.value if profile.sport else None,
            level=profile.level.value if profile.level else None,
            model=forecast.model,
            missing_profile=missing,
            summary=voice.incomplete_advice_summary(missing),
            sizing_rule="2.2*kg/kn; size for average; gusty -> warn",
            checklist=voice.checklist(gusty=False, drive_km=drive_km),
        )

    assert profile.sport is not None
    assert profile.weight_kg is not None
    assert profile.level is not None
    sport, level = profile.sport, profile.level
    weight, session_h = profile.weight_kg, profile.session_hours

    sst_source = None
    if sst_c is None and forecast.spot.lat is not None and forecast.spot.lon is not None:
        try:
            from guru.search.sst import SST_SOURCE, fetch_sst

            sst_c = fetch_sst(forecast.spot.lat, forecast.spot.lon)
            if sst_c is not None:
                sst_source = SST_SOURCE
        except Exception:  # noqa: BLE001
            sst_c = None

    note_text = profile.spot_notes.get(str(forecast.spot.id))
    preferred, offshore, shore_source = sectors_for_spot(
        forecast.spot.id, spot_note=note_text
    )

    if wave_by_hour is None and sport is Sport.SURFKITE:
        from guru.search.wave import wave_map_for_forecast

        wave_by_hour = wave_map_for_forecast(forecast)

    scored: list[
        tuple[
            ForecastHour,
            str,
            float | None,
            float | None,
            float | None,
            str | None,
            list[str],
            str,
        ]
    ] = []
    any_gusty = False
    for hour in forecast.hours:
        shore = classify_shore(
            hour.wind_dir_deg, preferred=preferred, offshore=offshore
        )
        verdict = hour_verdict(hour.wind_kn, hour.gust_kn, sport=sport, level=level)
        if shore == "offshore" and verdict != "no":
            verdict = "no" if level is Level.BEGINNER else "marginal"
        if verdict == "no":
            continue
        quality = wind_quality(hour.wind_kn, hour.gust_kn)
        if quality == "gusty":
            any_gusty = True
        ideal = ideal_kite_m2(
            weight, hour.wind_kn or 0.0, sport=sport, level=level, gust_kn=hour.gust_kn
        )
        owned, gap = pick_owned_kite(
            ideal, profile.kites_m2, level=level, sport=sport
        )
        rec_suit, accessories = recommend_wetsuit(
            hour.temp_c,
            wind_kn=hour.wind_kn,
            session_hours=session_h,
            level=level,
            sst_c=sst_c,
        )
        owned_suit = pick_owned_wetsuit(rec_suit, profile.wetsuits)
        note = _hour_note(
            sport=sport,
            level=level,
            wind_kn=hour.wind_kn,
            quality=quality,
            ideal=ideal,
            owned=owned,
            gap=gap,
            rec_suit=rec_suit,
            owned_suit=owned_suit,
            session_hours=session_h,
        )
        if shore == "offshore":
            tag = "offshore (known sector) -- advanced / rescue only"
            note = f"{note}; {tag}" if note else tag
        note = apply_spot_note(note, profile, forecast)
        scored.append(
            (hour, verdict, ideal, owned, gap, owned_suit or rec_suit, accessories, note)
        )

    shore_rel = "unknown"
    if any(
        classify_shore(h.wind_dir_deg, preferred=preferred, offshore=offshore)
        == "offshore"
        for h, *_ in scored
    ):
        shore_rel = "offshore"
    elif preferred or offshore:
        shore_rel = "preferred"

    windows = collapse_windows(
        scored,
        max_windows=max_windows,
        session_hours=session_h,
        level=level,
        sunrise=forecast.sunrise,
        sunset=forecast.sunset,
        sst_c=sst_c,
        shore_relation=shore_rel if shore_source != "unknown" else "unknown",
        wave_by_hour=wave_by_hour,
    )
    overall = apply_long_drive_gate(
        overall_verdict(windows), windows, drive_km=drive_km
    )
    summary = summary_line(
        overall, windows, sport=sport, level=level, session_h=session_h
    )

    return AdviceReport(
        verdict=overall,
        sport=sport.value,
        level=level.value,
        model=forecast.model,
        windows=windows,
        sizing_rule=sizing_rule_text(sport),
        checklist=voice.checklist(gusty=any_gusty, drive_km=drive_km),
        missing_profile=[],
        summary=summary,
        sst_c=sst_c,
        sst_source=sst_source,
        shore_source=shore_source if shore_source != "unknown" else None,
    )


def _hour_note(
    *,
    sport: Sport,
    level: Level,
    wind_kn: float | None,
    quality: str,
    ideal: float | None,
    owned: float | None,
    gap: float | None,
    rec_suit: str | None,
    owned_suit: str | None,
    session_hours: float,
) -> str:
    bits = voice.hour_bits(
        quality=quality,
        sport_foil_light=sport is Sport.KITEFOIL
        and wind_kn is not None
        and wind_kn < 12,
        gap=gap,
        ideal=ideal,
        owned=owned,
        owned_suit=owned_suit,
        rec_suit=rec_suit,
        session_hours=session_hours,
        beginner_strong=level is Level.BEGINNER
        and wind_kn is not None
        and wind_kn >= 20,
    )
    return "; ".join(bits) if bits else ""
