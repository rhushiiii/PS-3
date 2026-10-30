"""Read-only aggregates over stored data.

Rules shared by every report: only ACTIVE institutions/programmes count, only the
CURRENT activated snapshot of a scope contributes, and a scope without one is
reported as unknown (null + status), never as zero.
"""

import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.analytics.schemas import (
    AgeBucket,
    AnalyticsFilters,
    AnalyticsMeta,
    CaseTotals,
    CategoryCount,
    CompletenessRow,
    CoverageCounts,
    Drilldown,
    FreshnessStatus,
    GroupBy,
    InstitutionCases,
    RegionRollup,
    ResolutionStats,
    StatusCount,
    TrendRow,
    UtilisationRow,
)
from app.modules.cases.models import CLOSED_STATUSES, ReviewCase
from app.modules.cases.services import case_flags
from app.modules.institutions.models import Institution, IntakeRule, Programme
from app.modules.intake.services import (
    capacity_line,
    configured_rules,
    latest_declarations_bulk,
    utilisation_pct,
)
from app.modules.submissions.models import (
    ProcessingStatus,
    StudentRecordVersion,
    SubmissionBatch,
    SubmissionScope,
)
from app.modules.validation.rules import CATEGORIES

CASE_STATUSES = (
    "OPEN",
    "ASSIGNED",
    "UNDER_REVIEW",
    "AWAITING_CORRECTION",
    "RESPONSE_SUBMITTED",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
)
PRIORITIES = ("LOW", "MEDIUM", "HIGH", "URGENT")
AGE_BUCKETS: tuple[tuple[str, int, int | None], ...] = (
    ("0-7", 0, 7),
    ("8-14", 8, 14),
    ("15-30", 15, 30),
    ("31+", 31, None),
)

Unit = tuple[Institution, Programme]


@dataclass(frozen=True)
class Filters:
    academic_year: str | None = None
    institution_id: UUID | None = None
    region: str | None = None
    programme_code: str | None = None

    def echo(self, **extra: object) -> AnalyticsFilters:
        return AnalyticsFilters(**asdict(self), **extra)


@dataclass
class ScopeData:
    current_batch_id: UUID | None
    activated_at: datetime | None


@dataclass
class Counts:
    declared: int = 0
    active: int = 0
    unclassified_active: int = 0
    categories: dict[str, CategoryCount] = field(
        default_factory=lambda: {c: CategoryCount() for c in CATEGORIES}
    )

    def add(self, other: "Counts") -> None:
        self.declared += other.declared
        self.active += other.active
        self.unclassified_active += other.unclassified_active
        for name, value in other.categories.items():
            self.categories[name].declared_records += value.declared_records
            self.categories[name].active_records += value.active_records


def pick(**values: object) -> Drilldown:
    return {
        k: str(v).lower() if isinstance(v, bool) else str(v)
        for k, v in values.items()
        if v is not None
    }


# ---------------------------------------------------------------- shared loading


def institutions_in_scope(session: Session, f: Filters) -> list[Institution]:
    statement = (
        select(Institution)
        .where(Institution.active.is_(True))
        .order_by(Institution.permanent_id)
    )
    if f.institution_id is not None:
        statement = statement.where(Institution.id == f.institution_id)
    if f.region is not None:
        statement = statement.where(Institution.region == f.region)
    return list(session.scalars(statement))


def programme_units(session: Session, f: Filters) -> list[Unit]:
    statement = (
        select(Institution, Programme)
        .join(Programme, Programme.institution_id == Institution.id)
        .where(Institution.active.is_(True), Programme.active.is_(True))
        .order_by(Institution.permanent_id, Programme.code)
    )
    if f.institution_id is not None:
        statement = statement.where(Institution.id == f.institution_id)
    if f.region is not None:
        statement = statement.where(Institution.region == f.region)
    if f.programme_code is not None:
        statement = statement.where(Programme.code == f.programme_code)
    return [(i, p) for i, p in session.execute(statement)]


