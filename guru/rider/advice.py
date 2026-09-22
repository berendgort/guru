"""Build structured session advice from a forecast + rider profile."""

from __future__ import annotations

from datetime import datetime

from guru.models.forecast import Forecast, ForecastHour
from guru.models.profile import AdviceReport, AdviceWindow, Level, RiderProfile, Sport
from guru.rider.sizing import (
    hour_verdict,
    ideal_kite_m2,
    kiter_checklist,
    pick_owned_kite,
    pick_owned_wetsuit,
    recommend_wetsuit,
    sizing_rule_text,
    wind_quality,
)

_VERDICT_RANK = {"go": 2, "marginal": 1, "no": 0, "incomplete": -1}


def advise_forecast(
    forecast: Forecast,
    profile: RiderProfile,
    *,
    max_windows: int = 6,
    drive_km: float | None = None,
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
            summary=(
                "Rider profile incomplete — run guru setup before gear advice. "
                f"Missing: {', '.join(missing)}"
            ),
            sizing_rule="2.2*kg/kn; foil -40%; surfkite -15%; size for gusts",
            checklist=kiter_checklist(gusty=False, drive_km=drive_km),
        )

    assert profile.sport is not None
    assert profile.weight_kg is not None
    assert profile.level is not None
    sport = profile.sport
    level = profile.level
    weight = profile.weight_kg
    session_h = profile.session_hours

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
        verdict = hour_verdict(
            hour.wind_kn, hour.gust_kn, sport=sport, level=level
        )
        if verdict == "no":
            continue
        quality = wind_quality(hour.wind_kn, hour.gust_kn)
        if quality == "gusty":
            any_gusty = True
        ideal = ideal_kite_m2(
            weight,
            hour.wind_kn or 0.0,
            sport=sport,
            level=level,
            gust_kn=hour.gust_kn,
        )
        owned, gap = pick_owned_kite(ideal, profile.kites_m2)
        rec_suit, accessories = recommend_wetsuit(
            hour.temp_c,
            wind_kn=hour.wind_kn,
            session_hours=session_h,
            level=level,
        )
        owned_suit = pick_owned_wetsuit(rec_suit, profile.wetsuits)
        note = _hour_note(
            sport=sport,
            level=level,
            wind_kn=hour.wind_kn,
            gust_kn=hour.gust_kn,
            quality=quality,
            ideal=ideal,
            owned=owned,
            gap=gap,
            rec_suit=rec_suit,
            owned_suit=owned_suit,
            session_hours=session_h,
        )
        scored.append(
            (hour, verdict, ideal, owned, gap, owned_suit or rec_suit, accessories, note)
        )

    windows = _collapse_windows(
        scored, max_windows=max_windows, session_hours=session_h, level=level
    )
    overall = _overall_verdict(windows)
    # Far drive: demote marginal-only to no for ranking callers
    if drive_km is not None and drive_km > 90 and overall == "marginal":
        overall = "no"
        for w in windows:
            if w.verdict == "marginal":
                w.note = (w.note + "; " if w.note else "") + "far drive needs clearer GO"

    summary = _summary(overall, windows, sport=sport, level=level, session_h=session_h)

    return AdviceReport(
        verdict=overall,
        sport=sport.value,
        level=level.value,
        model=forecast.model,
        windows=windows,
        sizing_rule=sizing_rule_text(sport),
        checklist=kiter_checklist(gusty=any_gusty, drive_km=drive_km),
        missing_profile=[],
        summary=summary,
    )


