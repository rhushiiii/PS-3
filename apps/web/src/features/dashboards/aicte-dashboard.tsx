"use client";

import Link from "next/link";
import { useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { useSession } from "@/features/auth/session";
import { isUUID } from "@/lib/api/client";
import type { components, paths } from "@/lib/api/generated";
import {
  CategoryBars,
  CoverageBadge,
  DashboardFilters,
  DashboardTable,
  MetricCard,
  StatusDonut,
  countValue,
  displayCount,
  prettyLabel,
  valueObject,
} from "./components";

type Summary = components["schemas"]["InstitutionSummary"];
type Run = components["schemas"]["RunResponse"];
type Batch = components["schemas"]["BatchResponse"];
type InstitutionPage =
  paths["/api/v1/institutions"]["get"]["responses"][200]["content"]["application/json"];
type SubmissionPage =
  paths["/api/v1/submissions"]["get"]["responses"][200]["content"]["application/json"];

const dashboardYear = "2026-27";
const historyPageSize = 100;

type AssessmentSummary = {
  label: string;
  note: string;
  tone: "active" | "warning" | "neutral";
};

export function AicteDashboard() {
  const { session, request } = useSession();
  const isOfficer = session?.user.role === "AICTE_OFFICER";
  const isManager = session?.user.role === "AICTE_MANAGER";
  const [yearDraft, setYearDraft] = useState(dashboardYear);
  const [year, setYear] = useState(dashboardYear);
  const [region, setRegion] = useState("");
  const [institutionId, setInstitutionId] = useState("");
  const [regionDraft, setRegionDraft] = useState("");
  const [institutionDraft, setInstitutionDraft] = useState("");
  const [filterError, setFilterError] = useState("");
  const validYear =
    /^\d{4}-\d{2}$/.test(year) &&
    Number(year.slice(-2)) === (Number(year.slice(0, 4)) + 1) % 100;
  const baseKey = [
    "private",
    session?.generation,
    session?.user.id,
    "aicte-dashboard",
  ];
  const institutions = useQuery({
    queryKey: [...baseKey, "institutions"],
    enabled: !!session && (isOfficer || isManager),
    queryFn: ({ signal }) =>
      request<InstitutionPage>("/institutions?page=1&page_size=100", {
        signal,
      }),
  });
  const allInstitutions = institutions.data?.data ?? [];
  const regions = [
    ...new Set(allInstitutions.map((item) => item.region)),
  ].sort();
  const visibleInstitutions = allInstitutions.filter(
    (item) =>
      (!region || item.region === region) &&
      (!institutionId || item.id === institutionId),
  );
  const summaries = useQueries({
    queries: visibleInstitutions.map((item) => ({
      queryKey: [...baseKey, "summary", year, item.id],
      enabled: !!session && validYear,
      queryFn: ({ signal }: { signal: AbortSignal }) =>
        request<Summary>(
          `/institutions/${item.id}/summary?academic_year=${encodeURIComponent(year)}&page=1&page_size=100`,
          { signal },
        ),
      staleTime: 0,
    })),
  });
  const historyQueries = useQueries({
    queries: isOfficer
      ? visibleInstitutions.map((item) => ({
          queryKey: [...baseKey, "current-batch-history", year, item.id],
          enabled: !!session && validYear,
          queryFn: async ({ signal }: { signal: AbortSignal }) => {
            const collected: Batch[] = [];
            let page = 1;
            let total = Number.POSITIVE_INFINITY;
            while (collected.length < total) {
              const result = await request<SubmissionPage>(
                `/submissions?${new URLSearchParams({ institution_id: item.id, academic_year: year, page: String(page), page_size: String(historyPageSize) })}`,
                { signal },
              );
              collected.push(...result.data);
              total = result.pagination.total;
              page += 1;
            }
            return collected;
          },
          staleTime: 0,
        }))
      : [],
  });
  const currentBatches = historyQueries.flatMap((query) =>
    (query.data ?? []).filter((batch) => batch.snapshot_state === "CURRENT"),
  );
  const validationRuns = useQueries({
    queries: isOfficer
      ? currentBatches.map((batch) => ({
          queryKey: [
            ...baseKey,
            "current-validation",
            year,
            batch.id,
            batch.latest_validation_run_id,
          ],
          enabled:
            !!session &&
            !!batch.latest_validation_run_id &&
            isUUID(batch.latest_validation_run_id),
          queryFn: ({ signal }: { signal: AbortSignal }) =>
            request<Run>(
              `/submissions/${batch.id}/validation-runs/${batch.latest_validation_run_id}`,
              { signal },
            ),
          staleTime: 0,
        }))
      : [],
  });
  const categoryTotals: Record<string, number> = {};
  const statusTotals: Record<string, number> = {};
  for (const query of summaries) {
    const categories = valueObject(valueObject(query.data?.totals)?.categories);
    for (const [key, raw] of Object.entries(categories ?? {})) {
      const count = countValue(valueObject(raw)?.declared_records);
      if (count !== null)
        categoryTotals[key] = (categoryTotals[key] ?? 0) + count;
    }
    const statuses = valueObject(valueObject(query.data?.totals)?.statuses);
    for (const [key, raw] of Object.entries(statuses ?? {})) {
      const count = countValue(raw);
      if (count !== null) statusTotals[key] = (statusTotals[key] ?? 0) + count;
    }
  }
  const statusData = Object.entries(statusTotals)
    .map(([label, value]) => ({ label, value }))
    .filter((item) => item.value > 0);
  const statusTotal = statusData.reduce((sum, item) => sum + item.value, 0);
  const successfulSummaries = summaries.flatMap((query) =>
    query.data ? [query.data] : [],
  );
  const failedSummaries = summaries.filter((query) => query.isError);
  const pendingSummaries = summaries.some((query) => query.isPending);
  const totals = successfulSummaries.reduce(
    (acc, item) => {
      const data = valueObject(item.totals);
      acc.declared += countValue(data?.declared_records) ?? 0;
      acc.active += countValue(data?.demo_active_records) ?? 0;
      acc.programmes += countValue(valueObject(item.coverage)?.programmes) ?? 0;
      acc.covered +=
        countValue(valueObject(item.coverage)?.with_current_snapshot) ?? 0;
      return acc;
    },
    { declared: 0, active: 0, programmes: 0, covered: 0 },
  );
  const allNoDeclarations =
    successfulSummaries.length > 0 &&
    successfulSummaries.every(
      (item) => valueObject(item.coverage)?.status === "NONE",
    );
  const historyLoading =
    isOfficer && historyQueries.some((query) => query.isPending);
  const historyErrors = isOfficer
    ? historyQueries.filter((query) => query.isError).length
    : 0;
  const assessments: AssessmentSummary[] = isOfficer
    ? currentBatches.map((batch, index) => {
        const summary = summaries.find((query) =>
          query.data?.data.some(
            (program) => program.programme_id === batch.programme_id,
          ),
        )?.data;
        const run = validationRuns[index]?.data;
        const runError = validationRuns[index]?.isError;
        if (!summary)
          return {
            label: "Unavailable",
            note: "Institution summary unavailable",
            tone: "neutral",
          };
        if (!batch.latest_validation_run_id)
          return {
            label: "Unavailable",
            note: "Current snapshot has no completed validation run",
            tone: "neutral",
          };
        if (runError)
          return {
            label: "Unavailable",
            note: "Validation assessment could not be loaded",
            tone: "neutral",
          };
        if (!run)
          return {
            label: "Loading",
            note: "Loading current assessment",
            tone: "neutral",
          };
        const freshness = run.cross_current_freshness;
        const matching = run.summary.matching_assessment;
        if (freshness === "STALE")
          return {
            label: "Stale",
            note: "This assessment is out of date; overlap counts are unavailable",
            tone: "warning",
          };
        if (
          freshness !== "FRESH" ||
          matching !== "COMPLETE" ||
          run.current_overlap_records === null
        )
          return {
            label: "Incomplete",
            note: "Current overlap comparison is incomplete; this is not zero",
            tone: "warning",
          };
        return {
          label: "Fresh",
          note: "Current potential overlap assessment is complete",
          tone: "active",
        };
      })
    : [];
  const assessmentPending = validationRuns.some(
    (query) => query.isPending && !query.data,
  );
  const assessmentCounts = assessments.reduce(
    (acc, item) => {
      acc[item.label] = (acc[item.label] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <div className="dashboard-page">
      <header className="page-heading dashboard-heading">
        <div>
          <p className="eyebrow">AICTE WORKSPACE</p>
          <h1>{isManager ? "Aggregate overview" : "Institution dashboard"}</h1>
          <p>
            {isManager
              ? "Institution-level aggregates only. Student submissions and evidence are not available to manager accounts."
              : "Compare current activated declarations and assessment freshness across permitted institutions."}
          </p>
        </div>
        <span className="status-badge neutral">Synthetic data</span>
      </header>
      <section className="panel dashboard-panel" aria-label="Dashboard filters">
        <DashboardFilters
          year={yearDraft}
          setYear={setYearDraft}
          onApply={() => {
            if (
              !/^\d{4}-\d{2}$/.test(yearDraft) ||
              Number(yearDraft.slice(-2)) !==
                (Number(yearDraft.slice(0, 4)) + 1) % 100
            ) {
              setFilterError(
                "Enter a consecutive academic year, for example 2026-27.",
              );
              return;
            }
            setFilterError("");
            setYear(yearDraft);
            setRegion(regionDraft);
            setInstitutionId(institutionDraft);
          }}
        >
          <label>
            Region
            <select
              value={regionDraft}
              onChange={(event) => {
                setRegionDraft(event.target.value);
                setInstitutionDraft("");
              }}
              disabled={institutions.isPending || institutions.isError}
            >
              <option value="">All regions</option>
              {regions.map((item) => (
                <option key={item} value={item}>
                  {prettyLabel(item)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Institution
            <select
              value={institutionDraft}
              onChange={(event) => setInstitutionDraft(event.target.value)}
              disabled={institutions.isPending || institutions.isError}
            >
              <option value="">All institutions</option>
              {allInstitutions
                .filter((item) => !regionDraft || item.region === regionDraft)
                .map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
            </select>
          </label>
        </DashboardFilters>
        {filterError && (
          <p className="form-error" role="alert">
            {filterError}
          </p>
        )}
      </section>
      {institutions.isPending ? (
        <Loading label="Loading permitted institutions…" />
      ) : institutions.isError ? (
        <ErrorPanel
          error={institutions.error}
          retry={() => void institutions.refetch()}
        />
      ) : !validYear ? (
        <div className="empty-state">
          <h2>Apply a valid academic year</h2>
          <p>Dashboard metrics require a consecutive academic year.</p>
        </div>
      ) : visibleInstitutions.length === 0 ? (
        <div className="empty-state">
          <h2>No institutions match these filters</h2>
          <p>Change the institution or region filter.</p>
        </div>
      ) : (
        <>
          <section
            className="dashboard-metrics"
            aria-label="Current institution aggregates"
            aria-busy={pendingSummaries}
          >
            <MetricCard
              label="Current declared records"
              value={
                pendingSummaries
                  ? "Loading"
                  : allNoDeclarations
                    ? "No declarations"
                    : successfulSummaries.length === 0
                      ? "Unavailable"
                      : displayCount(totals.declared)
              }
              note={
                failedSummaries.length
                  ? "Partial result; some institution summaries failed"
                  : "Activated snapshots only; historical and candidate uploads excluded"
              }
            />
            <MetricCard
              label="Active enrolments"
              value={
                pendingSummaries
                  ? "Loading"
                  : allNoDeclarations
                    ? "No declarations"
                    : successfulSummaries.length === 0
                      ? "Unavailable"
                      : displayCount(totals.active)
              }
              note="Internal status accounting, not official policy"
            />
            <MetricCard
              label="Programme declaration coverage"
              value={
                pendingSummaries
                  ? "Loading"
                  : successfulSummaries.length === 0
                    ? "Unavailable"
                    : `${totals.covered.toLocaleString()} / ${totals.programmes.toLocaleString()}`
              }
              note={
                failedSummaries.length
                  ? "Coverage among successful summaries only"
                  : "Missing declarations remain separate from zero counts"
              }
            />
            {isOfficer ? (
              <MetricCard
                label="Current assessment freshness"
                value={
                  assessmentPending || historyLoading
                    ? "Loading"
                    : historyErrors
                      ? "Partial / unavailable"
                      : currentBatches.length === 0
                        ? "No current snapshots"
                        : `${assessmentCounts.Fresh ?? 0} fresh · ${(assessmentCounts.Stale ?? 0) + (assessmentCounts.Incomplete ?? 0)} stale / incomplete`
                }
                note={
                  historyErrors
                    ? `${historyErrors} institution histories unavailable; assessment coverage is incomplete`
                    : `${assessmentCounts.Unavailable ?? 0} unavailable assessment(s); unavailable overlap metrics are never zero`
                }
              />
            ) : (
              <MetricCard
                label="Institutions in view"
                value={visibleInstitutions.length.toLocaleString()}
                note="Institution metadata and aggregate declarations only"
              />
            )}
          </section>
          {failedSummaries.length > 0 && (
            <div className="dashboard-partial" role="status">
              Some institution summaries could not be loaded. Totals and
              coverage include only successfully returned summaries; unavailable
              values are not treated as zero.
            </div>
          )}
          {historyErrors > 0 && (
            <div className="dashboard-partial" role="status">
              Some submission histories could not be checked. Current assessment
              freshness is incomplete.
            </div>
          )}
          <div className="dashboard-grid">
            <section className="panel" aria-labelledby="aicte-category-title">
              <header className="panel-heading">
                <div>
                  <p className="eyebrow">CURRENT DECLARATIONS</p>
                  <h2 id="aicte-category-title">Category distribution</h2>
                </div>
                <span className="status-badge neutral">Local accounting</span>
              </header>
              {pendingSummaries ? (
                <Loading label="Loading category totals…" />
              ) : successfulSummaries.length === 0 ? (
                <p className="chart-empty">
                  Category totals are unavailable because no summaries loaded.
                </p>
              ) : (
                <CategoryBars
                  categories={Object.keys(categoryTotals).map((key) => ({
                    label: prettyLabel(key),
                    value: categoryTotals[key],
                  }))}
                  emptyLabel="No current declarations are available across this selection."
                />
              )}
              {!pendingSummaries && statusTotal > 0 && (
                <>
                  <h3 className="chart-subheading">Status breakdown</h3>
                  <StatusDonut statuses={statusData} total={statusTotal} />
                </>
              )}
              {failedSummaries.length > 0 && successfulSummaries.length > 0 && (
                <p className="partial-note">
                  Category totals include successful institution summaries only.
                </p>
              )}
            </section>
            <section className="panel" aria-labelledby="aicte-coverage-title">
              <header className="panel-heading">
                <div>
                  <p className="eyebrow">DECLARATION COVERAGE</p>
                  <h2 id="aicte-coverage-title">
                    Institution/programme comparison
                  </h2>
                </div>
                <span className="quiet-label">Current snapshots only</span>
              </header>
              {pendingSummaries ? (
                <Loading label="Loading institution summaries…" />
              ) : (
                <DashboardTable label="Institution declaration and category comparison">
                  <thead>
                    <tr>
                      <th scope="col">Institution</th>
                      <th scope="col">Region</th>
                      <th scope="col">Coverage</th>
                      <th scope="col">Declared</th>
                      <th scope="col">Active</th>
                      <th scope="col">Categories</th>
                      {isOfficer && <th scope="col">Assessment</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {visibleInstitutions.map((item, index) => {
                      const result = summaries[index];
                      const data = result?.data;
                      const coverage = valueObject(data?.coverage);
                      const institutionCategories: Record<
                        string,
                        { declared: number; active: number }
                      > = {};
                      for (const program of data?.data ?? [])
                        for (const [key, raw] of Object.entries(
                          valueObject(
                            valueObject(program.counts)?.categories,
                          ) ?? {},
                        )) {
                          institutionCategories[key] ??= {
                            declared: 0,
                            active: 0,
                          };
                          institutionCategories[key].declared +=
                            countValue(valueObject(raw)?.declared_records) ?? 0;
                          institutionCategories[key].active +=
                            countValue(valueObject(raw)?.demo_active_records) ??
                            0;
                        }
                      const current = coverage?.status !== "NONE" && !!data;
                      const historyIndex = visibleInstitutions.findIndex(
                        (candidate) => candidate.id === item.id,
                      );
                      const history = historyQueries[historyIndex];
                      const currentForInstitution = (
                        history?.data ?? []
                      ).filter((batch) => batch.snapshot_state === "CURRENT");
                      const assessmentRows = currentForInstitution.map(
                        (batch) => {
                          const position = currentBatches.findIndex(
                            (candidate) => candidate.id === batch.id,
                          );
                          return assessments[position];
                        },
                      );
                      const freshness = !isOfficer
                        ? null
                        : history?.isError
                          ? {
                              label: "Unavailable",
                              note: "History unavailable",
                              tone: "neutral" as const,
                            }
                          : history?.isPending
                            ? {
                                label: "Loading",
                                note: "Checking current snapshots",
                                tone: "neutral" as const,
                              }
                            : currentForInstitution.length === 0
                              ? {
                                  label: current
                                    ? "Unavailable"
                                    : "No current scope",
                                  note: current
                                    ? "Summary and history do not identify a current batch"
                                    : "No current declaration",
                                  tone: "neutral" as const,
                                }
                              : assessmentRows.some(
                                    (row) => row?.label === "Stale",
                                  )
                                ? {
                                    label: "Stale",
                                    note: "At least one current assessment is stale",
                                    tone: "warning" as const,
                                  }
                                : assessmentRows.some(
                                      (row) =>
                                        row?.label === "Incomplete" ||
                                        row?.label === "Unavailable",
                                    )
                                  ? {
                                      label: "Incomplete / unavailable",
                                      note: "At least one current comparison is incomplete",
                                      tone: "warning" as const,
                                    }
                                  : assessmentRows.some(
                                        (row) => row?.label === "Loading",
                                      )
                                    ? {
                                        label: "Loading",
                                        note: "Checking current assessments",
                                        tone: "neutral" as const,
                                      }
                                    : {
                                        label: "Fresh",
                                        note: "All available current assessments are fresh",
                                        tone: "active" as const,
                                      };
                      return (
                        <tr key={item.id}>
                          <th scope="row">
                            <Link
                              href={`/aicte/institutions/${item.id}`}
                              aria-label={`View ${item.name}`}
                            >
                              {item.name}
                            </Link>
                          </th>
                          <td>{prettyLabel(item.region)}</td>
                          <td>
                            {result?.isError ? (
                              <span className="status-badge warning">
                                Unavailable
                              </span>
                            ) : data ? (
                              <CoverageBadge
                                status={String(coverage?.status ?? "NONE")}
                              />
                            ) : (
                              <span>Loading</span>
                            )}
                            <small>
                              {data
                                ? `${displayCount(coverage?.with_current_snapshot)} / ${displayCount(coverage?.programmes)} programmes`
                                : result?.isError
                                  ? "Summary failed"
                                  : ""}
                            </small>
                          </td>
                          <td>
                            {result?.isError
                              ? "Unavailable"
                              : data && coverage?.status === "NONE"
                                ? "No declaration"
                                : displayCount(
                                    valueObject(data?.totals)?.declared_records,
                                  )}
                          </td>
                          <td>
                            {result?.isError
                              ? "Unavailable"
                              : data && coverage?.status === "NONE"
                                ? "No declaration"
                                : displayCount(
                                    valueObject(data?.totals)
                                      ?.demo_active_records,
                                  )}
                          </td>
                          <td>
                            {Object.keys(institutionCategories).length
                              ? Object.entries(institutionCategories)
                                  .map(
                                    ([key, value]) =>
                                      `${prettyLabel(key)} ${value.declared.toLocaleString()} declared · ${value.active.toLocaleString()} active`,
                                  )
                                  .join(" · ")
                              : data && coverage?.status === "NONE"
                                ? "No declaration"
                                : "Unavailable"}
                          </td>
                          {isOfficer && (
                            <td>
                              <span
                                className={`status-badge ${freshness?.tone ?? "neutral"}`}
                              >
                                {freshness?.label ?? "Unavailable"}
                              </span>
                              <small>{freshness?.note}</small>
                            </td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </DashboardTable>
              )}
            </section>
          </div>
          <section className="panel dashboard-note-panel">
            <h2>
              {isManager
                ? "Aggregate access boundary"
                : "Assessment interpretation"}
            </h2>
            {isManager ? (
              <p>
                This view uses institution metadata and aggregate summary
                responses only. Student submissions, student identifiers,
                findings and validation evidence are not requested for manager
                sessions.
              </p>
            ) : (
              <p>
                Freshness describes whether the local potential-overlap
                assessment reflects the current activated snapshots. Stale,
                incomplete or unavailable assessments are labeled explicitly;
                they are never presented as zero overlaps. Potential matches are
                not fraud determinations.
              </p>
            )}
            <p>
              Counts use current activated declarations only. Intake comparisons
              are configured local rules, not official AICTE compliance
              decisions.
            </p>
          </section>
        </>
      )}
      <p className="data-note">
        API-backed synthetic institutional data only. No government APAAR/ABC
        verification is shown.
      </p>
    </div>
  );
}
