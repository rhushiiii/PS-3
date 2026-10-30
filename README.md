# SIH26263 — Codex Project Context

**Project:** APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions  
**Status:** Implementation specification for a hackathon prototype; no production government integration is claimed.  
**Stack:** Next.js + TypeScript + Tailwind CSS (web), FastAPI + Python (API), PostgreSQL (database).

## Start here

1. `AGENTS.md` — operational instructions for Codex (read before making changes).
2. `docs/01_PRD.md` — problem, product scope, personas, MVP, acceptance criteria.
3. `docs/02_ARCHITECTURE.md` — five-section architecture, flows, trust boundaries.
4. `docs/03_DATA_MODEL.md` — PostgreSQL entities, relationships, constraints, indexing.
5. `docs/04_API_CONTRACT.md` — REST endpoints, payloads, pagination, errors.
6. `docs/05_VALIDATION_AND_ABC.md` — deterministic validation, APAAR mock, optional ABC reconciliation.
7. `docs/06_UI_UX.md` — required pages, information architecture, visual direction.
8. `docs/07_IMPLEMENTATION_PLAN.md` — vertical slices and Codex task prompts.
9. `docs/08_TESTING_SECURITY.md` — test cases, security, demo definition of done.
10. `docs/09_DECISIONS_AND_ASSUMPTIONS.md` — explicit decisions and unresolved details.

## Source hierarchy

- **Official-context paraphrase:** `SIH2026_AICTE_Five_Problem_Statements.pdf`, section SIH26263 on page 3. This source file is an October 2026 structured paraphrase, not verbatim official portal copy. Review original at https://www.sih.gov.in/sih2026PS for changes.
- **Agreed design:** the five-section diagram edited with an optional ABC credit block:
  https://lucid.app/lucidchart/3d74f649-0d75-4eec-99ef-719259b80200/edit
- **These docs:** proposed engineering decisions for a functional demonstration. They do not claim official AICTE approval, access or mandates.

## Key distinction

APAAR _format validation_ is local; _identity verification_ needs authorized external integration. Simulated responses must be permanently labeled `SIMULATED`. ABC credit reconciliation is an **optional extension** and cannot block core admission monitoring.

## Hand-off to Codex

Put `AGENTS.md` at the repository root. Copy the `docs/` folder there. Then ask Codex to implement **Phase 0 + Phase 1** from `docs/07_IMPLEMENTATION_PLAN.md`, requesting tests and command output. Do not ask it to implement every feature in one pass.

## Implemented scope — Phase 0, Phase 1 Milestones 1–4 and Milestone 5 Steps 5A–5E

The repository contains the Next.js shell, FastAPI health/readiness,
PostgreSQL/Alembic foundation, institution/programme/intake/user/audit models,
synthetic seeds and restricted demo authentication. Milestone 2 adds bounded
candidate CSV ingestion, immutable submitted rows, provenance, and scoped
upload/history/detail/row APIs. Milestone 3 adds local student validation,
immutable runs and evidence-linked findings, scoped result/history APIs and
formula-safe feedback CSV. Milestone 4 adds immutable review receipts, explicit
transactional activation with scope revision checks, omission acknowledgments,
activation provenance and current-only institution summaries. Milestone 5A adds
the responsive portal shell, in-memory local demo sessions, generated API types,
and API-backed institution/programme metadata pages. Step 5B adds institution CSV
upload, backend-configured upload policy and template, paginated submission history,
programme/year filters and candidate/current/previous labels. Step 5C adds local
validation results, immutable-run selection and evidence-linked findings. Step 5D
adds snapshot review and explicit activation. Step 5E adds API-backed institution,
AICTE officer and aggregate-only manager dashboards using current activated
snapshots. Step 5F accessibility/responsive polish remains staged. Cases, marketing
pages and APAAR/ABC provider integrations remain unimplemented.

### Runtime and dependency policy

- Target Node.js **22.x**, minimum **22.14.0**, and npm **11.x**.
- Target Python **3.13.x**; development verification uses **3.13.7**.
- PostgreSQL **17.11**, with an immutable multi-platform image digest in
  `infra/docker-compose.yml`.
