"""Surfer-bro / kite-beach voice — pleasure + honesty (objective_function).

Machine verdicts stay ``go`` / ``marginal`` / ``no``. Human + agent copy uses
beach slang. Never hype a soft session or a long haul (C1 / C4).
"""

from __future__ import annotations

from typing import Any

# Beach vocabulary agents should lean on when narrating weekend / best.
VOCABULARY: dict[str, str] = {
    "send it": "commit fully — clear GO, worth the drive",
    "sendy": "powered, committing conditions",
    "juiced": "well powered without being out of control",
    "nuking": "extreme wind (~30–40 kt) — advanced / sit for most",
    "overpowered": "kite pulling harder than you want — downsize / depower",
    "underpowered": "not enough pull — upsize or sit",
    "schlogging": "barely planing, fighting for power",
    "tea-bagging": "popping in/out of the water in light or gusty wind",
    "glassy": "smooth water / clean steady wind",
    "gusty": "big wind spike vs average — size for gusts",
    "boost": "send the kite for air",
    "lofted": "gust lifts you off the beach — serious hazard",
    "kitemare": "bad incident / close call",
    "side-shore": "wind along the beach — usually the sweet setup",
    "side-onshore": "angled in from sea — safe default for learning",
    "offshore": "blows out to sea — advanced-only, recovery plan required",
    "wind window": "sky arc where the kite can fly downwind of you",
    "power zone": "part of the window where the kite pulls hardest",
    "session": "your time on the water",
    "quiver": "the kite sizes you own",
    "rig": "the size you put up",
    "foil": "hydrofoil — works in lighter wind than twin-tip",
    "dead zone": "nothing rideable in range",
}

# Clear call tokens for headers (verdict field stays machine go|marginal|no)
CALL: dict[str, str] = {
    "go": "SEND IT",
    "marginal": "SOFT CALL",
    "no": "SIT IT OUT",
    "incomplete": "NEED YOUR SETUP",
}

VOICE_ID = "kite_bro"
VOICE_RULE = (
    "Speak like a solid kite bro on the beach: warm, direct, a little sendy — "
    "but honest. GO → SEND IT. Marginal → SOFT CALL (locals only / short session). "
    "NO → SIT IT OUT. Never hype a long drive on soft wind. Size for gusts. "
    "Offshore / lofted / kitemare = safety first. Use VOCABULARY. Lead with the "
    "call (spot, window, kite, suit) — don't dump raw model tables."
)


def call_label(verdict: str) -> str:
    return CALL.get(verdict, verdict.upper())


def voice_payload() -> dict[str, Any]:
    """Attach to instruct / MCP so every agent hosts the same register."""
    return {
        "id": VOICE_ID,
        "rule": VOICE_RULE,
        "calls": dict(CALL),
        "vocab": dict(VOCABULARY),
        "examples": [
            "SEND IT Thu Castelldefels — 14 gust 18, rig your 9, 4/3, beach check 5.",
            "SOFT CALL — juiced enough for a local foil lap, skip the 180 km haul.",
            "SIT IT OUT — dead zone in range; don't force a kitemare.",
        ],
    }


def advice_summary(
    overall: str,
    *,
    start: str,
    end: str,
    wind_kn: float,
    gust_kn: float | None,
    stars: str,
    kite: str,
    suit: str,
    session_h: float,
    sport: str,
    level: str,
) -> str:
    if overall == "no":
        return (
            f"{call_label('no')} — no sendable {sport} window for {level} "
            "in this forecast. Stay on the beach, protect the quiver."
        )
    if overall == "incomplete":
        return (
            f"{call_label('incomplete')} — drop your quiver + home range "
            "once (level required) before I call a session."
        )
    star_bit = f" · {stars}" if stars and stars != "—" else ""
    gust = f" gust {gust_kn:g}" if gust_kn is not None else ""
    return (
        f"{call_label(overall)} · {start}–{end} · {wind_kn:g} kt{gust}"
        f"{star_bit} · rig {kite} · {suit} · {session_h:g}h session"
    )


def incomplete_advice_summary(missing: list[str]) -> str:
    return (
        f"{call_label('incomplete')} — need your setup before gear calls. "
        f"Missing: {', '.join(missing)}"
    )