def load_scopes(
    session: Session, units: list[Unit], year: str | None
) -> dict[tuple[UUID, str], ScopeData]:
    statement = select(
        SubmissionScope.programme_id,
        SubmissionScope.academic_year,
        SubmissionScope.current_batch_id,
        SubmissionBatch.activated_at,
    ).outerjoin(SubmissionBatch, SubmissionBatch.id == SubmissionScope.current_batch_id)
    statement = statement.where(
        SubmissionScope.programme_id.in_([p.id for _, p in units])
    )
    if year is not None:
        statement = statement.where(SubmissionScope.academic_year == year)
    return {
        (programme_id, academic_year): ScopeData(batch_id, activated_at)
        for programme_id, academic_year, batch_id, activated_at in session.execute(
            statement
        )
    }


def load_counts(
    session: Session, scopes: dict[tuple[UUID, str], ScopeData]
) -> dict[UUID, Counts]:
    """Per current batch: declared rows and ACTIVE rows, by admission category."""
    batch_ids = [s.current_batch_id for s in scopes.values() if s.current_batch_id]
    counts: dict[UUID, Counts] = {batch_id: Counts() for batch_id in batch_ids}
    if not batch_ids:
        return counts
    active = StudentRecordVersion.enrollment_status == "ACTIVE"
    for batch_id, category, declared, active_n in session.execute(
        select(
            StudentRecordVersion.batch_id,
            StudentRecordVersion.admission_category,
            func.count(),
            func.count().filter(active),
        )
        .where(StudentRecordVersion.batch_id.in_(batch_ids))
        .group_by(
            StudentRecordVersion.batch_id, StudentRecordVersion.admission_category
        )
    ):
        entry = counts[batch_id]
        entry.declared += declared
        entry.active += active_n
        if category in entry.categories:
            entry.categories[category].declared_records += declared
            entry.categories[category].active_records += active_n
        else:
            entry.unclassified_active += active_n
    return counts


def years_for(
    units: list[Unit],
    f: Filters,
    scopes: dict[tuple[UUID, str], ScopeData],
    extra: set[tuple[UUID, str]] | None = None,
) -> dict[UUID, list[str]]:
    """Academic years per programme: the filter year, else every year on record."""
    found: dict[UUID, set[str]] = defaultdict(set)
    for programme_id, year in set(scopes) | (extra or set()):
        found[programme_id].add(year)
    return {
        p.id: [f.academic_year] if f.academic_year else sorted(found.get(p.id, ()))
        for _, p in units
    }


def build_meta(
    session: Session,
    f: Filters,
    now: datetime,
    units: list[Unit],
    scopes: dict[tuple[UUID, str], ScopeData],
    echo: AnalyticsFilters | None = None,
) -> AnalyticsMeta:
    with_snapshot = {pid for (pid, _), s in scopes.items() if s.current_batch_id}
    institution_ids = {i.id for i, _ in units}
    institutions = (
        institution_ids
        if f.programme_code is not None
        else {i.id for i in institutions_in_scope(session, f)}
    )
    return AnalyticsMeta(
        as_of=now,
        filters=echo or f.echo(),
        coverage=CoverageCounts(
            institutions_total=len(institutions),
            institutions_with_current_snapshot=len(
                {i.id for i, p in units if p.id in with_snapshot}
            ),
            programmes_total=len(units),
            programmes_with_current_snapshot=len(
                {p.id for _, p in units if p.id in with_snapshot}
            ),
        ),
    )


def freshness(
    activated_at: datetime | None, now: datetime, stale_days: int
) -> tuple[int | None, bool | None, FreshnessStatus]:
    """Stale when older than the integrity threshold (same rule as integrity)."""
    if activated_at is None:
        return None, None, "NO_CURRENT_SNAPSHOT"
    age = now - activated_at
    stale = age > timedelta(days=stale_days)
    return max(0, age.days), stale, "STALE" if stale else "FRESH"


# ---------------------------------------------------------------- enrolment trends


