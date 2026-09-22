"""First-pass rider intake — one efficient ask for agents/Cursor."""

from __future__ import annotations

import re
from typing import Any

# Fields the agent must collect in ONE message (not drip-fed).
INTAKE_FIELDS: list[dict[str, str]] = [
    {
        "key": "sport",
        "ask": "Sport",
        "hint": "kitesurf | kitefoil | surfkite",
    },
    {
        "key": "weight_kg",
        "ask": "Weight (kg)",
        "hint": "e.g. 78",
    },
    {
        "key": "level",
        "ask": "Level",
        "hint": "beginner | intermediate | advanced (default intermediate)",
    },
    {
        "key": "kites_m2",
        "ask": "Kite quiver (m²)",
        "hint": "comma sizes you own, e.g. 7,9,12",
    },
    {
        "key": "boards",
        "ask": "Boards (optional)",
        "hint": 'e.g. "foil 1300, TT 138"',
    },
    {
        "key": "wetsuits",
        "ask": "Wetsuits you own",
        "hint": 'e.g. "3/2,4/3,shorty"',
    },
    {
        "key": "session_hours",
        "ask": "Typical session length (h)",
        "hint": "2, 3, or 4 (kite sessions)",
    },
    {
        "key": "home",
        "ask": "Home base lat,lon",
        "hint": "e.g. 41.39,2.17 (Barcelona)",
    },
    {
        "key": "drive_km",
        "ask": "Max drive (km)",
        "hint": "e.g. 200",
    },
    {
        "key": "range_label",
        "ask": "Drive corridor label",
        "hint": 'e.g. "Trabucador → Leucate"',
    },
]

# Compact reply the user can paste in one message
REPLY_TEMPLATE = (
    "sport=kitefoil weight=78 level=intermediate kites=7,9,12 "
    'wetsuits=3/2,4/3 boards=foil 1300,TT 138 session=3 '
    "home=41.39,2.17 drive_km=200 range=Trabucador → Leucate"
)

AGENT_PROMPT_TO_USER = """\
Quick kite profile (one reply — paste or fill):

• sport: kitesurf / kitefoil / surfkite
• weight_kg · level (beg/int/adv)
• kites m² you own (e.g. 7,9,12)
• boards (optional)
• wetsuits you own (e.g. 3/2,4/3)
• session hours (2–4)
• home lat,lon · max drive_km · range label (e.g. Trabucador → Leucate)

Paste format (edit numbers):
sport=kitefoil weight=78 level=intermediate kites=7,9,12 \\
wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 \\
range=Trabucador → Leucate
"""


def intake_payload(*, needed: bool = True) -> dict[str, Any]:
    """Machine-readable first-pass intake for agents."""
    return {
        "needed": needed,
        "rule": (
            "On first use (profile not ready or not range_ready): show "
            "prompt_to_user ONCE, wait for one reply, then run guru setup. "
            "Do NOT ask fields one-by-one."
        ),
        "prompt_to_user": AGENT_PROMPT_TO_USER.strip(),
        "reply_template": REPLY_TEMPLATE,
        "fields": INTAKE_FIELDS,
        "setup_from_reply": (
            "guru setup --intake '<user paste>' --json"
        ),
    }


def parse_intake_text(raw: str) -> dict[str, Any]:
    """Parse a compact key=value (or key: value) intake line into setup kwargs."""
    text = raw.strip()
    if not text:
        raise ValueError("Empty intake text")

    # Normalize newlines to spaces; allow semicolon separators
    text = re.sub(r"[\n\r]+", " ", text)
    # Split on known keys while keeping values that contain spaces until next key
    keys = (
        "sport",
        "weight",
        "weight_kg",
        "level",
        "kites",
        "kites_m2",
        "boards",
        "wetsuits",
        "session",
        "session_hours",
        "home",
        "home_lat",
        "home_lon",
        "drive",
        "drive_km",
        "range",
        "range_label",
    )
    pattern = re.compile(
        r"(?i)\b(" + "|".join(keys) + r")\s*[=:]\s*",
    )
    parts = pattern.split(text)
    # parts: [preamble, key1, val1, key2, val2, ...]
    if len(parts) < 3:
        raise ValueError(
            "Could not parse intake. Use: sport=kitefoil weight=78 kites=7,9,12 ..."
        )

    kv: dict[str, str] = {}
    i = 1
    while i + 1 < len(parts):
        key = parts[i].lower()
        val = parts[i + 1].strip(" ,;")
        # Trim value at next accidental double-space junk
        kv[key] = val
        i += 2

    out: dict[str, Any] = {}
    if "sport" in kv:
        out["sport"] = kv["sport"].split()[0]
    for src in ("weight_kg", "weight"):
        if src in kv:
            out["weight_kg"] = float(kv[src].split()[0])
            break
    if "level" in kv:
        out["level"] = kv["level"].split()[0]
    for src in ("kites_m2", "kites"):
        if src in kv:
            out["kites_m2"] = [
                float(x) for x in re.split(r"[,;\s]+", kv[src]) if x and _is_float(x)
            ]
            break
    if "boards" in kv:
        out["boards"] = [b.strip() for b in re.split(r"[,;]+", kv["boards"]) if b.strip()]
    if "wetsuits" in kv:
        out["wetsuits"] = [
            w.strip() for w in re.split(r"[,;]+", kv["wetsuits"]) if w.strip()
        ]
    for src in ("session_hours", "session"):
        if src in kv:
            out["session_hours"] = float(kv[src].split()[0])
            break
    if "home" in kv:
        nums = re.findall(r"[-+]?\d*\.?\d+", kv["home"])
        if len(nums) >= 2:
            out["home_lat"] = float(nums[0])
            out["home_lon"] = float(nums[1])
    if "home_lat" in kv:
        out["home_lat"] = float(kv["home_lat"].split()[0])
    if "home_lon" in kv:
        out["home_lon"] = float(kv["home_lon"].split()[0])
    for src in ("drive_km", "drive"):
        if src in kv:
            out["drive_km"] = float(kv[src].split()[0])
            break
    for src in ("range_label", "range"):
        if src in kv:
            out["range_label"] = kv[src].strip().strip("\"'")
            break

    if not out:
        raise ValueError("No recognized intake fields")
    return out


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False
