# Engineering Decisions and Open Questions

## Approved Step 5B decisions

Add only a read-only authenticated /submissions/upload-policy endpoint in the
existing submissions module. Return parser headers and configured byte/record/
time budgets, not copied browser defaults; generate the header-only template
locally from that response. No template endpoint, migration, worker or dependency.
Retain existing direct API sessions, generated types, TanStack Query and shared UI.

The upload endpoint is not idempotent: every accepted repeated file creates a new
candidate. Do not add hidden retries or offline queuing. A missing response cannot
prove rollback; history is a reconciliation aid, not proof that an absent candidate
will never commit. Show explicit uncertainty and require a deliberate new upload
decision. Form limits/context checks are convenience only; backend validation,
authorization and configured bounds remain authoritative. Uploading never validates
or activates; history labels never imply official APAAR verification.
Only 5B is implemented in this increment; validation/results, review/activation
interfaces, dashboards, cases and providers remain outside its scope.

## Approved Milestone 5 / 5A decisions

5A is metadata/session foundation only. Institution upload-to-activation precedes
the dashboard, in 5B–5E. Shared submission pages, current-only metrics, explicit
receipt confirmations and privacy invariants remain the approved full-M5 plan.
No backend enhancement is implemented before its frontend dependency exists.
Use direct local API requests, /me-authoritative identity, memory-only bearer
tokens, per-session query keys and cancellation/cache clearing; no auth framework,
proxy, persistence or silent renewal. UI visibility flags do not grant access.
Generated types are required; automated browser testing (Playwright) was removed
and is no longer part of the toolchain. openapi-typescript 7.13.0 currently
requires TypeScript 5; the user approved a separate locked tools/api-types package
with TypeScript 5.9.3, preserving application TypeScript 6.0.3. No peer bypass.
Demo statistics mean API-backed synthetic records, never hard-coded UI figures.
Marketing/hero, cases, advanced analytics, provider/ABC integration and configurable
CSV mapping remain deferred. Canonical local browser URL is http://localhost:3000
with the existing default CORS origin. Configure CORS explicitly for other origins.
Frontend .env.local contains only public API base/UI flag; API secrets stay private.

## Approved Milestone 4 decisions
Receipts freeze information presented, not proof of reading. Acknowledgment occurs
only during activation, including explicit omissions when present. Add one batch
receipt reference and reuse activated_at; no separate activation module/table.
Own administrators create/activate their own receipts; officers inspect, managers
receive aggregates. NOWAIT scope locking/revisions protect atomic provenance/audit;
replay is 409. Older never-activated uploads may be newly reviewed against the
current revision without rewriting upload-time baseline fields.
Select a completed structurally compatible INITIAL/REVALIDATION run. No silent
substitution, ACTIVATION run kind or peer scan under the lock. Material structural
changes require revalidation/new review; reuse current structural checks as an
additional safeguard. Cross-assessment freshness remains separate from eligibility.
Current-only totals distinguish declaration coverage. Omissions are not inferred
withdrawals, transfers or APAAR merges. Report previously ACTIVE omissions and
require acknowledgment, with no automatic size threshold. Synthetic/DEMO only.

## Approved Milestone 3 refinements

Use explicit INITIAL validation, not automatic UPLOAD validation, preserving M2's
processing-only contract. M4 references a selected run without an ACTIVATION kind.
Immutable completed
runs/findings are appended atomically with audit; no mutable processing runs or
finding review state. Existing source rows and unused apaar_match_hash stay intact.
Use the existing database/session/auth/error infrastructure and a dedicated
REPEATABLE READ validation transaction; no global locks or background framework.

LOCAL-DEMO-v1 pins configuration and explicitly selected DEMO intake version.
Missing APAAR produces REQUIRED_FIELD_MISSING rather than a duplicate format
finding. Additional exact rule codes/classifications are in docs/05. All findings
survive INCOMPLETE > FLAGGED > VALID precedence. VALID is local and run-specific.

Matching key is an environment SecretStr with no fallback; absent/short keys
cause a controlled validation failure, not zero duplicates. Only current ACTIVE
same-year overlaps contribute to the current metric. Other version matches are
informational AS_OF_RUN, not proven simultaneous enrolment or fraud. Same-year
scope/revision freshness is conservative; existing-scope candidate uploads do not
change revisions. Stale/incomplete current metrics are null, original evidence
remains immutable. Prototype peer comparisons are bounded, not a scalable search
index. Real-data security and production authentication remain separately gated.

