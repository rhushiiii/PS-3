# SIH26263 — Remaining Work

Last updated: 30 October 2026.

## Master-plan execution (30 October 2026)

The PRAVYA master plan (Phases 0–10) was executed in order. Where this section and
older sections below disagree (for example Step 5F "staged", Phase 3/4 "planned"),
this section reflects the current code. Student data is still synthetic only.

| Phase | Result |
| ----- | ------ |
| 0 Audit | Feature matrix and baseline produced; baseline backend 268 passed with PostgreSQL |
| 1 Core | Excel (.xlsx) upload, optional upload `Idempotency-Key`, CORS fix, formatting fix (migration 0007) |
| 2 Cases | Priority/severity/due date, overdue + escalation, assignment, response and resolution reason, filters, in-app notifications (0008, 0009) |
| 3 Dashboards | Manager analytics (`/analytics`), audit explorer (`/audit`), institution correction-request card, verifier workspace (`/verify`) |
| 4 Registry | `/records` search and `/records/{id}` provenance, history, findings, cases |
| 5 Intake | Rule changes with audit, declared totals, immutable assessments, what-if simulator (0010) |
| 6 Integrity | Rule-based signals, score components, officer decisions (0011); no ML |
| 7 Verification | Format vs identity separation, timeout/retry/idempotency, signed Ed25519 credentials, verifier log (0012) |
| 8 Reports | CSV/XLSX/PDF reports reconciled with analytics, `/reports` page |
| 9 Security | Rate limits, security headers, log redaction, body cap, route-access sweep test |
| 10 Demo | `samples/demo/`, `python -m app.demo_scenario`, `tests/test_demo_e2e.py` |

Verification actually run on 30 October 2026 (final pass, by the main session):

- Backend `ruff check`, `ruff format --check` (124 files), `mypy` (124 files),
  `pip check`: all clean.
- Backend `pytest` without a test database: 149 passed, 506 skipped.
- Backend `pytest` with a PostgreSQL 16.15 test database: **655 passed, 0 failed**.
- Frontend `npm run lint`, `format:check`, `typecheck`, `api:check`: clean; `npm run build`:
  exit 0, all new routes present.
- Demo runner (reported by its subagent, plus the e2e test in the 655): 12/12 steps; validation
  findings TP 9 / FP 0 / FN 0; intake calculations 56/56 exact; integrity signals
  TP 11 / FP 0 / FN 0; report-vs-analytics 19/19 equal; 14/14 authorization checks; no raw
  APAAR in 126 scanned responses.

Known limitations and not done:

- **No browser has been used on any UI built in this run.** The frontend is verified by lint,
  typecheck and build only; a manual click-through, a keyboard/screen-reader audit and
  mobile checks are still required. No automated UI suite exists (removed by user direction).
- Tests ran against PostgreSQL 16.15, not the README's PostgreSQL 17; `alembic upgrade head`
  was exercised by the migration tests and the demo runner, not against the Docker image.
- Docs `03_DATA_MODEL.md` and `04_API_CONTRACT.md` have not been updated for the new tables
  and routes (OpenAPI is the current contract). Decisions are in `09_DECISIONS_AND_ASSUMPTIONS.md`.
- Rate limits are per process; credential key rotation, email notifications, QR image
  rendering and real-data security (retention, encryption, consent) are not implemented.
- Intake rule/declaration values, integrity severities/weights and thresholds are DEMO
  assumptions, not official AICTE values. Simulated APAAR verification is not government
  verification; no external integration is claimed.
- Admin dashboards fetch the first 100 institutions/programmes; assessment/simulation result
  shapes are loose objects in the generated types (local frontend types mirror the backend).
- During the run, two subagents executed a read-only git command by mistake; nothing in the
  repository was changed by them.

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
- Automated browser/e2e testing (Playwright, its WebKit/Chromium/Firefox coverage,
  the isolated test-stack harness and automated axe accessibility checks) has been
  removed from the project at the user's direction. Frontend verification is now
  limited to lint, strict typing, formatting, production build and manual
  browser testing; there is no automated UI regression suite.
- A real marketing/landing page now exists at `/` (previously it only redirected
  to `/login`), with a `framer-motion`-animated hero, a WebGL tricolor shader
  background (user-supplied), and a feature grid. Sign-in is now reachable
  from a navbar dropdown on all public pages, not only from the `/login` form.