def hour_bits(
    *,
    quality: str,
    sport_foil_light: bool,
    gap: float | None,
    ideal: float | None,
    owned: float | None,
    owned_suit: str | None,
    rec_suit: str | None,
    session_hours: float,
    beginner_strong: bool,
) -> list[str]:
    bits: list[str] = []
    if quality == "smooth":
        bits.append("glassy power")
    elif quality == "gusty":
        bits.append("gusty — size for the spikes, not the lull")
    elif quality == "ok":
        bits.append("clean enough")
    if sport_foil_light:
        bits.append("foil light-wind still rides")
    if gap is not None and abs(gap) > 2.0:
        bits.append(f"quiver gap {gap:+.1f} m² vs ideal {ideal}")
    elif owned is not None and ideal is not None:
        bits.append(f"rig {owned:g} m² (sweet spot ~{ideal:g})")
    if owned_suit and rec_suit and _norm(owned_suit) != _norm(rec_suit):
        bits.append(
            f"suit: your {owned_suit}, chart wants {rec_suit} ({session_hours:g}h)"
        )
    elif owned_suit:
        bits.append(f"suit {owned_suit} ({session_hours:g}h session)")
    if beginner_strong:
        bits.append("juiced for a beginner — take it easy")
    return bits


def far_drive_note(existing: str | None = None) -> str:
    extra = "long haul needs a clear SEND IT, not a soft maybe"
    if existing:
        return f"{existing}; {extra}"
    return extra


def weekend_summary(
    *,
    overall: str,
    lead_weekday: str | None,
    lead_name: str | None,
    lead_drive: float | str | None,
    lead_line: str | None,
    plan_days: str | None,
    top_name: str | None = None,
    top_id: int | None = None,
    top_drive: float | str | None = None,
    top_line: str | None = None,
) -> str:
    call = call_label(overall)
    if lead_weekday and lead_name and lead_line and plan_days:
        return (
            f"{call} · next: {lead_weekday} {lead_name} "
            f"~{lead_drive if lead_drive is not None else '?'} km — {lead_line} "
            f"| plan: {plan_days}"
        )
    if top_name is not None and top_line:
        return (
            f"{call}: {top_name} ({top_id}) "
            f"~{top_drive if top_drive is not None else '?'} km — {top_line}"
        )
    return f"{call_label('no')} — dead zone in your drive range this window."


def weekend_incomplete(missing: list[str]) -> str:
    return (
        f"{call_label('incomplete')} — need quiver + home range before I map "
        f"sessions. Missing: {', '.join(missing)}"
    )


def slot_line(
    *,
    verdict: str,
    start: str,
    end: str,
    wind_kn: float,
    gust_kn: float | None,
    stars: str | None,
    kite: str,
    agree: int,
) -> str:
    gust = f" gust {gust_kn:g}" if gust_kn is not None else ""
    star_bit = f" · {stars}" if stars and stars != "—" else ""
    return (
        f"{call_label(verdict)} · {start}–{end} · {wind_kn:g} kt{gust}"
        f"{star_bit} · rig {kite} · {agree}/3 models locked"
    )


def checklist(*, gusty: bool, drive_km: float | None = None) -> list[str]:
    items = [
        "Check avg + gusts — size for the send, not the lull",
        "Beach: watch 5 min — direction, consistency, downwind kitemare risks",
        "Side-shore / side-on preferred; offshore = advanced-only (don't get lofted)",
        "Models agree before a long haul",
    ]
    if gusty:
        items.append("Gusty → downsize / more depower / shorter session")
    if drive_km is not None and drive_km > 90:
        items.append(
            f"Long haul (~{drive_km:.0f} km) → require SEND IT, not a soft maybe"
        )
    return items


def thinking_headers(*, hours: int, top_models: int, range_label: str | None) -> list[str]:
    bits = [
        "Long haul only on a clear SEND IT — prefer models locked",
        f"Scan ~{hours}h with top {top_models} models; lay the week so Thu/Fri "
        "show up without re-asking",
    ]
    if range_label:
        bits.insert(0, f"Home range: {range_label}")
    return bits


AGENT_PROMPT_TO_USER = """\
Yo — before I call a session I need your quiver (one reply, paste or fill).
Level matters: it changes the SEND IT wind and which kite you rig.

• sport: kitesurf / kitefoil / surfkite
• weight_kg
• level: beginner | intermediate | advanced  ← required
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


BANNER_TAG = "GURU-CLI  ·  send it · right spot · thinking offloaded"


def _norm(raw: str) -> str:
    return raw.strip().lower().replace(" ", "")
