# AGENTS.md — how to extend `guru`

You are working on **guru**: a Windguru CLI/library reverse-engineered the same way [`fli`](https://github.com/punitarani/fli) reverse-engineers Google Flights.

## Hard rule: clone methods from fli

**Strongly prefer copying patterns from fli over inventing new ones.**

Keep a local checkout of fli (`git clone https://github.com/punitarani/fli /tmp/fli-ref`) and **read their search client before changing ours**.

| fli | guru | Copy this idea |
|-----|------|----------------|
| `fli/search/client.py` | `guru/search/client.py` | `curl_cffi` impersonation, retries, env timeouts |
| capture scripts + fixtures | `scripts/capture_fixtures.py` + `fixtures/` | Browser Network → fixture → offline parser tests |
| `fli/cli/` | `guru/cli/` | Typer + Rich + `--json` |
| `fli/models/` | `guru/models/` | Pydantic only — no I/O |
| `_tfs` migration when signed RPC broke | `docs/WIRE.md` SPA `rundef` form | When simple `forecast` dies, use page-derived params |

## Reverse-engineering workflow (required)

1. Open the spot in **Cursor browser** (`https://www.windguru.cz/201`).
2. CDP / Network: list requests matching `iapi.php`.
3. Note host (`.cz` vs `.net`), `q=`, and params (`id_spot`, `id_model`, `rundef`, `WGCACHEABLE`, `cache_index`).
4. Reproduce with `curl_cffi` + **Referer**.
5. Dump fixture → parser test → update `docs/WIRE.md`.

**Never HTML-scrape the forecast table** as the primary path.

## Product shape

```text
pipx install windguru
guru spots <query>
guru forecast <id|name> [--model gfs|icon|…] [--hours N] [--json]
```

## Do / don’t

- **Do** extend `MODELS` from live Network captures.
- **Do** keep free vs PRO failures explicit.
- **Do** stay polite on rate limits.
- **Don’t** commit cookies / PRO passwords / private nicknames as defaults.
- **Don’t** depend on `life-research` — this repo is public and clean-slate.

## Dev commands

```bash
pipx install -e ".[dev]"
guru spots "foster city"
guru forecast 201 -H 12
pytest -q
pytest -m live
ruff check .
```
