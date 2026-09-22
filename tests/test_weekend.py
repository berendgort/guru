"""Weekend report structure (offline, no network scan)."""

from __future__ import annotations

from guru.models.advice import ScheduleSlot
from guru.models.profile import Level, RiderProfile, Sport
from guru.rider.weekend_rank import pick_schedule, score_spot


def test_weekend_score_prefers_go_nearby() -> None:
    assert score_spot("go", 20) > score_spot("go", 100)
    assert score_spot("go", 100) > score_spot("marginal", 100)
    assert score_spot("go", 50, model_agree=3) > score_spot("go", 50, model_agree=1)
    # Soft <1h boost can beat a farther GO of equal model agree
    assert score_spot("go", 40) > score_spot("go", 80)


def test_pick_schedule_one_per_day() -> None:
    a = ScheduleSlot(
        day="2026-09-24",
        weekday="Thu",
        start="2026-09-24T11:00:00Z",
        end="2026-09-24T14:00:00Z",
        spot_id=1,
        name="Near",
        drive_km=5,
        verdict="go",
        wind_kn=12,
        model_agree=2,
        summary="a",
    )
    b = ScheduleSlot(
        day="2026-09-24",
        weekday="Thu",
        start="2026-09-24T12:00:00Z",
        end="2026-09-24T13:00:00Z",
        spot_id=2,
        name="Far",
        drive_km=80,
        verdict="marginal",
        wind_kn=10,
        model_agree=1,
        summary="b",
    )
    c = ScheduleSlot(
        day="2026-09-25",
        weekday="Fri",
        start="2026-09-25T11:00:00Z",
        end="2026-09-25T13:00:00Z",
        spot_id=1,
        name="Near",
        drive_km=5,
        verdict="go",
        wind_kn=14,
        model_agree=3,
        summary="c",
    )
    out = pick_schedule(
        [
            ("2026-09-24", a, 200.0),
            ("2026-09-24", b, 50.0),
            ("2026-09-25", c, 210.0),
        ]
    )
    assert len(out) == 2
    assert out[0].name == "Near"
    assert out[0].day == "2026-09-24"
    assert out[1].day == "2026-09-25"


def test_range_ready() -> None:
    p = RiderProfile(
        sport=Sport.KITEFOIL,
        weight_kg=78,
        level=Level.INTERMEDIATE,
        kites_m2=[9, 12],
        wetsuits=["3/2"],
        home_lat=41.39,
        home_lon=2.17,
        drive_km=200,
        range_label="Trabucador → Leucate",
    )
    assert p.is_ready()
    assert p.is_range_ready()
    bare = RiderProfile(
        sport=Sport.KITESURF,
        weight_kg=70,
        level=Level.INTERMEDIATE,
        kites_m2=[10],
        wetsuits=["3/2"],
    )
    assert bare.missing_range_fields()
    assert "level" not in bare.missing_fields()
    no_level = RiderProfile(
        sport=Sport.KITESURF, weight_kg=70, kites_m2=[10], wetsuits=["3/2"]
    )
    assert "level" in no_level.missing_fields()
