"""Deferred rider-logic — only ship when robust worldwide."""

## Tide / flat water for foil

Defer. Geometry > API. Ship later only when ALL hold:

1. Curated `tide_sensitive` tags on named lagoons (never infer from lat/lon).
2. Per-spot ride rule (mid–high only, min height, foil vs twin-tip).
3. Keyed source (WorldTides) opt-in via env — never required for core wind.
4. Validated on known lagoons before affecting GO.

Open-Meteo `sea_level_height_msl` is not trusted for inland lagoons.

## Wind direction / OSM coastline

Curated sectors + `guru note "dirs=SW-W offshore=N-NE"` are SHIPPED.
OSM ray-cast = future assist only — never silent NO-GO from guessed geometry.
Ignore Windguru `coast: true/false` for offshore.

## Crowd / lessons / nesting

Out of scope for core.

## SST

SHIPPED via Open-Meteo Marine (`guru/search/sst.py`). Suit uses SST base + air chill bump.
