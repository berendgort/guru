# guru

Windguru **CLI + MCP + Python library**. Same idea as [`fli`](https://github.com/punitarani/fli): reverse-engineered JSON, zero HTML scraping, agent-first.

> Free only — named spots + WINDGURU DEFAULT Tune top-3. No PRO lat/lon click-forecast.

## Install

```bash
# CLI (recommended)
pipx install windguru

# CLI + MCP server
pipx install 'windguru[mcp]'

guru --help
guru instruct --json
```

Until the PyPI release is live, install from GitHub:

```bash
pipx install 'git+https://github.com/berendgort/guru.git'
pipx install 'git+https://github.com/berendgort/guru.git[mcp]'
```

PyPI name **`windguru`**, command **`guru`**, MCP **`guru-mcp`**.

Or with pip:

```bash
pip install windguru
pip install 'windguru[mcp]'
```

## MCP Server

```bash
pipx install 'windguru[mcp]'

# STDIO (Cursor / Claude Desktop)
guru-mcp

# HTTP (streamable)
guru-mcp-http  # http://127.0.0.1:8000/mcp/
```

### Connecting to Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "guru": {
      "command": "guru-mcp"
    }
  }
}
```

> Tip: if the binary is not on PATH, use the full path from `which guru-mcp`
> (often `~/.local/bin/guru-mcp`).

### MCP tools

| Tool | Description |
|------|-------------|
| `instruct` | Agent recipe (WINDGURU_DEFAULT → top 3) |
| `search_spots` | Named spot search |
| `near_spots` | Free map markers near lat/lon |
| `resolve_spot` | Name/id → spot (`ambiguous` + candidates) |
| `best_forecast` | Tune weights → top models → forecasts |
| `get_forecast` | Single-model escape hatch |
| `list_models` | Known aliases |

## Agent recipe

```bash
guru instruct --json
guru spots "castelldefels" --json
guru best 201 --json
guru near --lat 51.9 --lon 4.1 --json
guru best 48309 -H 24 --json   # De Slufter
```

`guru best` always uses **WINDGURU_DEFAULT** Tune weights and returns the **top 3** models + forecasts. Prefer that over raw GFS.

JSON envelope: `{"ok": true|false, "api_version": 1, "data"|error fields}`. Shared `error_type` / `retryable` with MCP.

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

## Architecture

| Layer | Path | Role |
|-------|------|------|
| Core | `guru/core/` | Shared envelope, errors, instruct recipe |
| CLI | `guru/cli/` | Typer + Rich + `--json` (thin over core) |
| MCP | `guru/mcp/` | FastMCP over core (no CLI imports) |
| Search | `guru/search/` | HTTP (`curl_cffi`), blend_math, near, forecast |
| Models | `guru/models/` | Pydantic + aliases only |
| Wire | [`docs/WIRE.md`](docs/WIRE.md) | Captured `iapi.php` |
| MCP | [`docs/mcp.md`](docs/mcp.md) | `guru-mcp` setup + tools |

Read [`AGENTS.md`](AGENTS.md) before extending. Capture Network → fixtures → tests.

## Disclaimer

Unofficial. Not affiliated with Windguru. Personal / research use; respect ToS and rate limits.

## License

MIT
