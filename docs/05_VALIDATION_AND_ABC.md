# Validation Rules and APAAR–ABC Integration

## Milestone 4 structural eligibility and replacement
Require completed processing/evaluation, consistent row counts, an explicitly
selected compatible run, active owned scope, no ACTIVATION_BLOCKING findings,
and a never-activated candidate. INCOMPLETE row status is not itself a veto:
missing names/APAAR/dates may still be countable. Matching incompleteness,
missing intake rules, potential overlaps and DEMO intake findings remain visible
and reviewable, never automatic fraud or official-violation determinations.
New runs capture structural policy LOCAL-STRUCTURE-DEMO-v1. Legacy LOCAL-DEMO-v1
maps explicitly to structural v1 only, with exact category/status/programme/year
compatibility. Missing version data never implies future-policy compatibility.
Material structural changes must bump the policy version and require revalidation
and a new review. Activation also reuses current structural checks without
overwriting old evidence. Reviewable APAAR/intake configuration stays pinned to
the selected run; no hidden switch of runs or rules.
Compare exact trimmed case-sensitive college_student_id within one scope, never
merge on APAAR. Show added/retained/omitted counts, previously ACTIVE omissions,
current/candidate declared and ACTIVE totals, category/status deltas and transitions.
Omission means absence from replacement, not inferred withdrawal/transfer.
Require explicit omission acknowledgment without an automatic rejection threshold.
Only current activated rows supply current counts; history never accumulates.
ACTIVE alone counts as demo active; other supported statuses remain declared.
Invalid APAAR/name/date does not silently exclude countable rows.
Own-scope review staleness causes 409; cross-assessment staleness does not.
Stale/incomplete overlap metrics remain null, not a clean zero.

## Pipeline phases
A. CSV parsing / normalization  
B. Field validation  
C. Structural APAAR checks  
D. Cross-record, institution and intake rules  
E. Optional external APAAR identity check (authorized or simulated)  
F. Optional ABC credit reconciliation (authorized or simulated, **non-blocking**)  
G. Evidence/findings and officer review

## Deterministic MVP rules
| Rule code | Rule | Evidence and handling |
|---|---|---|
| `REQUIRED_FIELD_MISSING` | Required CSV field absent/empty | column + row |
| `INVALID_ACADEMIC_YEAR` | Year differs from upload context or malformed | observed/year |
| `INVALID_APAAR_FORMAT` | Nonempty structurally wrong identifier; missing uses REQUIRED_FIELD_MISSING; demo uses 12 ASCII digits | NEVER label as official invalid identity |
| `DUPLICATE_IN_BATCH` | Same normalized APAAR appears twice within batch | related row IDs |
| `POTENTIAL_CROSS_INSTITUTION_DUPLICATE` | Matching token appears in multiple institution record histories | show institutions; possible transfer |
| `INVALID_ENROLLMENT_STATUS` | Unsupported status enum | observed value |
| `INTAKE_EXCEEDED` | Compared to matched year+programme+seat category approved cap | approved vs reported, rule version |
| `MISSING_INTAKE_RULE` | No approved cap configured | pending rule review, not violation |
| `DECLARED_VS_ITEMIZED_COUNT_MISMATCH` | Optional declared totals disagree with row counts | flag missing population |
| `RECORD_CHANGED_AFTER_FLAG` | Later phase: deletion/edit after a warning | compare submission hashes and versions |

## Critical APAAR distinction
- Local format: e.g. demo `^[0-9]{12}$`; no checksum or official validity inferred.
- `APAARProvider.verify(...)`: requires authorized connection and consent/purpose; only authentic providers may produce official `MATCH/MISMATCH`.
- `MockAPAARProvider`: deterministic synthetic fixtures; returns `SIMULATED_MATCH`, `SIMULATED_MISMATCH`, `SOURCE_UNAVAILABLE`, `PENDING`.
- Prefer mock seed identifiers that are unmistakably synthetic and are never passed to external services.
- Never conflate syntactic pass with existence, person match, or availability of academic history.
- Provider payload retention should be minimized; log provider label, time, status and redacted evidence.

## Intake checks
- Count **current, applicable active enrolments** for institute+programme+academic year+category.
- Separate regular vs applicable approved supernumerary/other categories; avoid simplistic one-cap-for-all comparisons.
- A `DEMO` rule configuration is not a representation of the current AICTE handbook.
- If rules are absent, record `MISSING_INTAKE_RULE` and avoid making a violation claim.
- Count deltas may be computed per new batch/current view while retaining history; do not accidentally sum historical reuploads.

