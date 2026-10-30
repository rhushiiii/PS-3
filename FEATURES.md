# PRAVYA — Feature List & Idea Slide Content

**Project:** SIH26263 — APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions

> Prototype scope note: All government integrations (APAAR, ABC, DigiLocker, API Setu) are **simulated** in this prototype and permanently labeled `SIMULATED / DEMO DATA`. No official verification is claimed.

---

## 1. Idea Slide Content (copy-paste ready)

### Title
**PRAVYA — One Trusted Pipeline for Admission Data: Upload, Validate, Verify, Review**

### The Problem (2–3 lines)
AICTE-approved institutions submit student-level admission data in inconsistent formats. Officers have no single view of what is valid, duplicated, or suspicious — and no evidence trail behind the numbers they must regulate on. Manual checking is slow, error-prone, and unauditable.

### The Solution (2–3 lines)
PRAVYA gives institutions a guided upload pipeline that standardizes student data, validates APAAR format and admission rules, detects potential duplicates across institutions, and preserves every version immutably. AICTE officers get an evidence-linked review workspace with cases, integrity signals, and analytics — every number traceable to its source row.

### Key Features (bullets)
- **Standardized ingestion** — CSV/XLSX upload with server-enforced policy (size, row budget, canonical headers), immutable record versions, and idempotent retries.
- **Deterministic validation engine** — required fields, academic year, enrollment date, APAAR *format* checks, in-batch and cross-institution duplicate detection, and intake-capacity comparisons — every issue becomes an evidence-linked finding, never a silent discard.
- **Potential (not verdict-based) duplicate detection** — privacy-preserving token matching (raw identifiers never stored in plain form) with context classification so legitimate transfers/withdrawals are reviewable, not auto-flagged as fraud.
- **Simulated APAAR identity verification** — provider interface with deterministic demo adapter, consent/purpose capture, per-day attempt limits, and replay detection; results clearly labeled `SIMULATED`.
- **Officer review cases** — prioritized case queue with assignment, due dates, escalation, immutable action history, and notification fan-out.
- **Snapshot review & activation** — explicit, one-time activation with immutable review receipts; corrections are new submissions, never overwrites.
- **Intake governance** — audited capacity-rule changes, declared totals, immutable assessments, and a what-if simulator (category-aware, never a single blended cap).
- **Integrity signals** — rule-based risk signals (data quality, change ratios, repeated corrections, stale data) with officer decisions; explicitly *not* fraud determinations.
- **Analytics & exports** — enrolment trends, submission completeness, intake utilisation, case performance, plus reconciled CSV/XLSX/PDF report exports.
- **Audit trail everywhere** — every login, validation, activation, case action, and export recorded as a redacted audit event, browsable via an audit explorer.
- **Role-based access** — four roles (Institution Admin, AICTE Officer, AICTE Manager, Authorized Verifier) with server-side role and institution scoping on every endpoint.

### Tech Stack (one line)
Next.js 16 + TypeScript + Tailwind (web) · FastAPI + Pydantic v2 + SQLAlchemy 2 (API) · PostgreSQL 17 + Alembic (database) · JWT demo auth · Ed25519-signed demo credentials.

### Why It Wins (differentiators)
- **Privacy by design:** APAAR numbers are masked in logs, URLs, and audit payloads; duplicate matching uses HMAC tokens, not raw IDs.
- **Trust by construction:** immutable versions and DB-level triggers make history tamper-evident; "approved" always means *internally validated*, never *government-verified*.
- **Honest AI posture:** rules surface findings; only human officers make regulatory decisions.
- **Working end-to-end:** ~655 automated tests including a scripted 12-step demo validated against ground-truth expectations.

---

## 2. Full Feature List

### 2.1 Authentication & Access Control
| Feature | Description |
|---|---|
| Demo authentication mode | Clearly labeled `DEMO_AUTH` mode issuing HS256 JWTs with short TTL, loopback-only access, and origin allow-listing. |
| Four roles | `INSTITUTION_ADMIN` (institution-scoped), `AICTE_OFFICER`, `AICTE_MANAGER`, `AUTHORIZED_VERIFIER` — enforced server-side on every endpoint. |
| Session management | Frontend session provider with expiry tracking, generation-based in-flight request invalidation, and automatic 401 handling. |
| Audit of logins | Every demo login writes a `DEMO_LOGIN` audit event with timestamp and actor. |

