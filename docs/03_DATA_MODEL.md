# PostgreSQL Model — proposed MVP schema

## Milestone 4 storage contract
submission_reviews: id UUID PK, batch_id UUID, scope_id UUID, validation_run_id UUID,
reviewed_by UUID FK users, created_at UTC timestamptz, expected_scope_revision
integer >=0, expected_current_batch_id UUID nullable, review_policy_version
varchar(64), review_snapshot_json JSONB. Unique (id,batch_id); index
(batch_id,created_at,id). Composite foreign keys bind batch/scope, run/batch and
previous batch/scope. A trigger rejects review UPDATE/DELETE.
Review JSON freezes current/candidate/category/status totals and deltas, total
and previously ACTIVE omissions, local record UUIDs, blocking finding references,
reviewable counts, pinned configuration and assessment-at-review labels.
No raw APAAR/key/peer details enter receipts or audits. Omitted local identifiers
are recovered from immutable source rows. Ambiguous comparisons are unavailable,
never falsely zero. A receipt is not proof the administrator read the information.
submission_batches adds activation_review_id UUID nullable; a composite FK binds
it to the same batch's receipt. A check pairs it with existing activated_at.
A trigger prevents rewriting one-time activation provenance. Receipt plus audit
identifies actor, run, previous batch and resulting revision. No activation table
or duplicate provenance columns are introduced.

Use UUID primary keys, timestamptz UTC, SQLAlchemy 2, Alembic. Add `created_at`, `updated_at` where appropriate.

## Entities
| Entity | Key fields | Notes |
|---|---|---|
| `institutions` | id, permanent_id UNIQUE, name, region, active | Permanent ID belongs to institute, never student |
| `users` | id, email UNIQUE, password_hash nullable, role, institution_id nullable, active, demo_alias UNIQUE nullable, is_demo, created_at, updated_at | Demo login resolves only explicitly seeded synthetic identities; no passwords are used |
| `programmes` | id, institution_id, code, name, active, created_at, updated_at | Institute + programme unique |
| `intake_rules` | id, institution_id, programme_id, academic_year, category, approved_seats, rule_version, source_label | Seeded values marked `DEMO` |
| `submission_batches` | id, institution_id, uploaded_by, academic_year, programme_id, filename, file_sha256, schema_version, status, received_at, completed_at | Submission event is immutable metadata |
| `student_record_versions` | id, batch_id, source_row_number, institution_id, programme_id, academic_year, college_student_id, apaar_identifier_encrypted_or_demo_token, apaar_match_hash, full_name_demo, admission_category, enrollment_status, enrollment_date, original_json, normalized_json | Do not assume APAAR uniqueness across years or histories |
| `validation_findings` | id, record_version_id, rule_code, severity, explanation, evidence_json_redacted, status, created_at | Add `batch_id` if batch-wide |
| `apaar_verifications` | id, record_version_id, adapter_type, status, checked_at, external_reference_nullable, evidence_json_redacted | `SIMULATED` mandatory for mock |
| `review_cases` | id, institution_id, opened_by, assigned_to, status, category, summary, opened_at, resolved_at | A case can reference multiple records |
| `case_records` | case_id, record_version_id | M:N association |
| `case_events` | id, case_id, actor_id, action, comment, created_at | Append only |
| `audit_events` | id, actor_id, institution_id, action, entity_type, entity_id, occurred_at, metadata_redacted | No full identity in metadata |
| `consents` | id, student_reference, purpose, scope_json, issued_at, expires_at, revoked_at, evidence_ref | Later phase |

## ABC extension (optional tables)
`abc_reconciliations` (record_version_id, adapter_type, status, checked_at, evidence_json_redacted); `academic_credit_items` (reconciliation_id, source, course_code, semester, credit_value, year, record_status). Do not fabricate external credit truth.

## Core relationships
- Institution 1:N Programmes, IntakeRules, SubmissionBatches, Users.
- Batch 1:N RecordVersions.
- RecordVersion 1:N Findings and verification attempts.
- Case M:N RecordVersions; Case 1:N CaseEvents.
- Keep old submissions and verification attempts immutable; a new upload supersedes current-view projection, not historical rows.

## Suggested constraints/indexes
- Unique (`permanent_id`) on institutions.
- Unique (`institution_id`, `code`) on programmes.
- Unique (`institution_id`, `programme_id`, `academic_year`, `category`, `rule_version`) for intake.
- `approved_seats >= 0`, `source_row_number > 0`.
- Index `student_record_versions(batch_id)`, `(institution_id,academic_year,programme_id)`, `apaar_match_hash`, findings `(rule_code,status)`, cases `(status,assigned_to)`.
- Compute a keyed HMAC (not unsalted hash) for matching demo IDs where appropriate; encryption and key management must be production-reviewed.
- No blanket unique constraint on APAAR since duplicates and transfers are precisely what we must detect.

## Minimal CSV schema (v1)
`college_student_id,student_name,apaar_id,academic_year,programme_code,admission_category,enrollment_status,enrollment_date`

Allowed demo categories: `REGULAR`, `SUPERNUMERARY`, `NRI`, `OCI`, `FOREIGN_NATIONAL`; these are placeholders for official rule mapping, not policy equivalents. Allowed status: `ACTIVE`, `WITHDRAWN`, `TRANSFERRED`, `COMPLETED`.