## Duplicate checks
The same APAAR across institutions is reviewable, not proof of duplicate admission or fraud. Compare active date intervals when available; support transfer and withdrawal explanations. Same APAAR with changed names requires identity review but not automatic merging.

## ABC extension (optional)
Interface `ABCCreditProvider.get_credits(student_reference, purpose, consent_ref)`.
Expected provider result: `source_type`, `retrieved_at`, `status`, `credit_items` with course, term, awarding institution and credit value where disclosed. Compare only aligned terms/courses and only when both authorized source and college-reported credits exist.
Statuses: `NOT_REQUESTED`, `SIMULATED_MATCH`, `SIMULATED_MISMATCH`, `PENDING`, `SOURCE_UNAVAILABLE`, `INSUFFICIENT_DATA`.
Credit absence = insufficient or pending evidence, NOT misconduct.
ABC *credits* != grade points/CGPA. SGPA/grade-point checks are deferred optional work requiring course grading rules.

## Sample safe mock scenarios
- Demo APAAR identifier `900000000001` => simulated match
- `900000000002` => simulated mismatch
- `900000000003` => source unavailable
All synthetic and labeled mock; do not assert they correspond to any existing student.
- ABC fixture for demo `900000000001`: college reports 24 credits, mock source also 24 => simulated match.
- Demo `900000000002`: college reports 24, mock source 20 => simulated mismatch and officer review.
- ABC provider unavailable => intake monitoring still completes normally.

## Corrections
On correction, create a new submission batch/version, rerun checks, link unresolved findings and close only through authorized action. Don't delete old evidence.

## Testing criteria
Fixtures explicitly exercise each rule, rule version, category exception, transfer interpretation, consent denial, provider outage, and source labeling.

## Phase 1 processing, eligibility and review distinctions

File-processing failures include configured byte/row-limit excess, unsupported
encoding, binary/NUL content, malformed CSV, inconsistent column counts,
missing/duplicate/unexpected v1 headers, and zero data rows.
Accept UTF-8 with an optional BOM. Initial configurable limits are 5 MiB and
1,000 data rows. Failure never changes the current snapshot.

Strict CSV headers are a Phase 1 v1 limitation, not a source-derived restriction
on interoperable submissions. Configurable schema mapping is reserved for a
future enhancement; the initial uploader does not implement header mapping.

Activation blockers are:

- Missing or repeated normalized college_student_id.
- Missing, malformed or upload-context-mismatched academic year.
- Missing or upload-context-mismatched programme code.
- Missing or unsupported admission category.
- Missing or unsupported enrolment status.
- Incomplete/failed processing or required structural evaluation.

Activation additionally requires an authorized actor, an active institution and
programme, the correct scope, an eligible candidate and an unchanged reviewed
scope revision. Previously activated/superseded batches are not reusable as new
candidates.

Missing student names and missing/invalid enrolment dates are visible REVIEWABLE
findings when other fields allow reliable counting. Preserve their original
values. Missing/invalid APAAR, potential duplicates, intake excess and missing
intake configuration are also REVIEWABLE and do not independently block activation.

A required CSV column is different from a required value: v1 headers must exist,
but empty cell values are retained and assessed under the rules above.

VALID, FLAGGED and INCOMPLETE describe a record within a specified validation run.
INCOMPLETE means a required value is missing; FLAGGED means another finding
exists; VALID means no findings. INCOMPLETE/FLAGGED do not alone determine
activation eligibility. No new APPROVED status is introduced.

Current accounting uses only the activated snapshot:

- Total declared records: all its rows.
- Demo active enrolments: rows with normalized enrollment_status=ACTIVE.
- Category totals: declared and active counts separately.
- Potential duplicates: separate review metrics, never automatic record merging.

Invalid APAAR never silently removes an otherwise countable record. Intake
comparisons are against configured DEMO rules, not official AICTE violations.

Cross-institution evidence distinguishes current ACTIVE records in the compared
academic year from historical/inactive matches. Existing date fields cannot
prove overlapping enrolment intervals or establish a transfer explanation.

Assessments are FRESH only while the complete compared scope/revision map still
matches. Changes, additions or removals make them STALE. Earlier evidence is
unchanged. Stale duplicate totals must be labeled stale/unknown rather than
presented as current or zero. Officer revalidation appends a fresh run.

This freshness mechanism is conservative. Changes unrelated to a particular
match can still invalidate its assessment, and increasing institution counts
may trigger additional revalidation. More selective tracking is a possible
future enhancement, not part of the initial implementation.

