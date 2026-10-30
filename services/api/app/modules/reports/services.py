"""Report builders.

Every total comes from the same analytics service functions the dashboards use, so
a report and its dashboard cannot disagree for the same filters. Reports that have
no analytics counterpart (validation findings, verification activity) total their
own data rows.
"""

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.http import APIError
from app.core.query import latest_per_key
from app.modules.analytics import services as analytics
from app.modules.analytics.schemas import AnalyticsMeta, TrendRow, UtilisationRow
from app.modules.audit.services import record_action, redact
from app.modules.auth.dependencies import require_roles
from app.modules.auth.models import Role, User
from app.modules.cases.models import CLOSED_STATUSES, ReviewCase
from app.modules.cases.services import case_flags
from app.modules.credentials.models import AdmissionCredential, CredentialVerification
from app.modules.institutions.models import Institution
from app.modules.institutions.services import forced_institution_id
from app.modules.intake.services import utilisation_pct
from app.modules.reports.schemas import (
    Cell,
    ReportDocument,
    ReportFormat,
    ReportKind,
    ReportTable,
)
from app.modules.submissions.models import ProcessingStatus, SubmissionBatch
from app.modules.validation.models import ValidationFinding
from app.modules.validation.rules import CATEGORIES
from app.modules.validation.services import selected_runs_bulk
from app.modules.verification.models import ApaarVerification

AGGREGATE_ROLES = {Role.AICTE_OFFICER, Role.AICTE_MANAGER, Role.INSTITUTION_ADMIN}
KIND_ROLES: dict[str, set[Role]] = {
    "enrolment-summary": AGGREGATE_ROLES,
    "intake-utilisation": AGGREGATE_ROLES,
    "submission-completeness": AGGREGATE_ROLES,
    "resolution-times": AGGREGATE_ROLES,
    "validation-findings": AGGREGATE_ROLES,
    # Case work is an officer function; managers see aggregates only.
    "open-cases": {Role.AICTE_OFFICER, Role.INSTITUTION_ADMIN},
    "verification-activity": {Role.AICTE_OFFICER},
}
YEAR_FILTERS = ("academic_year", "institution_id", "region", "programme_code")
CASE_FILTERS = ("institution_id", "region", "priority", "severity")
FILTER_NAMES: dict[str, tuple[str, ...]] = {
    "enrolment-summary": YEAR_FILTERS,
    "intake-utilisation": YEAR_FILTERS,
    "submission-completeness": YEAR_FILTERS,
    "validation-findings": YEAR_FILTERS,
    "resolution-times": CASE_FILTERS,
    "open-cases": CASE_FILTERS,
    "verification-activity": ("institution_id", "region"),
}
NO_YEAR = "Not applicable: this report is not scoped by academic year"
UNATTRIBUTED = "(not attributable to an institution)"


@dataclass(frozen=True)
class ReportParams:
    filters: analytics.Filters
    priority: str | None = None
    severity: str | None = None

    def applied(self, kind: str) -> dict[str, str]:
        values: dict[str, object] = {
            **vars(self.filters),
            "priority": self.priority,
            "severity": self.severity,
        }
        return {
            name: str(values[name])
            for name in FILTER_NAMES[kind]
            if values[name] is not None
        }


def authorize(user: User, kind: str, params: ReportParams) -> ReportParams:
    """Role check, and institution forcing for institution admins."""
    require_roles(user, KIND_ROLES[kind])
    if user.role != Role.INSTITUTION_ADMIN:
        return params
    forced = forced_institution_id(user, params.filters.institution_id)
    return ReportParams(
        analytics.Filters(
            params.filters.academic_year,
            forced,
            params.filters.region,
            params.filters.programme_code,
        ),
        params.priority,
        params.severity,
    )


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def coverage_line(meta: AnalyticsMeta) -> str:
    c = meta.coverage
    return (
        f"{c.institutions_with_current_snapshot} of {c.institutions_total} "
        f"institutions and {c.programmes_with_current_snapshot} of "
        f"{c.programmes_total} programmes have a current activated snapshot. "
        "Programmes without one are unknown, not zero."
    )


def year_context(filters: analytics.Filters) -> str:
    if filters.academic_year:
        return f"Academic year {filters.academic_year}"
    return "All academic years on record (one row per year where applicable)"


