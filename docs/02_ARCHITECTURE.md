# System Architecture — five-section design

## Approved Milestone 5 and Step 5A boundary

Use a feature-based Next.js portal with server page/layout structure and client
session/data/interaction components. Step 5A implements only explicit demo sign-in,
memory-only sessions, role navigation, shared responsive shell and real institution/
programme metadata. Later upload, validation, review/activation and dashboards are
built sequentially in 5B–5F; no placeholder business modules or pages are required.
Browser requests go directly to FastAPI with bearer authorization, no credential
cookies, proxy/BFF or server-side private-data hydration. Backend local/demo,
identity and institution guards remain authoritative. /me establishes identity;
account labels never assert roles/institution IDs. Clear token, cached data and
in-flight requests on logout/expiry; discard old-session responses by generation.
A hard refresh requires sign-in. No persistent browser token storage or renewal.
TanStack Query owns server-state requests; local React state owns form choices.
Generate API types from local OpenAPI without starting the API or connecting to
PostgreSQL. Application TypeScript remains 6.0.3. User-approved isolated
tools/api-types pins openapi-typescript 7.13.0 and TypeScript 5.9.3 because the
generator declares a TypeScript-5-only peer. Its generated output is checked by
the application's strict TypeScript 6 compiler. Separate package locks, no force.
No backend API/database enhancements are needed for 5A; add later approved
enhancements only when their corresponding frontend feature is implemented.

## Milestone 4 review and activation
Submissions owns immutable review information and explicit activation. A receipt
records information presented, not proof it was read. Confirmation occurs only in
the activation request. Shared REPEATABLE READ sessions provide consistent review
and summary reads; activation uses a fresh READ COMMITTED transaction.
Lock only the relevant scope with NOWAIT, recheck authorization, active scope,
processing, selected-run compatibility, structural eligibility and revision.
Atomically set one-time activation provenance, replace current pointer, increment
revision and append audit. Known lock/revision conflicts are 409. Different scopes
need no global lock; no workers, provider adapters or new feature module.
Reuse INITIAL/REVALIDATION runs explicitly. No silent latest-run substitution or
full validation under the lock. Reuse current structural checks as a safeguard
even if a version label was mistakenly retained. Material structural changes
require revalidation and a new review. Cross-assessment staleness is reviewable,
not an independent gate; activation can stale its own selected assessment.

## Primary agreed diagram
https://lucid.app/lucidchart/3d74f649-0d75-4eec-99ef-719259b80200/edit

The latest edit inserts purple **Optional ABC credit check** after authorized APAAR verification in Section 3. This doc defines desired behavior, not proof of live provider access.

## Logical pipeline
1. **Institution / Input:** login -> CSV/API/form upload -> correction workspace.
2. **Ingestion / Standardization:** append immutable `submission_batch`, map schema, normalize values, run format checks, calculate prior-version diffs.
3. **Verification / Exception Handling:** APAAR format + provider status (independent), optional ABC provider/credit reconciliation, cross-record/student journey checks, year-specific regulatory checks, review decision and linked findings.
4. **AICTE Trusted Data:** PostgreSQL source of truth, immutable version lineage, validation and provider status, encryption/RBAC/audit/consent controls.
5. **Intelligence / Official Actions:** institution dashboards, manager insights, review cases, follow-up and authorized verification.

## Component diagram in words
`Next.js Web` -> `FastAPI REST` -> `PostgreSQL`. FastAPI modules: `Auth/RBAC`, `Institutions`, `Submission ingest`, `Normalization`, `Rule Engine`, `APAARProvider adapter`, `ABCCreditProvider adapter`, `Findings/Cases`, `Analytics`, `Audit`.

Implement provider interfaces even when only simulated adapters exist. Keep core validation independent of external calls; run external checks after local normalization so provider outages do not compromise upload availability. An ingestion worker/task queue is a later performance optimization, not needed for MVP.

## Data flow and consistency
- Batch is created with `RECEIVED`, then `PROCESSING`, then `COMPLETED` or `FAILED`.
- Each parsed row creates a `student_record_version` tied to that batch. Past versions never disappear.
- Record-level validation outcome: `VALID`, `FLAGGED`, `INCOMPLETE` (not synonymous with identity verified).
- Independently track APAAR identity: `NOT_CHECKED`, `SIMULATED_MATCH`, `SIMULATED_MISMATCH`, `PENDING`, `SOURCE_UNAVAILABLE` (real provider values only when authorized).
- Optional ABC: `NOT_REQUESTED`, `SIMULATED_MATCH`, `SIMULATED_MISMATCH`, `PENDING`, `SOURCE_UNAVAILABLE`.
- A `finding` stores rule code, severity, source row, observed and expected values when non-sensitive, explanatory text, evidence references and review state.
- Upload success is separate from row acceptance; ingestion never silently discards bad rows.

## Ownership and isolation
Institution administrators only touch their own institutions. AICTE officers have cross-institution read/review scope; managers get aggregates. Verifiers receive narrowly scoped outputs and only after role/purpose/consent checks.

