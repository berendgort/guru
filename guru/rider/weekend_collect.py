"""Collect ranked spots + schedule candidates from a where/weekend scan."""

from __future__ import annotations

__all__ = ("collect_scan_rows",)

from datetime import datetime
from typing import Any

from guru.models.advice import (
    AdviceWindow,
    ScanMode,
    ScheduleSlot,
    WeekendSpotAdvice,
)
from guru.models.profile import RiderProfile
from guru.rider.advice import advise_forecast
from guru.rider.weekend_rank import (
    model_agree_by_day,
    score_spot,
    slot_rank,
    slot_summary,
)
from guru.rider.weekend_spots import long_drive_ok, weekday_label
from guru.rider.weekend_window import (
    in_kite_weekend,
    model_weekend_coverage,
    parse_iso_utc,
)
from guru.search.blend import get_best_forecast


def collect_scan_rows(
    candidates: list[tuple[Any, float | None]],
    profile: RiderProfile,
    *,
    hours: int,
    top_models: int,
    shared_models: dict[str, Any] | None,
    sst_map: dict[tuple[float, float], float | None],
    mode: ScanMode,
    weekend_start: datetime | None,
    weekend_end: datetime | None,
    thinking: list[str],
) -> tuple[
    list[WeekendSpotAdvice],
    list[tuple[str, ScheduleSlot, float]],
    dict[str, Any] | None,
    bool,
]:
    results: list[WeekendSpotAdvice] = []
    day_candidates: list[tuple[str, ScheduleSlot, float]] = []
    coverage: dict[str, Any] | None = None
    uncertain = False
    coverage_done = False
    saw_forecast = False

    for spot, drive in candidates:
        best = get_best_forecast(
            spot.id, top=top_models, hours=hours, model_info=shared_models
        )
        if not best.forecasts:
            continue
        saw_forecast = True
        if (
            mode == "weekend"
            and not coverage_done
            and weekend_start is not None
            and weekend_end is not None
        ):
            coverage = model_weekend_coverage(
                best.models,
                best.forecasts,
                weekend_start=weekend_start,
                weekend_end=weekend_end,
            )
            uncertain = bool(coverage.get("uncertain"))
            thinking.append(str(coverage.get("note") or ""))
            coverage_done = True

        sst_c = (
            sst_map.get((float(spot.lat), float(spot.lon)))
            if spot.lat is not None and spot.lon is not None
            else None
        )
        model_advices = [
            advise_forecast(fc, profile, drive_km=drive, max_windows=12, sst_c=sst_c)
            for fc in best.forecasts
        ]
        agree_by_day = model_agree_by_day(model_advices)
        windows = _windows_for_mode(
            model_advices[0].windows, mode, weekend_start, weekend_end
        )
        if not windows:
            continue
        windows.sort(
            key=lambda w: -slot_rank(
                w, drive, agree_by_day.get(w.start[:10], 1)
            )
        )
        lead = windows[0]
        primary = model_advices[0]
        if lead.verdict in {"no", "incomplete"}:
            continue
        if not long_drive_ok(drive, verdict=lead.verdict, windows=windows):
            continue

        day_key = lead.start[:10]
        agree = agree_by_day.get(day_key, 1)
        score = score_spot(lead.verdict, drive, model_agree=agree)
        drive_r = round(drive, 1) if drive is not None else None

        results.append(
            WeekendSpotAdvice(
                spot_id=spot.id,
                name=spot.name,
                lat=spot.lat,
                lon=spot.lon,
                drive_km=drive_r,
                verdict=lead.verdict,
                summary=primary.summary,
                best_window=lead,
                model=primary.model,
                model_agree=agree,
                score=score,
                sst_c=sst_c,
            )
        )

        for w in windows:
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
                summary=slot_summary(w, a),
                hours_usable=w.hours_usable,
            )
            day_candidates.append((d, slot, slot_rank(w, drive, a)))

    if mode == "weekend" and not saw_forecast:
        uncertain = True
        thinking.append(
            "UNCERTAIN: no WINDGURU_DEFAULT forecasts returned for this range."
        )

    results.sort(
        key=lambda r: (-r.score, r.drive_km if r.drive_km is not None else 999)
    )
    return results, day_candidates, coverage, uncertain


def _windows_for_mode(
    windows: list[AdviceWindow],
    mode: ScanMode,
    weekend_start: datetime | None,
    weekend_end: datetime | None,
) -> list[AdviceWindow]:
    if mode != "weekend" or weekend_start is None or weekend_end is None:
        return list(windows)
    return [w for w in windows if _window_in_weekend(w, weekend_start, weekend_end)]


def _window_in_weekend(
    window: AdviceWindow, start: datetime, end: datetime
) -> bool:
    dt = parse_iso_utc(window.start)
    return dt is not None and in_kite_weekend(dt, start, end)