- Web direct dependencies use exact versions; `package-lock.json` locks the
  dependency graph. Use `npm ci` for repeatable installation.
- API direct dependencies use exact versions in `requirements*.txt`;
  `requirements.lock` records the full development graph. Install with the lock
  as constraints to pin transitive dependencies too. Dependency updates are
  deliberate, followed by the checks below. Pins do not replace security review.
- No global package installation or Git commands are needed.

Tooling limitation: Next.js's bundled lint plugins currently declare support for
ESLint 9, so it is pinned despite npm's deprecation notice. ESLint 10 produces an
invalid peer dependency graph with those plugins. Upgrade when the plugin set
supports it; do not bypass peer validation with force/legacy-peer-deps.
Next.js build/tracing roots are scoped to `apps/web`, avoiding workspace discovery
in unrelated parent directories.

### Windows PowerShell setup

Run from the repository root. Start Docker Desktop with its Linux engine first.
The example contains only fictional local credentials. Keep `.env` local.

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
python -m venv services/api/.venv
& services/api/.venv/Scripts/python.exe -m pip install -r services/api/requirements-dev.txt -c services/api/requirements.lock
Push-Location services/api
& .venv/Scripts/python.exe -m alembic upgrade head
& .venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-proxy-headers --reload
```

The API command stays running. No PowerShell virtual-environment activation or
execution-policy change is required. Settings load the repository-root `.env`
regardless of the working directory; process environment variables take precedence.
If PostgreSQL's host port or credentials change, update `DATABASE_URL` to match.
Percent-encode special characters in URL credentials.

In a second PowerShell terminal, from the repository root:

```powershell
Push-Location apps/web
npm ci
npm run dev
```

If PowerShell blocks the npm script shim, use `npm.cmd` instead of `npm`.
Web: http://localhost:3000 · API docs: http://127.0.0.1:8000/docs.
Follow the local portal instructions below to enable its demo UI and backend
authentication. The frontend uses server page/layout structure with client
session, API-query and interaction components. Public web configuration contains
only the local API URL and explicit demo UI flag; backend secrets stay private.

From another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/ready
```

Liveness returns 200 without contacting PostgreSQL. Readiness executes `SELECT 1`
and returns 200 or 503. PostgreSQL failure must not prevent API startup or liveness.
Configuration must still be valid; a missing or non-PostgreSQL `DATABASE_URL` is
a setup error. Connection, pool, and statement timeouts limit ordinary database
waits; they are not an absolute end-to-end deadline across network retries.

### Alembic workflow

Milestone 1 migration `0001_institution_foundation` creates institutions,
programmes, intake_rules, users and audit_events. Run `alembic upgrade head`,
`alembic current` and `alembic check` from services/api using the project virtual
environment. Feature models are explicitly imported in alembic/env.py; there is
no startup create_all. Downgrade/upgrade round trips are tested only in a temporary
test database, never by clearing the development database.

### Checks

Backend, from `services/api`:

```powershell
& .venv/Scripts/python.exe -m ruff check .
& .venv/Scripts/python.exe -m ruff format --check .
& .venv/Scripts/python.exe -m mypy
& .venv/Scripts/python.exe -m pytest
& .venv/Scripts/python.exe -m pip check
& .venv/Scripts/python.exe -m alembic upgrade head
& .venv/Scripts/python.exe -m alembic current
```

Frontend, from `apps/web`:

```powershell
npm run lint
npm run format:check
npm run typecheck
npm run build
```

Compose, from the repository root:

```powershell
docker compose --env-file .env -f infra/docker-compose.yml config --quiet
docker compose --env-file .env -f infra/docker-compose.yml exec -T postgres psql -U sih_demo -d sih26263 -c "SELECT 1;"
```

Use the configured user/database if you changed the example. Automated tests cover
liveness without a database connection, successful readiness, connection/query
failures, pool timeout, response redaction, and actual connection refusal.
Those tests do not require a running database. Verify successful real PostgreSQL
readiness and the migration commands separately with Compose running.

### Local security and lifecycle

