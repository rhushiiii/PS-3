# Testing, Security, and Demo QA

## Automated browser testing removed

Automated browser/e2e testing (Playwright, including its WebKit/Chromium/Firefox
coverage, the isolated test-stack helper and automated axe accessibility checks)
has been removed from this project. Frontend verification is limited to `eslint`,
`tsc --noEmit`, `prettier --check`, `next build` and manual testing in a browser.
There is no automated UI regression suite, no automated accessibility check, and
no owned-stack browser-test harness. Manual testing — including keyboard,
mobile-layout and screen-reader checks — is required before each release and is
not currently tracked as repeatable, scripted coverage.

Milestone 4 acceptance: explicit upload/validation separation; first activation
and replacement; immutable receipts/provenance; version compatibility and no silent
run substitution; current structural recheck; structural blockers versus permitted
reviewable findings; omission and previously ACTIVE omission totals, category/status
differences, required acknowledgment and no arbitrary omission threshold; ambiguous
comparisons unavailable; current-only counts/coverage without history double-count;
stale reviews/replays; active scope/actor checks; institution isolation and
aggregate-only manager access; redacted responses/audits; injected failure after
batch/scope/audit/commit writes with complete rollback; real same/different-scope
PostgreSQL races and NOWAIT conflict without global locking; stale cross-assessments;
migration round trips/drift and real loopback HTTP review/activation smoke.

## Test pyramid

Milestone 3 acceptance: every required field and structural/reviewable rule;
multiple findings retained despite status precedence; scoped initial validation
and officer revalidation; immutable runs/findings and original source preservation;
atomic rollback on database/budget failures; explicit missing/short matching-key
failure; deterministic rule snapshots and category/year-specific DEMO intake;
concurrent INITIAL requests (201/409) and concurrent append-only revalidations;
current ACTIVE matches separated from informational histories/candidates/inactive
or different-year matches; scope map additions/revisions/removals stale without
overwriting evidence; incomplete/stale metrics null, never false zero;
cross-institution redaction and no raw APAAR/hash/key exposure; selected-run
filters, invalid/foreign IDs, pagination and formula-injection-safe CSV.
Migration round trips and metadata drift run only in newly created PostgreSQL
test databases. Real loopback HTTP smoke covers upload -> validate -> findings ->
rows -> feedback -> officer revalidation; activation remains unimplemented.

- Unit: normalization, APAAR format, duplicate logic, intake per year/category, status mapping, mock fixtures.
- DB integration: migrations, row-version preservation, row scoping and audit.
- API: auth, upload, batch browse, results, case transitions, mock consent checks.
- UI: manual verification of upload -> findings -> officer reviews -> correction; no automated UI test runs this path.
- Security: unauthorized institution, IDOR, malformed CSV, oversized files, log redaction.

## Test matrix

| Case                                  | Expected                                                          |
| ------------------------------------- | ----------------------------------------------------------------- |
| Valid 12-digit demo token             | `format_ok`, no official identity claim                           |
| APAAR missing                         | row flagged, evidence preserved                                   |
| ID 11 digits or alphabetic            | structural error, not an official-provider result                 |
| Two rows same ID in batch             | duplicate finding                                                 |
| Same ID in different institutions     | potential overlap, do not merge                                   |
| Transfer status present               | case review can record legitimate transfer                        |
| 70 regular admissions, regular cap 60 | regular intake discrepancy                                        |
| NRI/supernumerary admissions          | evaluate against their configured category rules, not regular cap |
| Missing approved intake rule          | pending rule configuration, no automatic violation                |
| Reupload corrected CSV                | new batch; old records remain                                     |
| API mock `SOURCE_UNAVAILABLE`         | explicit label; local validation unaffected                       |
| ABC mock unavailable                  | core batch completes                                              |
| No consent for external mock call     | forbidden/denied                                                  |
| Institution A queries B batch         | 403 or privacy-preserving 404                                     |
| Student PII in log assertion          | redaction checks pass                                             |
| CSV formula cell export               | escaped; no spreadsheet formula execution                         |

## Security controls for prototype

- Demo-only credentials and auth explicitly indicated; never ship this mode to production.
- JWT/session signing secret via env; expiration and cookie handling when implemented.
- Authorization on every read, mutation and export; deny by default.
- File size/row count limits and explicit accepted formats; safe temporary file cleanup.
- AES-based encryption may be added with production security review; don't invent encryption compliance.
- Minimize PII, protect backups, no full APAAR in frontend list views or logs.
- CORS restricted to local dev frontend origins; secure deploy profile later.
- Audit actions append-only. Use synthetic data exclusively for demos.
- Don't use third-party LLM endpoints for student PII by default.
- A model or rule finding is a lead for review, not a conviction.

## CI target

Backend: `ruff check`, `ruff format --check`, `mypy` (if configured), `pytest`.  
Frontend: `npm run lint`, `npx tsc --noEmit`, `npm run build`. No automated E2E.  
Docker: `docker compose config`, migration tests.

## Demo script (6–8 minutes)

1. Show role-specific landing/overview.
2. College admin uploads sample bad CSV.
3. Explain exact validation findings and category-aware intake logic.
4. AICTE officer finds a cross-college overlap and reviews evidence.
5. Demonstrate simulated APAAR provider and visibly labeled result.
6. Officer requests correction; college uploads corrected version; show audit history.
7. Optional: ABC simulated credit mismatch/outage (must still preserve admission workflow).
8. Close with gaps before real deployment (auth, official API onboarding, legal/privacy and exact rules).

## Done criteria

Every demonstrated metric is sourced from synthetic DB fixtures, all demo-only verification is disclosed, tests pass or failures are clearly documented, and no statement implies current official integration.

## Phase 1 additional acceptance checks

Milestone 1: fresh PostgreSQL migrations; dedicated test-database isolation;
repeatable seeds; seed-conflict rollback; production/demo configuration guards;
local/proxy restrictions; server-controlled aliases; forged/expired tokens;
inactive identities; role permissions; institution/programme isolation;
parameter validation; audit redaction; unchanged health/readiness behavior.

Later milestones: reviewable missing names/dates/APAAR remain countable;
structural blockers prevent activation; reuploads never double-count;
same-scope concurrent activations produce one success and one conflict;
different scopes do not require a global lock; concurrent cross-institution
changes produce detectable stale assessments; revalidation preserves earlier runs.