def enrolment_trends(
    session: Session, f: Filters, group_by: GroupBy, now: datetime
) -> tuple[AnalyticsMeta, list[TrendRow]]:
    units = programme_units(session, f)
    scopes = load_scopes(session, units, f.academic_year)
    counts = load_counts(session, scopes)
    years = (
        [f.academic_year] if f.academic_year else sorted({year for _, year in scopes})
    )
    groups: dict[str, tuple[Unit, list[UUID]]] = {}
    for institution, programme in units:
        key = {
            "academic_year": "",
            "region": institution.region,
            "institution": str(institution.id),
            "programme": str(programme.id),
        }[group_by]
        groups.setdefault(key, ((institution, programme), []))[1].append(programme.id)
    rows: list[TrendRow] = []
    for year in years:
        for (institution, programme), programme_ids in groups.values():
            total = Counts()
            with_snapshot = 0
            for pid in programme_ids:
                scope = scopes.get((pid, year))
                if scope is not None and scope.current_batch_id is not None:
                    with_snapshot += 1
                    total.add(counts[scope.current_batch_id])
            known = with_snapshot > 0
            by_institution = group_by in {"institution", "programme"}
            by_programme = group_by == "programme"
            by_region = group_by in {"region", "institution", "programme"}
            rows.append(
                TrendRow(
                    academic_year=year,
                    status="NO_CURRENT_SNAPSHOT"
                    if not known
                    else "COMPLETE"
                    if with_snapshot == len(programme_ids)
                    else "PARTIAL",
                    institution_id=institution.id if by_institution else None,
                    institution_name=institution.name if by_institution else None,
                    programme_id=programme.id if by_programme else None,
                    programme_code=programme.code if by_programme else None,
                    region=institution.region if by_region else None,
                    programmes_total=len(programme_ids),
                    programmes_with_current_snapshot=with_snapshot,
                    declared_records=total.declared if known else None,
                    active_records=total.active if known else None,
                    categories=total.categories if known else None,
                    unclassified_active_records=total.unclassified_active
                    if known
                    else None,
                    drilldown=pick(
                        academic_year=year,
                        institution_id=institution.id if by_institution else None,
                        programme_id=programme.id if by_programme else None,
                        region=institution.region if group_by == "region" else None,
                    ),
                )
            )
    return build_meta(session, f, now, units, scopes, f.echo(group_by=group_by)), rows


# ---------------------------------------------------------------- completeness


def pending_candidates(
    session: Session, programme_ids: list[UUID]
) -> dict[tuple[UUID, str], int]:
    """Processed batches not yet activated (awaiting officer/admin review)."""
    rows = session.execute(
        select(
            SubmissionBatch.programme_id, SubmissionBatch.academic_year, func.count()
        )
        .where(
            SubmissionBatch.programme_id.in_(programme_ids),
            SubmissionBatch.activated_at.is_(None),
            SubmissionBatch.status == ProcessingStatus.COMPLETED,
        )
        .group_by(SubmissionBatch.programme_id, SubmissionBatch.academic_year)
    )
    return {(pid, year): n for pid, year, n in rows}


def submission_completeness(
    session: Session, f: Filters, settings: Settings, now: datetime
) -> tuple[AnalyticsMeta, list[CompletenessRow], list[RegionRollup]]:
    units = programme_units(session, f)
    scopes = load_scopes(session, units, f.academic_year)
    programme_ids = [p.id for _, p in units]
    declarations = latest_declarations_bulk(session, programme_ids)
    pending = pending_candidates(session, programme_ids)
    counts = load_counts(session, scopes)
    years = years_for(units, f, scopes, set(declarations) | set(pending))
    none_year: list[str | None] = [None]
    rows: list[CompletenessRow] = []
    for institution, programme in units:
        for year in years[programme.id] or none_year:
            scope = scopes.get((programme.id, year)) if year else None
            current = scope.current_batch_id if scope else None
            days, stale, status = freshness(
                scope.activated_at if scope and current else None,
                now,
                settings.integrity_stale_days,
            )
            declared = declarations.get((programme.id, year)) if year else None
            records = counts[current].declared if current else None
            rows.append(
                CompletenessRow(
                    institution_id=institution.id,
                    institution_name=institution.name,
                    region=institution.region,
                    programme_id=programme.id,
                    programme_code=programme.code,
                    academic_year=year,
                    has_current_snapshot=current is not None,
                    last_activated_at=scope.activated_at if scope and current else None,
                    freshness_days=days,
                    stale=stale,
                    freshness_status=status,
                    has_declaration=declared is not None,
                    declared_total=declared,
                    current_declared_records=records,
                    shortfall=max(0, declared - records)
                    if declared is not None and records is not None
                    else None,
                    pending_candidate_count=pending.get((programme.id, year), 0)
                    if year
                    else 0,
                    drilldown=pick(
                        institution_id=institution.id,
                        programme_id=programme.id,
                        academic_year=year,
                    ),
                )
            )
    rollups: dict[str, RegionRollup] = {}
    for institution in institutions_in_scope(session, f):
        rollups.setdefault(
            institution.region,
            RegionRollup(
                region=institution.region,
                institutions_total=0,
                programme_years_total=0,
                with_current_snapshot=0,
                stale=0,
                with_declaration=0,
                with_shortfall=0,
                pending_candidates=0,
            ),
        ).institutions_total += 1
    for row in rows:
        rollup = rollups[row.region]
        rollup.programme_years_total += 1
        rollup.with_current_snapshot += row.has_current_snapshot
        rollup.stale += row.stale is True
        rollup.with_declaration += row.has_declaration
        rollup.with_shortfall += bool(row.shortfall)
        rollup.pending_candidates += row.pending_candidate_count
    return (
        build_meta(session, f, now, units, scopes),
        rows,
        sorted(rollups.values(), key=lambda r: r.region),
    )