Health/readiness and OpenAPI are public infrastructure metadata. Identity and
institution APIs enforce backend authentication and role/institution permissions.
DEMO_AUTH defaults to false; when disabled, demo login is absent and demo bearer
tokens are rejected. No production authentication backend is implemented.
PostgreSQL, web, and API bind to loopback. CORS defaults to the local web origin
`http://localhost:3000`; explicitly configure `CORS_ORIGINS` when using another
browser origin. Database URLs are secret settings, SQL parameters are hidden,
and readiness never returns the underlying connection exception.

Stop application terminals with Ctrl+C. Stop PostgreSQL without deleting its
volume using `docker compose --env-file .env -f infra/docker-compose.yml stop`.
Package caches and Docker-managed storage may live outside the repository;
application source and the API virtual environment stay inside it.

## Phase 1 execution status and local demo

Milestones 1–4 and Milestone 5 Steps 5A–5E are implemented; Step 5F remains staged.
Demo access requires direct loopback requests, approved local
hosts/origins, APP_ENV=local, DEMO_AUTH=true and a separately generated signing
secret. Never expose this mode through a deployment, reverse proxy or tunnel.
Tokens expire after 900 seconds by default; expired sessions return
401 SESSION_EXPIRED without silent renewal. No passwords are used.

From services/api, after installing requirements and starting PostgreSQL:

```powershell
& .venv/Scripts/python.exe -m alembic upgrade head
$env:APP_ENV = 'local'
$env:DEMO_AUTH = 'true'
$env:DEMO_AUTH_SECRET = & .venv/Scripts/python.exe -c 'import secrets; print(secrets.token_urlsafe(48))'
& .venv/Scripts/python.exe -m app.seed
& .venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-proxy-headers --reload
```

The secret stays in that terminal's environment; no default key ships. Seeding
is transactional and repeatable and refuses conflicting fixtures. Demo account
aliases are cedar_admin, maple_admin, willow_admin, demo_officer and demo_manager.
POST /api/v1/auth/demo-login with {"demo_alias":"cedar_admin"}; use the returned
bearer token for /me and permitted institution APIs. Swagger /docs supports bearer
authorization.

Integration tests require TEST_DATABASE_URL pointing to a new local PostgreSQL
database named sih26263_m1_test_<8–32 lowercase hex characters>. Tests create and
remove only that new database; an existing target is never reused or dropped.
The local database role needs permission to create databases. Without
TEST_DATABASE_URL, database integration tests are explicitly skipped.

Using unchanged .env.example database credentials, run from services/api:

```powershell
$testName = 'sih26263_m1_test_' + [guid]::NewGuid().ToString('N')
$env:TEST_DATABASE_URL = "postgresql+psycopg://sih_demo:local_demo_only@127.0.0.1:5432/$testName"
& .venv/Scripts/python.exe -m pytest -q
```

Adjust credentials/port to match your local configuration. Existing Ruff, mypy
and dependency checks still apply. Milestone 1 adds no frontend functionality.

## Candidate CSV ingestion — synthetic data only

Run `alembic upgrade head` to apply `0002_candidate_submissions`. It adds
submission_scopes, submission_batches and student_record_versions; a database
trigger rejects submitted-row updates/deletes. Batch lifecycle metadata is
separate. The existing local demo setup, seed command and dedicated PostgreSQL
test-database instructions still apply.

POST /api/v1/submissions accepts multipart file, institution_id, programme_id,
academic_year and schema_version=v1. Use samples/synthetic_admissions.csv with the
Cedar DEMO-COMP programme and 2026-27 context. Institution/programme UUIDs are
available from /me and the scoped programme endpoint. Only an institution
administrator can upload for their institution; officers can read, and
managers/verifiers cannot access submissions.

GET /api/v1/submissions lists scoped history. GET /api/v1/submissions/{id} returns
metadata; GET /api/v1/submissions/{id}/rows returns a paginated masked preview.
A 201 COMPLETED response means parsing and persistence finished, not validation,
approval or APAAR verification. Every accepted upload creates a distinct
candidate; none becomes current automatically. Repeated-file warnings are
advisory, including under concurrent uploads.

