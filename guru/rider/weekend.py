"""Drive-range spot scanner -- ``where`` (~3d) and ``weekend`` (Fri eve-Sun)."""

from __future__ import annotations

from datetime import datetime, timezone

from guru.models.advice import (
    DEFAULT_WEEKEND_HOURS,
    DEFAULT_WHERE_HOURS,
    ScanMode,
    ScheduleSlot,
    WeekendReport,
    WeekendSpotAdvice,
)
from guru.models.profile import RiderProfile
from guru.rider import voice
from guru.rider.weekend_collect import collect_scan_rows
from guru.rider.weekend_rank import (
    filter_schedule_by_day,
    home_vs_far_line,
    parse_filter_day,
    pick_schedule,
    weekend_summary_text,
)
from guru.rider.weekend_spots import candidate_spots
from guru.rider.weekend_window import (
    filter_day_candidates_to_window,
    hours_to_cover,
    next_kite_weekend,
)
from guru.search.blend import model_info_full
from guru.search.sst import SST_SOURCE, fetch_sst_many

__all__ = (
    "DEFAULT_TOP_MODELS",
    "DEFAULT_WEEKEND_HOURS",
    "DEFAULT_WHERE_HOURS",
    "candidate_spots",
    "scan_weekend",
)

DEFAULT_TOP_MODELS = 3


def scan_weekend(
    profile: RiderProfile,
    *,
    hours: int | None = None,
    limit_spots: int = 8,
    top_models: int = DEFAULT_TOP_MODELS,
    filter_day: str | None = None,
    mode: ScanMode = "where",
    now: datetime | None = None,
) -> WeekendReport:
    """Rank spots + schedule. ``mode=weekend`` -> next Fri eve / Sat / Sun."""
    if mode not in ("where", "weekend"):
        raise ValueError(f"mode must be 'where' or 'weekend', got {mode!r}")
    now = now or datetime.now(tz=timezone.utc)
    weekend_start = weekend_end = None
    if mode == "weekend":
        weekend_start, weekend_end = next_kite_weekend(now)
        if hours is None:
            hours = hours_to_cover(now, weekend_end)
        filter_day = filter_day or "weekend"
    elif hours is None:
        hours = DEFAULT_WHERE_HOURS

    thinking = voice.thinking_headers(
        hours=hours,
        top_models=top_models,
        range_label=profile.range_label,
    ) + voice.checklist(gusty=False, drive_km=profile.drive_km)
    if mode == "weekend" and weekend_start and weekend_end:
        thinking.insert(
            0,
            f"Next kite weekend: Fri eve {weekend_start.date()} -> "
            f"Sun {weekend_end.date()} (WINDGURU_DEFAULT)",
        )

    missing = profile.missing_fields() + profile.missing_range_fields()
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
            mode=mode,
            weekend_start=weekend_start.isoformat() if weekend_start else None,
            weekend_end=weekend_end.isoformat() if weekend_end else None,
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
    shared_models = model_info_full() if candidates else None

    results, day_candidates, coverage, uncertain = collect_scan_rows(
        candidates,
        profile,
        hours=hours,
        top_models=top_models,
        shared_models=shared_models,
        sst_map=sst_map,
        mode=mode,
        weekend_start=weekend_start,
        weekend_end=weekend_end,
        thinking=thinking,
    )
    # Filter BEFORE pick_schedule so a strong Fri morning cannot eclipse Fri eve.
    if mode == "weekend" and weekend_start and weekend_end:
        day_candidates = filter_day_candidates_to_window(
            day_candidates, weekend_start, weekend_end
        )
    schedule = pick_schedule(day_candidates)
    if mode == "weekend" and weekend_start and weekend_end:
        if schedule:
            keep = {s.spot_id for s in schedule}
            results = [r for r in results if r.spot_id in keep] or results
        else:
            results = []
            thinking.append(
                "No Fri-eve/Sat/Sun windows in range yet "
                "(high-% models may not reach the weekend)."
            )
    else:
        schedule, results, thinking = _apply_day_filter(
            filter_day, schedule, results, thinking
        )

    overall = results[0].verdict if results else "no"
    if uncertain and (overall in {"go", "marginal"} or not schedule):
        overall = "uncertain"
    compare = home_vs_far_line(results)
    if compare:
        thinking.append(compare)

    summary = weekend_summary_text(overall, schedule, results)
    if uncertain and coverage and coverage.get("note"):
        summary = f"{summary} -- {coverage['note']}"

    return WeekendReport(
        verdict=overall,
        range_label=profile.range_label,
        home_lat=profile.home_lat,
        home_lon=profile.home_lon,
        drive_km=profile.drive_km,
        hours=hours,
        top_models=top_models,
        filter_day=filter_day,
        mode=mode,
        weekend_start=weekend_start.isoformat() if weekend_start else None,
        weekend_end=weekend_end.isoformat() if weekend_end else None,
        uncertain=uncertain,
        coverage=coverage,
        spots=results,
        schedule=schedule,
        missing_profile=[],
        summary=summary,
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
