# Backend Engineering Standard: The Korotkevich / Tourist Bar

Every line of code in `rubikmd-backend` must meet an elite, competitive-programming standard of mathematical clarity, modular purity, and machine readability. Sprawling monoliths, circular imports, hidden state mutations, and ambiguous contracts are strictly forbidden.

Automated enforcement: `python scripts/check_code_quality.py`

---

## 1. Architectural Layers & Dependency Hierarchy

The backend enforces a strict downward directed acyclic graph (DAG). Lower-rank layers cannot import from higher-rank layers. Cross-layer cycles are fatal.

```
Foundation (Cross-Cutting - Importable by any layer):
  app.config · app.metrics · app.rate_limit

Domain & Service Hierarchy (Strict Monotonic Layer Ranks):
  [10] security     (AES-256-GCM envelope crypto, key rotation)
  [15] auth.email   (canonical email normalization, audit hashing)
  [20] anonymize    (PHI detection, regex spans, harbor/masking)
  [20] ingest       (file format parsing, text extraction)
  [20] ocr          (scan gate classification, lockstep unread rule)
  [22] charts       (chart validation, sample bundles, note cleaning)
  [22] rater        (practice-chart schema, independent scores, invite roster)
  [25] jobs.entity  (Job, case_number, result_index, contract hashing)
  [30] store        (Postgres repositories, pg pool, SQL persistence)
  [35] gold         (Path A remainder archive: JSONL allowlist, GOLD key, bucket, outbox)
  [40] auth         (cookie signing, allowlist, session lifecycle)
  [45] review       (SuperGLP eval pins, LLM prompt stack, brief generation)
  [48] speech       (recorded audio to text; nothing stored; OpenRouter transcriptions)
  [50] mail         (transactional Resend/SMTP delivery, pace control)
  [55] jobs         (job creation, acceptance, queue row formatting)
  [60] worker       (async worker service, lease heartbeats, queue polling)
  [75] http         (FastAPI middleware, request tracing, error mapping)
  [80] api          (route handlers, request schemas, status codes)
  [90] main         (FastAPI application assembly and lifespan)
```

### Invariants
- **Zero Circular Dependencies**: Absolutely no cycles at module or package level.
- **Downward Imports Only**: Higher layers may import lower layers; lower layers never import higher layers (e.g. `store` never imports `review`, and `charts` never imports `jobs.service`).
- **Zero Import Side Effects**: Modules must never execute I/O, connect to databases, or inspect live network resources upon being imported.
- **Circular Import Elimination Strategies**:
  - Extract shared hashing/identity primitives (`audit_hash`) to foundational utility layers (`app.auth.email`).
  - Move cross-cutting transport protocols (`retry_after_s`) into foundational utilities (`app.rate_limit`).
  - Enclose type-only dependencies within `if TYPE_CHECKING:` guards.
  - Keep package `__init__.py` files as pure, thin facade re-exports without circular references back into internal implementation submodules.

---

## 2. Hard File Size Cap: <= 250 Lines of Code

No file in `app/` should exceed **250 lines of code**. When a module approaches this limit, decompose it into focused, single-responsibility submodules grouped inside a cohesive package with an `__init__.py` facade:

- **`app/charts/`** (was 446 LOC):
  - `hitl.py`: Director attestation digests, cryptographic receipt/fingerprint checking, and HITL gate requirements.
  - `fingerprint.py`: Public HITL key sets, note text formatting, and attestation/notes fingerprint hashing.
  - `normalize.py`: Chart validation, note text extraction, case numbering, and safe patient labeling.
  - `samples.py`: Practice sample bundles and demonstration payloads.
  - `__init__.py`: Unified public re-exports maintaining complete backward compatibility.
- **`app/mail/`** (was 375 LOC):
  - `templates.py`: Responsive email HTML formatting, typography tokens, and copy builders.
  - `transport.py`: Low-level SMTP and Resend wire dispatch and idempotency keying.
  - `send.py`: Transactional notifications, invites, contracts, and format request triggers.
- **`app/store/`** (was 366 LOC):
  - `job_cleanup.py`: Periodic TTL expiration sweeps, contract PDF cleanup, and timeout handling.
  - `jobs.py`: Core PostgreSQL row upserts, chart persistence, and retrieval queries.
- **`app/worker/`** (was 563 LOC):
  - `claim.py`: PostgreSQL FOR UPDATE SKIP LOCKED batch claiming with clinic-fair round robin.
  - `processor.py`: Chart review execution, lease heartbeat renewal, and persistence.
  - `reaper.py`: Lease expiration recovery, attempt exhaustion failure handling, and stuck job cancellation.
  - `service.py`: Concurrent worker event loop and lifecycle orchestration.