## Confirmed for prototype
- Tech: Next.js/TypeScript/Tailwind, FastAPI/Python, PostgreSQL.
- Two primary portals: institution administrators and AICTE officers.
- Architecture source: five-section Lucidchart with ABC optional block after APAAR verification.
- Build first vertical slice: CSV -> normalized rows -> rule findings -> stored records -> officer dashboard.
- Data: synthetic only; APAAR/ABC providers simulated, clearly labeled.
- APAAR validation format differs from authorized identity verification.
- ABC credit reconciliation is optional; credit points/CGPA outside MVP.
- Cases support humans reviewing signals, including legitimate transfers.

## Explicit design assumptions (not official AICTE rules)

### User-approved Phase 0 foundation decisions

- Implement Phase 0 only before starting the upload slice. Defer institution/demo
  user seeds to Phase 1 with their tables and authentication. No business endpoints,
  landing page, dashboard, provider adapters, or machine learning in Phase 0.
- Feature-based backend modules own their routes/models/schemas/business logic;
  shared configuration, database engine/session and declarative base stay in core.
  Do not create unused module directories or empty security/services files.
- Use synchronous SQLAlchemy with Psycopg. Alembic initializes against shared
  metadata without empty revisions; business migrations arrive with their features.
- Public liveness is independent of PostgreSQL. Public readiness executes
  `SELECT 1`, returns 503 on database failure, and exposes no exception details.
  The API starts with valid configuration even while PostgreSQL is unavailable.
- Target Node 22.x (minimum 22.14.0), npm 11.x, Python 3.13.x and PostgreSQL 17.
  Pin direct package versions and retain npm/full Python dependency locks.
- All source stays in the project. Normal installed-tool execution, package
  caching and Docker-managed storage are allowed; unrelated user files/projects
  remain out of scope. No Git commands or commits are authorized.
- Root `.env` is local and ignored; `.env.example` contains only fictional local
  credentials. Phase 0 does not implement authentication; `DEMO_AUTH=false`.

### Existing demo assumptions
- Default CSV v1 schema and admission-category enum are chosen for demo.
- Seed intake caps come from fictional demo configuration.
- `DEMO_AUTH` is an early scaffolding convenience, not production authentication.
- Simplified role set, case statuses, endpoint naming and performance target are proposed.
- Simulated APAAR responses are fixture-driven rather than official provider behavior.

## Still to verify before real rollout
- Exact current AICTE rules on year/seat-category cap, applicable exceptions, programmes.
- Actual official APAAR validation and ABC provider onboarding, permissions and response schemas.
- Legitimate legal basis, consent mechanisms, data retention, permissible employer checks.
- Certificate display requirements and identity confirmation policy.
- Hosting environment, accessibility certification and security review.
- Desired true intake accounting treatment for withdrawn/transferred students.

## Scope protection
Do not add extra modules just because they sound innovative. Every new feature must map to AICTE official need or explicitly be an optional enhancement with a measurable user benefit.

## Known diagram limitation
The Lucidchart five-column schematic has had ABC added in-place; visual connector routing was not comprehensively confirmed. Engineering semantics in `docs/02_ARCHITECTURE.md` and `docs/05_VALIDATION_AND_ABC.md` supersede ambiguous arrow layout.

## Phase 1 decisions

Complete replacement snapshots require explicit activation. Scope-row locks and
revision checks protect current references; no global activation lock is planned.
Immutable validation runs retain rule configuration and comparison versions.
Missing names/dates and APAAR problems remain reviewable when counting is reliable.
Accounting and intake comparisons are explicitly DEMO, not official policy.

Strict CSV headers are a Phase 1 v1 limitation; configurable schema mapping is a
future enhancement. Reuse existing HTTP/error-handling infrastructure instead of
duplicating middleware, utilities or abstractions. The comparison freshness
mechanism is conservative and may trigger additional revalidation as institution
counts grow.

The execution scope and restricted authentication/seed policy are specified in
docs/07_IMPLEMENTATION_PLAN.md. Milestone 1 is API-only. These decisions document
planned behavior, not evidence that the features are implemented.
