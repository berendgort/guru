<!--
guru product north star. Tag this file on product / scoring / agent work.
Job: name the rider outcome. Metrics are not the outcome.
-->

# Objective function — offload the kite call

## One line

**Help a kiter pick the right spot and session so they have the most pleasure on the water — with guru doing the forecast thinking for them.**

If every metric is green and the rider still drives to the wrong beach, under-rigs, freezes mid-session, or stares at Windguru tabs for an hour — we failed.

---

## Downstream goal (the maximand)

| Layer | Wrong | Right |
|-------|-------|-------|
| **Objective** | max forecast accuracy / CLI coverage / MCP tool count | **The rider arrives ready** — right place, right window, right kite/suit, clear GO / MARGINAL / NO-GO — without doing the model-blend homework |
| **Metric** | “the goal” | a slice we use to *check* (parse OK, weekend ranks, advice fields present) |
| **Fail** | Perfect JSON, rider still confused or unsafe | Metric green, session worse → we failed |

**Principals:** kiters (and agents helping them) who would otherwise burn evenings on windguru.cz Tune tabs.

**Pleasure** here means: powered and in control for their sport/level, comfortable for a real 2–4h session, worth the drive, low regret after. Not “any wind somewhere.”

**Offload the thinking** means: one intake → `weekend` / `best --advise` → a kiter-voice call. Agents follow the README protocol; humans do not re-derive WINDGURU_DEFAULT weights.

---

## What “right spot” means

Work backwards from the beach, not from the API.

1. **Worth going** — GO (or honest MARGINAL for locals); long haul (>150 km) needs ≥2h continuous GO. Soft home vs solid far: report both.
2. **Fits the rider** — sport (kite / foil / surfkite), level (incl. expert), quiver, suit ladder, session length, home range, local spot notes.
3. **Sized for reality** — size for **average**; gusty → warn (beginners stay MARGINAL). Foil light-wind rules ≠ twin-tip.
4. **Safe enough to say out loud** — side-shore preference when known; offshore = advanced-only if determinable; beach 5-min check in **agent voice** (not CLI preach).
5. **Decidable in one breath** — spot, window, kite, suit, verdict. Horizon = top-3 model data; beyond that: we have not hacked time yet.

---

## How to find the goal (guru tasks)

Ask, in order:

```
1. What are we building / changing in guru?
2. If this works, how does a kiter’s next session get better (or easier to decide)?
3. If we maxed JSON schema / test pass / scrape coverage and that session is *not* better — did we succeed?
4. No → those are proxies. The session/decision sentence is the objective.
5. What could we optimize that *looks* like a better CLI while missing better rides?
6. What must never happen even if it raised adoption? (hard constraints)
```

If (2) is “be agent-friendly” or “SOTA MCP,” keep walking: friendly *so the rider gets on the water with the right kit*.

---

## Proxies (useful — not the maximand)

| Proxy | What it checks | How it Goodharts |
|-------|----------------|------------------|
| Fixture / parser tests green | Wire still works | Ship a parse that never advises |
| `weekend` returns N spots | Scanner runs | Rank noise; send people 200 km for 7 kt |
| Advice always suggests a kite | Fields filled | Ignore gust spread / owned quiver |
| More models / PRO paths | “Completeness” | Complexity, ToS risk, no clearer call |
| Agent pastes README and runs | Onboarding works | Agent dumps JSON; rider still decides alone |

**Patient test → rider test:** high score, humans not helped on the water, still “success” → rewrite the objective.

---

## Hard constraints (pass/fail)

| # | Constraint |
|---|------------|
| C1 | **Honesty** — MARGINAL / NO-GO when it’s soft; never hype a long drive. Say uncertainty as uncertainty. |
| C2 | **Free-only core** — named spots + WINDGURU_DEFAULT. No PRO lat/lon click-forecast requirement. |
| C3 | **No HTML scrape** of forecast table / Tune / MapLibre as the primary path. |
| C4 | **Safety voice** — gust sizing, offshore caution, beach check. Never optimize “more sessions” over “don’t get hurt.” |
| C5 | **Ambiguity** — `error_type: ambiguous` + candidates; never silent first-match spot id. |
| C6 | **One-shot intake on first message** — sport/weight/**level**/quiver/range **once**; level required; never skip to weekend. |
| C7 | **Corrigible** — if the rider says the call is wrong for their local knowledge, listen; don’t argue the model. |

---

## Product mapping (score the goal)

| Rider question | guru move | Success looks like |
|----------------|-----------|-------------------|
| “What do you need from me?” | `instruct` / first-pass intake → `setup` | One paste; profile `ready` + `range_ready` |
| “Where can I kite?” | `weekend` | Ranked spots in drive range; far trips need clearer GO |
| “How’s Castelldefels?” | `best <id> --advise` | Verdict + window + kite from quiver + suit for session hours |
| Agent pasted the GitHub link | README protocol | Install PyPI → intake → weekend/best → **kiter narration** |

Default preset: **WINDGURU_DEFAULT** only. Raw `forecast -m gfs` is an escape hatch, not the product.

---

## Temporary objective function (this product)

```
maximize  rider pleasure on the water via a clear, honest spot+gear call
          with forecast thinking offloaded to guru (CLI / MCP / agent)
subject to
  C1 honesty (no hyped GO; gusts and drive distance named)
  C2 free-only / no PRO dependency
  C3 no HTML scrape primary path
  C4 safety voice in checklist / advice
  C5 ambiguous spots never silently resolved
  C6 one-shot intake for agents
  C7 rider can override with local knowledge
do not treat as objective:
  raw model count, bench F1, stars, “feels like a complete Weather API”
```

---

## Agent / ship contract

When this file is tagged on a task:

1. State the rider outcome in one line (not “add flag X”).
2. Name proxies and the Goodhart surface.
3. Keep C1–C7.
4. **Call:** next action that improves the beach decision, not the dashboard.
5. If shipping: SHIP only if a dry-run still produces a usable kiter-facing call (`weekend` or `best --advise`).

```
Deploy gate
SHIP  — goal still rider pleasure + offloaded thinking; dry-run advice is honest; constraints hold
HOLD  — metrics up, narration/decision quality unproven
KILL  — scrape/PRO shortcut, silent ambiguous match, or “always GO” to juice engagement
```

---

## Anti-patterns (guru-specific)

| Fake win | Why it fails the rider |
|----------|------------------------|
| Dump three model tables, no verdict | Thinking not offloaded |
| First fuzzy name match to a private spot id | Wrong beach |
| “GO” on 8 kt gust 18 so the tool feels useful | Regret / incident risk |
| Ask 10 onboarding questions | Agents (and humans) bounce |
| Worldwide spot dump in the wheel | Stale data; miss live `near`/`spots` |
| Optimize for PRO unlock | Breaks free product promise |

Manipulation test: would we still publish this objective if a kiter read the scoring code *and* the last `weekend` JSON we showed them?

---

## Learned

| When | Finding |
|------|---------|
| 2026-09-22 | Product maximand is **spot + pleasure + offloaded thinking**, not forecast-API completeness. `weekend` / `best --advise` + one-shot intake are the spine. |
| 2026-09-22 | CLI audit: `best` advice now **default on**; pass home→spot `drive_km` into advice (same honesty as weekend); instruct steps lead with weekend/best not spots/near. |
| 2026-09-22 | CLI/MCP **kite-bro voice** (`guru/rider/voice.py`): SEND IT / SOFT CALL / SIT IT OUT + beach vocab; machine verdicts unchanged; agents follow `instruct.voice` while keeping C1/C4 honesty. |
