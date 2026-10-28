# Implementation Plan / Codex Task Order

## Approved Milestone 5 execution sequence

5A: generated API types, simple in-memory demo sessions, role navigation, shared
responsive shell, existing institution/programme metadata and browser tests.
5B: configured CSV upload/template and submission history.
5C: explicit local validation, selected-run evidence and feedback export.
5D: immutable review comparisons, omission acknowledgment and explicit activation.
5E: current-only institution/officer dashboards and aggregate-only manager views.
5F: complete accessibility/responsive polish and integrated regression checks.
Complete and test each step before proceeding. Steps 5A–5E are complete; 5F
remains staged. Steps 5A and 5E required no new business endpoint or migration.
Keep compiler/generator locks separate as approved; generated types must match
the backend. No force/legacy peer overrides. Use pinned TanStack Query and
Playwright. Defer backend enhancements until the frontend feature needs them.

5B implements /institution/upload and shared /submissions history, with an
officer's institution-context link from metadata. Reuse existing upload/history
contracts and scoped programmes. The approved read-only upload-policy endpoint
provides configured limits and parser headers for the strict-v1 header-only
template; no database migration, dependency or new backend feature module.
Separate processing success, confirmed rejection and unknown outcomes. Never
automatically retry/queue uploads, activate a candidate, infer validation success
or sum historical rows as current enrolment. Test duplicate versions, configured
policy, filters/pagination, failure/recovery, expiry, account switching and mobile
accessibility against isolated synthetic PostgreSQL/API fixtures.

5E adds API-backed `/institution` and `/aicte` dashboards. Institution summaries,
DEMO intake rules, institution metadata, scoped recent submissions and current
validation-run details provide the metrics. Current activated snapshots are the
only source for enrolment totals; missing coverage is distinct from zero, and stale,
incomplete or unavailable assessment metrics are not zero. Managers use only
institution metadata and aggregate summaries, never submission/student endpoints.
The existing contracts were sufficient, so this step adds no backend endpoint,
migration or dependency. Officer assessment freshness composes per-institution
history/run requests and has a prototype-scale fan-out limitation. Tests cover
current-only calculations, partial/missing declarations, stale assessments, role
boundaries, filters, mobile layout and automated accessibility.

## Milestone 4 execution boundary

Immutable review receipts; explicit selected-run activation; conditional omission
acknowledgment; structural compatibility and current-rule recheck; NOWAIT scope
row locks; atomic current reference, revision, provenance and audit.
Reuse submissions, validation, institutions, audit and shared sessions. No new
feature module, workers, queues, activation validation-run kind or frontend.
Test independent PostgreSQL races, each write rollback, stale assessments,
current-only aggregates and real HTTP review/activation. Older never-activated
uploads may receive a new review at the current revision without rewriting their
upload-time base provenance. Previously activated batches cannot be reactivated.

**Rule:** Finish, test, and demonstrate each phase before expanding scope.

## Phase 0 — repository foundation

- Monorepo: `apps/web`, `services/api`, `infra`.
- Next.js + TS strict + Tailwind, FastAPI with typed schemas.
- Docker Compose PostgreSQL and `.env.example`.
- `/api/v1/health` status and OpenAPI.
- SQLAlchemy base and Alembic init.
- Seed three fictional institutions and demo users (demo mode only).
  **User-approved sequencing refinement:** defer these seeds to Phase 1 alongside
  their feature-owned tables and demo authentication; Phase 0 is foundation only.
  Initialize Alembic without an empty migration or business tables. Expose separate
  application liveness (`/api/v1/health`) and PostgreSQL readiness (`/api/v1/ready`).
  **Accept:** One-command database launch; web and API run locally; health response; lint/typecheck/pytest commands documented.

## Phase 1 — working upload and validation

- Migration for institution, programme, intake rule, user, batch, row version, findings, audit.
- Synthetic CSV template and seed data; size, encoding, header, row checks.
- Institution-scoped upload endpoint -> deterministic parse/normalize -> findings -> persistence.
- Batch/rows/findings endpoints and CSV feedback.
- Institution UI upload and results table; basic AICTE officer overview.
- Tests for missing, invalid, duplicates, intake by year/category, isolation and errors.
  **Accept:** Upload deliberately bad CSV, see issues in UI; retrieve via API; old batches still exist after resubmission.

### Phase 1 execution milestones

1. Institution foundation: institution/programme/intake/user/audit migrations,
   deterministic synthetic seeds, restricted demo authentication and scoped APIs.
2. Candidate upload: bounded synchronous CSV ingestion, immutable original and
   normalized records, candidate browsing and safe failure handling.
3. Validation: immutable validation runs, blocking/reviewable findings,
   evidence and formula-safe feedback export.
   Explicit INITIAL validation after upload; officer-only REVALIDATION, scoped
   history/selected-run results and feedback. Feature-owned validation models,
   schemas, rules, services and routes. No eligibility or activation workflow.
   Configure APAAR_MATCHING_KEY independently of authentication (>=32 bytes,
   environment only, never a fallback); health/upload work without it but validation
   fails explicitly. Defaults: VALIDATION_PROCESSING_TIMEOUT_SECONDS=30,
   VALIDATION_MAX_COMPARISON_RECORDS=100000, APAAR_FORMAT_LENGTH=12,
   VALIDATION_INTAKE_RULE_VERSION=DEMO-v1. Cooperative limits fail atomically;
   they are not guaranteed HTTP cancellation deadlines. No dependency additions.
4. Snapshot review/activation: scope-row locking, revision conflicts,
   replacement effects, current-only counts and assessment freshness.
5. Interface completion: institution upload/results/history and a minimal
   API-backed officer overview.

