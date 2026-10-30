# PRAVYA — Live Demo Script (SIH26263 prototype)

**Audience:** presenter / demo operator. Every expected outcome below is ground
truth from `samples/demo/expected.json` — the same script the automated
end-to-end test (`tests/test_demo_e2e.py`) verifies.

> SIMULATED / DEMO DATA — fictional institutions and learners, synthetic
> 12-digit APAAR-like numbers only. Local validation is never government
> identity verification. Say this out loud at least once during the demo. 🙂

---

## 0. One-time setup (if servers are not already running)

```powershell
# from the repository root
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
cd services/api
& .venv/Scripts/python.exe -m alembic upgrade head
& .venv/Scripts/python.exe -m app.seed
& .venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-proxy-headers
# second terminal
cd apps/web
npm run dev          # requires apps/web/.env.local with NEXT_PUBLIC_DEMO_UI_ENABLED=true
```

Open **http://localhost:3000**. Reset instructions are at the end.

## The cast (7 demo accounts, one click each, no passwords)

| Account | Role | Acts |
|---|---|---|
| **Cedar Institute** | Institution admin | Acts 1–3, 5–6 |
| **Maple Institute** | Institution admin | Act 4 |
| **Willow Institute** | Institution admin | Act 7 |
| **Admissions Officer** | AICTE officer | Acts 8–10 |
| **Admissions Manager** | AICTE manager | Act 11 |
| **Admissions Officer 2** | AICTE officer | Act 10 (handoff) |
| **Credential Verifier** | Authorized verifier | Act 12 |

Seeded rules (DEMO values, version `DEMO-v1`): **REGULAR cap 3, every other
seat category cap 1**. Academic year **2026-27**, programme **DEMO-COMP**.

---

## Act 1 — Clean upload and activation (Cedar Institute)

1. Sign in as **Cedar Institute** → Dashboard.
2. **Upload candidate** → choose `samples/demo/01_cedar_valid.csv`
   (6 rows), programme DEMO-COMP, year 2026-27 → **Upload candidate**.
3. Expected: success with no warnings; batch appears as **Candidate**.
4. Open the batch from **Submissions** → **Run Validation**.
5. Expected: run completes with **zero findings**, 6/6 VALID.
6. **Create review receipt** → review state **READY** →
   **Activate this snapshot**.
7. Expected: batch becomes **Current**; dashboard counts 6 declared / 6 active.

**Talking point:** rows are stored as immutable versions; nothing is ever
edited in place. Corrections arrive as new batches.

## Act 2 — APAAR format findings (still Cedar)

1. Upload `samples/demo/02_cedar_apaar_issues.csv` (5 rows) → **Run Validation**.
2. Expected findings (evidence-linked, each opens the affected row):
   - `REQUIRED_FIELD_MISSING` on field `apaar_id` (row 3) — WARNING
   - `INVALID_APAAR_FORMAT` rows 4, 5, 6 — WARNING (wrong length / non-digits)
3. Click **Download masked feedback CSV** — open it: APAAR values are masked
   (`*****100101` style), each row carries its status and rule code.

**Talking point:** format checks are local and configurable — the platform
never claims an APAAR is *verified* against a government system.

## Act 3 — Duplicates block activation (still Cedar)

1. Upload `samples/demo/03_cedar_duplicates.csv` (5 rows) → **Run Validation**.
2. Expected findings:
   - `DUPLICATE_COLLEGE_STUDENT_ID` rows 3–4 — **ERROR,
     ACTIVATION_BLOCKING**
   - `DUPLICATE_IN_BATCH` rows 5–6 — WARNING (same APAAR twice; nothing is
     merged or deleted)
3. **Create review receipt** → review state **BLOCKED** (structural blockers).

**Talking point:** the platform refuses to activate an ambiguous snapshot —
"potential duplicate" is a review lead, not a verdict.

## Act 4 — Cross-institution potential duplicate (Maple, then Cedar)

1. Sign out → **Maple Institute** → upload
   `samples/demo/04_maple_peer.csv` (3 rows) → **Run Validation** →
   **Create review receipt** → **Activate this snapshot**.
2. Sign out → **Cedar Institute** → upload
   `samples/demo/05_cedar_intake_excess_and_peer_match.csv` (4 rows) →
   **Run Validation**.
3. Expected findings:
   - `INTAKE_EXCEEDED` — calculation literally reads
     `ACTIVE 4 > approved 3 (rule DEMO-v1, REGULAR) = excess 1`
   - `POTENTIAL_CROSS_INSTITUTION_DUPLICATE` — context
     `CURRENT_ACTIVE` (a transfer or withdrawal may explain it; review, not
     delete).

**Talking point:** categories are never pooled into one cap; a peer match is
potential by design.

## Act 5 — Missing population vs declaration (still Cedar)

1. On the Cedar dashboard, find **Declared totals** and record a declaration of
   **6** for 2026-27 (synthetic basis text is fine).
2. Upload `samples/demo/06_cedar_missing_population.csv` (4 rows) →
   **Run Validation** → open **Intake assessment**.
3. Expected: `MISSING_POPULATION_DISCREPANCY` — candidate records 4 < declared
   6, shortfall 2. The wording says a shortfall is a comparison with a DEMO
   declaration, **not proof records are missing**.

## Act 6 — Correction and explicit omission acknowledgment (still Cedar)

1. Upload `samples/demo/07_cedar_corrected.csv` (6 rows) → **Run Validation** →
   **Create review receipt**.
2. Expected: the review lists **omitted records** from the earlier snapshot and
   activation requires ticking the explicit **omission acknowledgment**.