Defaults: 5 MiB CSV, 1,000 data records, file limit plus 64 KiB total multipart body,
30-second receive/processing budgets. Configure UPLOAD_MAX_BYTES, UPLOAD_MAX_ROWS,
UPLOAD_RECEIVE_TIMEOUT_SECONDS and UPLOAD_PROCESSING_TIMEOUT_SECONDS. Actual
received bytes are bounded before parsing. Uploads stay in bounded memory and
resources are closed on failure. A timeout response is possible only when the
application observes expiration; in-flight commits and disconnected clients have
no absolute HTTP cancellation guarantee.

Strict v1 headers and conservative normalization are documented in
docs/05_VALIDATION_AND_ABC.md. source_row_number counts logical CSV records,
header=1 and first student=2; quoted multiline fields do not increment it.
Malformed student values are preserved for later validation. Raw APAAR, stored
JSON and filenames are excluded from ordinary responses and error messages.
503 denotes connection/pool unavailability; other unexpected database errors
use a redacted 500.

Only synthetic records are permitted. Raw demo storage is not approved for real
student data; encryption/key management, retention/deletion/backups, lawful
purpose/consent and deployment/field-level access controls require a separate
approved security design.

## Local validation — synthetic data only

Apply 0003_student_validation with `alembic upgrade head`. In the API terminal,
explicitly supply a separate APAAR_MATCHING_KEY of at least 32 bytes, for example:

```powershell
$env:APAAR_MATCHING_KEY = & .venv/Scripts/python.exe -c 'import secrets; print(secrets.token_urlsafe(48))'
```

No key is supplied or generated by the application. Missing/short configuration
returns 422 MATCHING_CONFIGURATION_UNAVAILABLE; health and uploads remain available.

Upload samples/synthetic_validation.csv in the Cedar DEMO-COMP, 2026-27 context,
then POST /api/v1/submissions/{id}/validate. Institution administrators validate
their own candidates; officers can validate and POST /revalidate.
GET /validation-runs, /validation-runs/{run_id}, /findings and /feedback.csv are
scoped beneath that submission. Rows accept run_id and status; findings/export
default to the latest completed run. A run never activates a snapshot. VALID
means local validation for that run, not official APAAR verification.

Defaults: APAAR_FORMAT_LENGTH=12, VALIDATION_INTAKE_RULE_VERSION=DEMO-v1,
VALIDATION_PROCESSING_TIMEOUT_SECONDS=30 and
VALIDATION_MAX_COMPARISON_RECORDS=100000. Only current ACTIVE same-year overlaps
contribute to the current-overlap metric. Other matches are informational
AS_OF_RUN. Stale or incomplete current metrics are null, while original evidence
remains immutable. Feedback CSV masks APAAR and escapes spreadsheet formulas.
See docs/04_API_CONTRACT.md and docs/05_VALIDATION_AND_ABC.md for exact contracts
and limitations.

The existing full backend test command also runs real loopback HTTP smoke tests
covering review/activation and migration checks in a newly created test database.
Steps 5C–5E add validation results, review/activation screens and API-backed
role-specific dashboards. Case workflows, marketing pages and provider integrations
remain unimplemented.

## Snapshot review and activation — synthetic data only

Apply 0004_snapshot_review_activation using `alembic upgrade head`. Upload
samples/synthetic_snapshot_initial.csv for Cedar DEMO-COMP, 2026-27, explicitly
validate it, then POST /api/v1/submissions/{id}/reviews with
{"validation_run_id":"selected-run-uuid"}. A receipt preserves information
presented, not proof it was read. Inspect current versus candidate counts, total
and previously ACTIVE omissions, category/status differences, blockers and
reviewable warnings.

POST /api/v1/submissions/{id}/activate with
{"review_id":"review-uuid","expected_scope_revision":0,"confirm_complete_replacement":true,"acknowledge_review_warnings":true,"acknowledge_omissions":true},
using the actual reviewed revision. Omission acknowledgment is mandatory when
omissions exist. Only the receipt’s institution administrator can activate.
Unsupported structural policy or structural blockers prevent activation; missing
APAAR/names/dates and DEMO intake findings remain reviewable when counting is
reliable. No run is silently substituted.

Repeat with samples/synthetic_snapshot_replacement.csv to demonstrate an omitted
previously ACTIVE record, an explicit withdrawal and a category change.
GET /api/v1/submissions/{id}/reviews/{review_id} retrieves the immutable receipt
plus current state and paginated omissions.
GET /api/v1/institutions/{institution_id}/summary?academic_year=2026-27 reports
only activated declarations, with coverage and nullable counts for programmes
without a current snapshot. History is preserved and never summed into current
enrolment.

