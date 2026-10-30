"""Aggregate analytics responses. Counts only: no APAAR, names or student ids."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.pagination import Pagination
from app.modules.cases.models import CasePriority, CaseSeverity, CaseStatus

GroupBy = Literal["academic_year", "institution", "programme", "region"]
# NO_CURRENT_SNAPSHOT means "unknown", never zero enrolment.
TrendStatus = Literal["COMPLETE", "PARTIAL", "NO_CURRENT_SNAPSHOT"]
FreshnessStatus = Literal["FRESH", "STALE", "NO_CURRENT_SNAPSHOT"]
IntakeStatus = Literal["OK", "NO_CURRENT_SNAPSHOT", "NO_RULE"]
Drilldown = dict[str, str]

NOTICE = (
    "DEMO data. Counts are declared rows in current activated snapshots, not "
    "verified enrolment. Missing data is unknown, never zero."
)


class AnalyticsFilters(BaseModel):
    academic_year: str | None = None
    institution_id: UUID | None = None
    region: str | None = None
    programme_code: str | None = None
    group_by: GroupBy | None = None
    priority: CasePriority | None = None
    severity: CaseSeverity | None = None


class CoverageCounts(BaseModel):
    institutions_total: int
    institutions_with_current_snapshot: int
    programmes_total: int
    programmes_with_current_snapshot: int


class AnalyticsMeta(BaseModel):
    as_of: datetime
    filters: AnalyticsFilters
    coverage: CoverageCounts
    source_label: Literal["DEMO"] = "DEMO"
    notice: str = NOTICE


class CategoryCount(BaseModel):
    declared_records: int = 0
    active_records: int = 0


class TrendRow(BaseModel):
    academic_year: str
    status: TrendStatus
    institution_id: UUID | None = None
    institution_name: str | None = None
    programme_id: UUID | None = None
    programme_code: str | None = None
    region: str | None = None
    programmes_total: int
    programmes_with_current_snapshot: int
    declared_records: int | None
    active_records: int | None
    categories: dict[str, CategoryCount] | None
    unclassified_active_records: int | None
    drilldown: Drilldown


class TrendsResponse(AnalyticsMeta):
    group_by: GroupBy
    data: list[TrendRow]
    pagination: Pagination


class CompletenessRow(BaseModel):
    institution_id: UUID
    institution_name: str
    region: str
    programme_id: UUID
    programme_code: str
    academic_year: str | None
    has_current_snapshot: bool
    last_activated_at: datetime | None
    freshness_days: int | None
    stale: bool | None
    freshness_status: FreshnessStatus
    has_declaration: bool
    declared_total: int | None
    current_declared_records: int | None
    # Only when both a declaration and a current snapshot exist.
    shortfall: int | None
    pending_candidate_count: int
    drilldown: Drilldown


class RegionRollup(BaseModel):
    region: str
    institutions_total: int
    programme_years_total: int
    with_current_snapshot: int
    stale: int
    with_declaration: int
    with_shortfall: int
    pending_candidates: int


class CompletenessResponse(AnalyticsMeta):
    stale_after_days: int
    data: list[CompletenessRow]
    rollups_by_region: list[RegionRollup]
    pagination: Pagination


class UtilisationRow(BaseModel):
    institution_id: UUID
    institution_name: str
    programme_id: UUID
    programme_code: str
    academic_year: str
    category: str
    status: IntakeStatus
    approved_seats: int | None
    rule_version: str | None
    current_active: int | None
    utilisation_pct: float | None
    remaining_capacity: int | None
    exceeded: bool | None
    excess: int | None
    calculation: str
    drilldown: Drilldown


class UtilisationResponse(AnalyticsMeta):
    rule_version_in_use: str
    pooling_note: str
    data: list[UtilisationRow]
    pagination: Pagination


class StatusCount(BaseModel):
    status: CaseStatus
    total: int
    overdue: int
    escalated: int
    drilldown: Drilldown


class CaseTotals(BaseModel):
    all: int
    open: int
    overdue: int
    escalated: int


class AgeBucket(BaseModel):
    bucket: Literal["0-7", "8-14", "15-30", "31+"]
    min_days: int
    max_days: int | None
    count: int
    drilldown: Drilldown


class ResolutionStats(BaseModel):
    priority: CasePriority | Literal["ALL"]
    resolved_count: int
    mean_days: float | None
    median_days: float | None
    p90_days: float | None


class InstitutionCases(BaseModel):
    institution_id: UUID
    institution_name: str
    region: str
    open: int
    overdue: int
    resolved: int
    drilldown: Drilldown


class CasePerformanceResponse(AnalyticsMeta):
    totals: CaseTotals
    by_status: list[StatusCount]
    ageing: list[AgeBucket]
    resolution_days: list[ResolutionStats]
    p90_method: str = Field(default="nearest-rank on elapsed days")
    data: list[InstitutionCases]
    pagination: Pagination
