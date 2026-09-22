# MCP — `guru-mcp`

Same tools as the CLI. Prefer `weekend_spots` / `best_forecast` (advice on) over raw GFS.

## Install

```bash
pipx install 'windguru[mcp]'
which guru-mcp   # use full path in MCP config if needed
```

## Why Claude shell can’t hit Windguru (and how we fix it)

Anthropic’s **cloud sandbox shell** cannot dial `www.windguru.cz`. We do **not** ask humans to run tunnels.

**Turbo path:** the agent runs `guru wire` / `guru doctor` (or MCP `wire_mcp`). That installs local **STDIO** `guru-mcp` into Cursor / Claude Desktop / Claude Code. The MCP subprocess lives on the laptop → full network → Windguru works. Zero human config.

| Situation | Fix (agent does it) |
|-----------|---------------------|
| Cursor / Claude **Desktop** / **Claude Code** | `guru wire --json` → local STDIO MCP |
| Sandboxed shell can’t reach Windguru | Use wired MCP tools, not `curl` / raw shell |
| Claude.ai web custom connector only | Last resort: `guru-mcp-tunnel` (agent-started); prefer Desktop/Code STDIO |

## Run

| Command | Transport |
|---------|-----------|
| `guru-mcp` | STDIO — Cursor, Claude Desktop, Codex (local) |
| `guru-mcp-http` | Streamable HTTP at `http://127.0.0.1:8000/mcp/` (`GURU_MCP_HOST` / `GURU_MCP_PORT`) |
| `guru-mcp-tunnel` | HTTP + Cloudflare quick tunnel — prints `https://….trycloudflare.com/mcp/` for Claude connectors |

Requires `cloudflared` on PATH for the tunnel command.

### Which host?

| Host | Wire |
|------|------|
| **Cursor** | STDIO `guru-mcp` in MCP settings / `.cursor/mcp.json` (primary) |
| **Claude Desktop** | STDIO in `claude_desktop_config.json` — **not** the cloud sandbox |
| **Claude Cowork / claude.ai / Code cloud** | Remote custom connector: `guru-mcp-tunnel` → paste URL |
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

### Claude Cowork / claude.ai (remote) — one command

```bash
pipx install 'windguru[mcp]'   # once
# install cloudflared once: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
guru-mcp-tunnel
```

Copy the printed `https://….trycloudflare.com/mcp/` URL → Claude → Customize → Connectors → Add custom connector. Leave the tunnel running while you chat.

Anthropic’s cloud dials **you**; your laptop still talks to Windguru. See [custom connectors / remote MCP](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp).
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
