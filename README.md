# guru

```
  ██████╗ ██╗   ██╗██████╗ ██╗   ██╗      ██████╗ ██╗      ██╗
 ██╔════╝ ██║   ██║██╔══██╗██║   ██║     ██╔════╝ ██║      ██║
 ██║  ███╗██║   ██║██████╔╝██║   ██║ ███ ██║      ██║      ██║
 ██║   ██║██║   ██║██╔══██╗██║   ██║ ╚═╝ ██║      ██║      ██║
 ╚██████╔╝╚██████╔╝██║  ██║╚██████╔╝     ╚██████╗ ███████╗ ██║
  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝      ╚═════╝ ╚══════╝ ╚═╝
  GURU-CLI  ·  send it · right spot · thinking offloaded
  kite bro who compiles  ·  Wind + Guru energy, beach edition
  Dr. Berend Gort  ·  www.berendgort.dev
```

**guru** is the beach sibling of [Windguru](https://www.windguru.cz/) — named for the same idea: **Wind + Guru** (wind expert/guide). Václav Horník built Windguru as a Czech windsurfer who could code; this CLI is the kite bro / surfer dude who already blended the models and says SEND IT or SIT IT OUT. Less Tune tabs. More water time.

Windguru **CLI + MCP + Python library** for kiters and agents — free named spots, WINDGURU DEFAULT top models, gear advice. No HTML scraping. No PRO.

[![PyPI](https://img.shields.io/pypi/v/windguru.svg)](https://pypi.org/project/windguru/)
[![Python](https://img.shields.io/pypi/pyversions/windguru.svg)](https://pypi.org/project/windguru/)

> Free only — named spots + WINDGURU DEFAULT Tune top-3. No PRO lat/lon click-forecast.

**Humans:** paste this repo URL into Cursor, Claude, Codex, or ChatGPT and ask *“set this up and tell me where I can kite.”* The agent instructions below are written for that.

---

## For AI agents (mandatory protocol)

If the user pasted https://github.com/berendgort/guru (or this README), **you must follow this section exactly**. Do not invent a Windguru scrape, browser walkthrough, or multi-question onboarding.

### Goal

Onboard the rider on the **first message**, then answer kite questions with gear advice using the `windguru` package (`guru` CLI and/or `guru-mcp` tools). Speak like a **kite bro who ships code** (`instruct` → `data.voice`): SEND IT / SOFT CALL / SIT IT OUT — honest, lightly funny (programmer ∩ kiter jokes), never hype a long haul. Not a JSON dump. If asked about the name: `data.voice.lore` (Windguru = Wind + Guru).

### Bootstrap (do this first)

1. Prefer **PyPI**, and **upgrade every session** before briefing:
   ```bash
   pipx upgrade windguru || pipx install 'windguru[mcp]'
   # or: pip install -U 'windguru[mcp]'   (activate venv first)
   ```
2. Run `guru doctor --json` — check `network.reachable` and `upgrade.update_available`.
3. **Immediately check the profile.** If `first_pass` / `ready=false` / `range_ready=false`, your **first reply to the human** must be the intake prompt (include **level**). Do not run weekend/best yet.
4. **One path for every app:** run `guru … --json` on a host that reaches Windguru. Automate first. If `network.reachable` is false: run `guru unlock --json` yourself, then paste `say_to_rider` (new chat). Still blocked / no shell: paste exactly one `human_fix` recipe for ChatGPT Work, Codex cloud, or Claude — never invent Settings paths, never ask for pipx/shell/MCP JSON. No wire/tunnel unless shell `guru` is unavailable and a local MCP host needs it.

Optional MCP (only if the host already uses MCP):

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
| 2. “Where can I kite?” | `guru weekend --json` [`--day Thu`] | `weekend_spots` — narrate **`data.schedule`** (whole horizon) |
| Local knowledge | `guru note <id> "dirs=SW-W offshore=N-NE …"` | persists in profile |
| 3. Named / numeric spot | `guru best <id> --advise --json` | `best_forecast` with `advise=true` |
| 4. Ambiguous name | use `candidates` → ask user or pass id / `--pick` | same via `resolve_spot` |

**First pass (mandatory on the first kite message when `ready=false` or `range_ready=false` / `first_pass=true`):**

1. Your **first message to the human** must show **exactly** `data.intake.prompt_to_user` (or the template below). Collect sport, weight, **level** (required — changes GO wind and sizing), quiver, wetsuits, home range — **one message**.
2. Wait for **one** reply (key=value paste). Do **not** ask sport, then weight, then kites separately. Do **not** skip intake.
3. Run:
   ```bash
   guru setup --intake '<their paste>' --json
   ```
   or MCP `setup_profile` with the same fields (including `level`).
4. Only then continue with weekend / best.

Template to show if you cannot read `prompt_to_user` yet:

```text
sport=kitefoil weight=78 level=intermediate kites=7,9,12 wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 range=Trabucador → Leucate
```

### How to talk to the human

After tools return, **narrate** for a rider:

- Verdict: GO / MARGINAL / NO-GO
- **Week plan from `schedule`** (Tue / Wed / Thu…) — do not wait for “what about Thursday?”
- Best spot + rough drive distance
- Window in local-friendly terms if you can, else UTC
- Wind + gusts; model_agree; size for gusts
- Kite size from quiver; wetsuit for session hours
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
pipx install windguru          # CLI: guru …   ← canonical path for every app
pipx install 'windguru[mcp]'   # + optional STDIO/HTTP adapters
guru doctor --json
```

Or with pip: `pip install windguru` / `pip install 'windguru[mcp]'`.

PyPI: [`windguru`](https://pypi.org/project/windguru/)

**Every app:** `guru … --json` on a host that reaches Windguru. Optional `guru-mcp` is the same library for STDIO hosts. Cloud sandboxes that block Windguru are unsupported — move to a local agent; do not tunnel by default.

## CLI

| Command | Role |
|---------|------|
| `guru setup` | Rider + home range (sport / weight / **level** / quiver / drive_km) |
| `guru profile` | Show profile + missing fields |
| `guru weekend` | Where can I kite? ~4-day schedule + top-3 model agree (`--day Thu` filter) |
| `guru note` | Save local knowledge / wind sectors (`dirs=` `offshore=`) |
| `guru instruct` | Teach agents the workflow |
| `guru spots <q>` | Name search (resolve id) |
| `guru near --lat --lon` | Free map markers near a point |
| `guru best <spot>` | Spot call + gear advice (default; `--no-advise` for raw) |
| `guru forecast <spot> -m gfs` | Single model escape hatch |
| `guru models` / `schema` / `doctor` / `wire` | Discoverability + network probe + optional MCP adapters |

Ambiguous names fail with `error_type: ambiguous` + `candidates` (pass numeric id or `--pick`).

## Library

```python
from guru import get_best_forecast, search_spots
from guru.rider.advice import advise_forecast, drive_km_from_home
from guru.rider.profile_store import load_profile

spots = search_spots("castelldefels")
best = get_best_forecast(201, top=3, hours=24)
profile = load_profile()
advice = advise_forecast(
    best.forecasts[0], profile, drive_km=drive_km_from_home(profile, best.spot)
)
print(advice.verdict, advice.summary)
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
