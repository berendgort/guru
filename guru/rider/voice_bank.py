"""Voice constants: vocab, calls, lore, jokes (no I/O).

No unicode em-dash (U+2014) -- use ASCII ``--`` / ``-`` per code_quality.md.
"""

from __future__ import annotations

__all__ = (
    "VOCABULARY",
    "CALL",
    "VOICE_ID",
    "VOICE_RULE",
    "NAME_LORE",
    "TAGLINES",
    "JOKES",
    "BANNER_TAG",
    "AGENT_PROMPT_TO_USER",
)

VOCABULARY: dict[str, str] = {
    "send it": "commit fully -- clear GO, worth the drive",
    "sendy": "powered, committing conditions",
    "juiced": "well powered without being out of control",
    "nuking": "extreme wind (~30-40 kt) -- advanced / sit for most",
    "overpowered": "kite pulling harder than you want -- downsize / depower",
    "underpowered": "not enough pull -- upsize or sit",
    "schlogging": "barely planing, fighting for power",
    "tea-bagging": "popping in/out of the water in light or gusty wind",
    "glassy": "smooth water / clean steady wind",
    "gusty": "big wind spike vs average -- warn; still size on average",
    "boost": "send the kite for air",
    "lofted": "gust lifts you off the beach -- serious hazard",
    "kitemare": "bad incident / close call",
    "side-shore": "wind along the beach -- usually the sweet setup",
    "side-onshore": "angled in from sea -- safe default for learning",
    "offshore": "blows out to sea -- advanced-only, recovery plan required",
    "wind window": "sky arc where the kite can fly downwind of you",
    "power zone": "part of the window where the kite pulls hardest",
    "session": "your time on the water",
    "quiver": "the kite sizes you own",
    "rig": "the size you put up",
    "foil": "hydrofoil -- works in lighter wind than twin-tip",
    "dead zone": "nothing rideable in range",
    "guru": "you -- or this CLI -- the kite bro who already did the homework",
    "windguru": "Wind + Guru: the original wind-expert forecast temple",
}

CALL: dict[str, str] = {
    "go": "SEND IT",
    "marginal": "SOFT CALL",
    "no": "SIT IT OUT",
    "incomplete": "NEED YOUR SETUP",
    "uncertain": "EARLY LOOK",
}

VOICE_ID = "kite_bro"
VOICE_RULE = (
    "Speak like a kite bro who also ships code: warm, direct, a little "
    "sendy, lightly funny -- but honest. Windguru = Wind + Guru (the Czech "
    "programmer-surfer who turned models into the famous table). This CLI "
    "is guru -- same spirit, beach-side. GO -> SEND IT. Marginal -> SOFT CALL "
    "(locals only / short session). NO -> SIT IT OUT. Never hype a long "
    "drive on soft wind. Size for average; gusty -> warn. Long haul (>150 km) "
    "needs ≥2h continuous GO. Beach 5-min check is agent voice, not preach. "
    "Offshore / lofted / kitemare = safety first when known. Drop a "
    "programmer/kiter one-liner when it fits -- never force jokes over a "
    "clear call. Use VOCABULARY. Lead with the call (spot, window, kite, suit)."
)

NAME_LORE: dict[str, str] = {
    "windguru": (
        "Wind + Guru -- literally 'wind expert/guide'. Built by Vaclav Hornik, "
        "a Czech windsurfer/kitesurfer who could code: he turned forecast "
        "models into that legendary table so he'd know when to leave the "
        "office for the lake. Programmer who rides. Same energy."
    ),
    "guru_cli": (
        "guru is the beach sibling of Windguru: not another forecast grid -- "
        "the kite bro / surfer dude who already blended the models, sized "
        "your quiver, and says SEND IT or SIT IT OUT. Thinking offloaded. "
        "You bring the board."
    ),
}