- The application UI was rebranded **PRAVYA** and the landing page rebuilt into
  a full scroll-driven marketing site (7 sections) — see "PRAVYA rebrand and
  landing redesign" below.

All student data remains synthetic. Local APAAR format checks do not establish
official identity verification. Intake comparisons use configured DEMO rules.

## Frontend functional audit (28 October 2026)

Since no browser-automation tool is available in this session, "implement what's
on priority" was interpreted as: do the one thing possible without clicking
through a real browser — a careful manual trace of every recently-added
frontend component against its actual data/control flow, instead of trusting
that lint+typecheck+build passing meant the logic was right. It didn't, fully:

- [x] **Real bug found and fixed:** `components/public-nav.tsx` built its
      Sign In dropdown as a single JSX value (one `useState`, one `useRef`)
      and rendered that *same* value in two places — the desktop nav and the
      mobile panel. Both exist in the DOM simultaneously on a mobile
      viewport (the desktop one is only `display: none`, not unmounted), so
      the one `containerRef` got attached to two different DOM nodes and
      `.current` could only ever hold one of them — breaking click-outside-
      to-close unpredictably on mobile. Fixed by extracting a `SignInMenu`
      component with its own state/ref per mounted instance.
- [x] **Real bug found and fixed:** `features/auth/login.tsx` only read
      `?alias=` into state via a `useState` initializer, which only runs
      once at mount. Clicking a *different* account in the nav dropdown
      while already sitting on `/login` would not change the preselected
      radio. Fixed with React's documented "adjust state during render"
      pattern (not an effect — the stricter `react-hooks` lint rules now in
      this project's eslint config correctly reject synchronous `setState`
      in a `useEffect` body for this).
- [x] Those same stricter lint rules caught two more real issues once I
      actually read lint's output line-by-line instead of trusting an "exit
      0" summary: an unescaped apostrophe in `cases/detail.tsx`, and
      `StatusDonut` (`dashboards/components.tsx`) reassigning a closure
      variable (`offsetSoFar`) during render to compute cumulative donut
      offsets — rewritten as a pure derivation (`lengths`/`offsets` arrays)
      with no mutation. Worth noting for future sessions: `tail -N` on a
      background lint command's output is not the same as confirming it's
      actually clean — read the body.
- [x] Backend field-shape assumptions in the new chart wiring
      (`counts.statuses`, `counts.categories`) were re-verified directly
      against `services/api/.../submissions/services.py`'s
      `snapshot_counts()` — confirmed to always include all status/category
      keys (zero-filled, not omitted), matching what the frontend filters
      assume.
- [x] Lint, typecheck and production build clean after every fix; `/`,
      `/login`, `/login?alias=demo_officer`, `/cases` re-smoke-tested (200).
- [ ] This was a code-reading audit, not interaction testing. It catches
      "this will definitely misbehave" bugs, not "this looks wrong" or
      "this is confusing to use" ones. A real click-through pass is still
      the next thing that should happen before trusting this UI fully.

## PRAVYA rebrand and landing redesign (28 October 2026)

User-directed, cross-cutting. Supersedes most of the "Visual UI overhaul"
entry below (that entry is kept for history; this one reflects current state).

- [x] **Branding.** All visible "SIH26263"/brand-mark references across the
      app (public nav, portal sidebar/footer, `<title>`) now read **PRAVYA**.
      New shared `components/brand-mark.tsx` used by both the portal
      `AppShell` and the public nav, so the two don't drift. Google Fonts
      (Manrope for headings, Inter for body) loaded via `next/font/google` in
      `app/layout.tsx`, applied through CSS variables — no new dependency,
      this ships with Next.js.
- [x] **Demo wording removed from UI chrome**, not from data. Swept every
      visible label/heading/badge/button across `login.tsx`, `accounts.ts`
      (account display names only — `alias` values matching backend
      `demo_alias` fixtures are untouched), `feedback.tsx` (`DemoBanner` →
      `DataNotice`), both dashboards, `validation/workspace.tsx`,
      `submissions/review-activation.tsx`, `validation/guidance.ts`, and
      `lib/api/client.ts`'s error copy. Backend field names
      (`demo_active_records`, `demo_alias`, `demo_mode`), the
      `NEXT_PUBLIC_DEMO_UI_ENABLED` env var, and seed-data institution names
      (which literally contain "Demo " from fixtures) were deliberately left
      alone — those are contracts/fixtures, not UI copy, and the user's own
      instructions carved that out explicitly. Honest synthetic-data
      disclosures (e.g. "Synthetic data only") were kept; only the
      hackathon-prototype-coded vocabulary ("DEMO" badges, "prototype") was
      removed.
