"""Weekend / drive-range spot scanner -- 'where can I kite?'."""

from __future__ import annotations

from guru.models.advice import ScheduleSlot, WeekendReport, WeekendSpotAdvice
from guru.models.profile import RiderProfile
from guru.rider import voice
from guru.rider.advice import advise_forecast
from guru.rider.weekend_rank import (
    filter_schedule_by_day,
    home_vs_far_line,
    model_agree_by_day,
    parse_filter_day,
    pick_schedule,
    score_spot,
    slot_rank,
    slot_summary,
    weekend_summary_text,
)
from guru.rider.weekend_spots import candidate_spots, long_drive_ok, weekday_label
from guru.search.blend import get_best_forecast
from guru.search.sst import SST_SOURCE, fetch_sst_many

__all__ = (
    "DEFAULT_TOP_MODELS",
    "DEFAULT_WEEKEND_HOURS",
    "candidate_spots",
    "scan_weekend",
)

DEFAULT_WEEKEND_HOURS = 96
DEFAULT_TOP_MODELS = 3


def scan_weekend(
    profile: RiderProfile,
    *,
    hours: int = DEFAULT_WEEKEND_HOURS,
    limit_spots: int = 8,
    top_models: int = DEFAULT_TOP_MODELS,
    filter_day: str | None = None,
) -> WeekendReport:
    """Rank rideable spots + day-by-day schedule (top WINDGURU_DEFAULT models)."""
    missing = profile.missing_fields() + profile.missing_range_fields()
    thinking = voice.thinking_headers(
        hours=hours,
        top_models=top_models,
        range_label=profile.range_label,
    ) + voice.checklist(gusty=False, drive_km=profile.drive_km)

    if missing:
        return WeekendReport(
            verdict="incomplete",
            range_label=profile.range_label,
            home_lat=profile.home_lat,
            home_lon=profile.home_lon,
            drive_km=profile.drive_km,
            hours=hours,
            top_models=top_models,
            filter_day=filter_day,
            missing_profile=missing,
            summary=voice.weekend_incomplete(missing),
            thinking=thinking,
        )

    candidates = candidate_spots(profile, limit=limit_spots)
    coords = [
        (float(s.lat), float(s.lon))
        for s, _ in candidates
        if s.lat is not None and s.lon is not None
    ]
    sst_map = fetch_sst_many(coords) if coords else {}

    results: list[WeekendSpotAdvice] = []
    day_candidates: list[tuple[str, ScheduleSlot, float]] = []

    for spot, drive in candidates:
        best = get_best_forecast(spot.id, top=top_models, hours=hours)
        if not best.forecasts:
            continue
        sst_c = (
            sst_map.get((float(spot.lat), float(spot.lon)))
            if spot.lat is not None and spot.lon is not None
            else None
        )
        model_advices = [
            advise_forecast(fc, profile, drive_km=drive, max_windows=12, sst_c=sst_c)
            for fc in best.forecasts
        ]
        primary = model_advices[0]
        if primary.verdict in {"no", "incomplete"}:
            continue
        if not long_drive_ok(
            drive, verdict=primary.verdict, windows=primary.windows
        ):
            continue

        agree_by_day = model_agree_by_day(model_advices)
        window = primary.windows[0] if primary.windows else None
        day_key = window.start[:10] if window else ""
        agree = agree_by_day.get(day_key, 1) if day_key else 1
        score = score_spot(primary.verdict, drive, model_agree=agree)
        drive_r = round(drive, 1) if drive is not None else None

        results.append(
            WeekendSpotAdvice(
                spot_id=spot.id,
                name=spot.name,
                lat=spot.lat,
                lon=spot.lon,
                drive_km=drive_r,
                verdict=primary.verdict,
                summary=primary.summary,
                best_window=window,
                model=primary.model,
                model_agree=agree,
                score=score,
                sst_c=sst_c,
            )
        )

        for w in primary.windows:
            if w.verdict not in {"go", "marginal"}:
                continue
            if not long_drive_ok(drive, window=w):
                continue
            d = w.start[:10]
            a = agree_by_day.get(d, 1)
            slot = ScheduleSlot(
                day=d,
                weekday=weekday_label(w.start),
                start=w.start,
                end=w.end,
                spot_id=spot.id,
                name=spot.name,
                drive_km=drive_r,
                verdict=w.verdict,
                wind_kn=w.wind_kn,
                gust_kn=w.gust_kn,
                wind_dir_deg=w.wind_dir_deg,
                owned_kite_m2=w.owned_kite_m2,
                owned_wetsuit=w.owned_wetsuit or w.wetsuit,
                model_agree=a,
                rating_stars=w.rating_stars,
                rating_cold=w.rating_cold,
                rating=w.rating,
                summary=slot_summary(spot.name, w, a),
                hours_usable=w.hours_usable,
            )
            day_candidates.append((d, slot, slot_rank(w, drive, a)))

    results.sort(
        key=lambda r: (-r.score, r.drive_km if r.drive_km is not None else 999)
    )
    schedule = pick_schedule(day_candidates)
    schedule, results, thinking = _apply_day_filter(
        filter_day, schedule, results, thinking
    )

    overall = results[0].verdict if results else "no"
    compare = home_vs_far_line(results)
    if compare:
        thinking.append(compare)

    return WeekendReport(
        verdict=overall,
        range_label=profile.range_label,
        home_lat=profile.home_lat,
        home_lon=profile.home_lon,
        drive_km=profile.drive_km,
        hours=hours,
        top_models=top_models,
        filter_day=filter_day,
        spots=results,
        schedule=schedule,
        missing_profile=[],
        summary=weekend_summary_text(overall, schedule, results),
        thinking=thinking,
        sst_source=SST_SOURCE if sst_map else None,
    )


def _apply_day_filter(
    filter_day: str | None,
    schedule: list[ScheduleSlot],
    results: list[WeekendSpotAdvice],
    thinking: list[str],
) -> tuple[list[ScheduleSlot], list[WeekendSpotAdvice], list[str]]:
    wd, iso = parse_filter_day(filter_day)
    if not wd and not iso:
        return schedule, results, thinking
    schedule = filter_schedule_by_day(schedule, weekday=wd, iso_day=iso)
    if schedule:
        keep = {s.spot_id for s in schedule}
        results = [r for r in results if r.spot_id in keep] or results
    else:
        results = []
        thinking.append(
            f"Nothing on {filter_day} in this horizon "
            "(we have not hacked time yet beyond top-model range)"
        )
    return schedule, results, thinking