Activation atomically updates the current reference, increments the scope revision
and records provenance/audit. Scope contention or stale review returns 409; create
a new review when the current snapshot changed. Replays never create a second
activation. Inspect provenance after an uncertain HTTP result. Cross-institution
assessment staleness is separate from eligibility; unavailable overlap counts
are null, not zero. Milestone 4 adds no frontend, case workflow or provider integration.

## Milestone 5A — local portal foundation

Start the seeded local API using the instructions above. From `apps/web`:

```powershell
npm ci
npm ci --prefix tools/api-types
Copy-Item .env.example .env.local
# In .env.local, explicitly set NEXT_PUBLIC_DEMO_UI_ENABLED=true for local use.
npm run api:check
npm run dev
```

Open `http://localhost:3000`. The API base defaults to
`http://127.0.0.1:8000/api/v1`; localhost:3000 matches the backend's default CORS
origin. The public UI flag defaults to false and cannot enable backend demo
authentication. Never put signing, database or APAAR matching secrets in web
environment variables. Do not deploy or tunnel this local-only demo.

Select a server-controlled synthetic account. Institution administrators see their
dashboard and permitted institution/programme data; officers see the cross-institution
dashboard and directory; managers see aggregate dashboard data and institution
metadata only. Permissions remain enforced by FastAPI. Pages label synthetic data
and distinguish local checks from government verification.

Tokens live only in memory. Refreshing or closing the page requires sign-in again;
expiry returns to sign-in without silent renewal. Logout/expiry clears cached
private data and cancels outstanding requests. No browser token storage or
production authentication is provided. Loading, empty, failure and retry states
use actual API outcomes rather than fabricated records.

`npm run api:generate` regenerates declarations from local FastAPI OpenAPI without
a running database. `npm run api:check` detects drift. The separately locked
`tools/api-types` package pins openapi-typescript 7.13.0 and TypeScript 5.9.3 for its
peer requirements; application TypeScript remains 6.0.3 and checks the generated
declarations. No peer-dependency bypass is used.

```powershell
npm run lint
npm run typecheck
npm run format:check
npm run build
```

Automated browser/e2e testing (Playwright) has been removed from this project.
Frontend verification is limited to lint, strict typing, formatting, production
build and manual testing in a browser; there is no automated UI regression suite
or automated accessibility check. A full manual screen-reader and keyboard
accessibility audit remains follow-up work.

5A itself added no upload screens or backend contract/migration changes. The
following section describes the subsequently implemented 5B scope.

## Milestone 5B — institution CSV upload and submission history

Use the same local API, synthetic seed accounts and web setup as 5A. No new
dependencies, secrets or database migration are required; the migration head
remains 0004_snapshot_review_activation.

Sign in as an institution administrator and open **Upload candidate**. Select an
active programme belonging to that institution, enter a consecutive academic year
such as 2026-27, download the strict-v1 header-only template, choose a synthetic
student CSV and acknowledge synthetic-only data. The institution comes from the
authenticated account. `samples/synthetic_admissions.csv` works for DEMO-COMP and
2026-27 and includes intentionally malformed student values for later validation.

One CSV declares a complete candidate snapshot for exactly one institution,
programme and year, covering all admission categories. Uploading never validates
or activates it and never changes current enrolment. **Candidate stored** confirms
parsing and persistence only. Repeated accepted files create separate candidates
and may show advisory duplicate-upload warnings; history is preserved.

GET /api/v1/submissions/upload-policy supplies configured byte/record limits,
encoding, ordered headers and receive/processing budgets. It reuses existing
authentication, permits administrators/officers, denies managers/verifiers and
returns no-store. The browser generates its header-only template from that
response; no separate template API or duplicated browser limit configuration.
UTF-8 with an optional BOM and exact v1 headers are required. Empty templates are
not uploadable. Data-record limits count logical CSV records, not physical lines.