- [x] **Landing page rebuilt as a 7-section scroll experience**
      (`features/landing/home.tsx`): full-viewport hero (shader background,
      no card — headline sits directly on the gradient with a text-shadow
      for legibility instead of an opaque panel), Overview (3 pillars),
      How It Works (4-step timeline with a scroll-linked progress line via
      `useScroll`/`useTransform`), Features (6 cards), Platform Preview
      (reuses the real `MetricCard`/`CategoryBars`/`StatusDonut` components
      with illustrative numbers explicitly labeled "not live data" — nothing
      presented as real), Security & Trust (4 cards describing safeguards
      that are actually implemented, not aspirational ones), and a final
      CTA + footer.
- [x] **Sticky, scroll-spy navbar** (`components/public-nav.tsx` rewritten):
      transparent over the hero, frosts in on scroll; active-section
      highlighting via `IntersectionObserver`; animated underline pill
      (Framer Motion `layoutId`); mobile hamburger with an animated
      slide-down panel. Sign-in dropdown logic from the earlier slice kept
      as-is, just reskinned.
- [x] All Framer Motion animations respect `prefers-reduced-motion` via
      `useReducedMotion()` (hero, reveals, timeline, scroll indicator) on top
      of the existing CSS-level reduced-motion handling for the canvas.
- [x] Lint, typecheck and production build re-verified clean; `/`, `/login`,
      `/login?alias=...`, `/cases`, `/aicte`, `/institution` smoke-checked
      over HTTP (200s); confirmed no remaining "SIH26263" string in the
      rendered HTML of `/`, `/login`, or the portal shell.
- [ ] **Not verified visually** — same standing limitation as the previous
      UI slice: no browser-automation tool is available in this session.
      Specifically worth checking by eye: hero text legibility as the shader
      cycles through its white phase, the mobile hamburger menu's animation
      and tap targets, and the sticky nav's frosted transition while
      scrolling past a section boundary.

## Visual UI overhaul (28 October 2026, superseded above)

User-directed redesign, cross-cutting rather than tied to one phase. New
dependency: `framer-motion` (pinned `14.7.1`).

- [x] **Landing page.** `/` is a real page now (`features/landing/home.tsx`),
      not a redirect to `/login`. Bold two-tone gradient-text headline, a
      feature grid of six cards describing what the prototype actually does
      (immutable records, local-only APAAR format checks, evidence-linked
      findings, explicit activation, simulated verification, role-scoped
      dashboards — all drawn from existing docs/behavior, nothing invented),
      and a footer repeating the synthetic-data disclaimer. Framer Motion
      fades/slides the hero in on load and staggers the feature cards in as
      they scroll into view (`whileInView`, animates once).
- [x] **User-supplied WebGL background**, adapted into `components/
      tricolor-canvas.tsx` (the shader logic is unchanged from the provided
      file, just moved into a React-managed canvas with resize/cleanup and a
      `prefers-reduced-motion` opt-out, where it falls back to a static CSS
      gradient instead of trying to render WebGL at all). Sits behind the
      hero only, with a frosted-glass panel over it for the headline/copy so
      the colorful background never fights with text legibility.
- [x] **Sign-in moved into the navbar.** New `components/public-nav.tsx`
      renders on both `/` and `/login` via a new `app/(public)/` route group
      (mirrors the existing `(portal)` group pattern; URLs are unchanged). A
      "Sign in" button opens an animated dropdown (grouped: institution
      admin accounts vs. AICTE review accounts) that links to
      `/login?alias=<alias>`; the login page now reads that query param to
      preselect the account, so the full sign-in action is still one click
      from the navbar. The demo account list was extracted to
      `features/auth/accounts.ts` so the dropdown and the login form share
      one source of truth instead of duplicating it.