def table(
    title: str, columns: list[str], rows: Sequence[Sequence[Cell]]
) -> ReportTable:
    return ReportTable(title=title, columns=columns, rows=[list(r) for r in rows])


def document(
    kind: ReportKind,
    title: str,
    user: User,
    now: datetime,
    params: ReportParams,
    context: str,
    coverage: str,
    totals: ReportTable,
    data: ReportTable,
) -> ReportDocument:
    return ReportDocument(
        kind=kind,
        title=title,
        generated_at=now,
        generated_by=f"{user.role.value} ({user.demo_alias or 'UNNAMED_USER'})",
        filters=params.applied(kind),
        academic_year_context=context,
        coverage=coverage,
        totals=totals,
        data=data,
    )


# ------------------------------------------------------------------ analytics-based


def enrolment_summary(
    session: Session, user: User, params: ReportParams, now: datetime
) -> ReportDocument:
    f = params.filters
    meta, programme_rows = analytics.enrolment_trends(session, f, "programme", now)
    _, year_rows = analytics.enrolment_trends(session, f, "academic_year", now)
    category_columns = [f"active_{c}" for c in CATEGORIES]
    counts = ["programmes_total", "programmes_with_current_snapshot"]
    values = ["declared_records", "active_records"]
    tail = [*category_columns, "unclassified_active_records"]

    def measures(row: TrendRow) -> list[Cell]:
        by_category: list[Cell] = [
            row.categories[c].active_records if row.categories is not None else None
            for c in CATEGORIES
        ]
        return [
            row.programmes_total,
            row.programmes_with_current_snapshot,
            row.declared_records,
            row.active_records,
            *by_category,
            row.unclassified_active_records,
        ]

    return document(
        "enrolment-summary",
        "Enrolment summary (declared rows in current activated snapshots)",
        user,
        now,
        params,
        year_context(f),
        coverage_line(meta),
        table(
            "Totals by academic year",
            ["academic_year", "status", *counts, *values, *tail],
            [[r.academic_year, r.status, *measures(r)] for r in year_rows],
        ),
        table(
            "Programmes",
            [
                "academic_year",
                "institution",
                "region",
                "programme_code",
                "status",
                *counts,
                *values,
                *tail,
            ],
            [
                [
                    r.academic_year,
                    r.institution_name,
                    r.region,
                    r.programme_code,
                    r.status,
                    *measures(r),
                ]
                for r in programme_rows
            ],
        ),
    )


def intake_utilisation(
    session: Session,
    user: User,
    params: ReportParams,
    settings: Settings,
    now: datetime,
) -> ReportDocument:
    meta, rows = analytics.intake_utilisation(session, params.filters, settings, now)
    # Seat categories are never pooled: one total per (academic year, category),
    # over rows whose ACTIVE count is known (a missing snapshot is unknown, not 0).
    groups: dict[tuple[str, str], list[UtilisationRow]] = defaultdict(list)
    for row in rows:
        groups[(row.academic_year, row.category)].append(row)
    totals_rows: list[list[Cell]] = []
    for (year, category), members in sorted(groups.items()):
        known = [r for r in members if r.status == "OK"]
        approved = sum(r.approved_seats or 0 for r in known) if known else None
        active = sum(r.current_active or 0 for r in known) if known else None
        totals_rows.append(
            [
                year,
                category,
                len(members),
                len(known),
                approved,
                active,
                sum(1 for r in known if r.exceeded) if known else None,
                utilisation_pct(active, approved),
            ]
        )
    return document(
        "intake-utilisation",
        "Intake utilisation by seat category",
        user,
        now,
        params,
        year_context(params.filters),
        coverage_line(meta)
        + f" Rule version {settings.validation_intake_rule_version} (DEMO values). "
        "Seat categories are reported separately and never pooled.",
        table(
            "Totals by academic year and seat category (rows with known counts)",
            [
                "academic_year",
                "category",
                "rows_total",
                "rows_with_known_counts",
                "approved_seats",
                "current_active",
                "rows_exceeded",
                "utilisation_pct",
            ],
            totals_rows,
        ),
        table(
            "Programme-year-category rows",
            [
                "academic_year",
                "institution",
                "programme_code",
                "category",
                "status",
                "approved_seats",
                "rule_version",
                "current_active",
                "utilisation_pct",
                "remaining_capacity",
                "exceeded",
                "excess",
            ],
            [
                [
                    r.academic_year,
                    r.institution_name,
                    r.programme_code,
                    r.category,
                    r.status,
                    r.approved_seats,
                    r.rule_version,
                    r.current_active,
                    r.utilisation_pct,
                    r.remaining_capacity,
                    r.exceeded,
                    r.excess,
                ]
                for r in rows
            ],
        ),
    )


