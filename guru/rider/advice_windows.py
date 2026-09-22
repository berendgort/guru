"""Collapse scored hours into AdviceWindow blocks (pure)."""

from __future__ import annotations

from datetime import datetime

from guru.models.advice import AdviceWindow
from guru.models.forecast import ForecastHour, wind_dir_cardinal
from guru.models.profile import Level, Sport
from guru.models.rating import windguru_rating
from guru.rider import voice
from guru.rider.daylight import PRECIP_SOFT_MM, in_daylight
from guru.rider.sizing import recommend_wetsuit, wind_quality, window_duration_hours

__all__ = ("collapse_windows", "overall_verdict", "summary_line")

_VERDICT_RANK = {"go": 2, "marginal": 1, "no": 0, "incomplete": -1}

ScoredHour = tuple[
    ForecastHour,
    str,
    float | None,
    float | None,
    float | None,
    str | None,
    list[str],
    str,
]


def collapse_windows(
    scored: list[ScoredHour],
    *,
    max_windows: int,
    session_hours: float,
    level: Level,
    sunrise: str | None = None,
    sunset: str | None = None,
    sst_c: float | None = None,
    shore_relation: str | None = None,
    wave_by_hour: dict[int, tuple[float | None, float | None]] | None = None,
) -> list[AdviceWindow]:
    if not scored:
        return []

    day = [r for r in scored if in_daylight(r[0].time, sunrise, sunset)]
    scored = day or scored

    windows: list[AdviceWindow] = []
    block = [scored[0]]
    block_verdict = scored[0][1]

    def flush() -> None:
        nonlocal block
        if not block:
            return
        windows.append(
            _window_from_block(
                block,
                session_hours=session_hours,
                level=level,
                sst_c=sst_c,
                shore_relation=shore_relation,
                wave_by_hour=wave_by_hour,
            )
        )
        block = []

    for i in range(1, len(scored)):
        prev_t = block[-1][0].time
        cur = scored[i]
        contiguous = abs((cur[0].time - prev_t).total_seconds()) <= 3 * 3600
        if cur[1] == block_verdict and contiguous:
            block.append(cur)
        else:
            flush()
            block_verdict = cur[1]
            block = [cur]
    flush()

    windows.sort(
        key=lambda w: (
            -_VERDICT_RANK.get(w.verdict, 0),
            -(1 if (w.hours_usable or 0) >= session_hours else 0),
            -(w.hours_usable or 0.0),
            w.start,
        )
    )
    return windows[:max_windows]


def _window_from_block(
    block: list[ScoredHour],
    *,
    session_hours: float,
    level: Level,
    sst_c: float | None,
    shore_relation: str | None,
    wave_by_hour: dict[int, tuple[float | None, float | None]] | None,
) -> AdviceWindow:
    first, last = block[0][0], block[-1][0]
    hour, verdict, ideal, owned, gap, suit, accessories, note = block[len(block) // 2]
    spread = None
    if hour.gust_kn is not None and hour.wind_kn is not None:
        spread = round(hour.gust_kn - hour.wind_kn, 1)
    rec_suit, _ = recommend_wetsuit(
        hour.temp_c,
        wind_kn=hour.wind_kn,
        session_hours=session_hours,
        level=level,
        sst_c=sst_c,
    )
    rating = windguru_rating(hour.wind_kn, hour.temp_c)
    start, end = _iso(first.time), _iso(last.time)
    hours_u = window_duration_hours(start, end)
    hs_m, period_s = None, None
    if wave_by_hour:
        pair = wave_by_hour.get(int(hour.hour))
        if pair:
            hs_m, period_s = pair
    note = _enrich_note(
        note,
        hour=hour,
        verdict=verdict,
        hours_u=hours_u,
        session_hours=session_hours,
        shore_relation=shore_relation,
        hs_m=hs_m,
        period_s=period_s,
    )
    return AdviceWindow(
        start=start,
        end=end,
        wind_kn=float(hour.wind_kn or 0.0),
        gust_kn=hour.gust_kn,
        gust_spread_kn=spread,
        wind_dir_deg=hour.wind_dir_deg,
        wind_quality=wind_quality(hour.wind_kn, hour.gust_kn),
        kite_m2=ideal,
        owned_kite_m2=owned,
        kite_gap_m2=gap,
        wetsuit=rec_suit,
        owned_wetsuit=suit,
        accessories=accessories,
        verdict=verdict,
        rating_stars=rating.stars,
        rating_cold=rating.cold,
        rating=rating.label,
        note=note,
        hours_usable=round(hours_u, 2),
        precip_mm=hour.precip_mm,
        sst_c=sst_c,
        shore_relation=shore_relation,
        hs_m=hs_m,
        period_s=period_s,
    )


def _enrich_note(
    note: str,
    *,
    hour: ForecastHour,
    verdict: str,
    hours_u: float,
    session_hours: float,
    shore_relation: str | None,
    hs_m: float | None,
    period_s: float | None,
) -> str:
    bits: list[str] = [note] if note else []
    if hours_u + 1e-6 < session_hours and verdict == "go":
        bits.append(f"window {hours_u:g}h < session {session_hours:g}h")
    if hour.precip_mm is not None and hour.precip_mm >= PRECIP_SOFT_MM:
        bits.append(f"precip ~{hour.precip_mm:g} mm")
    if hour.wind_dir_deg is not None:
        bits.append(
            f"dir {wind_dir_cardinal(hour.wind_dir_deg)} {hour.wind_dir_deg:g}"
        )
    if shore_relation and shore_relation != "unknown":
        bits.append(f"shore {shore_relation}")
    if hs_m is not None:
        swell = f"swell ~{hs_m:g} m"
        if period_s is not None:
            swell += f" / {period_s:g}s"
        bits.append(swell)
    return "; ".join(bits)


def overall_verdict(windows: list[AdviceWindow]) -> str:
    if not windows:
        return "no"
    return max(windows, key=lambda w: _VERDICT_RANK.get(w.verdict, 0)).verdict


def summary_line(
    overall: str,
    windows: list[AdviceWindow],
    *,
    sport: Sport,
    level: Level,
    session_h: float,
) -> str:
    if overall == "no" or not windows:
        return voice.advice_summary(
            "no",
            start="",
            end="",
            wind_kn=0,
            gust_kn=None,
            stars="",
            kite="",
            suit="",
            session_h=session_h,
            sport=sport.value,
            level=level.value,
        )
    top = windows[0]
    kite = (
        f"{top.owned_kite_m2:g} m2"
        if top.owned_kite_m2 is not None
        else (f"~{top.kite_m2:g} m2" if top.kite_m2 else "kite n/a")
    )
    suit = top.owned_wetsuit or top.wetsuit or "suit n/a"
    stars = top.rating if top.rating and any(ch.isalnum() or ch == "*" for ch in top.rating) else ""
    return voice.advice_summary(
        overall,
        start=top.start,
        end=top.end,
        wind_kn=top.wind_kn,
        gust_kn=top.gust_kn,
        stars=stars,
        kite=kite,
        suit=suit,
        session_h=session_h,
        sport=sport.value,
        level=level.value,
    )


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.isoformat().replace("+00:00", "Z")