- [x] **Dashboard analytics.** Added `StatusDonut` (`features/dashboards/
      components.tsx`) — an animated SVG donut chart of current records by
      enrollment status — wired into both the institution dashboard and the
      AICTE dashboard, next to the existing `CategoryBars` bar chart (which
      now animates its bar width in with Framer Motion instead of a static
      CSS width). Both charts are driven entirely by the same real API data
      already being fetched; no new numbers or endpoints were invented, and
      the existing "no current declaration is not zero" distinctions are
      preserved (the donut simply doesn't render when there's nothing to
      show, same as the bar chart's existing empty state).
- [x] Fixed a real, unrelated-looking bug found while wiring this up:
      `CategoryBars` previously set its bar width via a `--bar-width` CSS
      custom property that nothing actually read correctly on rebuild
      (dead code once Framer Motion took over animating `width` directly) —
      removed instead of left as confusing dead CSS.
- [x] Lint, typecheck and production build all re-verified clean after every
      step; all pages (`/`, `/login`, `/login?alias=...`, `/cases`, `/aicte`,
      `/institution`) smoke-checked over HTTP (200, and landing page HTML
      confirmed to contain the new headline/nav markup).
- [ ] **Not verified visually.** As before, no browser-automation tool is
      available in this session, so none of this has actually been *seen*
      rendering — the shader, the dropdown animation, the donut chart colors,
      and overall readability all need a human look at
      `http://localhost:3100` before considering this done. In particular:
      check the frosted-glass hero card is legible against the shader in
      both light content and on a small/mobile viewport, and that the
      sign-in dropdown doesn't clip off-screen on narrow widths.

## Finish Phase 1 — Step 5F verification

Latest full local verification (28 October 2026), run end-to-end from a fresh
clone with Docker PostgreSQL, Python 3.13 venv and `npm install`:

| Check                            | Result                                                                 |
| --------------------------------- | ----------------------------------------------------------------------- |
| Backend ruff/format/mypy/pip check | All pass                                                                |
| Backend pytest, no test DB        | 63 passed, 188 skipped                                                  |
| Backend pytest, dedicated test DB | **251 passed**, 0 skipped, 0 failed                                     |
| Alembic upgrade/current           | Clean; head is `0004_snapshot_review_activation`                       |
| pip-audit                         | 0 vulnerabilities in project dependencies (only `pip` itself flagged)  |
| Frontend lint/typecheck/build      | All pass                                                                |
| Frontend format:check / api:check  | Pass (earlier apparent diffs were a Windows CRLF checkout artifact, not real drift) |
| Automated browser/e2e tests        | Removed; no longer applicable                                          |

Remaining work for Step 5F:

- [ ] Decide on and, if desired, implement a replacement manual (or future
      automated) UI test plan now that Playwright coverage is gone. At minimum,
      manually re-verify the previously-automated flows before each release:
      sign-in/role routing, upload → validation → review → activation →
      dashboard, history pagination/filters, expiry/account-switch isolation,
      and desktop/mobile layout.
- [ ] Complete a manual screen-reader and keyboard accessibility audit, including
      focus management, dialogs, mobile navigation and error announcements —
      previously partly covered by automated axe checks, now fully manual.
- [x] Firefox login bug fixed: `.account-monogram`, `.account-copy` and
      `.radio-indicator` (`apps/web/src/app/globals.css`) were in normal flow
      directly over the visually-hidden radio input they label
      (`.account-option input`), and Firefox's hit-testing routed clicks to
      those decorative spans instead of the input, blocking sign-in via click
      for some demo accounts. Added `pointer-events: none` to all three so
      clicks always fall through to the label/input, which is the standard
      fix for this "visually-hidden input + custom visual siblings" pattern.
      Lint/typecheck/build re-verified clean after the change. Not re-verified
      in an actual Firefox render in this session — no browser-automation tool
      was available after Playwright's removal; worth a quick manual click
      check in Firefox before treating this as fully closed.
- [ ] Run a Python dependency vulnerability audit periodically; `pip-audit` is
      now confirmed available and was run clean against project dependencies.
- [ ] After the above, obtain approval to reconcile any remaining README/roadmap
      statements that still describe Step 5F as staged or reference removed
      Playwright tooling.

See `docs/08_TESTING_SECURITY.md` for the testing context.

## Phase 2 — Officer cases and simulated APAAR

Status: backend and frontend implemented and tested; contracts approved
28 October 2026 (officer-triggered verification, manually-opened cases,
advisory-only correction loop — no upload lock). Remaining gaps are an
assign-to-officer control and a human visual check of the new pages.

- [x] Add the `APAARProvider` interface and a deterministic simulated adapter.
      New `services/api/app/modules/verification/` feature module:
      `provider.py` (`APAARProvider` protocol, `MockAPAARProvider`, deterministic
      fixtures `900000000001`→`SIMULATED_MATCH`, `...002`→`SIMULATED_MISMATCH`,
      `...003`→`SOURCE_UNAVAILABLE`, anything else→`PENDING`), `models.py`
      (`apaar_verifications`, append-only via trigger, migration
      `0005_apaar_verification`), `services.py`, `schemas.py`, `routes.py`
      (`POST`/`GET /api/v1/records/{record_version_id}/apaar-verify`).
- [x] Preserve independent local-validation and identity-check statuses.
      `apaar_verifications` is its own table, independent of `validation_runs`/
      `validation_findings`; nothing here touches validation state.
- [x] Enforce consent, purpose, role permissions and audit provenance for checks.
      `purpose`/`consent_ref` are required request fields and persisted on the
      evidence row. Only `AICTE_OFFICER` may request a check; officer and the
      record's own `INSTITUTION_ADMIN` may read history; `AICTE_MANAGER` gets
      403 on both (matches the existing aggregate-only manager pattern). Every
      request/read is scoped so an institution admin can never see another
      institution's record (404, not 403, to avoid confirming existence).
      `APAAR_VERIFICATION_REQUESTED` audit event recorded on every check.
- [x] Clearly distinguish simulated match, mismatch, pending and source-unavailable
      results in API responses and the interface. Every response carries
      `adapter_type: "MOCK_V1"` and a fixed `provenance_label`
      ("SIMULATED — not an official government identity verification").
- [x] Tested: 9 new backend tests (`tests/test_verification.py`) covering all
      four fixture outcomes, officer-only write / admin-plus-officer read,
      cross-institution 404 isolation, manager 403 on both verbs, missing/short
      matching-key 422 with no row persisted, newest-first history ordering,
      and append-only immutability (`UPDATE` raises, trigger-enforced). Full
      backend suite re-run clean: **260 passed** with the dedicated test
      database (was 251 before this slice). Verified live over real HTTP too
      (not just the test client): uploaded a sample batch, requested a
      verification as `demo_officer`, got back `SIMULATED_MATCH` with correct
      evidence; confirmed `cedar_admin` gets 403 on request but 200 on reading
      their own institution's history.
  - Found and fixed one real bug during this slice: the `GET .../apaar-verify`
    history route initially never checked `require_verification_role` at all —
    `AICTE_MANAGER` could read verification evidence it shouldn't see. Caught
    by the manager-403 test, fixed in `scoped_record`, confirmed in both the
    test suite and live HTTP.
- [x] Build the officer queue, evidence-linked case creation, correction requests
      and immutable case timeline. New `services/api/app/modules/cases/` feature
      module: `review_cases` (mutable status/assignment), `case_records` (M:N,
      append-only) and `case_events` (append-only timeline) — migration
      `0006_officer_cases`. Routes: `POST`/`GET /api/v1/cases`,
      `GET /api/v1/cases/{id}`, `POST /api/v1/cases/{id}/actions`. Officer opens
      a case against one or more record versions (must all share one
      institution — 422 otherwise); legal status machine is
      `OPEN`/`UNDER_REVIEW` → `COMMENT`/`REQUEST_CORRECTION`/`ASSIGNED`/`RESOLVED`,
      `AWAITING_CORRECTION` → `COMMENT`/`ASSIGNED` only, `RESOLVED` →
      `COMMENT`/`CLOSED`, `CLOSED` terminal; institution admins may only
      `COMMENT`, everything else is officer-only; manager 403 on all four verbs.
- [x] Let institutions see outstanding requests and submit corrections as new
      immutable batches, preserving the original findings and submissions.
      Implemented as the advisory-only loop from the approved contract: a hook
      in `submissions/activation.py`'s `activate()` (`record_correction_received`
      in `cases/services.py`) auto-appends a system `CORRECTION_RECEIVED` case
      event and moves any `AWAITING_CORRECTION` case for that institution to
      `UNDER_REVIEW` whenever a new batch activates — in the same DB
      transaction as the activation, so it can't desync from it. The upload and
      activation endpoints themselves are completely unchanged; nothing about
      them blocks or even knows about open cases.
