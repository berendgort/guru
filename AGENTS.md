# AGENTS.md — how to extend `guru`

You are working on **guru**: a Windguru CLI / library / MCP that helps kiters pick spots and gear (free named spots + WINDGURU_DEFAULT). Product goal: [`docs/objective_function.md`](docs/objective_function.md).

## Calling guru from an agent

```bash
pipx install 'windguru[mcp]'   # PyPI — do not require a git clone
guru instruct --json
guru setup --sport kitefoil --weight 78 --level intermediate --kites 7,9,12 \
  --wetsuits "3/2,4/3" --home-lat 41.39 --home-lon 2.17 --drive-km 200 \
  --range-label "Trabucador → Leucate" --session-hours 3 --json
guru weekend --json                  # where can I kite?
guru best <id_spot> --advise --json  # single spot + gear advice
```

- **First message:** if profile incomplete, show `intake.prompt_to_user` once (include **level**) before weekend/best.
- Prefer **`weekend` / `best --advise`**, not raw GFS.
- Preset is always **WINDGURU_DEFAULT** (only adaptive Tune preset we support).
- Onboard once: sport / weight / **level** / quiver / wetsuits / home range via `guru setup`.
- On `error_type: ambiguous`, pick from `candidates` — never silent first-match.
- Envelope: `ok`, `api_version`, `error_type`, `retryable` (shared CLI + MCP).
- Do **not** scrape HTML, Tune jBox, or MapLibre. Do **not** require PRO.

## Architecture patterns

Keep these conventions when extending:

| Area | Pattern |
|------|---------|
| HTTP | `curl_cffi` impersonation, retries, env timeouts (`guru/search/client.py`) |
| Errors | Shared CLI/MCP `error_type` vocabulary (`guru/core/errors.py`) |
| Fixtures | Browser Network → `scripts/capture_fixtures.py` → `fixtures/` + offline parser tests |
| CLI | Typer + Rich + `--json` |
| MCP | FastMCP STDIO + HTTP |
| Models | Pydantic only — no I/O |
| Wire break | When simple `forecast` dies, use page-derived `rundef` params ([`docs/WIRE.md`](docs/WIRE.md)) |

## Live capture workflow (required for new models / wire changes)

1. Open the spot in a browser (`https://www.windguru.cz/201`).
2. CDP / Network: list requests matching `iapi.php`.
3. Note host (`.cz` vs `.net`), `q=`, and params (`id_spot`, `id_model`, `rundef`, `opt=simplemap`, …).
4. Reproduce with `curl_cffi` + **Referer**.
5. Dump fixture → parser test → update `docs/WIRE.md`.

**Never HTML-scrape the forecast table or Tune UI** as the primary path.

## Product shape

```text
pipx install windguru          # or: pipx install 'windguru[mcp]'
guru setup --sport … --weight … --level … --kites … --wetsuits …
guru weekend --json            # where can I kite?
guru best <id|name> [--json]   # spot call + advice (default on)
guru spots <query>             # resolve id if needed
guru near --lat Y --lon X
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

**Deploy / ship / publish:** bump → PyPI upload → **`git push origin HEAD`** (always push with deploy) → reinstall local pipx.
