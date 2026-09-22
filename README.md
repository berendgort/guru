# guru

Windguru CLI + Python library. Same idea as [`fli`](https://github.com/punitarani/fli) for Google Flights: **no HTML scraping** — talk to the same internal JSON the Windguru SPA uses.

> **Status:** early scaffold (v0.1). Spot search + GFS forecast work. Models, PRO gates, stations, and rate-limits still need hardening. Read [`AGENTS.md`](AGENTS.md) before extending.

## Install

Same easy path as `fli`:

```bash
pipx install windguru
# or from this repo while developing:
pipx install -e .

guru --help
guru spots castelldefels
guru forecast 201 --hours 24
guru forecast "foster city" --model gfs --json
```

PyPI name is **`windguru`** (like `flights` → `fli`). The command is **`guru`**.

## Library

```python
from guru import search_spots, get_forecast

spots = search_spots("castelldefels")
fc = get_forecast(201, model="gfs", hours=24)
print(fc.hours[0].wind_kn, fc.hours[0].wind_dir_deg)
```

## Hand-off — open this repo next

1. Clone / open **`berendgort/guru`** in Cursor (leave `life-research`).
2. Read **[`AGENTS.md`](AGENTS.md)** — mandatory: clone methods from `fli`, use browser Network RE.
3. Skim **[`docs/WIRE.md`](docs/WIRE.md)** — captured `iapi.php` endpoints (`.cz` + `.net`, `rundef`, models).
4. Install: `pipx install -e ".[dev]"` then `guru spots maui`.
5. Extend models / stations / MCP the **fli way** (client → decode → Typer → fixtures).

## Architecture (mirror fli)

| Layer | Path | Role |
|-------|------|------|
| CLI | `guru/cli/` | Typer + Rich tables |
| Search | `guru/search/` | HTTP client (`curl_cffi`), spots, forecast |
| Models | `guru/models/` | Pydantic + model id map |
| Docs | `docs/WIRE.md` | Reverse-engineering notes |

**Do not invent APIs.** Capture with Cursor browser (Network → `iapi.php`), then encode.

## Disclaimer

Unofficial. Not affiliated with Windguru. Personal / research use; respect their ToS and rate limits. Prefer PRO / official channels for commercial use.

## License

MIT