Open **Submissions** for paginated history, programme/year filters, processing and
candidate/current/previous labels, and redacted provenance. Stored row counts are
declared rows, not current active-enrolment totals. Officers open an institution
from their directory and use **View submission history**; they cannot upload on
its behalf. Managers have no submission navigation or API access. No raw APAAR,
CSV contents or stored filenames appear in these screens or application logs.

Uploads are never automatically retried or queued for reconnect. A pending upload
locks submission controls, including after navigating away and back. Known CSV/
context/limit rejections are distinct from lost-response, timeout or unexpected
server outcomes. **Upload outcome unknown** directs users to history: persistence
may have completed, and an absent history entry does not prove an in-flight upload
failed. Preparing another upload is deliberate and may create another candidate.
If the session ends, sign in again and check your own history before re-uploading.
No absolute HTTP cancellation/completion guarantee or upload idempotency is added.

Upload/template/history, duplicate preservation, filters/pagination,
malformed/encoding/record-limit failures, configured policy and size checks,
unknown outcomes after actual persistence, pending-request navigation, expiry,
account switching and desktop/mobile accessibility require manual verification;
no automated browser suite covers them. Backend regression includes policy
permissions, nondefault settings, migration round trips/drift and loopback HTTP
smoke tests, run via `pytest`.

Step 5B adds the upload and submission-history workflows described here. Steps
5C–5E add validation, review/activation and API-backed dashboards. Step 5F polish,
case workflows, marketing and APAAR/ABC provider integrations remain staged or
deferred.

## Milestone 5E — institution, officer and aggregate dashboards

The institution dashboard uses the authenticated institution's current-snapshot
summary, configured intake rules, programme metadata and recent submission history.
It separates current declared records and demo ACTIVE enrolments from candidate
uploads, shows category totals and declaration coverage, and labels intake
comparisons as configured DEMO rules rather than official AICTE determinations.
Programmes without an activated declaration show missing coverage rather than zero.

The AICTE officer dashboard compares current activated summaries across permitted
institutions and reports current cross-institution assessment freshness. Stale,
incomplete or unavailable metrics are labeled and are not shown as zero. Institution
and region filters use API-backed metadata. The manager dashboard uses institution
metadata and aggregate summaries only; it does not request submissions, student
records, identifiers or findings. Backend authorization remains authoritative.

No analytics endpoint, database migration or new backend contract was added. The
officer view composes existing institution summaries, submission history and
current validation-run details; request fan-out will increase with institution
count. Dashboard data is synthetic and API-backed. No official identity verification,
regulatory compliance determination, case workflow, marketing page or provider
integration is represented.

## Master-plan additions (Phases 1–10)

Beyond Milestone 5, the repository now includes (all synthetic data, local demo auth only):
Excel (.xlsx) upload and optional upload idempotency keys; a full case workflow (priority,
severity, due date, overdue/escalation, assignment, response, resolution reason) with
in-app notifications; a student registry with record provenance and history; intake
governance (rule changes with audit, declared totals, immutable assessments, what-if
simulator); a rule-based integrity engine with score components and officer decisions;
hardened simulated APAAR verification and signed admission credentials with an authorized
verifier workspace; manager analytics, an officer audit explorer, and CSV/XLSX/PDF
reports; rate limits, security headers and log redaction.

Applied migrations are now through `0012_verification_credentials` (0007 upload
idempotency, 0008 case workflow, 0009 notifications, 0010 intake governance, 0011
integrity decisions, 0012 verification and credentials). New settings are listed in
`.env.example`; to use credentials set `CREDENTIAL_SIGNING_KEY` (base64 of 32 random
bytes). Extra demo accounts: `demo_officer_2` and `demo_verifier`.

Reproducible end-to-end demonstration (local DEMO_AUTH mode only; refuses otherwise),
from `services/api` after `alembic upgrade head` and `python -m app.seed`:

```bash
python -m app.demo_scenario          # in-process, ephemeral credential key
python -m app.demo_scenario --json   # machine-readable result
```

It uploads the files in `samples/demo/`, drives the 12-step sequence through the public
API and checks results against `samples/demo/expected.json`. Simulated verification is
never official verification, integrity signals are review prompts and not fraud
determinations, and no real APAAR/ABC/government access is claimed. The frontend has no
automated UI suite; verify it manually (lint, typecheck, build, browser).
