---
name: guru
description: >
  When the user pastes github.com/berendgort/guru, wants Windguru forecasts,
  kite weekend plans, or gear advice: upgrade windguru from PyPI first, ask for
  the full rider profile on the FIRST message (sport, weight, LEVEL, quiver,
  suits, home range), then guru weekend (schedule) / best. Never scrape
  windguru.cz. Never drip-feed onboarding questions.
license: MIT
---

# guru — agent skill (follow exactly)

If the user shared https://github.com/berendgort/guru or asks to use guru / Windguru via this project, obey this skill. Do not scrape Windguru HTML. Do not require PRO.

## Bootstrap (every session)

```bash
pipx upgrade windguru || pipx install 'windguru[mcp]'
guru doctor --json    # network.reachable + upgrade
guru instruct --json
guru profile --json
```

**One path every app:** `guru … --json` on a machine that reaches Windguru. If `network.reachable` is false: follow `on_unreachable` — never ask the human to install/run guru; intake in-chat only if needed; one sentence to switch to a local agent host.

## First message (mandatory if profile empty)

If `first_pass` / `ready=false` / `range_ready=false`:

1. Your **first reply to the human** is `intake.prompt_to_user` (must collect **level**)
2. Wait for **one** key=value reply — never ask fields one-by-one
3. `guru setup --intake '<paste>' --json` (or `setup_profile`)
4. Only then run weekend / best

**Level is required** — beginner / intermediate / advanced (expert → advanced).

Example intake paste:

```text
sport=kitefoil weight=78 level=intermediate kites=7,9,12 wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 range=Trabucador → Leucate
```

## After onboarded

- “Where can I kite?” → `guru weekend --json` / `weekend_spots`
- Narrate **`data.schedule`** day-by-day (covers ~4 days / top-3 models) — do **not** wait for “what about Thursday?”
- Named spot → `guru best <id> --json` / `best_forecast`
- Narrate like a kiter: GO/MARGINAL/NO-GO, plan, kt+gusts, kite, suit, beach 5‑min check

## Hard rules

- Preset **WINDGURU_DEFAULT** only
- Auto-upgrade when PyPI is ahead
- No HTML scrape, no invented PRO lat/lon forecasts
- Ambiguous names → `candidates` / numeric id
- Full protocol: repo README **For AI agents**
