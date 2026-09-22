"""Weekend / drive-range spot scanner — 'where can I kite?'."""

from __future__ import annotations

from datetime import datetime

from guru.models.forecast import Spot
from guru.models.profile import (
    AdviceWindow,
    RiderProfile,
    ScheduleSlot,
    WeekendReport,
    WeekendSpotAdvice,
)
from guru.rider.advice import advise_forecast
from guru.rider.sizing import kiter_checklist
from guru.search.blend import get_best_forecast
from guru.search.near import haversine_km, spots_near
from guru.search.spots import get_spot

_VERDICT_RANK = {"go": 2, "marginal": 1, "no": 0, "incomplete": -1}

# Free-model horizon that covers mid-week asks without “what about Thursday?”
DEFAULT_WEEKEND_HOURS = 96
DEFAULT_TOP_MODELS = 3


def candidate_spots(
    profile: RiderProfile,
    *,
    limit: int = 12,
) -> list[tuple[Spot, float | None]]:
    """Spots in drive range + explicit home_spots. Returns (spot, drive_km)."""
    by_id: dict[int, tuple[Spot, float | None]] = {}

    if profile.home_lat is not None and profile.home_lon is not None:
        radius = float(profile.drive_km or 80.0)
        near = spots_near(
            profile.home_lat, profile.home_lon, radius_km=radius, limit=limit
        )
        for s in near:
            d = None
            if s.lat is not None and s.lon is not None:
                d = haversine_km(profile.home_lat, profile.home_lon, s.lat, s.lon)
            by_id[s.id] = (s, d)

    for sid in profile.home_spots:
        if sid in by_id:
            continue
        spot = get_spot(sid)
        d = None
        if (
            profile.home_lat is not None
            and profile.home_lon is not None
            and spot.lat is not None
            and spot.lon is not None
        ):
            d = haversine_km(
                profile.home_lat, profile.home_lon, spot.lat, spot.lon
            )
        by_id[sid] = (spot, d)

    rows = list(by_id.values())
    rows.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else 9999))
    return rows[:limit]


def scan_weekend(
    profile: RiderProfile,
    *,
    hours: int = DEFAULT_WEEKEND_HOURS,
    limit_spots: int = 8,
    top_models: int = DEFAULT_TOP_MODELS,
) -> WeekendReport:
    """Rank rideable spots + day-by-day schedule (top WINDGURU_DEFAULT models)."""
    missing = profile.missing_fields() + profile.missing_range_fields()
    thinking = kiter_checklist(gusty=False, drive_km=profile.drive_km)
    thinking.insert(
        0,
        f"Scan drive range over ~{hours}h with top {top_models} models; "
        "emit a day schedule so riders see Thu/Fri without re-asking",
    )
    thinking.insert(
        0,
        "Farther trips need clearer GO; prefer model agreement",
    )
    if profile.range_label:
        thinking.insert(0, f"Home range: {profile.range_label}")

    if missing:
        return WeekendReport(
            verdict="incomplete",
            range_label=profile.range_label,
            home_lat=profile.home_lat,
            home_lon=profile.home_lon,
            drive_km=profile.drive_km,
            hours=hours,
            top_models=top_models,
            missing_profile=missing,
            summary=f"Need profile + home range — missing: {', '.join(missing)}",
            thinking=thinking,
        )

    candidates = candidate_spots(profile, limit=limit_spots)
    results: list[WeekendSpotAdvice] = []
    # (day, slot_candidate dict pieces) for schedule build
    day_candidates: list[tuple[str, ScheduleSlot, float]] = []

    for spot, drive in candidates:
        best = get_best_forecast(spot.id, top=top_models, hours=hours)
        if not best.forecasts:
            continue

        # Advise each top model; primary = highest-weight model
        model_advices = []
        for fc in best.forecasts:
            model_advices.append(
                advise_forecast(fc, profile, drive_km=drive, max_windows=12)
            )
        primary = model_advices[0]
        if primary.verdict in {"no", "incomplete"}:
            continue
        if drive is not None and drive > 90 and primary.verdict != "go":
            continue

        agree_by_day = _model_agree_by_day(model_advices)
        window = primary.windows[0] if primary.windows else None
        day_key = _day_key(window.start) if window else ""
        agree = agree_by_day.get(day_key, 1) if day_key else 1
        score = _score(primary.verdict, drive, model_agree=agree)

        results.append(
            WeekendSpotAdvice(
                spot_id=spot.id,
                name=spot.name,
                lat=spot.lat,
                lon=spot.lon,
                drive_km=round(drive, 1) if drive is not None else None,
                verdict=primary.verdict,
                summary=primary.summary,
                best_window=window,
                model=primary.model,
                model_agree=agree,
                score=score,
            )
        )

        for adv in model_advices[:1]:  # schedule from primary model windows
            for w in adv.windows:
                if w.verdict not in {"go", "marginal"}:
                    continue
                if drive is not None and drive > 90 and w.verdict != "go":
                    continue
                d = _day_key(w.start)
                a = agree_by_day.get(d, 1)
                slot = ScheduleSlot(
                    day=d,
                    weekday=_weekday(w.start),
                    start=w.start,
                    end=w.end,
                    spot_id=spot.id,
                    name=spot.name,
                    drive_km=round(drive, 1) if drive is not None else None,
                    verdict=w.verdict,
                    wind_kn=w.wind_kn,
                    gust_kn=w.gust_kn,
                    owned_kite_m2=w.owned_kite_m2,
                    owned_wetsuit=w.owned_wetsuit or w.wetsuit,
                    model_agree=a,
                    summary=_slot_summary(spot.name, w, a),
                )
                day_candidates.append((d, slot, _slot_rank(w, drive, a)))

    results.sort(
        key=lambda r: (-r.score, r.drive_km if r.drive_km is not None else 999)
    )
    schedule = _pick_schedule(day_candidates)

    overall = results[0].verdict if results else "no"
    if schedule:
        # Prefer schedule lead for human summary (covers whole horizon)
        lead = schedule[0]
        days = ", ".join(f"{s.weekday} {s.name}" for s in schedule[:4])
        summary = (
            f"{overall.upper()} · next: {lead.weekday} {lead.name} "
            f"~{lead.drive_km or '?'} km — {lead.summary} "
            f"| plan: {days}"
        )
    elif results:
        top = results[0]
        summary = (
            f"{overall.upper()}: {top.name} ({top.spot_id}) "
            f"~{top.drive_km or '?'} km — {top.summary}"
        )
    else:
        summary = "No rideable spot in your drive range for this forecast window."

    return WeekendReport(
        verdict=overall,
        range_label=profile.range_label,
        home_lat=profile.home_lat,
        home_lon=profile.home_lon,
        drive_km=profile.drive_km,
        hours=hours,
        top_models=top_models,
        spots=results,
        schedule=schedule,
        missing_profile=[],
        summary=summary,
        thinking=thinking,
    )


