# guru

<p align="center">
  <img src="docs/assets/guru-github-banner.png" alt="guru — kite forecast CLI" width="100%">
</p>

Windguru **CLI + MCP + Python library**. Same idea as [`fli`](https://github.com/punitarani/fli): reverse-engineered JSON, zero HTML scraping, agent-first.

[![PyPI](https://img.shields.io/pypi/v/windguru.svg)](https://pypi.org/project/windguru/)
[![Python](https://img.shields.io/pypi/pyversions/windguru.svg)](https://pypi.org/project/windguru/)

> Free only — named spots + WINDGURU DEFAULT Tune top-3. No PRO lat/lon click-forecast.

**Humans:** paste this repo URL into Cursor, Claude, Codex, or ChatGPT and ask *“set this up and tell me where I can kite.”* The agent instructions below are written for that.

---

## For AI agents (mandatory protocol)

If the user pasted https://github.com/berendgort/guru (or this README), **you must follow this section exactly**. Do not invent a Windguru scrape, browser walkthrough, or multi-question onboarding.

### Goal

Onboard the rider once, then answer kite questions with gear advice using the `windguru` package (`guru` CLI and/or `guru-mcp` tools). Speak to the human like a kiter, not like a JSON dump.

### Bootstrap (do this first)

1. Prefer **PyPI**, not a git clone:
   ```bash
   pipx install windguru
   # if the host supports MCP:
   pipx install 'windguru[mcp]'
   ```
   Fallback: `pip install windguru` / `pip install 'windguru[mcp]'` (activate any existing venv first).
2. Confirm: `guru doctor` and `guru instruct --json`.
3. Wire tools for the host you are in:
   - **Cursor / Claude Desktop / local Codex with MCP** → ensure MCP server `guru` runs `guru-mcp` (full path from `which guru-mcp` if needed). Then prefer MCP tools over shell.
   - **Shell-capable agent (Cursor Agent, Codex, Claude with bash)** → run `guru … --json` if MCP is not configured yet.
   - **Claude Cowork / claude.ai** → local STDIO MCP will not work. Either run CLI in a local terminal the user controls, or start `guru-mcp-http` and help them add a **public HTTPS** URL under Customize → Connectors. Do not pretend localhost is reachable from Anthropic’s cloud.
   - **ChatGPT cloud** → same as Cowork for MCP (needs public HTTP), otherwise guide install + have the user paste `guru … --json` output, or use whatever shell/Code Interpreter the product gives you.

MCP config (Cursor / Claude Desktop):

```json
{
  "mcpServers": {
    "guru": {
      "command": "guru-mcp"
    }
  }
}
```

### Operating loop (every kite question)

| Step | CLI | MCP |
|------|-----|-----|
| 0. Recipe / profile | `guru instruct --json` or `guru profile --json` | `instruct` / `get_profile` |
| 1. First pass if needed | see below | see below |
| 2. “Where can I kite?” | `guru weekend --json` | `weekend_spots` |
| 3. Named / numeric spot | `guru best <id> --advise --json` | `best_forecast` with `advise=true` |
| 4. Ambiguous name | use `candidates` → ask user or pass id / `--pick` | same via `resolve_spot` |

**First pass (mandatory when `ready=false` or `range_ready=false` / `first_pass=true`):**

1. Show the human **exactly** `data.intake.prompt_to_user` (or the template below) — **one message**.
2. Wait for **one** reply (key=value paste). Do **not** ask sport, then weight, then kites separately.
3. Run:
   ```bash
   guru setup --intake '<their paste>' --json
   ```
   or MCP `setup_profile` with the same fields.
4. Only then continue with weekend / best.

Template to show if you cannot read `prompt_to_user` yet:

```text
sport=kitefoil weight=78 level=intermediate kites=7,9,12 wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 range=Trabucador → Leucate
```

### How to talk to the human

After tools return, **narrate** for a rider:

- Verdict: GO / MARGINAL / NO-GO
- Best spot + rough drive distance (weekend) or spot name (best)
- Window in local-friendly terms if you can, else UTC
- Wind + gusts; say if gusty → size for gusts
- Kite size from quiver; wetsuit for a 2–4h session
- Short checklist: watch beach 5 min, side-shore preference, don’t long-drive for marginal

Do **not** dump raw model tables unless they ask.

### Hard rules

- Use preset **WINDGURU_DEFAULT** only (`guru best` / `best_forecast`). Do not default to raw GFS.
- Never scrape windguru.cz HTML, Tune UI, or MapLibre.
- Never require PRO or invent lat/lon click-forecasts.
- On `error_type: ambiguous`, pick from `candidates` — never silent first-match.
- Respect `retryable` on errors; don’t hammer rate limits.
- Profile lives at `~/.config/guru/profile.json` (override with `GURU_CONFIG_DIR`).

### MCP tool map

| Tool | Use for |
|------|---------|
| `instruct` | Load this recipe into context |
| `get_profile` / `setup_profile` | Onboarding |
| `weekend_spots` | “Where can I kite?” |
| `search_spots` / `resolve_spot` / `near_spots` | Find spot ids |
| `best_forecast` (`advise=true`) | Single spot + gear |
| `get_forecast` / `list_models` | Escape hatches only |

More: [`docs/mcp.md`](docs/mcp.md) · skill copy: [`skills/guru/SKILL.md`](skills/guru/SKILL.md)

---

## Install

```bash
pipx install windguru          # CLI: guru …
pipx install 'windguru[mcp]'   # + MCP: guru-mcp / guru-mcp-http
guru --help
```

Or with pip: `pip install windguru` / `pip install 'windguru[mcp]'`.

PyPI: [`windguru`](https://pypi.org/project/windguru/) · commands: `guru`, `guru-mcp`, `guru-mcp-http`

### Host cheat sheet

| Host | Wire |
|------|------|
| **Cursor** | MCP `guru-mcp` and/or shell `guru … --json` + optional [`skills/guru/SKILL.md`](skills/guru/SKILL.md) |
| **Claude Desktop** | Local STDIO in `claude_desktop_config.json` |
| **Claude Cowork / claude.ai** | Remote custom connector → public HTTPS to `guru-mcp-http` ([docs](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)) |
| **Codex / shell agents** | `pipx install windguru` then `guru … --json` |
| **ChatGPT cloud** | Public HTTP MCP/Action you host, or user runs CLI and pastes JSON |

`guru-mcp-http` listens at `http://127.0.0.1:8000/mcp/` — Cowork/claude.ai need that URL exposed publicly; there is no hosted Windguru MCP in this repo.
## CLI

| Command | Role |
|---------|------|
| `guru setup` | Rider + home range (sport / weight / quiver / drive_km) |
| `guru profile` | Show profile + missing fields |
| `guru weekend` | Where can I kite? Rank spots in drive range |
| `guru instruct` | Teach agents the workflow |
| `guru spots <q>` | Name search |
| `guru near --lat --lon` | Free map markers near a point |
| `guru best <spot> --advise` | WINDGURU_DEFAULT → top 3 → gear advice |
| `guru forecast <spot> -m gfs` | Single model |
| `guru models` / `schema` / `doctor` | Discoverability |

Ambiguous names fail with `error_type: ambiguous` + `candidates` (pass numeric id or `--pick`).

## Library

```python
from guru import search_spots, get_best_forecast, spots_near

spots = search_spots("castelldefels")
best = get_best_forecast(201, top=3, hours=24)
print(best.models[0].name, best.models[0].weight_pct)
print(best.forecasts[0].hours[0].wind_kn)
```

## Develop

```bash
git clone https://github.com/berendgort/guru.git
cd guru
pipx install -e ".[dev,mcp]"
# or: python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev,mcp]"
pytest -q
ruff check .
```

| Layer | Path | Role |
|-------|------|------|
| Core | `guru/core/` | Shared envelope, errors, instruct recipe |
| CLI | `guru/cli/` | Typer + Rich + `--json` (thin over core) |
| MCP | `guru/mcp/` | FastMCP over core (no CLI imports) |
| Rider | `guru/rider/` | Profile store + kite/wetsuit advice |
| Search | `guru/search/` | HTTP (`curl_cffi`), blend_math, near, forecast |
| Models | `guru/models/` | Pydantic + aliases only |
| Wire | [`docs/WIRE.md`](docs/WIRE.md) | Captured `iapi.php` |
| MCP | [`docs/mcp.md`](docs/mcp.md) | `guru-mcp` setup + tools |

Read [`AGENTS.md`](AGENTS.md) before extending. Capture Network → fixtures → tests.

Engineering standards (kept in-repo):

- [`docs/code_quality.md`](docs/code_quality.md) — Korotkevich / Tourist bar
- [`docs/data_engineering_standards.md`](docs/data_engineering_standards.md) — Gray / Stonebraker bar

## Disclaimer

Unofficial. Not affiliated with Windguru. Personal / research use; respect ToS and rate limits.

## License

MIT
