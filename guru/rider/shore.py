"""Shore wind sectors -- curated pack + spot_notes tokens (pure classify)."""

from __future__ import annotations

import json
import re
from importlib import resources
from pathlib import Path
from typing import Any

__all__ = (
    "BEARINGS",
    "classify_shore",
    "load_shore_pack",
    "parse_note_sectors",
    "sectors_for_spot",
)

BEARINGS: tuple[str, ...] = (
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
)
_BEARING_IX = {b: i for i, b in enumerate(BEARINGS)}
_TOKEN_RE = re.compile(
    r"\b(dirs|offshore)\s*=\s*([A-Za-z,\-]+)",
    re.IGNORECASE,
)


def _deg_to_bearing(deg: float) -> str:
    ix = int((deg % 360 + 11.25) // 22.5) % 16
    return BEARINGS[ix]


def _expand_sector(token: str) -> set[str]:
    token = token.strip().upper()
    if not token:
        return set()
    if "-" in token:
        a, b = token.split("-", 1)
        if a not in _BEARING_IX or b not in _BEARING_IX:
            return set()
        ia, ib = _BEARING_IX[a], _BEARING_IX[b]
        out: set[str] = set()
        i = ia
        while True:
            out.add(BEARINGS[i])
            if i == ib:
                break
            i = (i + 1) % 16
        return out
    if token in _BEARING_IX:
        return {token}
    return set()


def _expand_list(raw: str) -> set[str]:
    bits: set[str] = set()
    for part in raw.split(","):
        bits |= _expand_sector(part.strip())
    return bits


def parse_note_sectors(note: str) -> tuple[set[str], set[str], str]:
    """Extract dirs=/offshore= from note; return (preferred, offshore, remainder)."""
    preferred: set[str] = set()
    offshore: set[str] = set()
    remainder = note
    for m in _TOKEN_RE.finditer(note):
        kind, vals = m.group(1).lower(), m.group(2)
        if kind == "dirs":
            preferred |= _expand_list(vals)
        else:
            offshore |= _expand_list(vals)
        remainder = remainder.replace(m.group(0), " ")
    remainder = re.sub(r"\s+", " ", remainder).strip(" ;,")
    return preferred, offshore, remainder


def load_shore_pack() -> dict[str, Any]:
    try:
        root = resources.files("guru.data")
        text = (root / "shore_sectors.json").read_text(encoding="utf-8")
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, AttributeError):
        path = Path(__file__).resolve().parent.parent / "data" / "shore_sectors.json"
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return {}
        return {}


def sectors_for_spot(
    spot_id: int,
    *,
    spot_note: str | None = None,
    pack: dict[str, Any] | None = None,
) -> tuple[set[str], set[str], str]:
    """Merge pack + note. Note wins. Returns (preferred, offshore, source)."""
    pack = pack if pack is not None else load_shore_pack()
    preferred: set[str] = set()
    offshore: set[str] = set()
    source = "unknown"
    entry = (pack.get("sectors") or {}).get(str(spot_id))
    if isinstance(entry, dict):
        if entry.get("dirs"):
            preferred |= _expand_list(str(entry["dirs"]))
        if entry.get("offshore"):
            offshore |= _expand_list(str(entry["offshore"]))
        if preferred or offshore:
            source = "curated"
    if spot_note:
        p2, o2, _ = parse_note_sectors(spot_note)
        if p2 or o2:
            if p2:
                preferred = p2
            if o2:
                offshore = o2
            source = "note"
    return preferred, offshore, source


def classify_shore(
    wind_dir_deg: float | None,
    *,
    preferred: set[str],
    offshore: set[str],
) -> str:
    """preferred | offshore | unknown -- never invent offshore without sectors."""
    if wind_dir_deg is None or (not preferred and not offshore):
        return "unknown"
    bearing = _deg_to_bearing(float(wind_dir_deg))
    if bearing in offshore:
        return "offshore"
    if bearing in preferred:
        return "preferred"
    return "unknown"
