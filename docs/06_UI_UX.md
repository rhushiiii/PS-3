# UI / UX Blueprint

## Step 5B institution upload and submission history

/institution/upload is institution-administrator-only. Set the institution from
/me, list permitted active programmes from the API, accept a consecutive academic
year, and require synthetic-only acknowledgment. Explain that one file is a complete
candidate for one programme/year across all admission categories; a future explicit
activation replaces that scope, but uploading never does. Fetch configured byte/
record limits, encoding and exact ordered headers from /submissions/upload-policy.
Download a strict-v1 header-only template; no mapping or student-content preview.

/submissions provides own-institution history for administrators. Officers browse
an institution via /aicte/institutions/{id} and its history link, passing only an
institution UUID as context. Without context, offer the institution directory.
Managers/verifiers have no submission navigation or access. Backend authorization
remains authoritative. Paginate history and filter programme/year using existing
API parameters. Label CANDIDATE/CURRENT/PREVIOUS separately from processing status.
Show redacted provenance on demand; no filenames, CSV contents or APAAR values.
Stored row counts are declared rows, not current active-enrolment totals.

Show loading, empty, rejected and unknown-outcome states. Lock the form during
processing; never retry a POST automatically or queue it for reconnect. Confirm
storage only after a valid successful API response. An interrupted upload may
have completed; direct users to history without treating absence as proof of
failure. Explicitly prepare another upload after success/unknown outcome; it
creates a new candidate. Expiry/logout clears private state, and sign-in explains
checking history after interruption. No validation/results/review/activation
controls or dashboards are implemented in 5B.

## Approved Milestone 5 staging and 5A interface

Implement the institution journey before dashboards. 5A provides /login,
/institution, /aicte/institutions, /aicte/institutions/{id} and /access-denied with
role-specific functional navigation, real metadata, loading/empty/error/retry
states, responsive native-dialog navigation and a persistent synthetic-data notice.
The /aicte entry is the role-specific dashboard; /aicte/institutions is the
institution directory. Step 5E uses actual current-snapshot API data for dashboards.
Do not expose dead upload/dashboard/case controls in 5A.
Use the approved off-white/white/olive/bronze palette, system typography and clear
hierarchy. Darken action tones where needed for contrast; labels, not colour alone,
convey state. Active institution/programme labels are not official approvals.
Login is explicitly enabled with NEXT_PUBLIC_DEMO_UI_ENABLED=true for local use;
the default is disabled. Backend restrictions still control actual authentication.
A page refresh signs out. Tokens never appear in URLs, storage, logs or UI.
No public marketing hero, provider controls, fabricated KPI values, case ageing
or historical trend charts are built in this milestone. Subsequent screens use
actual API-backed synthetic declarations and explicitly label unavailable data.

## Step 5E institution, officer and manager dashboards

`/institution` is the institution administrator's dashboard. Use the authenticated
institution summary for current declared records, demo ACTIVE enrolments, category
counts and programme declaration coverage. A programme with no current snapshot is
missing coverage, not a zero count. Show configured intake comparisons as DEMO
rules, never as official AICTE compliance findings. Recent uploads remain labeled
candidate/current/previous and provide next actions without implying activation.

`/aicte` is the shared officer/manager dashboard. Officers may compare permitted
institutions, filter by academic year, institution and available region, and inspect
current cross-institution assessment freshness. Freshness must distinguish fresh,
stale, incomplete and unavailable; stale or unavailable overlap metrics are not
zero. Managers receive aggregate summaries and institution metadata only: do not
request or render submission histories, student rows, identifiers or findings.
Use backend responses for all counts and chart values, preserve role-based navigation,
and keep the synthetic-data banner visible. These dashboards make no government
verification or official regulatory-compliance claim.

The officer freshness view composes current submission histories and latest
validation-run details from existing APIs. It is suitable for the seeded prototype;
the number of requests grows with the institution list. No additional analytics
endpoint is part of Step 5E.

