"""Weekend ranking helpers (pure)."""

from __future__ import annotations

from guru.models.advice import (
    AdviceReport,
    AdviceWindow,
    ScheduleSlot,
    WeekendSpotAdvice,
)
from guru.rider import voice
from guru.rider.sizing import LONG_DRIVE_KM, NEAR_DRIVE_KM
from guru.rider.weekend_window import slot_is_kite_weekend_day

__all__ = (
    "filter_schedule_by_day",
    "home_vs_far_line",
    "model_agree_by_day",
    "parse_filter_day",
    "pick_schedule",
    "score_spot",
    "slot_rank",
    "slot_summary",
    "weekend_summary_text",
)

_VERDICT_RANK = {"go": 2, "marginal": 1, "no": 0, "incomplete": -1}

_WEEKDAYS = {
    "mon": "Mon",
    "monday": "Mon",
    "tue": "Tue",
    "tues": "Tue",
    "tuesday": "Tue",
    "wed": "Wed",
    "wednesday": "Wed",
    "thu": "Thu",
    "thur": "Thu",
    "thurs": "Thu",
    "thursday": "Thu",
    "fri": "Fri",
    "friday": "Fri",
    "sat": "Sat",
    "saturday": "Sat",
    "sun": "Sun",
    "sunday": "Sun",
}


def parse_filter_day(raw: str | None) -> tuple[str | None, str | None]:
    """Return (weekday_abbrev|weekend|None, iso_date|None)."""
    if not raw:
        return None, None
    text = raw.strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return None, text[:10]
    key = text.lower().rstrip(".")
    if key in {"weekend", "sat-sun", "satsun", "we"}:
        return "weekend", None
    return _WEEKDAYS.get(key), None


def filter_schedule_by_day(
    schedule: list[ScheduleSlot],
    *,
    weekday: str | None = None,
    iso_day: str | None = None,
) -> list[ScheduleSlot]:
    if iso_day:
        return [s for s in schedule if s.day == iso_day]
    if weekday == "weekend":
        return [s for s in schedule if slot_is_kite_weekend_day(s)]
    if weekday:
        return [s for s in schedule if s.weekday == weekday]
    return schedule


def model_agree_by_day(advices: list[AdviceReport]) -> dict[str, int]:
    """Count how many top models have a GO on each UTC day."""
    counts: dict[str, int] = {}
    for adv in advices:
        days = {w.start[:10] for w in adv.windows if w.verdict == "go"}
        for d in days:
            counts[d] = counts.get(d, 0) + 1
    return counts


def home_vs_far_line(results: list[WeekendSpotAdvice]) -> str | None:
    near = [
        r
        for r in results
        if r.drive_km is not None and r.drive_km <= NEAR_DRIVE_KM
    ]
    far = [
        r
        for r in results
        if r.drive_km is not None and r.drive_km > LONG_DRIVE_KM and r.verdict == "go"
    ]
    if not near or not far:
        return None
    n, f = near[0], far[0]
    return (
        f"Home {n.name} ({n.drive_km:g} km, {n.verdict}) vs far {f.name} "
        f"({f.drive_km:g} km, GO) -- report both; far only on clear SEND IT"
    )


def slot_summary(w: AdviceWindow, agree: int) -> str:
    kite = (
        f"{w.owned_kite_m2:g} m2"
        if w.owned_kite_m2 is not None
        else (f"~{w.kite_m2:g} m2" if w.kite_m2 else "kite n/a")
    )
    return voice.slot_line(
        verdict=w.verdict,
        start=w.start,
        end=w.end,
        wind_kn=w.wind_kn,
        gust_kn=w.gust_kn,
        stars=w.rating,
        kite=kite,
        agree=agree,
    )


def score_spot(
    verdict: str,
    drive_km: float | None,
    *,
    model_agree: int = 1,
) -> float:
    base = float(_VERDICT_RANK.get(verdict, 0)) * 100.0
    base += model_agree * 15.0
    if drive_km is None:
        return base
    if drive_km <= NEAR_DRIVE_KM:
        base += 25.0
    return base - drive_km


def slot_rank(w: AdviceWindow, drive: float | None, agree: int) -> float:
    base = float(_VERDICT_RANK.get(w.verdict, 0)) * 100.0
    base += agree * 15.0
    dur = w.hours_usable or 0.0
    base += min(dur, 6.0) * 3.0  # prefer longest usable window
    if drive is not None:
        if drive <= NEAR_DRIVE_KM:
            base += 25.0
        base -= drive
    return base


def pick_schedule(
    candidates: list[tuple[str, ScheduleSlot, float]],
) -> list[ScheduleSlot]:
    """One best slot per UTC day, chronological."""
    best: dict[str, tuple[ScheduleSlot, float]] = {}
    for day, slot, rank in candidates:
        cur = best.get(day)
        if cur is None or rank > cur[1]:
            best[day] = (slot, rank)
    return [best[d][0] for d in sorted(best.keys())]


def weekend_summary_text(
    overall: str,
    schedule: list[ScheduleSlot],
    results: list[WeekendSpotAdvice],
) -> str:
    if schedule:
        lead = schedule[0]
        days = ", ".join(f"{s.weekday} {s.name}" for s in schedule[:4])
        return voice.weekend_summary(
            overall=overall,
            lead_weekday=lead.weekday,
            lead_name=lead.name,
            lead_drive=lead.drive_km,
            lead_line=lead.summary,
            plan_days=days,
        )
    if results:
        top = results[0]
        return voice.weekend_summary(
            overall=overall,
            lead_weekday=None,
            lead_name=None,
            lead_drive=None,
            lead_line=None,
            plan_days=None,
            top_name=top.name,
            top_id=top.spot_id,
            top_drive=top.drive_km,
            top_line=top.summary,
        )
    return voice.weekend_summary(
        overall=overall,
        lead_weekday=None,
        lead_name=None,
        lead_drive=None,
        lead_line=None,
        plan_days=None,
    )
