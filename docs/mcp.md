# MCP — `guru-mcp`

Same tools as the CLI. Prefer `weekend_spots` / `best_forecast` (advice on) over raw GFS.

## Install

```bash
pipx install 'windguru[mcp]'
which guru-mcp   # use full path in MCP config if needed
```

## Run

| Command | Transport |
|---------|-----------|
| `guru-mcp` | STDIO — Cursor, Claude Desktop, Codex (local) |
| `guru-mcp-http` | Streamable HTTP at `http://127.0.0.1:8000/mcp/` — for remote connectors |

### Which host?

| Host | Wire |
|------|------|
| **Cursor** | STDIO `guru-mcp` in MCP settings / `.cursor/mcp.json` (primary) |
| **Claude Desktop** | STDIO in `claude_desktop_config.json` |
| **Claude Cowork / claude.ai** | Remote custom connector only — public HTTPS URL to `guru-mcp-http` (Anthropic’s cloud dials you; localhost alone is not enough) |
| **Codex / shell agents** | Prefer CLI `guru … --json`; or local STDIO MCP if the client supports it |
| **ChatGPT cloud** | Needs a public HTTP MCP / Action you host — no local spawn |

### Cursor / Claude Desktop (local STDIO)

```json
{
  "mcpServers": {
    "guru": {
      "command": "guru-mcp"
    }
  }
}
```

### Claude Cowork / claude.ai (remote)

1. `guru-mcp-http`
2. Publish `https://<host>/mcp/` (tunnel or VPS) reachable from the public internet
3. Customize → Connectors → Add custom connector → paste URL

See Anthropic’s [custom connectors / remote MCP](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp) notes: the connection originates from Anthropic’s cloud, not your laptop.
## Tools

| Tool | Args | Returns |
|------|------|---------|
| `instruct` | — | Agent recipe (intake → weekend / best) |
| `setup_profile` | `intake?`, sport, weight_kg, **level**, kites, wetsuits, home_lat/lon, drive_km, session_hours… | Merged profile |
| `get_profile` | — | Profile + ready / range_ready / first_pass |
| `weekend_spots` | `hours?` (default 96), `limit?`, `top?` (default 3) | Day `schedule` + ranked spots |
| `search_spots` | `query`, `limit?` | Named spots (no lat/lon) |
| `near_spots` | `lat`, `lon`, `radius_km?`, `limit?` | Free map markers near a point |
| `resolve_spot` | `spot`, `pick?` | Spot id/name → spot |
| `best_forecast` | `spot`, `top?`, `hours?`, `pick?`, `advise?` (default true) | Weights + forecasts + `advice` |
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

1. Call `instruct` / `get_profile` / `doctor` — if `upgrade.update_available`, upgrade first.
2. If `first_pass`: show `intake.prompt_to_user` once (include **level**), then `setup_profile`.
3. For “where can I kite?” call `weekend_spots` and narrate **`schedule`** for the whole horizon.
4. For a named spot call `best_forecast` (advice on by default).
5. Do not scrape windguru.cz; never invent PRO lat/lon forecasts.

See also: [`WIRE.md`](WIRE.md), `guru instruct --json`, [`skills/guru/SKILL.md`](../skills/guru/SKILL.md).