### 2.2 Data Ingestion (Submissions)
| Feature | Description |
|---|---|
| Upload policy endpoint | Backend-advertised limits: max bytes (5 MiB), max rows (1000), accepted formats, canonical headers, downloadable template. |
| CSV/XLSX parsing | Hardened multipart parsing with format detection, deadline-budgeted parsing, and strict header validation. |
| Immutable record versions | Each candidate row is stored as a versioned record with normalization, provenance, and masked sensitive identifiers. |
| Idempotent uploads | Optional per-institution `Idempotency-Key` with fingerprint checking; replays return the original response (200 + `Idempotent-Replayed`). |
| Submission history | Paginated, institution-scoped history with programme/year filters and candidate/current/previous batch labels. |
| Row browsing | Per-batch row listing with per-record validation status. |

### 2.3 Validation Engine
| Feature | Description |
|---|---|
| Rules engine | Deterministic local ruleset (`LOCAL-DEMO-v1`): `REQUIRED_FIELD_MISSING`, `INVALID_ACADEMIC_YEAR`, `INVALID_ENROLLMENT_DATE`, `INVALID_APAAR_FORMAT` (format-only, configurable length), `DUPLICATE_IN_BATCH`, `POTENTIAL_CROSS_INSTITUTION_DUPLICATE`, `MISSING_INTAKE_RULE`, `INTAKE_EXCEEDED`. |
| Findings, not discards | Every issue is an evidence-linked finding with rule ID, severity, classification, and affected-record evidence — nothing fails silently. |
| Severity & blocking | Structural missing fields are activation-blocking errors; others are reviewable warnings. |
| Privacy-preserving duplicate detection | In-batch grouping and cross-institution matching use HMAC-SHA256 tokens of identifiers; raw APAAR values are never compared or stored in plain form. |
| Duplicate context classification | Matches classified as current-active, current-inactive, different-year, historical, unactivated candidate, or local-inactive — "potential" by design, reviewable by humans. |
| Immutable validation runs | Runs and findings are append-only (DB trigger protected); revalidation creates a new run. |
| Feedback CSV export | Formula-injection-safe feedback file so institutions can fix rows and re-upload. |
| Validation guardrails | Missing/short matching key returns a structured 422 (never a silent clean pass); comparison record caps prevent silent truncation. |

### 2.4 Review, Receipts & Activation
| Feature | Description |
|---|---|
| Immutable review receipts | Snapshot review recorded once; receipts cannot be edited (DB trigger protected). |
| Explicit activation | One-time activation with scope revision checks, structural blockers, concurrency-safe (row-locked), and provenance capture. |
| Snapshot semantics | Activated batch becomes the institution's current snapshot; activating a new batch stales older candidates and dependent assessments. |
| Omission acknowledgments | Review captures declared omissions before activation. |
| Corrections as new batches | Prior submissions are never overwritten; corrections enter as fresh candidate batches. |

### 2.5 APAAR Identity Verification (Simulated)
| Feature | Description |
|---|---|
| Provider interface | `APAARProvider` protocol with a deterministic `MockAPAARProvider` fixture adapter — no real government integration. |
| Simulated outcomes | `SIMULATED_MATCH`, `SIMULATED_MISMATCH`, `SOURCE_UNAVAILABLE`, `SOURCE_TIMEOUT`, `PENDING` — all labeled `SIMULATED`. |
| Consent & purpose | Explicit consent/purpose fingerprint required per request; default deny when absent. |
| Abuse controls | Per-day attempt cap, retry-of-validation semantics, and replay detection. |
| Append-only history | Verification results stored once (trigger-protected) with per-record history endpoint. |
| Status distinction | `SOURCE_UNAVAILABLE` vs `PENDING` vs `MATCH` vs `MISMATCH` are never conflated. |

