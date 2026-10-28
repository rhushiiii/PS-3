# REST API Contract — v1 proposal

## Step 5B upload policy and existing-contract integration

GET /api/v1/submissions/upload-policy is authenticated and read-only. Institution
administrators and AICTE officers may read it; managers/verifiers are denied.
Return Cache-Control: no-store and typed JSON with schema_version="v1",
required_headers (the parser's existing eight ordered headers), encoding="UTF-8",
accepts_utf8_bom=true, max_file_bytes=UPLOAD_MAX_BYTES, max_rows=UPLOAD_MAX_ROWS
(data records, excluding the header), receive_timeout_seconds and
processing_timeout_seconds from their configured upload budgets. No secrets or
student data are included, and no migration is required. Authentication and errors
reuse existing infrastructure. Register the static route before /{batch_id}.

The browser generates a header-only CSV template from required_headers; there is
no separate template endpoint. Programmes come from existing scoped metadata;
POST /submissions and filtered/paginated GET /submissions remain unchanged.
No upload idempotency/correlation contract is added. Disable automatic POST retries
and offline queuing. A lost response, observed timeout, malformed success response
or unexpected server failure means outcome unknown: check history before deciding
to upload again. History absence does not prove an in-flight commit failed.
Confirmed processing rejection remains distinct from uncertain delivery/persistence.
Each repeated accepted upload is a separate candidate, with advisory warnings.
Never activate or validate as part of this browser workflow.

## Step 5A browser integration

5A reuses POST /auth/demo-login, GET /me, institution directory/detail and programme
listing unchanged. Submit only demo_alias. The server controls identity/role/scope;
the browser does not send role/institution impersonation fields. Fixed demo account
labels are presentation, not authorization. Token stays in tab memory and is sent
only in Authorization headers to the configured local API. Requests use no-store
and omit cookies. No passwords, token persistence, silent renewal or new auth API.
401 SESSION_EXPIRED clears the session and private caches with the documented
expiry message. Other 401 responses also end the session. Role/scope denials,
database failures and network errors remain separate errors, not empty data.
No automatic POST retry or fallback identity/data. Types are generated from the
existing OpenAPI, including the locally enabled demo-login contract; generation
serves no requests and performs no DB work. No route/schema/permission changes
are introduced in 5A. Later upload policy, filters and analytics remain planned.

## Milestone 4 exact additions
POST /submissions/{batch_id}/reviews body {validation_run_id: UUID}, 201, own
institution administrator only. Pin the exact completed run, never silently latest.
GET /submissions/{batch_id}/reviews/{review_id} accepts page/page_size (1–100);
own admins or officers may read. Managers/verifiers have no receipt access.
Return candidate/scope/run/reviewer IDs, created_at, expected_scope_revision,
expected_current_batch_id, review_policy_version, immutable snapshot, eligibility,
assessment_now, omitted_records and omission_pagination. Derived receipt states:
READY/BLOCKED/STALE/CONSUMED. Omitted rows expose only own local student ID, version
UUID, logical row number, previous category and status. Ambiguous omissions and
pagination are null, not a misleading empty list.
POST /submissions/{batch_id}/activate body:
{review_id: UUID, expected_scope_revision: integer >=0,
confirm_complete_replacement: true, acknowledge_review_warnings: true,
acknowledge_omissions: boolean=false}. Reject unknown fields/coerced confirmations.
Omissions require acknowledge_omissions=true, else 422
OMISSIONS_ACKNOWLEDGMENT_REQUIRED. No omission-size threshold rejects activation.
Only the receipt's administrator may activate it; another admin creates their own.
200 returns batch_id, scope_id, review_id, validation_run_id, previous_batch_id,
scope_revision, activated_by, activated_at, established counts and source_label=DEMO.
409: SCOPE_REVISION_CONFLICT, ACTIVATION_CONFLICT (NOWAIT contention),
CANDIDATE_INELIGIBLE, REVALIDATION_REQUIRED, REVIEW_POLICY_CHANGED,
ALREADY_ACTIVATED. Replays do not increment revision or append another audit.
After an uncertain HTTP result, inspect provenance; commit cancellation is not
guaranteed. Existing 401 expiry, 403 role/owner, 404 inaccessible resources,
422 malformed input, 503 genuine DB outage and redacted 500 remain authoritative.
Batch detail/history add snapshot_state=CANDIDATE|CURRENT|PREVIOUS,
activation_review_id, activation_provenance and run-specific activation_eligibility.
GET /institutions/{institution_id}/summary requires academic_year and accepts
programme_id, page, page_size. Admins read own institution, officers across
institutions, managers aggregates only; verifiers denied. No student/batch IDs
appear in aggregate summaries. Totals cover all filtered programmes, not just the
displayed page. Only current snapshots contribute. Missing programme snapshots
have has_current_snapshot=false and counts=null. Coverage NONE/PARTIAL/COMPLETE
and count_basis=AVAILABLE_ACTIVATED_DECLARATIONS distinguish missing declarations.
All responses are no-store. Review candidate counts stay separate from current.

Base: `/api/v1` · JSON unless multipart · UUID identifiers · UTC ISO timestamps · OpenAPI at `/docs`.
All endpoints perform server-side role and institution checks. Example responses are illustrative.

## Phase 0 infrastructure exception — user approved

Health and OpenAPI endpoints are public infrastructure metadata, containing no
student data. Business endpoints retain the role/institution requirements above.

- `GET /health` -> `200 { "status":"ok" }`. Application liveness only; no
  PostgreSQL connection or query. Remains available during database outages.
- `GET /ready` -> `200 { "status":"ready", "database":"reachable" }` after
  PostgreSQL `SELECT 1`; otherwise
  `503 { "status":"unavailable", "database":"unreachable" }`.
- Readiness has a typed status payload rather than the business-error envelope.
  Connection details and exception messages are never included.
- OpenAPI JSON remains `/openapi.json`, interactive documentation `/docs`.
- All business routes below are proposals for later phases, not Phase 0 endpoints.

## Identity
- `POST /auth/demo-login` body `{ "demo_alias": "cedar_admin" }`.
  Reject unknown body fields, including role and institution_id.
  Resolve an active, explicitly seeded synthetic user on the server.
  Return `{ "access_token":"...", "token_type":"bearer",
  "expires_in":900, "demo_mode":true }`.
  Available only under the restricted local demo configuration.
- `GET /me` -> `{ id, role, institution_id, demo_mode }`.

## Institutions / intake
- `GET /institutions?region=&q=&page=1&page_size=20` officer/manager
- `GET /institutions/{id}` scoped
- `GET /institutions/{id}/programmes?page=1&page_size=20` scoped.
- `GET /institutions/{id}/intake?academic_year=2026-27&programme_id=...` scoped
- `GET /institutions/{id}/summary?academic_year=...` scoped

## Submission
- `POST /submissions` multipart `file`, `institution_id`, `programme_id`,
  `academic_year`, `schema_version=v1` processes synchronously and returns
  `201 { "id":"...", "status":"COMPLETED" }` after candidate persistence.
  COMPLETED means processing finished, not validation passed or activation.
- `GET /submissions/{id}` -> batch metadata and counts.
- `GET /submissions/{id}/rows?page=&page_size=&status=` -> paginated normalized preview with masked APAAR.
- `GET /submissions/{id}/findings?page=&rule_code=&severity=` -> findings.
- `GET /submissions/{id}/feedback.csv` -> formula-safe feedback export.
- `POST /submissions/{id}/revalidate` (privileged) -> re-run config-pinned rules; never mutate prior findings in place.

## APAAR simulated provider
- `POST /verification/apaar/{record_version_id}/check` body `{ "consent_reference": "...", "purpose": "REGULATORY_REVIEW" }`
  -> `{ "status":"SIMULATED_MATCH", "source_type":"SIMULATED", "checked_at":"...", "message":"Demo provider only" }`.
- Missing consent/purpose => `403/422`. Use deterministic fixture map; not random outcomes.

## Optional ABC
- `POST /verification/abc/{record_version_id}/reconcile` with purpose/consent -> status e.g. `SIMULATED_MISMATCH`, `SOURCE_UNAVAILABLE`; never block admissions flow.
- Optional endpoints implemented only in Phase 3 or later.

## Cases
- `GET /cases?status=&institution_id=&page=`
- `POST /cases` `{ "record_version_ids":[], "summary":"Potential duplicate", "category":"DUPLICATE_REVIEW" }`
- `GET /cases/{id}` findings, evidence, events
- `POST /cases/{id}/actions` `{ "action":"REQUEST_CORRECTION", "comment":"..." }`
- Allowed actions and transitions governed by role and server rules.

## Analytics
- `GET /analytics/overview?academic_year=&programme_id=&region=` -> institution count, row states, unresolved findings, case ageing.
- `GET /analytics/intake?institution_id=&academic_year=&programme_id=&category=` -> approved, reported, discrepancy, demo_rule label.
- `GET /analytics/anomalies?academic_year=&rule_code=&page=` -> aggregate by finding type.

## Contract conventions
Success for a list: `{ "data":[...], "pagination":{ "page":1, "page_size":20, "total":53 } }`.
Errors: `{ "error":{ "code":"FORBIDDEN_INSTITUTION", "message":"Not authorized", "request_id":"..." } }`.
Possible codes: `INVALID_CSV`, `SCHEMA_MISMATCH`, `FILE_TOO_LARGE`, `INVALID_YEAR`, `RESOURCE_NOT_FOUND`, `NOT_AUTHENTICATED`, `FORBIDDEN_INSTITUTION`, `PROVIDER_UNAVAILABLE`, `RULESET_NOT_CONFIGURED`.
HTTP: 400 invalid input; 401 auth; 403 scope/consent; 404 missing; 409 incompatible state; 413 too large; 422 validation; 500 unexpected server.

## Security expectations
No APAAR in URL or query parameters (only record UUID). Never return full identifier in dashboards. Uploaded CSV not publicly hosted. Same upload SHA may be accepted as a *separate version* with a duplicate-upload warning, not silently overwritten.

## Contract tests
For every endpoint test happy path, invalid payload, no auth, cross-institution isolation and deterministic response format.

## Phase 1 permissions and staged additions

Milestone 1 implements demo-login, /me, institution listing/detail,
programme listing and intake listing only.

Institution listing is officer/manager only. Institution administrators may
read their own institution, programmes and intake. Officers and managers may
read institution/programme/intake metadata across institutions. These routes
do not expose student records. AUTHORIZED_VERIFIER has no business access
until its permitted workflow is implemented.

Intake listing requires academic_year and optionally programme_id. A programme
filter must belong to the requested institution. List page_size is 1–100.
Inaccessible institution resources return privacy-preserving 404 responses;
role-level denial returns 403.

Missing, invalid or expired bearer credentials return 401 with
WWW-Authenticate: Bearer. Expired credentials use SESSION_EXPIRED.
A disabled/inactive identity is not authenticated. No silent token renewal occurs.
Demo login returns 404 when disabled and 403 for disallowed local-access context.

Later Phase 1 milestones add:

- GET /submissions: institution-scoped, paginated history.
- POST /submissions/{id}/activate:
  Requires the receipt and explicit confirmations in the Milestone 4 contract.
  Institution administrators activate eligible candidates for their own scope.
  Return 200 on success, 409 for stale review or incompatible state.
- GET /submissions/{id}: include processing status, activation eligibility,
  blocking reasons, reviewed revision, counts and replacement effects.
- POST /submissions/{id}/revalidate: officer-only, append an immutable run.
  Do not overwrite earlier findings.

Findings responses identify their validation run and evaluation timestamp.
Cross-institution assessments report freshness separately from review state.
Health/readiness contracts remain unchanged.

## Milestone 3 local validation contract

All paths use /api/v1. POST /submissions/{id}/validate creates one INITIAL run
(institution administrator for own batch, or officer), returning 201. Repeating
it returns 409 VALIDATION_ALREADY_PERFORMED. POST /submissions/{id}/revalidate
remains officer-only, requires an initial run, and returns a new 201 run.

GET /submissions/{id}/validation-runs is paginated history;
GET /submissions/{id}/validation-runs/{run_id} returns the selected run, pinned
configuration, summary, evaluated/completed times, cross_current_freshness and
current_overlap_records. The latter is null when stale or matching is incomplete.
Frozen current_overlap_records_at_evaluation is explicitly a known-match count
at evaluation, not a live total. historical_assessment=AS_OF_RUN.

GET /submissions/{id}/findings accepts run_id, rule_code, severity, classification,
page and page_size. Each finding carries its run/time/freshness and redacted
evidence. GET /submissions/{id}/feedback.csv accepts run_id. Without run_id,
these reads select and identify the latest completed run. Before validation,
findings/export return 409 VALIDATION_NOT_RUN. Foreign or inaccessible run IDs
return 404. Managers/verifiers remain denied; administrators cannot read peers'
student or institution references. Officers receive permitted version references,
with no full APAAR in ordinary responses. Responses use Cache-Control: no-store.

Batch history/detail add validation_performed, latest_validation_run_id and
validation_summary. Rows accept run_id and status=VALID|FLAGGED|INCOMPLETE and
identify validation_run_id; unvalidated rows remain null. Filtering status before
a run returns 409. POST upload still returns validation_performed=false.
VALID means local checks for the selected run, never official identity verification.

Missing/short APAAR_MATCHING_KEY returns controlled 422
MATCHING_CONFIGURATION_UNAVAILABLE; no fallback key or false zero result.
Observed evaluation/comparison limits return 422 VALIDATION_LIMIT_EXCEEDED.
Incomplete processing returns 409 SUBMISSION_NOT_PROCESSED. Existing errors apply:
401 for authentication/session expiry, 403 role denial, 404 inaccessible resources,
422 invalid filters, 503 genuine database unavailability, redacted 500 otherwise.
No absolute HTTP cancellation or commit deadline is promised.

Feedback columns: run_id,evaluated_at,ruleset_version,cross_current_freshness,
record_version_id,source_row_number,college_student_id,apaar_id_masked,
validation_status,rule_code,severity,classification,field_name,explanation.
One row per finding/affected local record, one row for a record without findings,
and empty record columns for batch-only findings. Escape spreadsheet formula cells,
including leading whitespace/control variants. CSV escaping never changes storage.

## Milestone 2 candidate ingestion contract

Implement POST /submissions, GET /submissions, GET /submissions/{id} and
GET /submissions/{id}/rows only. Administrators upload/read their own institution;
officers read across institutions but cannot upload as an institution. Managers
and verifiers have no submission access. Use 403 for role denial and 404 for
inaccessible resources. Verify active institution/programme and their ownership.

POST accepts one multipart file and institution_id, programme_id, academic_year,
schema_version=v1, rejecting duplicate/unexpected fields. Return 201 with id,
status=COMPLETED, validation_performed=false and warnings. Identical prior files
in the same scope may produce DUPLICATE_UPLOAD, never overwrite/deduplication.
COMPLETED means parsing, normalization and persistence only.

History supports institution_id, programme_id, academic_year, page and page_size
(1–100), ordered by received_at descending then ID. Administrator queries always
retain institution scoping. Batch responses include IDs/scope, actor, source,
file hash/byte count, schema/mode, status/row count, base batch/revision, timestamps,
is_current, validation_performed and warnings. New candidates are not current.
No eligibility or active-enrolment totals are calculated.

Row responses whitelist normalized preview fields and apaar_id_masked, never
raw APAAR, filename, original_json or unrestricted normalized_json. Values of four
or fewer characters are fully masked; longer values expose at most four trailing
characters. Return validation_status=null, apaar_verification_status=NOT_CHECKED
and abc_reconciliation_status=NOT_REQUESTED. Row status filtering returns 422
until validation is implemented. Submission responses use Cache-Control: no-store.

Use the existing redacted error envelope without CSV values/filenames:
- 400 INVALID_CSV for malformed multipart/CSV, encoding, NUL, column counts or
  zero data records; a disconnected client may receive no response.
- 422 SCHEMA_MISMATCH for v1 header differences; INVALID_REQUEST for bad context
  or multipart fields; ROW_LIMIT_EXCEEDED for excess data records.
- 413 FILE_TOO_LARGE for actual file/body bounds.
- 408 UPLOAD_TIMEOUT only when the application observes its receive/processing
  budget expire before committing/responding. No absolute network deadline is promised.
- 503 DATABASE_UNAVAILABLE for connection/pool unavailability.
- 500 DATABASE_ERROR for other unexpected database errors; INTERNAL_ERROR for
  other unexpected application errors. Do not classify every SQL error as outage.

All candidate writes roll back on failure. Validation findings, eligibility,
revalidation, feedback export and activation remain unimplemented in Milestone 2.
