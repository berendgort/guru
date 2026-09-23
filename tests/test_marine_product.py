"""Daylight, shore sectors, day filter (offline)."""

from __future__ import annotations

from datetime import datetime, timezone

from guru.models.advice import ScheduleSlot
from guru.rider.daylight import in_daylight, parse_hhmm
from guru.rider.shore import classify_shore, parse_note_sectors, sectors_for_spot
from guru.rider.suit import recommend_wetsuit
from guru.rider.weekend_rank import filter_schedule_by_day, parse_filter_day


def test_parse_hhmm() -> None:
    assert parse_hhmm("07:42") == 7 * 60 + 42
    assert parse_hhmm(None) is None


def test_in_daylight() -> None:
    noon = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    night = datetime(2026, 6, 1, 23, 0, tzinfo=timezone.utc)
    assert in_daylight(noon, "07:00", "20:00")
    assert not in_daylight(night, "07:00", "20:00")
    assert in_daylight(night, None, None)  # missing bounds → allow


def test_parse_note_sectors() -> None:
    pref, off, rem = parse_note_sectors("dirs=SW-W offshore=N-NE Bunker dies in NE")
    assert "SW" in pref and "W" in pref
    assert "N" in off and "NE" in off
    assert "Bunker" in rem


def test_classify_offshore() -> None:
    pref, off, _ = parse_note_sectors("dirs=SW-W offshore=N-NE")
    assert classify_shore(20.0, preferred=pref, offshore=off) == "offshore"  # NNE-ish
    assert classify_shore(225.0, preferred=pref, offshore=off) == "preferred"  # SW
    assert classify_shore(90.0, preferred=pref, offshore=off) == "unknown"


def test_sectors_for_spot_pack() -> None:
    pref, off, src = sectors_for_spot(201)
    assert src in {"curated", "unknown"}
    # example pack has offshore N-NE
    if src == "curated":
        assert off


def test_suit_sst_base() -> None:
    label, _ = recommend_wetsuit(28, wind_kn=10, sst_c=12, session_hours=2)
    assert label == "6/4"
    cold, acc = recommend_wetsuit(5, wind_kn=20, sst_c=4, session_hours=2)
    assert cold == "6/4+jacket+gloves+boots"
    assert "gloves" in acc


def test_parse_filter_day() -> None:
    assert parse_filter_day("Thu") == ("Thu", None)
    assert parse_filter_day("thursday") == ("Thu", None)
    assert parse_filter_day("2026-09-25") == (None, "2026-09-25")
    assert parse_filter_day("weekend") == ("weekend", None)


def test_filter_schedule_by_day() -> None:
    slots = [
        ScheduleSlot(
            day="2026-09-24",
            weekday="Thu",
            start="2026-09-24T11:00:00Z",
            end="2026-09-24T14:00:00Z",
            spot_id=1,
            name="A",
            verdict="go",
        ),
        ScheduleSlot(
            day="2026-09-25",
            weekday="Fri",
            start="2026-09-25T11:00:00Z",
            end="2026-09-25T13:00:00Z",
            spot_id=1,
            name="A",
            verdict="go",
        ),
        ScheduleSlot(
            day="2026-09-26",
            weekday="Sat",
            start="2026-09-26T11:00:00Z",
            end="2026-09-26T13:00:00Z",
            spot_id=1,
            name="A",
            verdict="go",
        ),
        ScheduleSlot(
            day="2026-09-25",
            weekday="Fri",
            start="2026-09-25T17:00:00Z",
            end="2026-09-25T19:00:00Z",
            spot_id=1,
            name="A",
            verdict="go",
        ),
    ]
    thu = filter_schedule_by_day(slots, weekday="Thu")
    assert len(thu) == 1 and thu[0].weekday == "Thu"
    we = filter_schedule_by_day(slots, weekday="weekend")
    assert len(we) == 2
    assert {s.weekday for s in we} == {"Fri", "Sat"}