### 2.6 Officer Cases
| Feature | Description |
|---|---|
| Case creation & queue | Officers open cases from findings; queue supports filters and pagination. |
| Workflow | Assignment (with assignee directory), priority/severity, due dates by priority, overdue escalation, resolution reasons, immutable event history. |
| Evidence linkage | Cases link directly to record versions, findings, and verification evidence. |
| Notifications | In-app notifications with unread counts, per-item and mark-all read. |

### 2.7 Intake Governance
| Feature | Description |
|---|---|
| Rule-change history | Audited, immutable capacity rule changes per institution/programme/category/year. |
| Declarations | Institutions declare intake totals; stored immutably. |
| Assessments | Immutable comparisons of declared totals vs activated snapshot rows per seat category (never a blended cap). |
| What-if simulator | Category-aware capacity simulator for planning scenarios. |

### 2.8 Integrity Signals
| Feature | Description |
|---|---|
| Rule-based signals | Data-quality/identity issues, snapshot change ratios, repeated correction requests, stale programmes, case-derived signals. |
| Scoring & bands | Weighted score with configurable MEDIUM/HIGH thresholds and overview of institutions requiring review. |
| Officer decisions | Append-only decision records per institution. |
| Honest framing | Signals are advisory flags — explicitly *not* fraud determinations; only officers make regulatory calls. |

### 2.9 Records Registry
| Feature | Description |
|---|---|
| Cross-batch registry | Searchable, filterable registry of student record versions across batches with tenant scoping. |
| Provenance detail | Per-record detail with version history, findings, and linked cases. |
| Snapshot-aware state | Current vs historical vs candidate record states. |

### 2.10 Dashboards, Analytics & Reports
| Feature | Description |
|---|---|
| Institution dashboard | Current-snapshot metrics for institution admins. |
| AICTE officer dashboard | Multi-institution directory with profile, intake panels, and integrity signals. |
| Manager dashboard | Aggregate-only view (no per-record access). |
| Analytics explorer | Enrolment trends, submission completeness, intake utilisation, case performance — clearly labeled synthetic/demo aggregates. |
| Report exports | Reconciled CSV/XLSX/PDF exports with rate-limited download endpoints. |

### 2.11 Audit Trail
| Feature | Description |
|---|---|
| Action events | Timestamped, actor-attributed events for logins, validations, activations, case actions, exports, and more. |
| Redaction | Sensitive identifiers scrubbed from event payloads and application logs. |
| Audit explorer | Filterable, paginated event browser with distinct-action listing. |

### 2.12 Demo Credentials (Simulated)
| Feature | Description |
|---|---|
| Signed credentials | Ed25519-signed, Verifiable-Credential-style demo admission credentials (issue, list, revoke). |
| Offline verification | `POST /verify` validates signature and status without DB writes; verification log kept. |
| Key management | Configurable signing key, key ID, issuer, TTL; issuing without a key fails safely with 422. |

### 2.13 Platform & Engineering Quality
| Feature | Description |
|---|---|
| OpenAPI-first contract | FastAPI publishes OpenAPI; frontend types generated from it (`api:generate` / `api:check` pipeline). |
| Uniform pagination | `Page<T>` envelope with bounded page sizes across all list endpoints. |
| Structured errors | Consistent `{error: {code, request_id}}` bodies with shared exception handling. |
| Middleware stack | Body size limits, security headers, CORS, log redaction, request IDs, sliding-window rate limiting (per-user and per-IP buckets). |
| Consistent reads | Repeatable-read snapshot sessions for multi-statement validation reads. |
| Migrations | Linear Alembic chain (0001–0012), one migration per feature, with DB triggers enforcing immutability of history tables. |
| Seeded demo data | Deterministic synthetic seeds (3 fictional institutions, 2 demo programmes, 7 demo users); refuses to run outside local demo mode. |
| Test suite | ~655 pytest tests with real PostgreSQL: per-module coverage, tenant scoping, concurrency, immutability, security hardening, a route-sweep that verifies every endpoint's role decision, and a scripted 12-step E2E demo validated against `expected.json`. |
| Typed frontend | TypeScript strict mode, shared UI components, accessible responsive layout, empty/loading/error states. |

