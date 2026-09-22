---
name: guru
description: >
  Install and use guru (Windguru CLI + MCP). Use when setting up windguru with pipx,
  running guru best/spots/near, configuring Cursor/Claude with guru-mcp, or teaching
  an agent the WINDGURU_DEFAULT top-3 forecast recipe.
license: MIT
---

# guru install and usage skill

## Primary path

1. `pipx install 'windguru[mcp]'` (or from checkout: `pipx install -e ".[mcp]"`)
2. Until PyPI is live: `pipx install 'windguru[mcp] @ git+https://github.com/berendgort/guru.git'`
3. CLI: `guru`
4. MCP STDIO: `guru-mcp`
5. MCP HTTP: `guru-mcp-http` only when needed

Do not default to cloning the repo unless the user wants to contribute.

## Agent workflow (always)

1. `guru instruct --json` (or MCP `instruct`) if unfamiliar
2. Resolve a **named spot**: `guru spots "<place>" --json` or `guru near --lat --lon --json`
3. `guru best <id> --json` — WINDGURU_DEFAULT Tune → top 3 models → forecasts
4. Ignore lower-weighted models unless asked for a specific `guru forecast -m`

Never scrape windguru.cz. Never ask for PRO credentials for core forecasts.

## JSON contract

Success: `{"ok": true, "api_version": 1, "data": ...}`  
Failure: `{"ok": false, "api_version": 1, "error", "error_type", "retryable"}`  
Ambiguous spot: `error_type: "ambiguous"` + `candidates[]`.

## Claude / Cursor MCP config

```json
{
  "mcpServers": {
    "guru": {
      "command": "guru-mcp"
    }
  }
}
```

Find the binary with `which guru-mcp` after pipx ensurepath.