3. **Activate this snapshot.**
4. Dashboard now reads: **6 declared / 5 active** (REGULAR 3, SUPERNUMERARY 1,
   NRI 1), with 3 pending candidates kept as history.
5. Upload the same file again — the platform warns `DUPLICATE_UPLOAD` and a
   repeat submit with the same Idempotency-Key replays the original receipt.

## Act 7 — XLSX + a quiet institution (Willow)

1. Sign out → **Willow Institute** → upload
   `samples/demo/08_willow_valid.csv` (rename to `.xlsx` if you want to show
   Excel support; the same file is the generated XLSX in the scripted demo) →
   **Run Validation** → **Create review receipt** → **Activate this snapshot**.
2. Willow's dashboard shows a small clean snapshot; Cedar's dashboard, by
   contrast, shows the full story.

## Act 8 — Officer: registry and simulated verification

1. Sign out → **Admissions Officer** (OFF).
2. **Student registry** — search a Cedar student id. Expected: **masked APAAR**
   (`*****100001` style), snapshot state badges, validation status.
3. **APAAR verification** → pick any Cedar record → purpose `demo`,
   consent ref `demo-consent` → request.
   Expected: status `PENDING` (the simulated provider returns
   `SIMULATED_MATCH` for `900000000001`, `SIMULATED_MISMATCH` for
   `900000000002`, `SOURCE_UNAVAILABLE` for `900000000003`,
   `SOURCE_TIMEOUT` for `900000000004`, `PENDING` for everything else).
   To show the special statuses, upload a 2-row CSV for Cedar containing
   `900000000001` and `900000000002` first, then verify those records.
4. Every result carries the **SIMULATED / DEMO DATA** provenance label —
   point at it.

**Talking point:** `SOURCE_UNAVAILABLE` is not a mismatch; retry caps apply
per record per day.

## Act 9 — Officer: case from a finding

1. From the flagged finding (Act 4's cross-institution duplicate is the best
   story) click **Open case for this finding** → summary text → open.
2. Assign it to **Admissions Officer 2**, **Start review**, then
   **Request correction** (institution gets a notification).
3. Sign out → **Cedar Institute** → **Notifications** → open the case →
   add a **COMMENT** / respond.
4. Sign out → back as **Admissions Officer** (or Officer 2) → mark
   **Resolved** (reason) → **Closed**.
5. The case timeline now shows the full chain:
   `OPENED → ASSIGNED → START_REVIEW → REQUEST_CORRECTION →
   CORRECTION_RECEIVED → COMMENT → START_REVIEW → RESOLVED → CLOSED`.

## Act 10 — Officer: audit explorer

1. **Audit explorer** — filter by action (`CASE_OPENED`, `REPORT_EXPORTED`,…)
   or institution.
2. Expected: every step so far has an append-only event with actor and
   timestamp, no APAAR values in any payload (click one open).

## Act 11 — Manager: oversight without actions

1. Sign out → **Admissions Manager** (MG).
2. **Analytics** — enrolment trends, submission completeness, intake
   utilisation (Cedar REGULAR shows 3/3 with `exceeded: false` after the
   correction; explain per-category rows).
3. **Reports** — export *Enrolment summary* as CSV/XLSX/PDF; numbers match the
   dashboards because reports reuse the same service functions.
4. **Institutions** → Cedar profile — integrity signals expected on record:
   `CMP_INTAKE_EXCEEDED`, `CMP_MISSING_POPULATION`,
   `CMP_UNUSUAL_SNAPSHOT_CHANGE`, `DQ_MISSING_FIELDS`,
   `IDU_CROSS_INSTITUTION_DUPLICATE` (plus `CMP_OVERDUE_CASES` if a case went
   overdue). Scores form MEDIUM/HIGH bands; officers can record decisions
   (dismiss/false-positive) — managers see them.

**Talking point:** the manager role sees aggregates only — no case actions,
no record-level tools. Segregation of duties is enforced server-side.

## Act 12 — Verifier: signed demo credentials

1. Sign out → **Cedar Institute** → **Credentials** → pick an **ACTIVE**
   record in the current snapshot → **Issue**.
2. Copy the token (JWT-lookalike, Ed25519-signed).
3. Sign out → **Credential Verifier** (VF) → **Verify credential** → paste →
   Expected outcome `VALID` with permitted claims
   (institution, programme, year, category, status, issued/expires).
4. Show **Verification log**; back as Cedar you can **Revoke** the credential
   and verify again — outcome becomes `REVOKED`.

**Talking point:** verification checks a DEMO signature only — this is the
credential pipeline shape, not a government integration.

---

## Closing slide (permitted claims — say exactly this)

- `APPROVED` means the record passed **configured internal validation**; it is
  **not** official APAAR verification.
- Validation status, APAAR verification status and ABC reconciliation are
  independent statuses.
- Missing/invalid APAAR, duplicates and intake exceptions become
  **evidence-linked findings**, never silent discards.
- Cross-institution duplicates are **potential** — transfer/withdrawal may
  explain them; only officers make regulatory decisions, and rule-based
  signals are **not fraud determinations**.
- All data is synthetic; providers are simulated and permanently labeled
  `SIMULATED / DEMO DATA`.

## Reset the demo state (fresh start)

```powershell
docker compose --env-file .env -f infra/docker-compose.yml down -v
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
cd services/api
& .venv/Scripts/python.exe -m alembic upgrade head
& .venv/Scripts/python.exe -m app.seed
# restart the API server
```

⚠️ This wipes the local demo database (demo data only). Tests use a separate
database and are unaffected.
