---
name: guru
description: >
  Install and use guru (Windguru CLI + MCP). Use for first-pass rider intake,
  guru setup/weekend/best, home drive range, or Cursor/Claude MCP.
license: MIT
---

# guru install and usage skill

## Primary path (PyPI)

```bash
pipx install windguru
pipx install 'windguru[mcp]'
```

## First pass (mandatory if profile empty)

1. Run `guru instruct --json` or `guru profile --json`
2. If `first_pass` / `ready=false` / `range_ready=false`: **show `intake.prompt_to_user` to the human once**
3. Wait for **one** reply (key=value paste)
4. `guru setup --intake '<their paste>' --json`
5. Continue with weekend / best

**Do not** ask sport, then weight, then kites separately. One message. One reply.

Example paste:

```text
sport=kitefoil weight=78 level=intermediate kites=7,9,12 wetsuits=3/2,4/3 session=3 home=41.39,2.17 drive_km=200 range=Trabucador → Leucate
```

## After onboarded

- "Where can I kite this weekend?" → `guru weekend --json`
- Named spot → `guru best <id> --advise --json`
- Narrate advice (gusts, kite, 2–4h wetsuit, checklist)

Never scrape windguru.cz. Never require PRO.
