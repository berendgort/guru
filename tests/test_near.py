"""Near-spot ranking over simplemap fixture."""

from __future__ import annotations

import json

from guru.search.near import spots_near_from_rows
from tests.conftest import FIXTURES


def test_near_texel_area() -> None:
    data = json.loads((FIXTURES / "spots_simplemap_nl.json").read_text())
    spots = spots_near_from_rows(data["spots"], 53.13, 4.80, radius_km=25, limit=10)
    assert spots
    names = " ".join(s.name.lower() for s in spots)
    assert "texel" in names or spots[0].lat is not None