# ---------------------------------------------------------------- intake utilisation


def intake_utilisation(
    session: Session, f: Filters, settings: Settings, now: datetime
) -> tuple[AnalyticsMeta, list[UtilisationRow]]:
    version = settings.validation_intake_rule_version
    units = programme_units(session, f)
    scopes = load_scopes(session, units, f.academic_year)
    counts = load_counts(session, scopes)
    rule_scopes = {
        (pid, year)
        for pid, year in session.execute(
            select(IntakeRule.programme_id, IntakeRule.academic_year)
            .where(
                IntakeRule.programme_id.in_([p.id for _, p in units]),
                IntakeRule.rule_version == version,
                IntakeRule.source_label == "DEMO",
            )
            .distinct()
        )
        if f.academic_year in (None, year)
    }
    years = years_for(units, f, scopes, rule_scopes)
    rows: list[UtilisationRow] = []
    for institution, programme in units:
        for year in years[programme.id]:
            rules = configured_rules(
                session, institution.id, programme.id, year, version
            )
            scope = scopes.get((programme.id, year))
            current = scope.current_batch_id if scope else None
            for category in CATEGORIES:
                rule = rules.get(category)
                active = (
                    counts[current].categories[category].active_records
                    if current
                    else None
                )
                line = capacity_line(category, rule, active or 0, "ACTIVE")
                approved = rule.approved_seats if rule else None
                if rule is None:
                    status, calculation = "NO_RULE", line["calculation"]
                    values: tuple[int | None, bool | None, int | None] = (
                        None,
                        None,
                        None,
                    )
                elif active is None:
                    status = "NO_CURRENT_SNAPSHOT"
                    calculation = (
                        f"no current activated snapshot; ACTIVE count unknown (not "
                        f"zero); approved {approved} (rule {rule.rule_version}, "
                        f"{category})"
                    )
                    values = (None, None, None)
                else:
                    status, calculation = "OK", line["calculation"]
                    values = (
                        line["remaining_capacity"],
                        line["exceeded"],
                        line["excess"],
                    )
                rows.append(
                    UtilisationRow(
                        institution_id=institution.id,
                        institution_name=institution.name,
                        programme_id=programme.id,
                        programme_code=programme.code,
                        academic_year=year,
                        category=category,
                        status=status,
                        approved_seats=approved,
                        rule_version=rule.rule_version if rule else None,
                        current_active=active,
                        utilisation_pct=utilisation_pct(active, approved),
                        remaining_capacity=values[0],
                        exceeded=values[1],
                        excess=values[2],
                        calculation=calculation,
                        drilldown=pick(
                            institution_id=institution.id,
                            programme_id=programme.id,
                            academic_year=year,
                        ),
                    )
                )
    return build_meta(session, f, now, units, scopes), rows


# ---------------------------------------------------------------- case performance


