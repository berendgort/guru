---
name: guru
description: >
  When the user pastes github.com/berendgort/guru, wants Windguru forecasts,
  kite weekend plans, or gear advice: install windguru from PyPI, ask for the
  full rider profile on the FIRST message (sport, weight, LEVEL, quiver,
  suits, home range), then guru weekend / best --advise. Never scrape
  windguru.cz. Never drip-feed onboarding questions.
license: MIT
---

# guru — agent skill (follow exactly)

If the user shared https://github.com/berendgort/guru or asks to use guru / Windguru via this project, obey this skill. Do not scrape Windguru HTML. Do not require PRO.

## Bootstrap

```bash
pipx install windguru
pipx install 'windguru[mcp]'   # when MCP is available
guru doctor
guru instruct --json
guru profile --json
```

- **Cursor / Claude Desktop / local MCP:** configure `"command": "guru-mcp"` (use `which guru-mcp` full path if needed), then prefer MCP tools.
- **Shell agents (Cursor Agent, Codex, Claude bash):** `guru … --json`.
- **Claude Cowork / claude.ai / ChatGPT cloud:** local STDIO MCP will not work; use CLI where possible, or public HTTPS to `guru-mcp-http` as a custom connector / Action.

## First message (mandatory if profile empty)

If `first_pass` / `ready=false` / `range_ready=false`:

1. Your **first reply to the human** is `intake.prompt_to_user` (must collect **level**)
2. Wait for **one** key=value reply — never ask fields one-by-one
3. `guru setup --intake '<paste>' --json` (or `setup_profile`)
4. Only then run weekend / best

**Level is required** — beginner / intermediate / advanced changes GO wind floors and kite sizing. Do not default silently.

Example intake paste:

```text
sport=kitefoil weight=78 level=intermediate kites=7,9,12 wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 range=Trabucador → Leucate
```

## After onboarded

- “Where can I kite?” → `guru weekend --json` / `weekend_spots`
- Named spot → resolve id; on `ambiguous` use `candidates`. Then `guru best <id> --advise --json` / `best_forecast(advise=true)`
- Narrate like a kiter: GO/MARGINAL/NO-GO, spot, window, kt+gusts, kite from quiver, 2–4h wetsuit, beach 5‑min check. No raw JSON dump.

## Hard rules

- Preset **WINDGURU_DEFAULT** only (`best` / `best_forecast`)
- No HTML scrape, no invented PRO lat/lon forecasts
- Ambiguous names → `candidates` / numeric id — never silent first-match
- Full protocol: repo README section **For AI agents (mandatory protocol)**