---

## 3. Roles → Capabilities Matrix

| Capability | Institution Admin | AICTE Officer | AICTE Manager | Authorized Verifier |
|---|---|---|---|---|
| Upload / validate / activate submissions | ✅ | — | — | — |
| View own institution dashboards | ✅ | — | — | — |
| Browse all institutions, intake, integrity | — | ✅ | ✅ (aggregates only) | — |
| Open/manage cases | — | ✅ | — | — |
| APAAR (simulated) verification | — | ✅ | — | ✅ |
| Integrity decisions | — | ✅ | — | — |
| Analytics & reports | — | ✅ | ✅ | — |
| Audit explorer | — | ✅ | ✅ | — |
| Demo credentials (issue/verify) | ✅ | — | — | ✅ |

---

## 4. Status & Roadmap

**Implemented:** Ingestion → validation → review → activation pipeline; simulated APAAR verification; officer cases; notifications; intake governance; integrity signals; records registry; dashboards; analytics; reports; audit explorer; demo credentials; full test suite.

**Remaining / staged:**
- Accessibility & responsive polish pass (step 5F).
- Deeper case-management UI depth and marketing pages.
- Optional ABC credit reconciliation (simulated) — planned as non-blocking extension.
- Docs 03 (data model) and 04 (API contract) need refresh against the live OpenAPI.
- Key rotation, multi-process rate limiting, and dashboard pagination beyond first 100 institutions.

---

## 5. How PRAVYA Works — End-to-End Pipeline

### Step 1 — Upload (Standardize)
An institution admin uploads a student admission file (CSV/XLSX). The platform enforces a **backend-defined upload policy**: file size cap (5 MiB), row budget (1,000 rows), canonical headers, and a downloadable template. Every row is normalized and stored as an **immutable, versioned record** with provenance metadata — the original file is never mutated. Retries are safe: an `Idempotency-Key` fingerprint means a re-upload returns the original result instead of creating duplicates.

### Step 2 — Validate (Find, Don't Discard)
A deterministic rules engine checks every row: missing required fields, academic-year format, enrollment date sanity, and APAAR **format** (digit length/shape — explicitly *not* identity verification). Duplicates are detected two ways: within the batch, and across institutions. Every problem becomes an **evidence-linked finding** — rule ID, severity, affected records, row numbers — so nothing fails silently and nothing is discarded without a trace.

### Step 3 — Review (Human in the Loop)
The institution reviews findings in a validation workspace with per-rule guidance, exports a formula-injection-safe **feedback CSV**, fixes rows offline, and re-uploads corrections as a **new batch** — never overwriting history. When satisfied, they submit a **review receipt** (immutable) and explicitly **activate** the batch — a one-time, concurrency-safe action that promotes it to the institution's *current snapshot*.

### Step 4 — Verify (Simulated, Honest)
Optionally, records go through APAAR identity verification via a **provider interface** backed by a deterministic simulated adapter. Consent and purpose are captured per request, daily attempt limits apply, and every outcome (`SIMULATED_MATCH`, `SIMULATED_MISMATCH`, `SOURCE_UNAVAILABLE`, `PENDING`) is **permanently labeled SIMULATED** — the prototype never claims real government verification.

### Step 5 — Monitor (Officer View)
AICTE officers see everything with evidence: officer cases with priorities/due dates/escalation, intake governance (declared vs actual, category-wise), integrity signals (data quality, suspicious change ratios, repeated corrections), records registry with full provenance, and an audit explorer. Managers see aggregate-only analytics. Every dashboard number traces back to its source rows.

### Step 6 — Audit (Trust)
Every login, validation run, activation, case action, verification attempt, and export writes a **redacted audit event** — timestamped, actor-attributed, and browsable. History tables are protected by **database triggers**, not just application code: even a compromised app process cannot rewrite the past.

---

## 6. Novelty — What Makes PRAVYA Different