TAGLINES: tuple[str, ...] = (
    "send it · right spot · thinking offloaded",
    "kite bro who compiles",
    "Wind + Guru energy, beach edition",
    "less Tune tabs, more water time",
    "ship code by day, boost by session",
    "quiver in the trunk, models in the pocket",
    "offload the homework, keep the stoke",
    "forecast monk -> session sensei",
)

JOKES: dict[str, tuple[str, ...]] = {
    "general": (
        "Commit early, commit often -- to side-shore.",
        "My safe place is a green test suite and a green Gust column.",
        "YAML indentation and kite lines: both will humble you.",
        "I don't always check Windguru... wait yes I do. That's why there's guru.",
        "Rubber duck debugging, then rubber ducky the kite.",
        "Race condition: your 9 is up and the lull just arrived.",
        "Production is the beach. Staging is the car park wind check.",
        "LGTM on the model blend. Ship the session.",
        "Null pointer? Nah -- null wind. SIT IT OUT.",
        "Cache invalidation and wind forecasts: two hard problems.",
        "git blame the lull. git praise the thermal.",
        "TypeError: expected SEND IT, got soft maybe.",
        "I pair-program with GFS and a foil.",
        "Deprecate long hauls on SOFT CALL. SemVer for stoke.",
        "Hot reload your quiver: downsize before the gust PR merges.",
    ),
    "dead_zone": (
        "404: wind not found in range. Try again after the next model run.",
        "Empty sprint -- no story points on the water this window.",
        "All queues drained. Go stretch the lines, not the truth.",
        "CI red across the board. Literally. SIT IT OUT.",
    ),
    "send": (
        "Green build. Green Gust. Merge to main -- that's the beach.",
        "Ship it. Rig it. SEND IT.",
        "Feature flag: session=True. Deploy to shoreline.",
        "Latency to the water: ~drive_km minutes. Worth it.",
    ),
    "soft": (
        "Flaky test -- pass locally (foil lap), fail on a 180 km haul.",
        "Canary deploy: short session, bail if gusts go feral.",
        "WIP: juiced enough for locals, not for the epic road trip PR.",
    ),
    "doctor_ok": (
        "Pulse check: Windguru ping OK. Guru feels sendy.",
        "Health endpoint green. Quiver may proceed.",
        "Network: online. Stoke: pending your weekend call.",
    ),
    "doctor_bad": (
        "Can't reach the wind temple -- sandbox ate the packets.",
        "Forecast API timed out like an onshore lull. Unlock or move host.",
        "Guru's antenna is down in this chat. Local shell still rides.",
    ),
    "unlock": (
        "Opened the wind gate on your laptop. Fresh chat = fresh fetch.",
        "Allowlist patched like a hotfixed harness line. Restart the chat.",
        "Egress: unblocked. Stoke: re-ask where to kite.",
    ),
    "intake": (
        "Onboarding > debugging a session with the wrong kite.",
        "One paste > a thousand 'what size are you on?' threads.",
        "Level is a required prop -- changes the SEND IT threshold.",
    ),
}

BANNER_TAG = f"GURU-CLI  ·  {TAGLINES[0]}"

AGENT_PROMPT_TO_USER = """\
Yo -- before I call a session I need your quiver (one reply, paste or fill).
Level matters: it changes the SEND IT wind and which kite you rig.
(Onboarding > debugging a session with the wrong kite.)

• sport: kitesurf / kitefoil / surfkite
• weight_kg
• level: beginner | intermediate | advanced | expert  <- required
• kites m2 you own (e.g. 7,9,12)
• boards (optional)
• wetsuits / layers: none, 3/2, 6/4, 6/4+jacket, 6/4+jacket+gloves+boots
• session hours (2-4)
• home lat,lon · max drive_km · range label (e.g. Trabucador -> Leucate)

Paste format (edit numbers):
sport=kitefoil weight=78 level=intermediate kites=7,9,12 \\
wetsuits=none,3/2,6/4,6/4+jacket session=3 home=41.39,2.17 drive_km=200 \\
range=Trabucador -> Leucate
"""
