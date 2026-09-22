# Data Engineering Standard: The Gray / Stonebraker Bar

Every stored fact in `rubikmd-backend` has one writer, one clock, and an
effectively-once projection. Dual-writes, silent null of gold sources, a
foreign key that would delete gold with jobs, and plaintext notes in any
warehouse are strictly forbidden.

Jim Gray: put all the eggs in one basket and watch that basket. Michael
Stonebraker: that basket is Postgres. Exactly-once delivery across two
systems does not exist. At-least-once plus an idempotent sink does.

Law: [`.cursor/rules/path-a-gold.mdc`](../.cursor/rules/path-a-gold.mdc).
Pipeline: [`gold_store.md`](gold_store.md). Keys: [`encryption-at-rest.md`](encryption-at-rest.md).
Code shape: [`code_quality.md`](code_quality.md).

Automated enforcement: gold tests + `verify_gold_store.py` + `verify_encryption_at_rest.py`.

---

## 1. Architectural Layers (one mode per fact)

Reis lifecycle, mapped onto the existing rank DAG. Lower ranks never import
higher ranks. A later mart reads `gold_index`, never `job_charts.note_body`.

```
Generate (clinic PC, not our process):
  convert · leftover marks · NAK sign · bound hashes

Working store (mutable, short clock):
  [20] ingest / anonymize / ocr / charts   accept gates
  [25] jobs.entity                         identity, contract hash
  [30] store                               jobs, job_charts, decisions, audit

Immutable archive (append-only, gold clock):
  [35] gold                                JSONL allowlist, GOLD key, bucket, outbox

Orchestrate / serve:
  [45] review                              coded decisions (sibling object)
  [55] jobs  [60] worker                   SKIP LOCKED claim, flush, reaper
  [80] api                                 portal, export (stateless)

Eval gold (different word, different repo):
  rubikmd-evals labeled fixtures           synthetic / public; no clinic PHI
```

| Mode | What | Mutability | Clock |
|---|---|---|---|
| Working | `jobs` + `job_charts` + leases | mutable | ~30 days, then hard-delete |
| Gold archive | object + `gold_index` | append-only | product life; no FK to jobs |
| Serve | portal poll, reports, `gold_export` | read | request |
| Marts later | eval slices / customer-bucket fine-tune | built from snapshots | pin by sha256 |

Do not stand up Iceberg, Spark, Kafka, Debezium, dbt, Airflow, or a second
warehouse copy of notes. Postgres plus encrypted JSONL is the warehouse
until volume forces a mart. Data Vault and one-big-table as the write path
are forbidden.

### Two words named "gold"

- **Gold archive**: Path A remainder after convert + NAK (`app/gold/`).
- **Eval gold**: labeled fixtures in `rubikmd-evals` (BoardQA, ClinOCR, `gold_briefs.py`).

Do not train on live `job_charts`. Promote archive → eval only through
`scripts/gold_export.py`, pinned by `object_key` + `sha256` + `schema_version`.

---

## 2. Hard Constraints

### Path A only

Identifiable charts stay on the clinic PC. Rubik receives the Safe Harbor
remainder after leftover gate + NAK + bound hashes (FAQ 2085). FAQ 544
(convert after arrival) and FAQ 2077 (encrypted host that still sees PHI)
are closed. Path B and Path C stay closed. A leftover unused Safe Harbor
type is still PHI.

### One writer, no dual-write

A fact has one commit. The second store is an outbox relay from that commit,
not a second `COMMIT`. App write to Postgres *and* bucket / Redis / SQS /
warehouse in two independent commits is a defect (Kleppmann).

### Two clocks

| Clock | What | Action |
|---|---|---|
| Working | notes next to email, `case_number`, `safe_name` | hard-null after gold ack; expire ~30d |
| Gold pending | `ready` + `gold_status` in `{pending, failed}` | hold to 90d, log it |
| Gold archive | object + `gold_index` | keep; survives job delete |
| Not gold | cancelled / mismatch / stuck / exhausted | null now; do not archive |

`clinics.gold_retain` defaults to 1. Off is explicit, then skip + null today.

### Declared grain

- Job object: one finished list (`job_id`), one JSONL line per chart.
- Decision object: one coded click (`job_id`, `idx`), written later.
- Rater score export: one coded click (`dataset_id`, `item_id`, `rater_id_hash`).
  `schema_version` 2. `rater_id_hash` is an HMAC under `RATER_EXPORT_KEY`.
  `action` and `reason_code` only. The explanation and the email stay on the
  working row, which is the rater queue. Not a line in the clinic gold object.
- `dt` in the key is `finished_at` UTC, not write time (retry lands on the same key).
- Do not mix grains. Do not put one chart per object (3,300 PUTs/hour) or
  one clinic-week per object (rewrite + mix).

### Schema-on-write

The builder is the contract. Unknown or forbidden keys raise at any depth.
`schema_version` lives on every line and in the path (`gold/v1/`). Consumers
ignore unknown *non-identity* keys; producers never delete a key a shipped
reader still reads. Breaking change = `v2` beside `v1`.

DDL is expand, then migrate, then contract. Additive columns first. Drop,
rename, or type-change only after nothing reads the old shape. Dual-writing
two columns during expand is allowed. Dual-writing two systems is not.

### SLIs (not API uptime)

- **Freshness**: `ready` → `gold_status=stored`. Warn if pending > 15m; error > 2h.
- **Completeness**: every retain=1 ready job is `stored` or `skipped` or
  parked `failed`; HEAD `Content-Length` equals ciphertext bytes;
  `gold_index.charts` equals JSONL chart lines.
- **Correctness**: leftover fixture, allowlist raise, AAD fail-closed,
  payload / attestation / HITL hashes bind.