def submission_completeness(
    session: Session,
    user: User,
    params: ReportParams,
    settings: Settings,
    now: datetime,
) -> ReportDocument:
    meta, rows, rollups = analytics.submission_completeness(
        session, params.filters, settings, now
    )
    rollup_columns = [
        "institutions_total",
        "programme_years_total",
        "with_current_snapshot",
        "stale",
        "with_declaration",
        "with_shortfall",
        "pending_candidates",
    ]
    rollup_rows: list[list[Cell]] = [
        [r.region, *(getattr(r, name) for name in rollup_columns)] for r in rollups
    ]
    if rollup_rows:
        rollup_rows.append(
            [
                "ALL REGIONS",
                *(sum(int(row[i + 1] or 0) for row in rollup_rows) for i in range(7)),
            ]
        )
    return document(
        "submission-completeness",
        "Submission completeness and freshness",
        user,
        now,
        params,
        year_context(params.filters),
        coverage_line(meta)
        + f" Stale means older than {settings.integrity_stale_days} days.",
        table("Totals by region", ["region", *rollup_columns], rollup_rows),
        table(
            "Programme-year rows",
            [
                "academic_year",
                "institution",
                "region",
                "programme_code",
                "freshness_status",
                "last_activated_at",
                "freshness_days",
                "stale",
                "has_declaration",
                "declared_total",
                "current_declared_records",
                "shortfall",
                "pending_candidate_count",
            ],
            [
                [
                    r.academic_year,
                    r.institution_name,
                    r.region,
                    r.programme_code,
                    r.freshness_status,
                    iso(r.last_activated_at),
                    r.freshness_days,
                    r.stale,
                    r.has_declaration,
                    r.declared_total,
                    r.current_declared_records,
                    r.shortfall,
                    r.pending_candidate_count,
                ]
                for r in rows
            ],
        ),
    )


def resolution_times(
    session: Session,
    user: User,
    params: ReportParams,
    settings: Settings,
    now: datetime,
) -> ReportDocument:
    f = params.filters
    report = analytics.case_performance(
        session,
        analytics.Filters(institution_id=f.institution_id, region=f.region),
        params.priority,
        params.severity,
        settings,
        now,
    )
    t = report.totals
    return document(
        "resolution-times",
        "Case resolution times (elapsed days from opening to resolution)",
        user,
        now,
        params,
        NO_YEAR,
        coverage_line(report.meta)
        + " Statistics cover resolved cases only; p90 is nearest-rank.",
        table(
            "Case totals",
            ["cases_total", "open", "overdue", "escalated"],
            [[t.all, t.open, t.overdue, t.escalated]],
        ),
        table(
            "Resolution time by priority",
            ["priority", "resolved_count", "mean_days", "median_days", "p90_days"],
            [
                [r.priority, r.resolved_count, r.mean_days, r.median_days, r.p90_days]
                for r in report.resolution
            ],
        ),
    )


def open_cases(
    session: Session,
    user: User,
    params: ReportParams,
    settings: Settings,
    now: datetime,
) -> ReportDocument:
    f = params.filters
    scope = analytics.Filters(institution_id=f.institution_id, region=f.region)
    report = analytics.case_performance(
        session, scope, params.priority, params.severity, settings, now
    )
    institutions = analytics.institutions_in_scope(session, scope)
    names = {i.id: i.name for i in institutions}
    open_ = [
        c
        for c in analytics.scoped_cases(
            session, institutions, params.priority, params.severity
        )
        if c.status not in CLOSED_STATUSES
    ]
    entries = [(c, case_flags(c, settings, now)) for c in open_]
    # Overdue first, then earliest due date; undated cases last. Stable tie-break.
    entries.sort(
        key=lambda e: (
            not e[1][0],
            e[0].due_at is None,
            e[0].due_at or now,
            str(e[0].id),
        )
    )
    t = report.totals
    return document(
        "open-cases",
        "Open and overdue review cases",
        user,
        now,
        params,
        NO_YEAR,
        f"{len(entries)} open cases across {len(institutions)} institutions in "
        "scope. Flags are rule-based review prompts, not findings of fraud.",
        table(
            "Open case totals",
            ["open", "overdue", "escalated"],
            [[t.open, t.overdue, t.escalated]],
        ),
        table(
            "Open cases (overdue first)",
            [
                "case_ref",
                "institution",
                "status",
                "priority",
                "severity",
                "due_at",
                "age_days",
                "overdue",
                "escalated",
            ],
            [
                [
                    case_ref(c),
                    names[c.institution_id],
                    c.status,
                    c.priority,
                    c.severity,
                    iso(c.due_at),
                    age,
                    overdue,
                    escalated,
                ]
                for c, (overdue, escalated, age) in entries
            ],
        ),
    )


