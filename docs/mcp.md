# MCP — `guru-mcp`

Same library and error vocabulary as the CLI. Prefer `best_forecast` over raw GFS.

## Install

```bash
pipx install 'windguru[mcp]'
which guru-mcp   # use full path in MCP config if needed
```

## Run

| Command | Transport |
|---------|-----------|
| `guru-mcp` | STDIO (Cursor / Claude Desktop) |
| `guru-mcp-http` | Streamable HTTP at `http://127.0.0.1:8000/mcp/` |

### Cursor / Claude Desktop

```json
{
  "mcpServers": {
    "guru": {
      "command": "guru-mcp"
    }
  }
}
```

## Tools

| Tool | Args | Returns |
|------|------|---------|
| `instruct` | — | Agent recipe (setup → best advise) |
| `setup_profile` | sport, weight, kites, wetsuits, home_lat/lon, drive_km, session_hours… | Merged profile |
| `get_profile` | — | Profile + ready / range_ready |
| `weekend_spots` | `hours?`, `limit?` | Ranked spots in drive range + advice |
| `search_spots` | `query`, `limit?` | Named spots (no lat/lon) |
| `near_spots` | `lat`, `lon`, `radius_km?`, `limit?` | Free map markers near a point |
| `resolve_spot` | `spot`, `pick?` | Spot id/name → spot |
| `best_forecast` | `spot`, `top?`, `hours?`, `pick?`, `advise?` | Weights + forecasts + `advice` |
| `get_forecast` | `spot`, `model?`, `hours?`, `pick?` | Single-model escape hatch |
| `list_models` | — | Known aliases → id_model |

All responses: `{ "ok", "api_version": 1, "data" | error fields }`.

## Errors (shared with CLI `--json`)

| `error_type` | `retryable` | Meaning |
|--------------|-------------|---------|
| `validation_error` | false | Bad input |
| `not_found` | false | No spot / no models |
| `ambiguous` | false | Multiple name hits → use `candidates` / numeric id |
| `parse_error` | false | Unexpected JSON shape |
| `http_error` | 429/5xx only | Upstream HTTP; may include `http_status` |
| `timeout` | true | Request timed out |
| `connection_error` | true | Network/DNS |
| `rate_limited` | true | Slow down |
| `unexpected_error` | false | Bug |

Client already retries with backoff. On `retryable: true`, wait seconds before at most 1–2 more attempts.

## Agent rules

1. Call `instruct` once if unfamiliar.
2. Ensure rider + home range (`get_profile` / `setup_profile`).
3. For “where can I kite?” call `weekend_spots`; else resolve a named spot.
4. Call `best_forecast` with `advise=true` for a single spot.
5. Do not scrape windguru.cz; never invent PRO lat/lon forecasts.

See also: [`WIRE.md`](WIRE.md), `guru instruct --json`, [`skills/guru/SKILL.md`](../skills/guru/SKILL.md).