## Important separation
- **Institution-declared**: admitted student information supplied by college.
- **Locally validated**: internal data-format and rule checks.
- **Provider-verified**: only when authorized official source actually confirms.
- **Simulated**: deterministic mock responses for demo; unmistakably marked.

## ABC credits — optional, non-blocking branch
Post-APAAR stage may invoke authorized ABC service only when permission and requested field access exist. Compare source/institution/term/course/credits where aligned, record status and timestamp. If unpermitted or unavailable, mark as such. Do not reclassify APAAR identity, reject core submissions or fabricate academic-credit data.

## Security architecture
Pseudonymous logs, TLS for deployed environments, secret injection by env, hashed credentials, file size limits, MIME+content validation, CSV formula injection defense in exports, SQL parameterization, rate limiting, audit trail, least privilege and data minimization.

## Local repository layout (proposed)
```
/
  AGENTS.md
  README.md
  docs/
  apps/web/                # Next.js App Router
  services/api/            # FastAPI
    app/core/              # shared configuration, engine/session and base
    app/modules/           # feature-owned routes/models/schemas/logic
      health.py            # Phase 0 liveness and readiness, kept in one file
    alembic/
    tests/
  infra/docker-compose.yml
  samples/synthetic_admissions.csv
  .env.example
```
No frontend-to-database direct access. API is the policy enforcement point.

User-approved foundation refinement: feature modules replace global technical
layer folders. Add institutions, submissions, validation, verification, cases,
analytics, and authentication modules only when their working feature is built.
Each owns its SQLAlchemy models and Pydantic schemas as applicable. Keep database
connection/session configuration and Alembic centralized. Do not create empty
feature or security placeholders. Frontend shared shell code lives in
`src/components`; future feature-specific code belongs in `src/features/<feature>`.

Phase 0 uses synchronous SQLAlchemy with Psycopg. Engine creation is lazy and
shutdown disposes it. `/api/v1/health` is database-independent liveness;
`/api/v1/ready` checks PostgreSQL with `SELECT 1`. Neither route accesses business
data. PostgreSQL unavailability does not block application startup or liveness.

## Observability
Correlate requests and uploads by UUID; never log full APAAR identifiers. Include event `actor`, `institution_id`, `action`, `object_id`, `occurred_at` in audits. Report provider adapter type in tracing and UI.

## Phase 1 snapshot design — implementation staged by milestone

Uploads are complete replacement snapshots for one institution, programme and
academic year, including all declared admission categories. Uploading creates a
candidate; it never automatically changes the current dataset.

Activation uses a PostgreSQL row lock on the relevant submission scope and an
expected revision check. A changed revision returns 409 Conflict. Updating the
current reference, incrementing its revision and recording the activation audit
event occur in one transaction. No global activation lock is planned.

Cross-institution checks are reviewable assessments, not activation prerequisites.
Each assessment captures a consistent view of the compared scope revisions.
Changed revisions or newly appearing scopes make that assessment stale.
Concurrent activation in different scopes is permitted; it may make assessments
stale and require explicit revalidation.

This freshness mechanism is conservative: even an unrelated change within the
compared scopes may invalidate an assessment. As the number of institutions
increases, it may trigger additional revalidation. More selective dependency
tracking is a possible future enhancement, not part of the initial implementation.

Feature modules own their applicable models, schemas, routes and services.
Authentication exposes one replaceable token-verification interface through
the current-user dependency. Only the restricted demo implementation is planned
for Milestone 1; no production authentication implementation is claimed.

Reuse the existing HTTP/error-handling infrastructure wherever possible, including
the existing application and CORS middleware configuration and FastAPI exception
handling. Extend shared handling only for missing requirements such as the agreed
error envelope and request IDs. Do not duplicate middleware/utilities or mandate
a new HTTP abstraction or file when the existing structure is sufficient.

No workers, queues, event-sourcing framework or provider adapters are required
for Phase 1.

## Milestone 3 — local validation boundary

The feature-owned validation module evaluates an already stored COMPLETED candidate
only after an explicit action. Upload success remains independent of validation.
Use a short-lived REPEATABLE READ PostgreSQL transaction, chosen before its first
statement; recheck the actor and institution scope within that transaction.
Persist the complete run, findings and action audit atomically. Never mutate source
rows, their unused matching-hash column, current pointers or scope revisions.
No global locks are needed. A partial unique index permits one INITIAL run per
batch; concurrent initial requests return one 201 and one 409. Officer
revalidations append independent immutable runs.

Current ACTIVE same-year cross-institution overlaps are separate from INFO
historical, inactive, different-year and unactivated-candidate matches. Complete
same-year scope/revision maps determine current-assessment FRESH/STALE status.
Historical/candidate matches are AS_OF_RUN: uploading into an existing scope does
not increment its revision. This conservative freshness mechanism may require
additional revalidation as institutions grow. Freshness is independent of local
record validity, and stale/incomplete current-overlap metrics are null, never
silently zero or resolved. Original evaluation evidence remains available.