- [x] Test case permissions, institution isolation, state transitions, simulated
      provider failures and the complete correction loop. 8 new backend tests
      (`tests/test_cases.py`): officer-open/admin-denied, manager 403 on all
      four verbs, cross-institution case rejected at creation (422) and at read
      (404), unknown record id (404), admin-may-only-comment, illegal
      transitions (`CLOSED` directly from `OPEN` → 409, `ASSIGNED` without
      `assigned_to` → 422, no actions after `CLOSED`), and a full
      open → request-correction → reupload → auto-`CORRECTION_RECEIVED` →
      resolve loop confirming the reupload was never blocked. Full backend
      suite: **268 passed** with the dedicated test database (was 260 before
      this slice). Verified live over real HTTP too: opened a case as
      `demo_officer` against a real uploaded record, requested correction,
      confirmed `demo_manager` gets 403 on the list and `cedar_admin` gets 200
      reading their own case.
  - Found and fixed one real bug during this slice, caught by the correction-loop
    test: `case_events` ordered by `(created_at, id)`, but `id` is a random
    UUID, so two events timestamped in the same tick could sort in the wrong
    order — the test caught `CORRECTION_RECEIVED` sorting before the
    `REQUEST_CORRECTION` that caused it. Fixed by adding a DB-assigned
    monotonic `ordinal` (`BigInteger` + `Identity()`) to `case_events` and
    ordering by that instead.