### N1. "Potential, not verdict" duplicate detection
Existing solutions either miss duplicates or auto-accuse institutions of fraud. PRAVYA classifies every cross-institution match by **context** (current-active, current-inactive, different-year, historical transfer, unactivated candidate) — because a legitimate transfer/withdrawal can explain a match. Duplicates are *reviewable findings*, never automated accusations. *(Invariant: "Duplicate across institutions is potential." )*

### N2. Privacy-preserving matching by design
Cross-institution duplicate detection runs on **HMAC-SHA256 tokens** of identifiers — raw APAAR numbers are never compared, logged, or stored in plain form across institutions. One institution's data never exposes another's. *(This is real privacy engineering, not a checkbox.)*

### N3. Format ≠ Identity — an honest APAAR boundary
PRAVYA is explicit where most demos fudge: APAAR **format validation is local**; **identity verification needs authorized government access**. The prototype ships a provider interface with a simulated adapter, and every simulated result carries `source_type=SIMULATED` with a visible `SIMULATED / DEMO DATA` label. Swapping in a real authorized provider later changes one adapter — not the architecture.

### N4. Tamper-evident history at the database level
Immutability isn't a UI convention — **PostgreSQL triggers** block UPDATE/DELETE on validation runs, findings, review receipts, activations, verification results, case history, and integrity decisions. Corrections are always *new versions*. The audit story survives even application-level compromise.

### N5. Findings, never silent discards
Most pipelines drop bad rows and report a clean success. PRAVYA has no silent path: every validation issue is a finding with rule ID + evidence; a misconfigured matching key returns a structured error (never a "clean" zero-duplicate result); comparison caps raise a visible limit error instead of quietly truncating. **The system is honest about what it does and doesn't know.**

### N6. Evidence-linked everything
Every number an officer sees traces to source rows: findings link to record versions and row numbers; cases link to findings and verification evidence; dashboards read from activated snapshots with provenance. No black-box aggregates.

### N7. Statuses that don't lie
The platform keeps **independent statuses** — validation status, APAAR verification status, ABC reconciliation status — and distinguishes `SOURCE_UNAVAILABLE` from `PENDING` from `MATCH` from `MISMATCH`. "Approved" always means *internally validated*, never *government-verified*. This prevents the classic failure of demos that blur these into one green checkmark.

### N8. Category-aware intake governance
Intake capacity is compared per `academic_year` × `programme` × `seat_category` against configured approved capacity — never a single blended cap — with audited rule-change history, immutable declared totals, immutable assessments, and a what-if simulator.

### N9. Human-in-the-loop integrity posture
Integrity signals (change ratios, repeated corrections, stale data) are **advisory flags with evidence** — explicitly *not* fraud determinations. Only human officers make regulatory decisions. The system is built to *assist judgment*, not replace it.

### N10. Verified by construction
~655 automated tests against a real PostgreSQL instance — including a **route-sweep test that proves every endpoint has a server-side role decision**, immutability tests, concurrency tests, tenant-isolation tests, and a scripted 12-step demo validated against ground-truth expectations. The claim "it works" is test-backed.

---

## 7. Data Integrity & Trust Model

| Layer | Mechanism |
|---|---|
| **Row level** | Every student record is a versioned, immutable entity (`StudentRecordVersion`) with provenance; the source file is parsed once, then never mutated. |
| **Batch level** | Batches are candidates until reviewed; activation is one-time, concurrency-safe (row locks), and captured with provenance; activating a new snapshot stales older candidates. |
| **History level** | DB triggers make validation runs, findings, review receipts, activations, verification results, case events, intake changes, and integrity decisions append-only. Corrections are new records. |
| **Consistency level** | Multi-statement validation reads run under `REPEATABLE READ` snapshot isolation, so a report can't mix two moments in time. |
| **Identity level** | HMAC-token matching means raw sensitive identifiers never flow between institutions or into logs/audit payloads; UI masks APAAR except in authorized detail views. |
| **Access level** | Server-side role **and** institution scoping on every endpoint (enforced by a route-sweep test), not just hidden frontend buttons. |
| **Accountability level** | Redacted audit events for every consequential action, browsable by officers with filters. |
| **Communication level** | Independent statuses + explicit `SIMULATED` labeling + "approved ≠ verified" semantics prevent over-claiming at every UI surface. |

