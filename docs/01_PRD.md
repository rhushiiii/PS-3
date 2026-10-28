# Product Requirements Document — SIH26263

## 1. Product overview
**Working name:** AICTE Student Intelligence Platform (prototype name, not an official government product).  
**Problem owner:** AICTE Regulation Bureau.  
**Statement:** Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions.

### Source-grounded problem
Institutional reports vary from student-level detail to aggregate counts, preventing reliable individual-level monitoring and authenticity checks. AICTE wants secure, interoperable institution submission/update of APAAR-linked student records, centralized validation, monitoring, and controlled downstream verification.

### Product objective
Make every admission data submission traceable, validate records against reliable rules, surface exceptions, and support evidence-driven action by authorized officials.

## 2. Personas and jobs to be done
| User | Needs |
|---|---|
| Institution administrator | Upload/upsert institution-scoped student records, understand errors, correct, track submission status |
| AICTE officer | Compare colleges, investigate duplicates and possible intake excesses, request clarifications |
| AICTE manager | Monitor region/programme/year trends, stale submissions, ageing of review cases |
| Authorized verifier | Verify only permitted fields for a consented purpose (later phase) |

## 3. Scope and traceability
**R = present in supplied SIH26263 source; D = proposed solution design; O = optional extension.**

| ID | Requirement | Class | Priority |
|---|---|---|---|
| R01 | Institution-facing secure upload/update via UI/APIs | R | P0 |
| R02 | APAAR identifier on student-level records | R | P0 |
| R03 | Approved intake, actual enrolment, supernumerary/NRI/OCI/Foreign National categories | R | P0 |
| R04 | Detect duplicates, missing/invalid APAAR, intake excess, inconsistencies, cross-institution duplicates | R | P0 |
| R05 | Institution + AICTE dashboards | R | P0 |
| R06 | Controlled verification with consent, access roles and audit trails | R | P1 |
| R07 | Regulatory/accreditation reporting; certificate ID display support | R | P2 |
| D01 | Versioned batch submissions and correction loops | D | P0 |
| D02 | Evidence-linked anomaly/case work queue | D | P1 |
| D03 | Missing-population reconciliation against declared totals | D | P1 |
| D04 | Rule-by-academic-year and seat category | D | P0 |
| D05 | Change/deletion anomaly detection | D | P2 |
| O01 | Authorized/simulated ABC credit record reconciliation | O | P2 |
| O02 | Subject-level grade points/SGPA check only with valid institutional grading scheme | O | Deferred |

## 4. MVP — must work end-to-end
1. Admin chooses one of three seeded synthetic institutions, then uploads CSV records for a specific academic year/programme.
2. System preserves batch metadata (actor, source, hash, upload timestamp) and row-level original/normalized content.
3. Deterministic validation flags required fields, APAAR structure, within-batch duplicates, cross-institution potential duplicates, incompatible statuses, and category-aware intake exceedance.
4. Institution sees results and can correct/resubmit as a new version.
5. Officer dashboard summarizes submissions, counts, flags, and evidence; officer may open a case and request correction.
6. Every mutation is auditable; data reads are institution-scoped.
7. APAAR identity status is `NOT_CHECKED` or a **simulated** independent result; never imply real government validation.

## 5. Primary user stories
- As a college admin, I upload a CSV, see per-row errors and can download a corrective feedback CSV.
- As a college admin, I can see previous submission versions and outstanding officer requests.
- As an AICTE officer, I can view flagged records with evidence, involved institutions and year-specific rules.
- As an officer, I can mark a duplicate signal `UNDER_REVIEW`, `EXPLAINED_TRANSFER`, or `NEEDS_CORRECTION` without deleting source records.
- As a manager, I can filter enrolment totals and active cases by year, programme, region, institution and category.
- As an authorized verifier, I get a minimal response only when role, purpose and consent allow it (later).

## 6. Non-goals for MVP
No production government API access, actual ABC wallet management or credit transfer, legal determination of misconduct, biometric/Aadhaar collection, automatic approval or rejection of institutions, real student data, production SSO, or large-scale ML training.

## 7. Demo acceptance scenarios
- Upload 6 synthetic students including invalid APAAR, missing APAAR, duplicate ID, and category-specific intake excess; UI shows distinct findings and row references.
- Seed another institution with an overlapping APAAR; officer sees *potential* duplicate, not automatic fraud.
- Officer requests correction; college resubmits and old version remains visible.
- Toggle simulated APAAR provider to `MATCH`/`MISMATCH`/`SOURCE_UNAVAILABLE`; status and evidence update without confusing format/identity states.
- Optional later: ABC simulated credits match/mismatch and non-blocking unavailable state.

## 8. Nonfunctional goals (proposed, not official targets)
- MVP demo: 1,000 CSV rows processed under 10 seconds on ordinary laptop **as a target, not a guarantee**.
- All APIs scoped by role/tenant and tested for isolation.
- Fully reproducible local startup, deterministic seed data, and responsive desktop/mobile views.
- Logs redact identifiers; audits preserve actions without raw student PII.

## 9. Success metrics
Upload pass rate, valid vs flagged rows, time to review, unresolved cases by age, duplicate alert precision on seeded fixtures, false positives from allowed seat categories, and share of external statuses correctly labeled simulated/pending.

## 10. Required authoritative checks before deployment
Review current AICTE intake/APH rules, APAAR integration documentation, ABC access terms, legal basis for processing, consent model, and official API availability. The provided PDF is a structured paraphrase, not binding technical/API documentation.
