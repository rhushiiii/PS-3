# AGENTS.md — Repository Instructions for Codex

## Mission
Build the SIH26263 **prototype**: institutions upload student-level admission data; the platform standardizes it, validates APAAR format and admission rules, detects potential duplicate records, preserves audit history, and gives AICTE officers actionable, evidence-linked review tools. Optional ABC credit reconciliation is simulated unless official access is authorized.

## Required reading before changes
Read `README.md`, `docs/01_PRD.md`, `docs/02_ARCHITECTURE.md`, `docs/05_VALIDATION_AND_ABC.md`, and the relevant contract/test docs. Prefer these documents to guesses; surface contradictions and record decisions in `docs/09_DECISIONS_AND_ASSUMPTIONS.md`.

## Implementation constraints
- Web: Next.js App Router, TypeScript strict, Tailwind CSS. Accessible, responsive UI; server/client components deliberately separated.
- API: FastAPI + Pydantic v2, SQLAlchemy 2, Alembic migrations, Python type hints, pytest.
- Storage: PostgreSQL. Do not replace it with SQLite in the application; unit tests may use mocks/test PostgreSQL.
- Local development: Docker Compose for PostgreSQL; `.env.example`, never commit real `.env` or credentials.
- API must publish OpenAPI; the frontend gets types from schemas or a generated typed client where practical.
- Run formatter/linter/type checker/tests for touched code. Report what ran and failures.
- Small, reviewable increments. Implement one complete vertical slice per task; avoid broad rewrites.

## Government integration / claims — hard rules
- NEVER claim that syntactically valid APAAR is verified against the government system.
- Never invent access to APAAR, ABC, DigiLocker, API Setu, or AICTE's restricted databases.
- External providers use interfaces (`APAARProvider`, `ABCCreditProvider`) with deterministic simulated adapters for the prototype.
- Simulated results MUST carry `source_type=SIMULATED`, a visible `SIMULATED / DEMO DATA` label in UI, and testable provenance. Never mark as official verified.
- Do not hard-code a supposed official APAAR checksum; keep format checks configurable. No unauthorized scraping or authentication bypass.
- Do not assume grade points, SGPA, CGPA or academic credits are interchangeable.
- Optional ABC lookups failing must not block core enrolment checks.
- AI-generated or rules-generated anomaly flags are NOT fraud determinations. Only officers make regulatory decisions.

## Data and security
- Use **only synthetic records** and fake institutions in seed/demo data. Never create or include real student PII, real APAAR numbers, or publicly usable identities.
- Treat APAAR as sensitive identifier: avoid logs and URLs; mask in UI except authorized detail views; avoid storing raw values in audit event payloads.
- Enforce server-side role and institution scoping on every endpoint, not only hiding frontend controls.
- Minimum roles: `INSTITUTION_ADMIN`, `AICTE_OFFICER`, `AICTE_MANAGER`, `AUTHORIZED_VERIFIER` (last role may be phase 2).
- For MVP, seeded demo accounts are acceptable only behind a clearly labeled `DEMO_AUTH` mode. No claim of production-grade auth; keep passwords hashed if passwords are used.
- Use explicit consent/purpose fields for verification; default deny if absent. Track action audit events with timestamp and actor.
- Store record submissions as immutable versions. Never silently overwrite prior batch data.

## Core business invariants
1. `APPROVED` means record passed configured internal validation, **not** official APAAR verification.
2. Independent statuses: `validation_status` and `apaar_verification_status` and `abc_reconciliation_status`.
3. Missing/invalid APAAR, potential duplicates, seat-category/intake exceptions create evidence-linked findings with rule IDs and severity, not silent discards.
4. Duplicate across institutions is **potential**, since transfer/withdrawal may explain it; allow review.
5. Intake comparisons use `academic_year`, `programme`, `seat_category`, and configured approved capacity; do not sum all seat categories into a single cap blindly.
6. No invented official rule values. Seed rules are illustrative and explicitly marked demo.
7. Distinguish `SOURCE_UNAVAILABLE`, `PENDING`, `MATCH`, and `MISMATCH` for verification results.

## Engineering workflow for each task
1. State files to be created/changed and how acceptance criteria will be met.
2. Implement the smallest functional scope with database migration and tests where relevant.
3. Run commands; fix failures where possible.
4. State results, known limitations, security implications, and follow-up tasks.
5. Update docs for contract or behavior changes; do not modify the source-derived requirements to rationalize implementation.

## Definition of done for a feature
Working happy path, failure path, server authorization, deterministic seeded example, tests, UI empty/loading/error states where applicable, and documented run instructions. A visual-only mock is **not** a complete feature.

## First Codex task
Implement `Phase 0 + Phase 1` in `docs/07_IMPLEMENTATION_PLAN.md` only: monorepo scaffold, Docker PostgreSQL, FastAPI health, Next.js shell, migration, seed data, secure CSV ingest and validation results. Run tests and explain remaining work. Do not build ABC provider or machine learning in the first sprint.

## Additional project ground rules

These user-approved rules govern all future work. Where they conflict with
earlier repository guidance or proposed layouts, these rules take precedence.

### Git and workspace boundaries
- Do not execute any Git commands or create commits. The user handles all
  version control.
- Work strictly within the current project directory and its subdirectories.
  Do not read, create, modify, or delete files outside this directory without
  explicit user permission.

### Approval and authoritative context
- Before changing the architecture, API routes, database design, technology
  stack, or established conventions, explain the proposed change and obtain
  explicit user approval.
- Treat existing context documents as authoritative. For any deviation,
  including minor deviations, explain what would change and why, invite the
  user's suggestions, and obtain approval before proceeding.
- Never silently modify documentation. Present proposed documentation edits
  and obtain approval before applying them.
- Before significant implementation work, briefly explain the plan.
- When multiple valid approaches involve meaningful trade-offs, discuss them
  with the user and recommend an approach before proceeding.
- Never silently make assumptions that conflict with agreed specifications.

### Feature-based modular architecture
- Use a clean, minimal, feature-based backend structure. Each feature owns its
  routes, services, business logic, SQLAlchemy models, Pydantic schemas, and
  database-related definitions as applicable.
- Do not organize the entire backend into global technical-layer folders.
  This supersedes the proposed global backend folder layout in
  docs/02_ARCHITECTURE.md.
- Keep database connection/session configuration and Alembic migration
  infrastructure centralized where necessary.
- Do not collect all feature models or schemas in global folders.
- Keep feature modules cohesive; do not create unnecessary files or layers.

### Reuse, simplicity, and readability
- Follow DRY principles. Extract repeated cross-cutting logic into shared
  utilities, dependencies, decorators, or middleware where appropriate.
- Use middleware for genuine request-wide concerns, such as logging,
  authentication context, and request IDs. Keep feature business logic within
  its feature.
- Prefer simple, maintainable solutions. Avoid unnecessary abstractions,
  premature optimization, excessive files, and overengineering.
- Keep code readable, properly typed, and consistently named.

### Teach while developing
- Explain bugs, technical discrepancies, architectural trade-offs, and
  unfamiliar concepts clearly, using examples where helpful.
- Describe the available solutions and recommend the best approach with
  reasons before making consequential decisions.
- Explain meaningful fixes rather than applying them silently.