Milestone 1 excludes CSV processing, validation rules, submission/activation
tables and workflows, dashboards, cases and APAAR/ABC integrations.

Demo authentication:

- APP_ENV defaults to production; DEMO_AUTH defaults to false.
- Explicit APP_ENV=local and DEMO_AUTH=true are both required.
- Startup rejects DEMO_AUTH=true outside the local profile.
- Demo issuance and authentication require loopback peers and approved local
  hosts/origins. Forwarded/proxied demo access is rejected; forwarded address
  headers are not trusted as proof of local access.
- Local demo mode must not be exposed through a reverse proxy or tunnel.
- Use server-controlled seeded identities and expiring signed bearer tokens.
- Require a separately generated signing secret; ship no default signing key.
- Disabling demo mode disables demo-token authentication as well as issuance.
- Bind local development to loopback and disable Uvicorn proxy-header trust.
- Authentication is replaceable through one token-verification interface and
  the shared current-user dependency. No production backend is implemented.

Seeds use stable identifiers and fictional .invalid email addresses:

- Institutions: Demo Cedar, Demo Maple and Demo Willow Institute.
- Two programmes per institution: DEMO-COMP and DEMO-ELEC.
- Academic year: 2026-27; rule version DEMO-v1; source_label=DEMO.
- Illustrative independent category capacities per programme:
  REGULAR=3, SUPERNUMERARY=1, NRI=1, OCI=1, FOREIGN_NATIONAL=1.
- Accounts: cedar_admin, maple_admin, willow_admin, demo_officer, demo_manager.

These intentionally small capacities demonstrate rule behavior; they represent
no official entitlement or relationship between seat categories.

Seed execution is explicitly local/demo gated and transactional. Repeating it
adds no duplicate rows or events. Conflicting existing seed data causes a clear
failure rather than silently resetting roles, reactivating users or changing rules.

Reuse existing HTTP/error-handling infrastructure wherever possible. Extend
existing middleware/configuration and shared handling rather than duplicating
them. New utilities, abstractions or files require a concrete unmet need.

Phase 1 v1 uses strict CSV headers; configurable schema mapping is a future
enhancement. Assessment freshness is conservative and may cause additional
revalidation as the number of institutions increases.

## Phase 2 — cases and mock APAAR

- `APAARProvider` interface and deterministic mock with `SIMULATED` labels.
- Officer queue, case creation, correction requests; immutable case timeline.
- UI evidence panels and upload/correction loop; explicit authorization checks.
  **Accept:** Mock success/mismatch/unavailable visibly differentiated; case flows; no official verification claims.

## Phase 3 — optional ABC credits

- `ABCCreditProvider` mock, consent/purpose checks, optional credit records and reconciliation.
- Non-blocking error paths, evidence and officer review.
  **Accept:** Match/mismatch/unavailable demos; admission reports unaffected by ABC outage.

## Phase 4 — advanced insights and polish

- Missing student population flags where declared totals exist.
- Version-diff anomaly detection, rule-time-machine read-only view.
- Enhanced charts, authorized verifier prototype, UX accessibility, performance tests.
- Deployment instructions (but no live government integration without permissions).

## Suggested Codex prompts

### Prompt A: foundation

"Read AGENTS.md and docs/01_PRD.md through docs/09_DECISIONS_AND_ASSUMPTIONS.md. Implement only Phase 0 of docs/07_IMPLEMENTATION_PLAN.md. Create scaffolding, Docker PostgreSQL, health endpoint, configs and .env.example, run checks, and report files/commands. Never claim official APAAR/ABC access."

### Prompt B: upload slice

"Implement Phase 1 end to end. Use schema/rules/contracts from docs. Include one deterministic synthetic CSV with errors; Alembic migrations; API/DB tests; frontend upload/results and officer summary. Enforce institution-level scoping server-side. Run tests and show results."

### Prompt C: mock identity and cases

"Implement Phase 2 only. Provider adapter must always mark simulated responses; no real national API integration. Build evidence-linked officer case workflow and tests."

### Prompt D: optional credits

"Implement Phase 3 only. ABC reconciliation is advisory and non-blocking. Keep real credit vs grade points separate and validate consent/purpose."

## Initial local commands (target structure, Codex to implement)

```
docker compose -f infra/docker-compose.yml up -d
cd services/api && python -m venv .venv && pip install -r requirements.txt
cd services/api && alembic upgrade head && uvicorn app.main:create_app --factory --host 127.0.0.1 --no-proxy-headers --reload
cd apps/web && npm install && npm run dev
```

These are target commands, not evidence that the repository already exists.

### Milestone 2 resource bounds and verification

Default configurable limits are 5 MiB per CSV and 1,000 data records. Bound the
complete multipart body to the file limit plus 64 KiB overhead, counting actual
received bytes even without/trusting no Content-Length. Read the bounded body
before multipart parsing; use memory-backed upload resources and always close
them, including incomplete multipart/parse failure/timeout/disconnect paths.

Use configurable 30-second receive and processing budgets and existing database
timeouts. Budget checks before commit cannot guarantee cancellation of an
in-flight database commit or delivery of an HTTP timeout to a disconnected client.
Use 408 only when the application actually detects expiration. No background work.

Test actual over-limit streams, malformed/incomplete bodies, timeouts, disconnects,
closed resources, rollback and independent concurrent uploads against PostgreSQL.
Only synthetic fixtures may be used; real-data privacy/security work remains gated.

## Definition of ready for each task

Endpoint contract, entity changes, UI views, fixture, test cases and role permissions clearly stated. Record ambiguities in decisions log instead of inventing official regulatory parameters.