## Event lineage
`batch_id + source_row_number` identifies a particular uploaded row. `student_record_versions` reflects that row in that version; an optional `logical_student_record` may later link corrected snapshots using institution+local_student_id, with conflict handling to avoid destructive updates.

## Privacy
Synthetic data in seeds; real deployment would need retention, encryption, consent and data subject rights reviews before collecting any PII.

## Phase 1 schema refinements

Milestone 1 creates institutions, programmes, intake_rules, users and audit_events.
Submission and validation tables are introduced only in later milestones.

Institution administrators require an institution association. Programme/intake
relationships must prevent intake configuration from referencing a programme
owned by another institution. Approved seat values must be non-negative.
Seed intake configurations carry source_label=DEMO and an explicit rule version.

Add submission_scopes:

- id, institution_id, programme_id, academic_year
- current_batch_id nullable, revision, created_at, updated_at
- Unique institution/programme/academic_year; revision starts at zero.

Extend submission_batches with scope_id, submission_mode=SNAPSHOT,
base_batch_id nullable, base_scope_revision and activated_at nullable.
Original submission content is immutable; processing state and a one-time
activation timestamp are operational metadata.

Add immutable validation_runs:

- id, batch_id, kind, evaluated_at
- ruleset_version, ruleset_snapshot_json
- compared_scope_revisions_json

Kinds remain INITIAL and REVALIDATION. Milestone 4 references an explicitly
selected run, without adding an ACTIVATION kind. INITIAL is never CSV ingestion.
The comparison snapshot includes
all current scopes in the compared academic year, including scopes with no match.

Add run_id to validation_findings and classify findings as
ACTIVATION_BLOCKING or REVIEWABLE. Each finding retains its rule, severity,
record/batch references and redacted evidence.

### Milestone 3 concrete storage contract

validation_runs: id UUID primary key; batch_id UUID foreign key; requested_by UUID
foreign key to users; kind INITIAL/REVALIDATION; evaluated_at and completed_at UTC
timestamptz; ruleset_version varchar(64); ruleset_snapshot_json,
compared_scope_revisions_json and summary_json JSONB. Unique (id,batch_id), partial
unique batch_id WHERE kind=INITIAL, index (batch_id,evaluated_at,id).

validation_findings: id UUID primary key; run_id and batch_id UUID; nullable
record_version_id UUID; positive ordinal; rule_code varchar(64); severity
ERROR/WARNING/INFO; classification ACTIVATION_BLOCKING/REVIEWABLE; nullable
field_name varchar(64); explanation text; evidence_json_redacted JSONB; created_at
UTC timestamptz. Unique (run_id,ordinal), index (run_id,record_version_id).
Composite foreign keys tie run and optional record to the same batch. Supporting
unique (id,batch_id) is added to student_record_versions without changing rows.

Group findings retain affected local UUIDs and logical record numbers in evidence;
batch findings have no affected records. Derived record statuses do not require
another table. All applicable findings survive status precedence. Triggers reject
run/finding UPDATE/DELETE. No partial/failed run is persisted. The earlier proposed
mutable finding review status is deferred to officer case workflows, not evidence.
Internal peer version references are returned only to permitted officers; raw
APAAR and HMAC digests never enter finding evidence or audit payloads.

Row validation_status is derived from findings in a specified validation run.
It is not a mutable field on immutable submitted content. Missing or invalid
normalized values may be null while original values remain preserved.

Audit events support a nullable actor_id for system seeding, with actor kind
recorded in redacted metadata. User actions identify their authenticated actor.
Audit payloads contain no passwords, tokens or raw student identifiers.

## Milestone 2 candidate storage contract

Create submission_scopes, submission_batches and student_record_versions using
UUIDs and UTC timestamptz. Scopes are unique by institution/programme/year and
start with current_batch_id=null and revision=0. Uploading changes neither field.
Batch provenance includes the approved fields plus source=CSV_UPLOAD,
file_size_bytes and row_count. SHA-256 hashes cover original file bytes;
identical files are permitted as separate batches. Filenames are untrusted
internal provenance, never filesystem destinations or public response fields.

Rows retain original_json and normalized_json as JSONB with CSV values as strings.
Canonical scope columns come from the upload context; JSON retains row-declared
scope values, including contradictions. Empty and malformed student values remain
stored for later validation. Invalid typed dates and apaar_match_hash may be null.
Matching hashes are not populated in this milestone.

source_row_number counts logical CSV records: header=1, first data record=2.
A quoted value spanning physical lines is still one logical record. This field
is not a physical line number. Enforce unique batch_id/source_row_number.

Composite foreign keys protect programme/institution/scope/batch/row ownership
and keep current/base batch references within their scope. APAAR, college student
IDs and file hashes are not unique. A PostgreSQL trigger rejects row UPDATE/DELETE.
Submitted content stays immutable; batch lifecycle status/completion/activation
metadata remains manageable for later milestones without rewriting row payloads.

Use uniqueness and INSERT ON CONFLICT for race-safe scope creation. No extra
scope/global upload lock is required. Each accepted upload atomically commits
scope creation if needed, batch, all rows and its audit event. Failure rolls back
all new records; rejected files create no batch or rows. Repeated-upload warnings
are advisory: simultaneous identical uploads may not see each other's hashes,
but both persist as distinct candidates without changing the current snapshot.

Synthetic records only. Plain demo tokens/original payloads are not a real-data
security design. Before real student data, approve encryption/key management,
retention/deletion/backup policies, field-level access, lawful purpose/consent,
deployment authentication and security review. No real identifiers are permitted.