def resolution_stats(priority: str, days: list[float]) -> ResolutionStats:
    if not days:
        return ResolutionStats(
            priority=priority,
            resolved_count=0,
            mean_days=None,
            median_days=None,
            p90_days=None,
        )
    ordered = sorted(days)
    rank = -(-9 * len(ordered) // 10)  # ceil(0.9 * n) in integers
    return ResolutionStats(
        priority=priority,
        resolved_count=len(ordered),
        mean_days=round(statistics.fmean(ordered), 2),
        median_days=round(statistics.median(ordered), 2),
        p90_days=round(ordered[rank - 1], 2),
    )


def scoped_cases(
    session: Session,
    institutions: list[Institution],
    priority: str | None,
    severity: str | None,
) -> list[ReviewCase]:
    """The case population behind every case total (shared with reports)."""
    statement = select(ReviewCase).where(
        ReviewCase.institution_id.in_([i.id for i in institutions])
    )
    if priority is not None:
        statement = statement.where(ReviewCase.priority == priority)
    if severity is not None:
        statement = statement.where(ReviewCase.severity == severity)
    return list(session.scalars(statement))


@dataclass
class CaseReport:
    meta: AnalyticsMeta
    totals: CaseTotals
    by_status: list[StatusCount]
    ageing: list[AgeBucket]
    resolution: list[ResolutionStats]
    institutions: list[InstitutionCases]


def case_performance(
    session: Session,
    f: Filters,
    priority: str | None,
    severity: str | None,
    settings: Settings,
    now: datetime,
) -> CaseReport:
    units = programme_units(session, f)
    scopes = load_scopes(session, units, None)
    institutions = institutions_in_scope(session, f)
    cases = scoped_cases(session, institutions, priority, severity)

    totals: defaultdict[str, int] = defaultdict(int)
    by_status = {s: [0, 0, 0] for s in CASE_STATUSES}
    ages = {name: 0 for name, _, _ in AGE_BUCKETS}
    durations: dict[str, list[float]] = {p: [] for p in PRIORITIES}
    per_institution: dict[UUID, list[int]] = {i.id: [0, 0, 0] for i in institutions}
    for case in cases:
        overdue, escalated, age_days = case_flags(case, settings, now)
        is_open = case.status not in CLOSED_STATUSES
        totals["all"] += 1
        totals["open"] += is_open
        totals["overdue"] += overdue
        totals["escalated"] += escalated
        entry = by_status[case.status]
        entry[0] += 1
        entry[1] += overdue
        entry[2] += escalated
        row = per_institution[case.institution_id]
        row[0] += is_open
        row[1] += overdue
        if is_open:
            for name, low, high in AGE_BUCKETS:
                if age_days >= low and (high is None or age_days <= high):
                    ages[name] += 1
                    break
        if case.resolved_at is not None:
            row[2] += 1
            durations[case.priority].append(
                (case.resolved_at - case.opened_at).total_seconds() / 86400
            )
    scope = pick(institution_id=f.institution_id, priority=priority, severity=severity)
    return CaseReport(
        meta=build_meta(
            session,
            f,
            now,
            units,
            scopes,
            f.echo(priority=priority, severity=severity),
        ),
        totals=CaseTotals(
            all=totals["all"],
            open=totals["open"],
            overdue=totals["overdue"],
            escalated=totals["escalated"],
        ),
        by_status=[
            StatusCount(
                status=status,
                total=n,
                overdue=o,
                escalated=e,
                drilldown={**scope, "status": status},
            )
            for status, (n, o, e) in by_status.items()
        ],
        ageing=[
            AgeBucket(
                bucket=name,
                min_days=low,
                max_days=high,
                count=ages[name],
                drilldown={**scope, "min_age_days": str(low)},
            )
            for name, low, high in AGE_BUCKETS
        ],
        resolution=[resolution_stats(p, durations[p]) for p in PRIORITIES]
        + [resolution_stats("ALL", [d for ds in durations.values() for d in ds])],
        institutions=[
            InstitutionCases(
                institution_id=i.id,
                institution_name=i.name,
                region=i.region,
                open=per_institution[i.id][0],
                overdue=per_institution[i.id][1],
                resolved=per_institution[i.id][2],
                drilldown=pick(
                    institution_id=i.id, priority=priority, severity=severity
                ),
            )
            for i in institutions
        ],
    )