- **`app/security/`**:
  - `cipher.py`: AES-256-GCM cipher primitives, rotation keyrings, and envelope formatting.
  - `phi_crypto.py`: Process singleton lifecycle, key status reporting, and functional encryption facades.
- **`app/jobs/`**:
  - `contract_store.py`: Local filesystem and S3 storage backends for encrypted contract PDFs.
  - `contract.py`: Signed statement byte marker validation and director attestation verification.
- **`app/api/auth/`** (was 328 LOC):
  - `login.py`: Password sign-in and logout with granular failure auditing.
  - `links.py`: Magic links and password reset consumption without credential loss.
  - `account.py`: Password change, signature, profile, and mail preferences.
  - `me.py`: Session identity and fresh-link state inspection.
  - `shared.py`: Regex validation cards and payload helpers.
- **`app/api/admin/`** (was 274 LOC):
  - `usage.py`: Clinic usage statistics and historical job pagination.
  - `staff.py`: Clinic staff listing and role assignment.
  - `settings.py`: Weekly quota, gold retain switches, and tuning thresholds.
  - `shared.py`: Admin permission dependency.
- **`app/api/jobs/`** (was 312 LOC):
  - `create.py`: Review job inception, expected chunk bounds, and chunked upload assembly.
  - `read.py`: Historical listing and status polling with ETag caching.
  - `actions.py`: Job cancellation and soft deletion with gold decision snapshotting.
- **`app/review/`**:
  - `wire.py`: OpenRouter URL safety validation, HTTP error recovery, and payload shaping.
  - `client.py`: Resilient chat completion execution with fleet slot limiting and backoff retries.

---

## 3. Functional Core, Imperative Shell

- **Pure Business Logic**: Core algorithms (PHI detection, token matching, score computation, row formatting) must be deterministic functions of their inputs.
- **Explicit Invariants**: Validate preconditions and bounds on function entry. Fail closed (raise `HTTPException` or `ValueError`) on invalid inputs.
- **Immutable Domain Objects**: Prefer `@dataclass(frozen=True)` or typed dictionaries for internal transfers. Avoid mutable shared objects across async boundaries.

---

## 4. Data Protection & Cryptographic Zero-Trust

- **Zero Plaintext PHI in Persistence**: Patient notes and review results stored in Postgres must be encrypted with AES-256-GCM using `PHI_ENCRYPTION_KEY`. The Path A remainder archive uses `GOLD_ENCRYPTION_KEY` (AAD `gold.job.v1`).
- **Zero Plaintext PHI in Logs or Metrics**: Never log raw notes, patient identifiers, or session tokens. Use `audit_hash` (truncated SHA-256) for tracing.
- **Leftover Detection at the Gate**: Ingested notes must pass `leftover_hits()` inspection before job creation. Dirty notes are rejected immediately with HTTP 400.
- **Gold retain**: After Path A convert + NAK, keep the cleaned remainder (`app/gold/`). Do not null `note_body` on `ready` while gold is configured. Law: `.cursor/rules/path-a-gold.mdc`.
- **Attestation & Receipts**: Client chart bundles must match SHA-256 digests on receipt and contract signing before jobs enter the queue.

---

## 5. PostgreSQL & Queue Engine Hygiene

- **Connection Pool Discipline**: All database interactions use `psycopg_pool.AsyncConnectionPool` via `run_read` / `run_write` helpers. Never leak raw connections.
- **Zero SQL String Concatenation**: Every SQL query must use parameterized placeholders (`%s`). String interpolation into SQL is forbidden.
- **Concurrency & Fair Leases**: The worker queue uses `SELECT ... FOR UPDATE SKIP LOCKED` with explicit lease timeouts and clinic-fair round-robin scheduling.
- **Stateless API**: API instances carry zero persistent in-memory job state; Postgres is the single source of truth.

---

## 6. Machine Readability & Type Enforcement

- **Strict Mypy Compliance**: `mypy --strict` passes with 0 errors across all source files.
- **Explicit Exports**: Every library module must define `__all__` to publish its public interface and decouple internal implementation helpers.
- **No Em-Dashes**: Strictly no unicode em-dash (`\u2014`) in any API responses, error messages, or logs.
- **Zero Print Statements**: Use structured `logging.getLogger("rubikmd.<subsystem>")`. Never use bare `print()` in application code.

---

## 7. Verification Commands

```bash
# 1. Architecture, layer hierarchy, line count, and cycle checks
python scripts/check_code_quality.py

# 2. Strict static analysis & linting
ruff check .
mypy app scripts/check_code_quality.py

# 3. Test suite execution (100% deterministic, 588+ tests)
export DATABASE_URL="postgresql://rubik:rubik_password@localhost:5432/rubik_portal"
python -m pytest -q -m "not live_review"
```