def _model_agree_by_day(advices: list) -> dict[str, int]:
    """Count how many of the top models have go/marginal on each UTC day."""
    counts: dict[str, int] = {}
    for adv in advices:
        days = {
            _day_key(w.start)
            for w in adv.windows
            if w.verdict in {"go", "marginal"}
        }
        for d in days:
            counts[d] = counts.get(d, 0) + 1
    return counts


def _day_key(iso: str) -> str:
    return iso[:10]


def _weekday(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso[:10]
    return dt.strftime("%a")


def _slot_summary(name: str, w: AdviceWindow, agree: int) -> str:
    kite = (
        f"{w.owned_kite_m2:g} m²"
        if w.owned_kite_m2 is not None
        else (f"~{w.kite_m2:g} m²" if w.kite_m2 else "kite n/a")
    )
    gust = f" gust {w.gust_kn:g}" if w.gust_kn is not None else ""
    return (
        f"{w.verdict.upper()}: {w.start}–{w.end} · {w.wind_kn:g} kt{gust} · "
        f"{kite} · {agree}/3 models"
    )


def _slot_rank(w: AdviceWindow, drive: float | None, agree: int) -> float:
    base = float(_VERDICT_RANK.get(w.verdict, 0)) * 100.0
    base += agree * 15.0
    if drive is not None:
        base -= drive
    return base


def _pick_schedule(
    candidates: list[tuple[str, ScheduleSlot, float]],
) -> list[ScheduleSlot]:
    """One best slot per UTC day, chronological."""
    best: dict[str, tuple[ScheduleSlot, float]] = {}
    for day, slot, rank in candidates:
        cur = best.get(day)
        if cur is None or rank > cur[1]:
            best[day] = (slot, rank)
    return [best[d][0] for d in sorted(best.keys())]


def _score(
    verdict: str,
    drive_km: float | None,
    *,
    model_agree: int = 1,
) -> float:
    base = float(_VERDICT_RANK.get(verdict, 0)) * 100.0
    base += model_agree * 15.0
    if drive_km is None:
        return base
    return base - drive_km
