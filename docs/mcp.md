# MCP — optional adapter (CLI is canonical)

**Universal path for every app:** local `guru … --json` on a machine that reaches Windguru.
`guru-mcp` is the **same library** over STDIO for hosts that spawn MCP processes — not a second product, not a Claude-specific tunnel.

```bash
pipx install 'windguru[mcp]'
guru doctor --json          # probe + upgrade (does not wire MCP)
guru where --json           # canonical (~3 days)
guru-mcp                    # optional STDIO — same tools
guru wire --json            # ONLY if shell guru unavailable + MCP host needs it
```

## Sandbox / allowlist failures

If `doctor` / `instruct` reports `network.reachable: false`, the **runtime** cannot dial Windguru. MCP JSON and Cloudflare tunnels do not fix that. Move to a **local** agent host (Cursor Agent, Claude Code/Desktop on the laptop, Codex shell, etc.) and run `guru` there. Never invent forecasts. Never ask the human to paste connector URLs.

## Optional MCP

| Command | Transport |
|---------|-----------|
| `guru-mcp` | STDIO — any host that can spawn a local process |
| `guru wire --json` | Opt-in only — when shell `guru` cannot run and local STDIO MCP is required |
| `guru-mcp-http` | Local HTTP at `http://127.0.0.1:8000/mcp/` |
| `guru-mcp-tunnel` | Escape hatch only — not the default path |

```json
{
  "mcpServers": {
    "guru": {
      "command": "guru-mcp"
    }
  }
}
```

Agents use the CLI. Call `guru wire` / `wire_mcp` only when absolutely necessary (no shell `guru` + MCP host missing guru). Humans are not asked to edit configs.

## Tools

| Tool | Args | Returns |
|------|------|---------|
| `instruct` | — | Agent recipe (intake → where / best) + `path` + `network` |
| `wire_mcp` | `status_only?` | Optional local STDIO adapters |
| `setup_profile` | `intake?`, sport, weight_kg, **level**, kites, wetsuits, home_lat/lon, drive_km, session_hours… | Merged profile |
| `get_profile` | — | Profile + ready / range_ready / first_pass |
| `where_spots` | `hours?` (default 72), `limit?`, `top?` | ~3-day `schedule` + ranked spots |
| `weekend_spots` | `hours?` (auto to Sunday), `limit?`, `top?` | Fri eve / Sat / Sun; `uncertain` + `coverage` |
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

1. Call `instruct` / `get_profile` / `doctor` — check `network.reachable` and `upgrade.update_available`.
2. If `first_pass`: show `intake.prompt_to_user` once (include **level**), then `setup_profile`.
3. For “where can I kite?” call `where_spots`. For “this weekend?” call `weekend_spots` and narrate **`schedule`**; if `uncertain`, say high-% models are not in range yet.
4. For a named spot call `best_forecast` (advice on by default).
5. Do not scrape windguru.cz; never invent PRO lat/lon forecasts.

See also: [`WIRE.md`](WIRE.md), `guru instruct --json`, [`skills/guru/SKILL.md`](../skills/guru/SKILL.md).