Institution responses redact other institutions' student details. Authorized
officer evidence retains permitted version references.

## Milestone 2 parsing and normalization

Headers must match documented v1 names and order exactly. Accept UTF-8 with an
optional BOM, comma delimiters and standard CSV quoting. Blank physical records
are rejected rather than discarded; eight empty cells remain a data record.
Logical record numbering counts header=1, then records=2,3,... independently of
physical lines inside quoted fields. Preserve decoded original cell values,
whitespace, leading zeros, malformed identifiers and quoted multiline content.

Normalization trims surrounding whitespace and uppercases programme/category/
status strings, retaining unknown values. Names and student IDs are not case-folded.
APAAR is never numeric-converted, padded or stripped of internal punctuation.
Parse only unambiguous YYYY-MM-DD dates; other strings stay in normalized_json
with a null typed date. No student validation/duplicate/intake rules run here.
Complete-snapshot intent does not prove complete population coverage. No row is
excluded just because its student values are malformed.

## Milestone 3 exact local rules

Ruleset LOCAL-DEMO-v1 checks all eight required v1 values. Missing student ID,
year, programme, category or status is ERROR/ACTIVATION_BLOCKING. Missing name,
APAAR or date is WARNING/REVIEWABLE. Missing values do not additionally receive a
format error for the same absence. Every other applicable finding is preserved.

Additional ERROR/ACTIVATION_BLOCKING rules: DUPLICATE_COLLEGE_STUDENT_ID (trimmed,
case-sensitive), INVALID_ACADEMIC_YEAR (nonconsecutive/malformed or context
mismatch), PROGRAMME_MISMATCH, INVALID_ADMISSION_CATEGORY and
INVALID_ENROLLMENT_STATUS. Supported categories/statuses remain the documented
DEMO values. INVALID_ENROLLMENT_DATE checks actual YYYY-MM-DD calendar dates and
is WARNING/REVIEWABLE. No name/date/APAAR finding alone excludes countable rows.

INVALID_APAAR_FORMAT uses configurable APAAR_FORMAT_LENGTH (default 12), ASCII
digits only, without checksum. Only structurally valid nonempty tokens participate
in keyed HMAC matching. Dedicated APAAR_MATCHING_KEY comes from environment,
requires at least 32 bytes, and has no hard-coded/generated fallback. Missing
configuration prevents a successful run. The key and digests are never returned,
logged or stored in evidence; the submitted-row hash column stays unchanged.
APAAR verification remains NOT_CHECKED and ABC remains NOT_REQUESTED.

DUPLICATE_IN_BATCH is WARNING/REVIEWABLE. Cross-institution matches against
current ACTIVE peers in the same year are WARNING/REVIEWABLE only for local
ACTIVE records. Other matches are INFO/REVIEWABLE, labeled CURRENT_INACTIVE,
LOCAL_INACTIVE, HISTORICAL, DIFFERENT_YEAR or UNACTIVATED_CANDIDATE. They do not
contribute to current_overlap_records. No fraud inference, merging or interval
proof is made. Invalid candidate identifiers or unclassifiable structural rows,
and invalid identifiers in relevant current ACTIVE peers, make matching incomplete;
the current metric is null, with known evaluation evidence retained separately.

Candidate summaries separate reported rows, candidate demo ACTIVE rows, declared
category totals, allocated ACTIVE category totals, ambiguous student IDs,
unclassifiable rows and potential matches. Do not sum prior uploads or add a
candidate to current enrolment. Missing/repeated student IDs make counting
uncertain; do not deduplicate silently. Structural inconsistencies make intake
comparisons incomplete; a below-capacity partial count is not a pass.

Select VALIDATION_INTAKE_RULE_VERSION explicitly (default DEMO-v1), restricted
to source_label=DEMO, exact institution/programme/year/category. Never infer the
latest version by sorting. Snapshot rule IDs, capacities and versions in each run.
INTAKE_EXCEEDED is WARNING/REVIEWABLE for allocated ACTIVE rows above the matching
DEMO cap; MISSING_INTAKE_RULE is WARNING/REVIEWABLE for any of the five supported
categories without configuration, including zero-count categories. Neither is an
official AICTE violation. Batch-only findings do not change individual row status.

Status precedence is INCOMPLETE > FLAGGED > VALID for the selected immutable run;
all findings remain accessible. VALID means no applicable local record findings,
not official APAAR verification, batch eligibility, or a fresh external assessment.
Freshness and completeness are separate from this record status. Stale evidence
is retained and labeled, never automatically resolved or presented as a clean zero.
