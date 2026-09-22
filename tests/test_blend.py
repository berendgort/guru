"""Offline blend weight ranking from fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from guru.search.blend import (
    calc_sort_by_weights,
    get_default_blend_settings,
    list_spot_weather_models,
)
from guru.search.blend_math import calc_sort_by_weights as calc_pure

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_castelldefels_top3_matches_high_res_models() -> None:
    data = json.loads((FIXTURES / "forecast_spot_201.json").read_text())
    info = json.loads((FIXTURES / "model_info_full.json").read_text())
    blend = get_default_blend_settings(data)
    assert "WINDGURU DEFAULT" in str(blend.get("name") or "").upper()
    models = list_spot_weather_models(data, info, spot_id=201)
    ranked = calc_sort_by_weights(models, blend, info)
    assert calc_pure(models, blend, info)[0].id_model == ranked[0].id_model
    top_ids = [r.id_model for r in ranked[:3]]
    # High-res local models dominate Castelldefels (captured RE).
    assert top_ids[0] == 52  # AROME-FR 1.3
    assert 109 in top_ids  # HARM-DK
    assert sum(r.weight for r in ranked) == 1.0 or abs(sum(r.weight for r in ranked) - 1.0) < 1e-6


def test_slufter_blend_has_default_preset() -> None:
    data = json.loads((FIXTURES / "forecast_spot_48309.json").read_text())
    blend = get_default_blend_settings(data)
    assert int(blend.get("id_blend_settings") or 0) == 1
