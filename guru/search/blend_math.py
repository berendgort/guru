"""Pure WINDGURU DEFAULT weight math (no I/O) — SPA ``di.calcSortByWeights``."""

from __future__ import annotations

from typing import Any

from guru.models.blend import BlendWeight
from guru.search.exceptions import GuruNotFoundError, GuruParseError

SKIP_MODEL_IDS = {100}


def ri(sensitivity: float, resolution: float) -> float:
    return float(resolution) ** (-2.0 * sensitivity)


def ai(sensitivity: float, age_hours: float) -> float:
    value = 100.0 * (age_hours + 4.0) ** (-0.5 * sensitivity) - 3.0 * sensitivity * age_hours
    return max(0.0, value)


def normalize(
    weights: dict[int, float],
    *,
    target: float = 1.0,
    cap: float = 1.5,
) -> dict[int, float]:
    if not weights:
        return {}
    vals = list(weights.values())
    lo, hi = min(vals), max(vals)
    scale = (2.0 * target / (hi + lo)) if (hi + lo) else 1.0
    if hi * scale > cap:
        scale = cap / hi
    return {k: v * scale for k, v in weights.items()}


def weather_model_ids(
    spot_id: int,
    forecast_spot: dict[str, Any],
    model_info: dict[str, Any],
) -> list[int]:
    spots = forecast_spot.get("spots") or {}
    meta = spots.get(str(spot_id)) or spots.get(spot_id) or {}
    models = meta.get("models") or []
    out: list[int] = []
    for raw in models:
        mid = int(raw)
        if mid in SKIP_MODEL_IDS:
            continue
        row = model_info.get(str(mid)) or {}
        if not row or row.get("wave") or row.get("virtual"):
            continue
        out.append(mid)
    if not out:
        raise GuruNotFoundError(f"No weather models for spot {spot_id}")
    return out


def blend_from_forecast_spot(data: dict[str, Any]) -> dict[str, Any]:
    tabs = data.get("tabs") or []
    if not tabs:
        raise GuruParseError("No forecast tabs")
    blend = tabs[0].get("blend")
    if not isinstance(blend, dict):
        raise GuruParseError("No blend settings on first tab")
    return blend


def calc_sort_by_weights(
    model_ids: list[int],
    blend: dict[str, Any],
    model_info: dict[str, Any],
) -> list[BlendWeight]:
    """Port of SPA ``di.calcSortByWeights``."""
    res_raw = blend.get("res_sensitivity")
    init_raw = blend.get("init_sensitivity")
    res_s = float(res_raw if res_raw is not None else 0.5)
    init_s = float(init_raw if init_raw is not None else 0.5)
    koef_raw = blend.get("model_koef") or {}
    koef = {int(k): float(v) for k, v in koef_raw.items()}

    usable: list[int] = []
    for mid in model_ids:
        row = model_info.get(str(mid)) or {}
        if not row or row.get("initstamp") is None or row.get("resolution") is None:
            continue
        usable.append(mid)
    if not usable:
        raise GuruParseError("No models with init/resolution for blend weights")

    inits = {mid: int(model_info[str(mid)]["initstamp"]) for mid in usable}
    max_init = max(inits.values())

    res_w = normalize(
        {mid: ri(res_s, float(model_info[str(mid)]["resolution"])) for mid in usable}
    )
    init_w = normalize(
        {mid: ai(init_s, max_init / 3600.0 - inits[mid] / 3600.0) for mid in usable}
    )

    raw_rows: list[tuple[int, float, int]] = []
    total = 0.0
    for mid in usable:
        w = res_w[mid] * init_w[mid] * koef.get(mid, 1.0)
        priority = int(model_info[str(mid)].get("priority") or 0)
        raw_rows.append((mid, w, priority))
        total += w

    raw_rows.sort(key=lambda row: (-(row[1] / total if total else 0.0), row[2]))

    out: list[BlendWeight] = []
    for rank, (mid, w, _prio) in enumerate(raw_rows, start=1):
        pct = (w / total) if total else 0.0
        info = model_info[str(mid)]
        res = info.get("resolution")
        out.append(
            BlendWeight(
                id_model=mid,
                name=str(info.get("model_name") or info.get("model") or mid),
                weight=pct,
                weight_pct=round(pct * 100.0, 1),
                rank=rank,
                resolution_km=float(res) if res is not None else None,
                initstamp=inits.get(mid),
            )
        )
    return out