def _hour_note(
    *,
    sport: Sport,
    level: Level,
    wind_kn: float | None,
    gust_kn: float | None,
    quality: str,
    ideal: float | None,
    owned: float | None,
    gap: float | None,
    rec_suit: str | None,
    owned_suit: str | None,
    session_hours: float,
) -> str:
    bits: list[str] = []
    if quality == "smooth":
        bits.append("smooth wind")
    elif quality == "gusty":
        bits.append("gusty — size for gusts")
    if sport is Sport.KITEFOIL and wind_kn is not None and wind_kn < 12:
        bits.append("foil light-wind ok")
    if gap is not None and abs(gap) > 2.0:
        bits.append(f"quiver gap {gap:+.1f} m² vs ideal {ideal}")
    elif owned is not None and ideal is not None:
        bits.append(f"rig {owned:g} m² (ideal ~{ideal:g})")
    if owned_suit and rec_suit and _normalize_compare(owned_suit) != _normalize_compare(
        rec_suit
    ):
        bits.append(f"suit: own {owned_suit}, chart wants {rec_suit} ({session_hours:g}h)")
    elif owned_suit:
        bits.append(f"suit {owned_suit} ({session_hours:g}h session)")
    if level is Level.BEGINNER and wind_kn is not None and wind_kn >= 20:
        bits.append("strong for beginner")
    return "; ".join(bits) if bits else ""


def _normalize_compare(raw: str) -> str:
    return raw.strip().lower().replace(" ", "")


def _collapse_windows(
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
    ],
    *,
    max_windows: int,
    session_hours: float,
    level: Level,
) -> list[AdviceWindow]:
    if not scored:
        return []

    windows: list[AdviceWindow] = []
    block_hours = [scored[0]]
    block_verdict = scored[0][1]

    def flush() -> None:
        nonlocal block_hours
        if not block_hours:
            return
        first = block_hours[0][0]
        last = block_hours[-1][0]
        mid = block_hours[len(block_hours) // 2]
        hour, verdict, ideal, owned, gap, suit, accessories, note = mid
        spread = None
        if hour.gust_kn is not None and hour.wind_kn is not None:
            spread = round(hour.gust_kn - hour.wind_kn, 1)
        rec_suit, _acc = recommend_wetsuit(
            hour.temp_c,
            wind_kn=hour.wind_kn,
            session_hours=session_hours,
            level=level,
        )
        windows.append(
            AdviceWindow(
                start=_iso(first.time),
                end=_iso(last.time),
                wind_kn=float(hour.wind_kn or 0.0),
                gust_kn=hour.gust_kn,
                gust_spread_kn=spread,
                wind_quality=wind_quality(hour.wind_kn, hour.gust_kn),
                kite_m2=ideal,
                owned_kite_m2=owned,
                kite_gap_m2=gap,
                wetsuit=rec_suit,
                owned_wetsuit=suit,
                accessories=accessories,
                verdict=verdict,
                note=note,
            )
        )
        block_hours = []

    for i in range(1, len(scored)):
        prev_t = block_hours[-1][0].time
        cur = scored[i]
        same_verdict = cur[1] == block_verdict
        contiguous = _hours_adjacent(prev_t, cur[0].time)
        if same_verdict and contiguous:
            block_hours.append(cur)
        else:
            flush()
            block_verdict = cur[1]
            block_hours = [cur]
    flush()

    windows.sort(key=lambda w: (-_VERDICT_RANK.get(w.verdict, 0), w.start))
    return windows[:max_windows]


def _hours_adjacent(a: datetime, b: datetime) -> bool:
    return abs((b - a).total_seconds()) <= 3 * 3600


def _overall_verdict(windows: list[AdviceWindow]) -> str:
    if not windows:
        return "no"
    return max(windows, key=lambda w: _VERDICT_RANK.get(w.verdict, 0)).verdict


def _summary(
    overall: str,
    windows: list[AdviceWindow],
    *,
    sport: Sport,
    level: Level,
    session_h: float,
) -> str:
    if overall == "no" or not windows:
        return f"No rideable {sport.value} window for {level.value} in this forecast."
    top = windows[0]
    kite = (
        f"{top.owned_kite_m2:g} m²"
        if top.owned_kite_m2 is not None
        else (f"~{top.kite_m2:g} m²" if top.kite_m2 else "kite n/a")
    )
    suit = top.owned_wetsuit or top.wetsuit or "suit n/a"
    return (
        f"{overall.upper()}: {top.start}–{top.end} · "
        f"{top.wind_kn:g} kt"
        + (f" gust {top.gust_kn:g}" if top.gust_kn else "")
        + f" · {kite} · {suit} · {session_h:g}h"
    )


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.isoformat().replace("+00:00", "Z")
