# guru

Windguru **CLI + MCP + Python library**. Same idea as [`fli`](https://github.com/punitarani/fli): reverse-engineered JSON, zero HTML scraping, agent-first.

[![PyPI](https://img.shields.io/pypi/v/windguru.svg)](https://pypi.org/project/windguru/)
[![Python](https://img.shields.io/pypi/pyversions/windguru.svg)](https://pypi.org/project/windguru/)

> Free only — named spots + WINDGURU DEFAULT Tune top-3. No PRO lat/lon click-forecast.

## Install

```bash
pipx install windguru
guru --help
```

Need MCP (Cursor / Claude Desktop)?

```bash
pipx install 'windguru[mcp]'
guru-mcp
```

Or with pip: `pip install windguru` / `pip install 'windguru[mcp]'`.

PyPI: [`windguru`](https://pypi.org/project/windguru/) · commands: `guru`, `guru-mcp`, `guru-mcp-http`

## Quick start

```bash
guru instruct --json
guru spots "castelldefels" --json
guru best 201 --json
guru near --lat 51.9 --lon 4.1 --json
guru best 48309 -H 24 --json   # De Slufter
```

`guru best` always uses **WINDGURU_DEFAULT** Tune weights and returns the **top 3** models + forecasts. Prefer that over raw GFS.

JSON envelope: `{"ok": true|false, "api_version": 1, "data"|error fields}`. Shared `error_type` / `retryable` with MCP.

## MCP (Cursor / Claude Desktop)

```bash
pipx install 'windguru[mcp]'
guru-mcp          # STDIO
guru-mcp-http     # http://127.0.0.1:8000/mcp/
```

```json
{
  "mcpServers": {
    "guru": {
      "command": "guru-mcp"
    }
  }
}
```

> If needed, use the full path from `which guru-mcp` (often `~/.local/bin/guru-mcp`).

| Tool | Description |
|------|-------------|
| `instruct` | Agent recipe (WINDGURU_DEFAULT → top 3) |
| `search_spots` | Named spot search |
| `near_spots` | Free map markers near lat/lon |
| `resolve_spot` | Name/id → spot (`ambiguous` + candidates) |
| `best_forecast` | Tune weights → top models → forecasts |
| `get_forecast` | Single-model escape hatch |
| `list_models` | Known aliases |

More: [`docs/mcp.md`](docs/mcp.md).

## CLI

| Command | Role |
|---------|------|
| `guru instruct` | Teach agents the workflow |
| `guru spots <q>` | Name search |
| `guru near --lat --lon` | Free map markers near a point |
| `guru best <spot>` | WINDGURU_DEFAULT → top 3 → forecasts |
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
| Search | `guru/search/` | HTTP (`curl_cffi`), blend_math, near, forecast |
| Models | `guru/models/` | Pydantic + aliases only |
| Wire | [`docs/WIRE.md`](docs/WIRE.md) | Captured `iapi.php` |

Read [`AGENTS.md`](AGENTS.md) before extending. Capture Network → fixtures → tests.

Engineering standards (kept in-repo):

- [`docs/code_quality.md`](docs/code_quality.md) — Korotkevich / Tourist bar
- [`docs/data_engineering_standards.md`](docs/data_engineering_standards.md) — Gray / Stonebraker bar

## Disclaimer

Unofficial. Not affiliated with Windguru. Personal / research use; respect ToS and rate limits.

## License

MIT