- [x] Frontend UI for verification and cases. New `apps/web/src/features/cases/`
      (`queue.tsx`, `detail.tsx`, `record-verification.tsx`, `shared.ts`) and
      pages `/cases` (queue, scoped server-side by role same as the API) and
      `/cases/{id}` (linked records with a per-record "Request simulated APAAR
      verification" button and history, the append-only event timeline with
      color-coded entries, and action buttons filtered client-side to the
      legal transitions for the case's current status — backend remains the
      real enforcement). Added a "Cases" nav link and a `flag` icon. Added an
      "Open case for this finding" button on `POTENTIAL_CROSS_INSTITUTION_
      DUPLICATE` findings in the existing validation workspace (officer-only),
      which creates the case and navigates straight to its detail page.
      Institution-side correction visibility came for free from the same
      role-scoped `/cases` queue — no separate screen was needed.
  - UI polish pass: discovered and fixed a real pre-existing gap while
    styling the new "warning" badges — `.status-badge.warning` was used
    throughout the app (activation-blocking findings, stale assessments) but
    was **never actually defined** in `globals.css`, so every warning badge
    rendered with no background at all. Added it, benefiting the existing
    screens too, not just the new ones. Also added mobile alignment for the
    new status badge in list rows, left-border color-coding on timeline
    entries, and an `sr-only` heading per linked record for screen readers.
  - Extracted shared case status/event label/tone logic into `cases/shared.ts`
    to avoid duplicating it across the queue and detail components.
  - Lint, typecheck and production build all re-verified clean after every
    change in this slice.
  - Not yet done: an officer-facing "assign to" control (would need a
    directory of officer accounts, which doesn't exist in the UI yet, so
    `ASSIGNED` is deliberately left API-only for now); and I have not
    personally seen the pages render in a real browser — no browser-
    automation tool was available in this session, so this still needs a
    human visual check at `http://localhost:3100/cases`.

Acceptance: an officer can investigate a potential overlap, request correction and
review a new submission with the earlier evidence still available. Provider results
must carry `SIMULATED` provenance and must never imply government verification or
an automatic fraud determination. Met end-to-end, backend and frontend.

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
- An automated UI/e2e test suite (previously Playwright) is no longer present;
  reinstating one, or defining an alternative automated UI regression approach,
  is deferred future work.

## Recommended next action

Fix the known Firefox pointer-events bug on the login screen, decide on a manual
or future automated UI test plan now that Playwright is removed, and complete the
manual accessibility audit. Then review and approve the Phase 2 database, API,
permissions, case lifecycle and simulated-provider contracts before implementation.
Continue following the feature-based architecture, immutable history,
synthetic-data restrictions, workspace boundaries and prohibition on Git commands.

Sources: `README.md`, `docs/01_PRD.md`, `docs/02_ARCHITECTURE.md`,
`docs/05_VALIDATION_AND_ABC.md`, `docs/07_IMPLEMENTATION_PLAN.md` and
`docs/08_TESTING_SECURITY.md`.