def case_ref(case: ReviewCase) -> str:
    return str(case.id)[:8]


# ------------------------------------------------------------------ self-totalled


def validation_findings(
    session: Session, user: User, params: ReportParams, now: datetime
) -> ReportDocument:
    f = params.filters
    units = analytics.programme_units(session, f)
    by_programme = {p.id: (i, p) for i, p in units}
    batch_statement = latest_per_key(
        select(SubmissionBatch.id, SubmissionBatch.programme_id).where(
            SubmissionBatch.programme_id.in_(list(by_programme)),
            SubmissionBatch.status == ProcessingStatus.COMPLETED,
        ),
        key=[SubmissionBatch.programme_id, SubmissionBatch.academic_year],
        stamp=SubmissionBatch.received_at,
        tie=SubmissionBatch.id,
    )
    if f.academic_year is not None:
        batch_statement = batch_statement.where(
            SubmissionBatch.academic_year == f.academic_year
        )
    batch_rows = session.execute(
        batch_statement.add_columns(SubmissionBatch.academic_year)
    ).all()
    batch_info = {b: (pid, year) for b, pid, year in batch_rows}
    run_by_batch = selected_runs_bulk(session, list(batch_info))
    run_owner = {run: batch_info[batch] for batch, run in run_by_batch.items()}
    counts: Counter[tuple[UUID, str, str, str, str]] = Counter()
    for run_id, rule, severity, classification, n in session.execute(
        select(
            ValidationFinding.run_id,
            ValidationFinding.rule_code,
            ValidationFinding.severity,
            ValidationFinding.classification,
            func.count(),
        )
        .where(ValidationFinding.run_id.in_(list(run_owner)))
        .group_by(
            ValidationFinding.run_id,
            ValidationFinding.rule_code,
            ValidationFinding.severity,
            ValidationFinding.classification,
        )
    ):
        programme_id, year = run_owner[run_id]
        counts[(programme_id, year, rule, severity, classification)] += n
    order = {p.id: n for n, (_, p) in enumerate(units)}
    rows = sorted(
        counts.items(), key=lambda kv: (order[kv[0][0]], kv[0][1], kv[0][2], kv[0][3])
    )
    by_severity: Counter[str] = Counter()
    for (_, _, _, severity, _), n in rows:
        by_severity[severity] += n
    covered = len(run_by_batch) > 0
    return document(
        "validation-findings",
        "Validation findings by rule and severity (latest completed runs)",
        user,
        now,
        params,
        year_context(f),
        f"{len(run_by_batch)} of {len(batch_info)} latest completed submissions have "
        "a validation run; submissions without a run are excluded, not counted as "
        "clean. Counts are findings, not records, and not fraud determinations. "
        "Basis: the most recently received completed submission per programme and "
        "academic year (candidate or active), and its latest validation run.",
        table(
            "Totals by severity",
            ["severity", "findings"],
            [
                [s, by_severity[s] if covered else None]
                for s in ("ERROR", "WARNING", "INFO")
            ]
            + [["ALL", sum(by_severity.values()) if covered else None]],
        ),
        table(
            "Findings by programme and rule",
            [
                "academic_year",
                "institution",
                "programme_code",
                "rule_code",
                "severity",
                "classification",
                "findings",
            ],
            [
                [
                    year,
                    by_programme[programme_id][0].name,
                    by_programme[programme_id][1].code,
                    rule,
                    severity,
                    classification,
                    n,
                ]
                for (programme_id, year, rule, severity, classification), n in rows
            ],
        ),
    )


