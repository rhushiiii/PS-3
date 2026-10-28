# SIH26263 — Remaining Work

Last updated: 28 October 2026.

This file summarizes the remaining work from the approved project documents and
the latest verification results. It does not authorize implementation or replace
`AGENTS.md` and the context documents in `docs/`.

## Current position

- Phase 0 is implemented: web/API foundation, PostgreSQL, Alembic, configuration,
  liveness and database readiness.
- Phase 1 Milestones 1–4 are implemented: institution foundation, restricted demo
  authentication, immutable candidate ingestion, local validation, evidence-linked
  findings, snapshot review and explicit activation.
- Phase 1 Milestone 5 Steps 5A–5E are implemented: authenticated portal, upload and
  history, validation evidence, review/activation interfaces, institution dashboard,
  AICTE officer dashboard and manager aggregates.
- Step 5F stabilization work has been performed, but final verification remains
  open. Phase 1 should not yet be described as fully verified across browsers.

All student data remains synthetic. Local APAAR format checks do not establish
official identity verification. Intake comparisons use configured DEMO rules.

## Finish Phase 1 — Step 5F verification

- [ ] Diagnose the intermittent isolated browser-stack `OSError` and obtain a
      complete Chromium regression run after the latest test corrections.
- [ ] Complete or diagnose the broader WebKit suite; several scenarios timed out.
- [ ] Resolve Firefox headless startup or verify Firefox on a supported host.
- [ ] Run the database-dependent backend regression and migration tests with the
      required dedicated PostgreSQL test configuration.
- [ ] Complete a manual screen-reader and keyboard accessibility audit, including
      focus management, dialogs, mobile navigation and error announcements.
- [ ] Run a Python dependency vulnerability audit when an approved audit tool is
      available; an offline npm audit alone is not a complete dependency review.
- [ ] After verification, obtain approval to reconcile the README and roadmap
      statements that still describe Step 5F as staged.

Latest recorded evidence:

| Check                           | Result / limitation                                                                                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Full Chromium suite             | 49/50 passed in the latest completed run; the remaining history-recovery test was corrected and passed alone. The subsequent full rerun did not complete because of the stack error. |
| Complete institution UI journey | Passed in Chromium: login → upload → validation → review → activation → updated current dashboard.                                                                                   |
| WebKit smoke                    | Four scenarios passed: review/activation with omissions, activated institution dashboard, accessible sign-in, and upload/history.                                                    |
| Full WebKit suite               | Repeated 30-second timeouts; interrupted before a complete summary.                                                                                                                  |
| Firefox                         | Headless process did not become ready; no test coverage claimed.                                                                                                                     |
| Backend pytest                  | 63 passed, 188 skipped; skipped integration checks still need the dedicated test configuration.                                                                                      |
| Static checks and build         | Frontend lint, strict typing, formatting, API-type drift and production build passed; backend Ruff, formatting and mypy passed.                                                      |
| Database migration checks       | Alembic upgrade and metadata drift checks passed; no new migration was needed for UI stabilization.                                                                                  |
| Accessibility                   | Automated axe and mobile checks passed in covered scenarios; manual assistive-technology review remains open.                                                                        |
| Dependency security             | Offline npm audit reported zero vulnerabilities; `pip-audit` was unavailable.                                                                                                        |

See `docs/08_TESTING_SECURITY.md` for the testing context.

## Phase 2 — Officer cases and simulated APAAR

Status: planned; implementation approval and precise contracts are required.

- [ ] Add the `APAARProvider` interface and a deterministic simulated adapter.
- [ ] Preserve independent local-validation and identity-check statuses.
- [ ] Enforce consent, purpose, role permissions and audit provenance for checks.
- [ ] Clearly distinguish simulated match, mismatch, pending and source-unavailable
      results in API responses and the interface.
- [ ] Build the officer queue, evidence-linked case creation, correction requests
      and immutable case timeline.
- [ ] Let institutions see outstanding requests and submit corrections as new
      immutable batches, preserving the original findings and submissions.
- [ ] Test case permissions, institution isolation, state transitions, simulated
      provider failures and the complete correction loop.

Acceptance: an officer can investigate a potential overlap, request correction and
review a new submission with the earlier evidence still available. Provider results
must carry `SIMULATED` provenance and must never imply government verification or
an automatic fraud determination.

## Phase 3 — Optional simulated ABC credit reconciliation

Status: optional, planned; requires separate approval.

- [ ] Add the `ABCCreditProvider` interface and deterministic simulated fixtures.
- [ ] Enforce consent and purpose checks before accessing permitted credit fields.
- [ ] Compare aligned institution, course, term and credit records only where
      sufficient comparable evidence exists.
- [ ] Preserve reconciliation status, evidence and provenance independently of
      admission validation and APAAR identity status.
- [ ] Present simulated match, mismatch, insufficient-data, pending and unavailable
      outcomes clearly for officer review.
- [ ] Test authorization, consent denial, incomplete evidence and provider outages.

Acceptance: credit reconciliation can be demonstrated without blocking core
admission processing when the provider is unavailable. Academic credits must not
be treated as grade points, SGPA or CGPA. Grade calculations remain deferred until
an appropriate institutional grading scheme is specified.

## Phase 4 — Advanced insights and further polish

Status: planned; approve each feature as a small vertical slice.

- [ ] Flag missing student populations when separately declared totals are available.
- [ ] Detect significant changes or removals between immutable submission versions,
      without treating an omission as proof of withdrawal or misconduct.
- [ ] Add a read-only rule-history view explaining which rules applied to a run.
- [ ] Add enhanced charts and insights supported by actual stored evidence.
- [ ] Build the authorized-verifier prototype with minimum necessary fields,
      explicit consent/purpose checks and backend authorization.
- [ ] Extend accessibility, performance and scalability verification.
- [ ] Prepare deployment instructions and document operational prerequisites.

Acceptance: insights remain explainable and traceable to versioned records and
rules; verifier access is narrowly scoped; deployment guidance makes the prototype's
limits explicit.

## Deferred items and deployment gates

These items are documented future work or requirements requiring further design;
they are not additional approved implementation phases.

- Configurable CSV schema mapping; Phase 1 v1 currently requires strict headers.
- More selective assessment freshness tracking and reduced dashboard request
  fan-out if institution volumes justify the additional complexity.
- Remaining source requirements such as regulatory/accreditation reporting and
  certificate-ID display need an approved implementation milestone and contracts.
- Marketing/landing pages remain deferred and outside the completed portal scope.
- Production authentication and deployment security require a separate approved
  design; local demo authentication must never be exposed as production access.
- Real student data requires approved encryption/key management, retention and
  deletion policies, backup handling, lawful purpose/consent and access controls.
- Real APAAR, ABC, DigiLocker, API Setu or restricted AICTE access requires official
  authorization and verified integration documentation. No such access is claimed.
- Machine-learning features require a separate approved scope and justified data;
  they are not a prerequisite for the deterministic prototype.

## Recommended next action

Close the remaining Step 5F verification gaps first. Then review and approve the
Phase 2 database, API, permissions, case lifecycle and simulated-provider contracts
before implementation. Continue following the feature-based architecture, immutable
history, synthetic-data restrictions, workspace boundaries and prohibition on Git
commands.

Sources: `README.md`, `docs/01_PRD.md`, `docs/02_ARCHITECTURE.md`,
`docs/05_VALIDATION_AND_ABC.md`, `docs/07_IMPLEMENTATION_PLAN.md` and
`docs/08_TESTING_SECURITY.md`.