---

## 3. Functional Core, Imperative Shell

Pure (deterministic, no I/O):

- `leftover_hits()` gate
- `build_job_lines` / `build_decision_lines` allowlist
- object key layout, `item_id_hash`, digest bind
- grain and SLI arithmetic

Shell (I/O, retries, leases):

- PUT → HEAD size → `gold_index` → `stored` → `null_notes` (one transaction)
- `FOR UPDATE SKIP LOCKED` claim (charts and gold flush)
- expire sweep, decisions snapshot, `gold_export`

Frozen dataclasses for gold lines. Fail closed (`ValueError` / HTTP 400).
Do not `SELECT *` into a builder. Do not join or score inside the builder
(that is a mart).

---

## 4. Data Protection & Cryptographic Zero-Trust

- Working notes and results: AES-256-GCM, `PHI_ENCRYPTION_KEY`.
- Gold objects: AES-256-GCM, `GOLD_ENCRYPTION_KEY`, AAD `gold.job.v1`.
- Same wire (`enc1:`). Different HKDF info. PHI ciphertext opened as gold
  must fail. Railway volume / bucket AES is Layer 1; app GCM is the control.
  Railway Buckets have no SSE-S3 and no versioning.
- Production: `GOLD_*` lives on the worker, not on API replicas, once
  `rubikmd-worker` exists. Staging still embeds the worker.
- Never archive: `email`, `signer_name`, `safe_name`, `case_number`,
  `subject`, `reason_text`, `decided_by`, `note_body`, `worker_id`,
  `lease_until`. The patient map stays on the clinic PC.
- Never log notes, signer names, session tokens, or gold plaintext.
  Trace with `audit_hash`. Audit actions `gold.store` / `gold.decisions` /
  `gold.export` carry the object digest only.
- Do not claim leftover-free, OCR-certified, or a product HIPAA seal.
  Do claim HIPAA Safe Harbor-compliant de-identification when Path A meets
  §164.514(b)(2). Director copy never says `remainder`. The signed fourth
  line is locked in `portal/contract.js` `STATEMENT`.

Train / eval pin `schema_version` + object key + sha256. Split keys are
`clinic_id` / `job_id` / `item_id_hash` / `idx` only.

---

## 5. PostgreSQL, Queue, and the Outbox

Postgres is the system of record and the queue. Redis or SQS as a *primary*
job broker while the payload lives in Postgres is a dual-write.

```
pending_upload → queued → running → ready | cancelled
chart: queued → leased → done | failed     (lease 180s, heartbeat 60s, max 3)
gold:  pending → stored | skipped | failed (max 10 attempts, one claim per tick)
```

- Pool only: `run_read` / `run_write`. Parameterized `%s`. No string
  interpolation into SQL. Identifiers are allowlisted, never bound.
- Claim = `SELECT … FOR UPDATE SKIP LOCKED` + status flip in the same
  statement. Clinic-fair (`in_flight ASC`, then FIFO). Reaper exists.
- Hold the lease across the LLM call; do not hold the SQL transaction.
- Gold outbox: `ready AND gold_status='pending' AND gold_attempts < 10`.
  Inbox is `gold_index` PK + HEAD ack. Retry is the same key, `ON CONFLICT`.
- `gold_index` has **no FK** to `jobs`. Clinician delete and `expire_jobs`
  cannot take the only pointer. Snapshot failure must not block delete.
- `note_body` is nulled in the same transaction as `gold_status=stored`.
  Failed PUT or HEAD mismatch leaves notes and counts one attempt.
- Cancelled / mismatch / stuck / exhausted: null immediately, not gold.
- Do not null `note_body` on `ready` while gold is configured.
- Do not expire ready+pending/failed at 30 days.
- API instances hold zero in-memory job maps.

`jobs.status` and `job_charts.status` are application machines (no CHECK
yet). `jobs.gold_status` is CHECKed: `pending|stored|skipped|failed`.
Do not invent a fifth gold state.

---

## 6. Machine Readability & Contracts

- Gold line keys sorted, UTF-8, one record per line, provenance repeated
  so a split line is still a training example.
- Object key:
  `gold/v1/clinic=<id>/dt=<YYYY-MM-DD>/job=<id>.jsonl.enc`
  (sibling `….decisions.jsonl.enc`). Ids are `[A-Za-z0-9_-]`.
- `mypy --strict`, `__all__`, no em-dash (`\u2014`), no `print()`.
- pytest is the contract (not ODCS / Great Expectations / Monte Carlo).
  Add those only when a second team consumes the archive.
- When marts exist: staging = allowlist reshape; marts = grain-declared
  facts built only from gold. No `SELECT *` from working identity columns.

---

## 7. Verification Commands

```bash
# 1. Architecture DAG (imports, ranks, cycles)
python scripts/check_code_quality.py

# 2. Working-store ciphertext
python scripts/verify_encryption_at_rest.py

# 3. Archive: index ↔ object, size, digest, no plaintext
python scripts/verify_gold_store.py
# python scripts/verify_gold_store.py --sample 5

# 4. Schema, outbox, clocks, allowlist, AAD, no-FK
python -m pytest -q tests/test_gold_schema.py \
  tests/test_gold_store.py tests/test_gold_flush.py \
  tests/test_encryption_at_rest.py

# 5. Director copy lockstep (keep line; never "remainder")
#    in rubikmd-frontend: portal/copy.test.mjs
```

Export for evals: `python scripts/gold_export.py` (refuses an API-only
service once the worker is split). It also refuses forbidden fields and any
decision key outside `GOLD_DECISION_KEYS`. Do not treat `pg_dump` as gold.