def verification_activity(
    session: Session, user: User, params: ReportParams, now: datetime
) -> ReportDocument:
    f = params.filters
    apaar = (
        select(
            Institution.name,
            ApaarVerification.purpose,
            ApaarVerification.status,
            func.count(),
        )
        .join(SubmissionBatch, SubmissionBatch.id == ApaarVerification.batch_id)
        .join(Institution, Institution.id == SubmissionBatch.institution_id)
        .group_by(Institution.name, ApaarVerification.purpose, ApaarVerification.status)
    )
    credential = (
        select(
            Institution.name,
            CredentialVerification.purpose,
            CredentialVerification.outcome,
            func.count(),
        )
        .select_from(CredentialVerification)
        .outerjoin(
            AdmissionCredential,
            AdmissionCredential.id == CredentialVerification.credential_id,
        )
        .outerjoin(Institution, Institution.id == AdmissionCredential.institution_id)
        .group_by(
            Institution.name,
            CredentialVerification.purpose,
            CredentialVerification.outcome,
        )
    )
    for clause in (
        (Institution.id == f.institution_id) if f.institution_id else None,
        (Institution.region == f.region) if f.region else None,
    ):
        if clause is not None:
            apaar = apaar.where(clause)
            credential = credential.where(clause)
    rows: list[tuple[str, str, str, str, int]] = []
    for source, statement in (
        ("SIMULATED_APAAR_VERIFICATION", apaar),
        ("CREDENTIAL_VERIFICATION", credential),
    ):
        for name, purpose, status, n in session.execute(statement):
            # Purpose is free text: keep digit runs (possible identifiers) out.
            rows.append((source, name or UNATTRIBUTED, redact(purpose), status, n))
    rows.sort()
    totals: Counter[tuple[str, str]] = Counter()
    for source, _, _, status, n in rows:
        totals[(source, status)] += n
    total_rows: list[list[Cell]] = [
        [source, status, n] for (source, status), n in sorted(totals.items())
    ]
    total_rows.append(["ALL", "ALL", sum(totals.values())])
    return document(
        "verification-activity",
        "Verification activity (simulated APAAR checks and credential verifications)",
        user,
        now,
        params,
        NO_YEAR,
        f"{sum(totals.values())} verification attempts. APAAR results come from a "
        "simulated provider and are never government verification; credential "
        "verifications check DEMO-signed credentials only.",
        table(
            "Totals by source and status",
            ["source", "status", "attempts"],
            total_rows,
        ),
        table(
            "Attempts by source, institution, purpose and status",
            ["source", "institution", "purpose", "status", "attempts"],
            [[a, b, c, d, e] for a, b, c, d, e in rows],
        ),
    )


# ------------------------------------------------------------------ entry points


def build_report(
    session: Session,
    kind: ReportKind,
    user: User,
    requested: ReportParams,
    settings: Settings,
    now: datetime,
) -> ReportDocument:
    params = authorize(user, kind, requested)
    match kind:
        case "enrolment-summary":
            report = enrolment_summary(session, user, params, now)
        case "intake-utilisation":
            report = intake_utilisation(session, user, params, settings, now)
        case "submission-completeness":
            report = submission_completeness(session, user, params, settings, now)
        case "resolution-times":
            report = resolution_times(session, user, params, settings, now)
        case "open-cases":
            report = open_cases(session, user, params, settings, now)
        case "validation-findings":
            report = validation_findings(session, user, params, now)
        case "verification-activity":
            report = verification_activity(session, user, params, now)
    if len(report.data.rows) > settings.report_max_rows:
        raise APIError(
            422,
            "REPORT_TOO_LARGE",
            f"Report exceeds {settings.report_max_rows} rows; narrow the filters",
        )
    return report


def record_export(
    session: Session,
    user: User,
    report: ReportDocument,
    file_format: ReportFormat,
) -> None:
    """Audit the export: kind, format, filter keys/ids and row count; never data."""
    institution = report.filters.get("institution_id")
    details = {
        "kind": report.kind,
        "format": file_format,
        "filter_keys": ",".join(sorted(report.filters)),
        "row_count": str(len(report.data.rows)),
    }
    if institution is not None:
        details["institution_id"] = institution
    record_action(
        session,
        actor_id=user.id,
        institution_id=UUID(institution) if institution else user.institution_id,
        action="REPORT_EXPORTED",
        entity_type="REPORT",
        entity_id=uuid4(),
        details=details,
    )
    session.commit()