Milestone 4 is API-only. Future review screens must distinguish current/candidate
totals, total omissions and previously ACTIVE omissions, category/status changes,
structural blockers and reviewable warnings. Receipts record presented information,
not proof it was read. Activation requires separate replacement/warning confirmations
and omission acknowledgment when applicable. Stale own reviews require a new
review; stale duplicate assessments remain explicit warnings. Omission must not
be displayed as inferred withdrawal. No screens are implemented in this milestone.

## Visual direction

Premium minimal style inspired by user-selected Synex fintech hero reference, **not** a copy. Background `#F5F5F2`, cards `#FFFFFF`, text `#111111`, muted gray `#6F6A64`, olive/bronze `#8D8C59` / `#926C30`; data accent blue for verification. Maintain WCAG-minded contrast and accessible typography.

## Navigation architecture

### Landing (public demo)

Hero: **Monitor Admissions. Verify Records. Detect Anomalies.** Two CTAs: `Explore Demo` and `How It Works`. Right-side dashboard illustration using fictional data; clearly label demo metrics. Login leads to role-scoped app.

### Institution portal

- Overview: current AY, uploaded students, incomplete records, pending fixes.
- Upload: CSV template download, drag-drop, upload context (programme/year), mapping preview.
- Batch review: per-row validation messages, filter/export feedback, see history.
- Corrections: cases and reply/resubmit actions.
- Settings: institution details and operator accounts (later).

### AICTE officer

- Overview: institution counts, reported enrolment, unresolved anomalies, time-to-resolution, year/programme/region filters.
- Institutions directory: searchable and sortable, intake vs reported by category.
- Anomaly center: list by type/severity, evidence, source timestamps.
- Case detail: student record versions (masked), possible transfer explanation, supporting evidence, requests, audit trail.
- Reports: safe aggregate downloads.

### Manager

Aggregate dashboard for current institution/programme declarations, without
student-level submissions, identifiers or findings. Trend and ageing analytics
remain future enhancements; Step 5E does not imply these metrics are implemented.

### Authorized verifier (later)

Explicit purpose + consent, scoped lookup, minimal result, access audit. No public student search.

## Key UX rules

- Labels distinguish **Format checked**, **Simulated identity check**, **Source unavailable**, **Review required**, and **Officially verified** (the last only if actually supported).
- Every anomaly contains `Why flagged`, `Which record(s)`, `Which rule`, `What action`.
- Avoid "fraud", "fake", or "verified by government" labels for internal checks.
- Use loading, empty, invalid CSV, partial success and API outage states.
- Use clean vertical panels and minimal crossing connectors, matching user preference for uncluttered diagrams.
- Dashboard statistics come from API-backed synthetic records, never hard-coded UI figures, and must show `Demo data`.

## Component inventory

`AppShell`, `RoleNav`, `FilterBar`, `KpiCard`, `StudentTable`, `BatchUploader`, `ValidationSummary`, `FindingBadge`, `EvidenceTimeline`, `ReviewActionPanel`, `VerificationStatus`, `SeatCategoryChart`, `AuditTrail`, `DemoSourceBanner`.

## Responsive behavior

Desktop 12-column layout; mobile stacked KPI cards and scrollable tables with safe truncation. Mask APAAR like `********0001` where demo authorizations allow disclosure.

## First-page acceptance

Officer dashboard populated from API, not hard-coded chart data; data states and demo labels visible; institution admin cannot navigate API endpoints for other institutions.

## Phase 1 staged interface behavior

Milestone 1 is API-only; no new frontend screens are included.

Later milestones distinguish candidate, current and previous snapshots.
Review shows blockers separately from reviewable findings, replacement counts,
and previously declared identifiers omitted by the candidate. Omission means
absence from the new declaration, not an inferred withdrawal or transfer.

Activation requires explicit confirmation and handles revision conflicts.
Show demo accounting/rule labels and stale duplicate assessments clearly.

Phase 1 v1 requires the documented CSV headers. Configurable schema mapping and
the mapping-preview interaction described above are future enhancements, not
part of the initial uploader.

When a session expires, clear the in-memory token and show:
"Your demo session expired. Select a demo account to continue."
Do not silently impersonate another identity or automatically renew the session.