**One-line summary:** *PRAVYA treats data integrity as a property of the system's construction (immutability, isolation, tokens, audit) rather than a promise.*

---

## 8. Security & Privacy Design

- **Sensitive identifier handling:** APAAR numbers are masked in UI, excluded from URLs and log outputs (automated log-redaction middleware), and never stored raw in audit payloads.
- **Auth:** JWT bearer sessions with short TTL, issuer/audience/jti claims; demo accounts only behind labeled `DEMO_AUTH` mode restricted to loopback with origin allow-listing.
- **Authorization:** Role checks + institution scoping server-side on every endpoint; a test sweeps all routes to assert a reviewed access decision exists.
- **Input hardening:** Body-size limits, row budgets, parse deadlines, format detection, formula-injection-safe CSV output, structured error codes (no stack traces to clients).
- **Rate limiting:** Sliding-window per-user and per-IP buckets on sensitive buckets (auth, verification, exports).
- **Credentials:** Ed25519-signed demo credentials with key ID, issuer, TTL; issuing without a configured key fails safely.
- **CORS:** Loopback-only in demo mode, enforced by configuration validators.

---

## 9. Impact & Relevance to AICTE

- **For institutions:** Guided, self-service pipeline — fewer rejected submissions, actionable feedback CSVs, clear status of what's pending and why.
- **For AICTE officers:** Evidence-linked review instead of blind trust — cases, integrity signals, and analytics that trace to source rows, cutting investigation time.
- **For students:** Duplicate/identity issues surface early and are reviewable, protecting legitimate transfers from false flags.
- **For the ecosystem:** A reference architecture for how APAAR-based monitoring *should* handle privacy, immutability, and honest verification boundaries when real integrations arrive.

---

## 10. Slide-by-Slide PPT Kit

**Slide A — Title:** PRAVYA — One Trusted Pipeline for Admission Data: Upload, Validate, Verify, Review. *(SIH26263)*

**Slide B — Problem:** Institutions submit inconsistent, unverifiable student admission data; AICTE officers regulate on numbers they can't trace. No evidence trail, no duplicate visibility, no audit story.

**Slide C — Solution:** A working platform: standardized ingestion → deterministic validation with evidence-linked findings → human review & one-time activation → simulated APAAR verification (honestly labeled) → officer cases, integrity signals & analytics → audit trail everywhere.

**Slide D — Key Features:** (pick 4–5 from Section 1 bullets; lead with *standardized ingestion*, *evidence-linked validation*, *potential-duplicate detection*, *immutable audit history*.)

**Slide E — Novelty:** Lead with N1 (potential-not-verdict duplicates), N2 (HMAC privacy-preserving matching), N3 (format ≠ identity boundary), N4 (DB-trigger immutability), N5 (no silent discards).

**Slide F — Integrity & Trust:** Show the pipeline as a chain with locks: immutable versions → one-time activation → trigger-protected history → redacted audit → role-scoped access. Punchline: *"History that can't be rewritten; numbers that trace to rows."*

**Slide G — Tech Stack:** Next.js 16 + TypeScript · FastAPI + Pydantic v2 + SQLAlchemy 2 · PostgreSQL 17 + Alembic · JWT demo auth · Ed25519 credentials · ~655 automated tests.

**Slide H — Demo Flow:** The 8 seeded scenarios tell a story: valid upload → APAAR format issues → in-batch duplicates → cross-institution match (transfer context) → intake excess → missing population → corrected re-upload → activation. Each produces visible, evidence-linked findings.

**Slide I — Impact:** Faster, evidence-backed officer review; fewer false fraud accusations (context-aware duplicates); privacy-safe cross-institution visibility; honest boundary for future government integration.

**Slide J — Roadmap:** 5F accessibility polish → deeper case UI → optional simulated ABC reconciliation (non-blocking) → docs refresh → key rotation & multi-process rate limiting.

---

*All data in this prototype is synthetic; all institutions and identifiers are fictional. See `AGENTS.md` and `docs/09_DECISIONS_AND_ASSUMPTIONS.md` for hard rules on government-integration claims.*
