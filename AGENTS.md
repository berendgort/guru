# AGENTS.md — how to extend `guru`

You are working on **guru**: a Windguru CLI/library/MCP reverse-engineered the same way [`fli`](https://github.com/punitarani/fli) reverse-engineers Google Flights.

## Calling guru from an agent

```bash
pipx install 'windguru[mcp]'
guru instruct --json
guru spots "<place>" --json          # or: guru near --lat --lon --json
guru best <id_spot> --json           # WINDGURU_DEFAULT → top 3 forecasts
```

- Prefer **`best` / `best_forecast`**, not raw GFS.
- Preset is always **WINDGURU_DEFAULT** (only adaptive Tune preset we support).
- On `error_type: ambiguous`, pick from `candidates` — never silent first-match.
- Envelope: `ok`, `api_version`, `error_type`, `retryable` (shared CLI + MCP).
- Do **not** scrape HTML, Tune jBox, or MapLibre. Do **not** require PRO.

## Hard rule: clone methods from fli

**Strongly prefer copying patterns from fli over inventing new ones.**

Keep a local checkout of fli (`git clone https://github.com/punitarani/fli /tmp/fli-ref`) and **read their search client before changing ours**.

| fli | guru | Copy this idea |
|-----|------|----------------|
| `fli/search/client.py` | `guru/search/client.py` | `curl_cffi` impersonation, retries, env timeouts |
| `fli/core/errors.py` | `guru/core/errors.py` | Shared CLI/MCP `error_type` vocabulary |
| capture scripts + fixtures | `scripts/capture_fixtures.py` + `fixtures/` | Browser Network → fixture → offline parser tests |
| `fli/cli/` | `guru/cli/` | Typer + Rich + `--json` |
| `fli/mcp/` | `guru/mcp/` | FastMCP STDIO + HTTP |
| `fli/models/` | `guru/models/` | Pydantic only — no I/O |
| `_tfs` migration when signed RPC broke | `docs/WIRE.md` SPA `rundef` form | When simple `forecast` dies, use page-derived params |

## Reverse-engineering workflow (required)

1. Open the spot in **Cursor browser** (`https://www.windguru.cz/201`).
2. CDP / Network: list requests matching `iapi.php`.
3. Note host (`.cz` vs `.net`), `q=`, and params (`id_spot`, `id_model`, `rundef`, `opt=simplemap`, …).
4. Reproduce with `curl_cffi` + **Referer**.
5. Dump fixture → parser test → update `docs/WIRE.md`.

**Never HTML-scrape the forecast table or Tune UI** as the primary path.

## Product shape

```text
pipx install windguru
guru spots <query>
guru near --lat Y --lon X
guru best <id|name> [--top 3] [--hours N] [--json]
guru-mcp
```

## Do / don’t

- **Do** extend `MODELS` from live Network captures.
- **Do** keep free vs PRO failures explicit (PRO is out of core).
- **Do** stay polite on rate limits.
- **Don’t** commit cookies / PRO passwords / private nicknames as defaults.
- **Don’t** ship a worldwide spot dump in the wheel (live `near` / `spots` only).
- **Don’t** depend on `life-research` — this repo is public and clean-slate.

## Engineering standards

Keep and follow (do not delete):

- [`docs/code_quality.md`](docs/code_quality.md) — Korotkevich / Tourist bar
- [`docs/data_engineering_standards.md`](docs/data_engineering_standards.md) — Gray / Stonebraker bar

## Dev commands

```bash
pipx install -e ".[dev,mcp]"
# or: source .venv/bin/activate && pip install -e ".[dev,mcp]"
guru spots "foster city"
guru best 201 -H 12 --json
pytest -q
pytest -m live
ruff check .
```
