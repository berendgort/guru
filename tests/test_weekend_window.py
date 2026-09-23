"""Next kite-weekend window + coverage (offline)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from guru.models.advice import ScheduleSlot
from guru.models.blend import BlendWeight
from guru.models.forecast import Forecast, ForecastHour, Spot
from guru.rider.weekend_rank import pick_schedule
from guru.rider.weekend_window import (
    filter_day_candidates_to_window,
    filter_slots_to_window,
    forecast_reaches,
    hours_to_cover,
    in_kite_weekend,
    model_weekend_coverage,
    next_kite_weekend,
)


def test_fri_morning_is_not_yet_kite_weekend() -> None:
    """Friday 10:00 UTC -> next_kite_weekend still starts Fri 15:00 same day."""
    now = datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)
    fri, sun = next_kite_weekend(now)
    assert fri == datetime(2026, 9, 25, 15, 0, tzinfo=timezone.utc)
    assert sun.date().isoformat() == "2026-09-27"
    assert in_kite_weekend(now, fri, sun) is False


def test_next_kite_weekend_from_wednesday() -> None:
    now = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)  # Wed
    fri, sun = next_kite_weekend(now)
    assert fri == datetime(2026, 9, 25, 15, 0, tzinfo=timezone.utc)
    assert sun.date().isoformat() == "2026-09-27"
    assert hours_to_cover(now, sun) >= 48


def test_filter_schedule_weekend_uses_shared_fri_eve_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from guru.rider import weekend_window as ww
    from guru.rider.weekend_rank import filter_schedule_by_day

    slots = [
        ScheduleSlot(
            day="2026-09-25",
            weekday="Fri",
            start="2026-09-25T14:00:00+00:00",
            end="2026-09-25T15:00:00+00:00",
            spot_id=1,
            name="A",
            verdict="go",
        ),
        ScheduleSlot(
            day="2026-09-25",
            weekday="Fri",
            start="2026-09-25T16:00:00+00:00",
            end="2026-09-25T18:00:00+00:00",
            spot_id=1,
            name="A",
            verdict="go",
        ),
    ]
    kept = filter_schedule_by_day(slots, weekday="weekend")
    assert len(kept) == 1
    assert kept[0].start.startswith("2026-09-25T16")
    monkeypatch.setattr(ww, "FRI_EVENING_HOUR_UTC", 17)
    assert filter_schedule_by_day(slots, weekday="weekend") == []


def test_next_kite_weekend_already_saturday() -> None:
    now = datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)  # Sat
    fri, sun = next_kite_weekend(now)
    assert fri.date().isoformat() == "2026-09-25"
    assert sun.date().isoformat() == "2026-09-27"


def test_in_kite_weekend_fri_evening_only() -> None:
    fri, sun = next_kite_weekend(datetime(2026, 9, 23, tzinfo=timezone.utc))
    morning = datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)
    evening = datetime(2026, 9, 25, 16, 0, tzinfo=timezone.utc)
    assert in_kite_weekend(morning, fri, sun) is False
    assert in_kite_weekend(evening, fri, sun) is True


def test_filter_slots_fri_eve() -> None:
    fri, sun = next_kite_weekend(datetime(2026, 9, 23, tzinfo=timezone.utc))
    slots = [
        ScheduleSlot(
            day="2026-09-25",
            weekday="Fri",
            start="2026-09-25T10:00:00+00:00",
            end="2026-09-25T12:00:00+00:00",
            spot_id=1,
            name="A",
            verdict="go",
        ),
        ScheduleSlot(
            day="2026-09-25",
            weekday="Fri",
            start="2026-09-25T17:00:00+00:00",
            end="2026-09-25T19:00:00+00:00",
            spot_id=1,
            name="A",
            verdict="go",
        ),
        ScheduleSlot(
            day="2026-09-26",
            weekday="Sat",
            start="2026-09-26T11:00:00+00:00",
            end="2026-09-26T14:00:00+00:00",
            spot_id=1,
            name="A",
            verdict="go",
        ),
    ]
    out = filter_slots_to_window(slots, fri, sun)
    assert len(out) == 2
    assert out[0].start.startswith("2026-09-25T17")
    assert out[1].weekday == "Sat"


def test_pick_schedule_keeps_fri_evening_not_morning() -> None:
    """Strong Fri morning must not eclipse Fri evening when filtered first."""
    morning = ScheduleSlot(
        day="2026-09-25",
        weekday="Fri",
        start="2026-09-25T10:00:00+00:00",
        end="2026-09-25T12:00:00+00:00",
        spot_id=1,
        name="Near",
        drive_km=5,
        verdict="go",
        wind_kn=18,
        model_agree=3,
        summary="am",
    )
    evening = ScheduleSlot(
        day="2026-09-25",
        weekday="Fri",
        start="2026-09-25T17:00:00+00:00",
        end="2026-09-25T19:00:00+00:00",
        spot_id=1,
        name="Near",
        drive_km=5,
        verdict="go",
        wind_kn=14,
        model_agree=2,
        summary="pm",
    )
    fri, sun = next_kite_weekend(datetime(2026, 9, 23, tzinfo=timezone.utc))
    candidates = [
        ("2026-09-25", morning, 250.0),
        ("2026-09-25", evening, 200.0),
    ]
    # Bug class: pick then filter drops Friday entirely.
    wrong = filter_slots_to_window(pick_schedule(candidates), fri, sun)
    assert wrong == []
    # Fix: filter candidates, then pick.
    out = pick_schedule(filter_day_candidates_to_window(candidates, fri, sun))
    assert len(out) == 1
    assert out[0].start.startswith("2026-09-25T17")


def _fc(last_iso: str, model_id: int = 3) -> Forecast:
    last = datetime.fromisoformat(last_iso.replace("Z", "+00:00"))
    return Forecast(
        spot=Spot(id=1, name="T"),
        model=f"m{model_id}",
        model_id=model_id,
        hours=[ForecastHour(hour=0, time=last, wind_kn=12)],
    )


def test_coverage_uncertain_when_hires_short() -> None:
    fri = datetime(2026, 9, 25, 15, 0, tzinfo=timezone.utc)
    sun = datetime(2026, 9, 27, 23, 59, tzinfo=timezone.utc)
    models = [
        BlendWeight(
            id_model=52, name="AROME", weight=0.5, weight_pct=50.0, rank=1
        ),
        BlendWeight(
            id_model=3, name="GFS", weight=0.3, weight_pct=30.0, rank=2
        ),
        BlendWeight(
            id_model=10, name="ICON", weight=0.2, weight_pct=20.0, rank=3
        ),
    ]
    forecasts = [
        _fc("2026-09-24T18:00:00Z", 52),  # stops Thu
        _fc("2026-09-28T00:00:00Z", 3),
        _fc("2026-09-28T00:00:00Z", 10),
    ]
    cov = model_weekend_coverage(
        models, forecasts, weekend_start=fri, weekend_end=sun
    )
    assert cov["uncertain"] is True
    assert "UNCERTAIN" in cov["note"]
    assert forecast_reaches(forecasts[0], fri) is False
    assert forecast_reaches(forecasts[1], fri) is True
