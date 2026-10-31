"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { useSession } from "@/features/auth/session";
import { DeclaredTotalsPanel } from "@/features/intake/declarations-panel";
import { IntegritySignalsPanel } from "@/features/integrity/panel";
import { SimulatorPanel } from "@/features/intake/simulator-panel";
import { validAcademicYear } from "@/features/submissions/data";
import { isUUID } from "@/lib/api/client";
import type { components, paths } from "@/lib/api/generated";
import {
  CategoryBars,
  CoverageBadge,
  DashboardFilters,
  DashboardTable,
  DashboardTableRow,
  MetricCard,
  StatusDonut,
  countValue,
  displayCount,
  prettyLabel,
  valueObject,
} from "./components";

type Summary = components["schemas"]["InstitutionSummary"];
type Institution = components["schemas"]["InstitutionResponse"];
type Programmes =
  paths["/api/v1/institutions/{institution_id}/programmes"]["get"]["responses"][200]["content"]["application/json"];
type Intake =
  paths["/api/v1/institutions/{institution_id}/intake"]["get"]["responses"][200]["content"]["application/json"];
type History =
  paths["/api/v1/submissions"]["get"]["responses"][200]["content"]["application/json"];

type CasePage =
  paths["/api/v1/cases"]["get"]["responses"][200]["content"]["application/json"];

const dashboardYear = "2026-27";

function CorrectionRequestsCard() {
  const { session, request } = useSession();
  const key = [
    "private",
    session?.generation,
    session?.user.id,
    "correction-requests",
  ];
  const count = (overdue: boolean) =>
    request<CasePage>(
      `/cases?status=AWAITING_CORRECTION&page=1&page_size=1${overdue ? "&overdue=true" : ""}`,
    );
  const open = useQuery({
    queryKey: [...key, "open"],
    enabled: !!session,
    queryFn: () => count(false),
  });
  const overdue = useQuery({
    queryKey: [...key, "overdue"],
    enabled: !!session,
    queryFn: () => count(true),
  });
  const hasOverdue = (overdue.data?.pagination.total ?? 0) > 0;
  return (
    <section
      className={`panel dashboard-panel ${hasOverdue ? "panel-critical-alert" : ""}`}
      aria-labelledby="correction-requests-title"
    >
      <div className="panel-header-inline">
        <h2 id="correction-requests-title">Open correction requests</h2>
        {hasOverdue && (
          <span className="status-badge danger">
            Action required · Overdue cases
          </span>
        )}
      </div>
      <div aria-live="polite">
        {open.isPending ? (
          <Loading label="Loading correction requests…" />
        ) : open.isError ? (
          <ErrorPanel error={open.error} retry={() => void open.refetch()} />
        ) : (
          <p className="correction-summary-text">
            <strong>{open.data.pagination.total.toLocaleString()}</strong> case
            {open.data.pagination.total === 1 ? "" : "s"} awaiting your
            correction
            {overdue.data ? (
              hasOverdue ? (
                <>
                  {" · "}
                  <span className="overdue-highlight">
                    {overdue.data.pagination.total.toLocaleString()} overdue
                  </span>
                </>
              ) : (
                ` · 0 overdue`
              )
            ) : overdue.isError ? (
              " · overdue count unavailable"
            ) : (
              ""
            )}
            .
          </p>
        )}
      </div>
      <p className="card-quick-links">
        <Link href="/cases?status=AWAITING_CORRECTION" className="quick-link-primary">
          View correction requests →
        </Link>
        <span className="divider-dot">·</span>
        <Link href="/records" className="quick-link-secondary">
          Student registry
        </Link>
      </p>
    </section>
  );
}

export function InstitutionDashboard({
  institutionId,
}: {
  institutionId: string;
}) {
  const { session, request } = useSession();
  const [yearDraft, setYearDraft] = useState(dashboardYear);
  const [year, setYear] = useState(dashboardYear);
  const [programmeDraft, setProgrammeDraft] = useState("");
  const [programmeId, setProgrammeId] = useState("");
  const [filterError, setFilterError] = useState("");
  const valid = isUUID(institutionId);
  const baseKey = [
    "private",
    session?.generation,
    session?.user.id,
    "institution-dashboard",
    institutionId,
  ];
  const institution = useQuery({
    queryKey: [...baseKey, "metadata"],
    enabled: !!session && valid,
    queryFn: ({ signal }) =>
      request<Institution>(`/institutions/${institutionId}`, { signal }),
  });
  const programmes = useQuery({
    queryKey: [...baseKey, "programmes"],
    enabled: !!session && valid,
    queryFn: ({ signal }) =>
      request<Programmes>(
        `/institutions/${institutionId}/programmes?page=1&page_size=100`,
        { signal },
      ),
  });
  const filtersValid = validAcademicYear(year);
  const filterParams = new URLSearchParams({
    academic_year: year,
    page: "1",
    page_size: "100",
  });
  if (programmeId) filterParams.set("programme_id", programmeId);
  const summary = useQuery({
    queryKey: [...baseKey, "summary", year, programmeId],
    enabled:
      !!session &&
      valid &&
      filtersValid &&
      (programmes.data?.data.length ?? 0) > 0,
    queryFn: ({ signal }) =>
      request<Summary>(
        `/institutions/${institutionId}/summary?${filterParams}`,
        { signal },
      ),
  });
  const intakeParams = new URLSearchParams({
    academic_year: year,
    page: "1",
    page_size: "100",
  });
  if (programmeId) intakeParams.set("programme_id", programmeId);
  const intake = useQuery({
    queryKey: [...baseKey, "intake", year, programmeId],
    enabled:
      !!session &&
      valid &&
      filtersValid &&
      (programmes.data?.data.length ?? 0) > 0,
    queryFn: ({ signal }) =>
      request<Intake>(`/institutions/${institutionId}/intake?${intakeParams}`, {
        signal,
      }),
  });
  const historyParams = new URLSearchParams({
    academic_year: year,
    page: "1",
    page_size: "5",
  });
  if (programmeId) historyParams.set("programme_id", programmeId);
  const submissions = useQuery({
    queryKey: [...baseKey, "recent-submissions", year, programmeId],
    enabled:
      !!session &&
      valid &&
      filtersValid &&
      (programmes.data?.data.length ?? 0) > 0,
    queryFn: ({ signal }) =>
      request<History>(`/submissions?${historyParams}`, { signal }),
  });

  const programmeNames = new Map(
    (programmes.data?.data ?? []).map((item) => [item.id, item.name]),
  );
  const counts = valueObject(summary.data?.totals);
  const coverage = valueObject(summary.data?.coverage);
  const coverageStatus =
    typeof coverage?.status === "string" ? coverage.status : "NONE";
  const summaryPrograms = summary.data?.data ?? [];
  const categoryKeys = Object.keys(valueObject(counts?.categories) ?? {});
  const categoryData = categoryKeys.map((key) => ({
    label: prettyLabel(key),
    value:
      coverageStatus === "NONE"
        ? null
        : countValue(
            valueObject(valueObject(counts?.categories)?.[key])
              ?.declared_records,
          ),
  }));
  const statusTotals = valueObject(counts?.statuses) ?? {};
  const statusData = Object.entries(statusTotals)
    .map(([label, value]) => ({ label, value: countValue(value) ?? 0 }))
    .filter((item) => item.value > 0);
  const statusTotal = statusData.reduce((sum, item) => sum + item.value, 0);
  const programById = new Map(
    summaryPrograms.map((item) => [item.programme_id, item]),
  );
  const intakeRows = intake.data?.data ?? [];

  if (!valid)
    return (
      <section className="empty-state">
        <h1>Dashboard unavailable</h1>
        <p>The institution reference is invalid.</p>
      </section>
    );

  return (
    <div className="dashboard-page">
      <header className="page-heading dashboard-heading">
        <div>
          <p className="eyebrow">INSTITUTION WORKSPACE</p>
          <h1>Institution dashboard</h1>
          <h2 className="dashboard-institution-name">
            {institution.data?.name ?? "Your institution"}
          </h2>
          <p>Current activated declarations for the selected academic year.</p>
        </div>
        <div className="dashboard-actions">
          <Link className="button primary" href="/institution/upload">
            ↑ Upload candidate batch
          </Link>
          <Link className="button secondary" href="/records">
            Student registry
          </Link>
          <Link className="button secondary" href="/submissions">
            Submissions history
          </Link>
        </div>
      </header>
      <CorrectionRequestsCard />
      {institution.isError && (
        <ErrorPanel
          error={institution.error}
          retry={() => void institution.refetch()}
        />
      )}

      <section className="panel dashboard-panel" aria-label="Dashboard filters">
        <DashboardFilters
          year={yearDraft}
          setYear={setYearDraft}
          onApply={() => {
            if (!validAcademicYear(yearDraft)) {
              setFilterError(
                "Enter a consecutive academic year, for example 2026-27.",
              );
              return;
            }
            setFilterError("");
            setYear(yearDraft);
            setProgrammeId(programmeDraft);
          }}
        >
          <label>
            Programme
            <select
              value={programmeDraft}
              onChange={(event) => setProgrammeDraft(event.target.value)}
              disabled={programmes.isPending || programmes.isError}
            >
              <option value="">All programmes</option>
              {(programmes.data?.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.code})
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
        {programmes.isError && (
          <ErrorPanel
            error={programmes.error}
            retry={() => void programmes.refetch()}
          />
        )}
      </section>

      {!filtersValid ? (
        <div className="empty-state">
          <h2>Apply a valid academic year</h2>
          <p>
            Current metrics are queried only for a valid consecutive academic
            year.
          </p>
        </div>
      ) : programmes.isPending ? (
        <Loading label="Loading programmes…" />
      ) : programmes.isError ? (
        <ErrorPanel
          error={programmes.error}
          retry={() => void programmes.refetch()}
        />
      ) : programmes.data.data.length === 0 ? (
        <div className="empty-state">
          <h2>No programmes found</h2>
          <p>
            No programme records are available for this institution dashboard.
          </p>
        </div>
      ) : summary.isPending ? (
        <Loading label="Loading current institution declaration…" />
      ) : summary.isError ? (
        <ErrorPanel
          error={summary.error}
          retry={() => void summary.refetch()}
        />
      ) : (
        <>
          <section
            className="dashboard-metrics"
            aria-label="Current declaration metrics"
            aria-busy={summary.isFetching}
          >
            <MetricCard
              label="Current declared records"
              value={
                coverageStatus === "NONE"
                  ? "No declaration"
                  : displayCount(counts?.declared_records)
              }
              note={
                coverageStatus === "PARTIAL"
                  ? "Available activated programme snapshots only"
                  : "Activated snapshots only; candidates and history excluded"
              }
              tone="neutral"
            />
            <MetricCard
              label="Active enrolments"
              value={
                coverageStatus === "NONE"
                  ? "No declaration"
                  : displayCount(counts?.demo_active_records)
              }
              note="Internal status accounting, not official policy"
              tone={coverageStatus !== "NONE" ? "success" : "neutral"}
            />
            <MetricCard
              label="Programme coverage"
              value={`${displayCount(coverage?.with_current_snapshot)} / ${displayCount(coverage?.programmes)}`}
              note={`${coverageStatus === "NONE" ? "No current declarations" : prettyLabel(coverageStatus)} · missing is not zero`}
              tone={
                coverageStatus === "PARTIAL"
                  ? "warning"
                  : coverageStatus === "COMPLETE"
                    ? "success"
                    : "neutral"
              }
            />
            <MetricCard
              label="Configured intake comparisons"
              value={
                coverageStatus === "NONE"
                  ? "Unavailable"
                  : intakeRows.length.toLocaleString()
              }
              note="Illustrative category rules; not official AICTE compliance"
              tone="neutral"
            />
          </section>
          <div className="dashboard-grid">
            <section
              className="panel"
              aria-labelledby="institution-category-title"
            >
              <header className="panel-heading">
                <div>
                  <p className="eyebrow">CURRENT DECLARATIONS</p>
                  <h2 id="institution-category-title">
                    Records by admission category
                  </h2>
                </div>
                <span className="status-badge neutral">Local accounting</span>
              </header>
              <CategoryBars
                categories={categoryData}
                emptyLabel="No current declarations are available for this scope."
              />
              {coverageStatus !== "NONE" && (
                <>
                  <h3 className="chart-subheading">Status breakdown</h3>
                  <StatusDonut statuses={statusData} total={statusTotal} />
                </>
              )}
              {coverageStatus === "PARTIAL" && (
                <p className="partial-note">
                  Totals include only programmes with an activated snapshot.
                  Other programmes have no declaration.
                </p>
              )}
            </section>
            <section
              className="panel"
              aria-labelledby="institution-coverage-title"
            >
              <header className="panel-heading">
                <div>
                  <p className="eyebrow">PROGRAMME STATUS</p>
                  <h2 id="institution-coverage-title">Declaration coverage</h2>
                </div>
                <CoverageBadge status={coverageStatus} />
              </header>
              <DashboardTable label="Programme declaration coverage">
                <thead>
                  <tr>
                    <th scope="col">Programme</th>
                    <th scope="col">Programme code</th>
                    <th scope="col">Status</th>
                    <th scope="col">Declared</th>
                    <th scope="col">Active</th>
                  </tr>
                </thead>
                <tbody>
                  {summaryPrograms.map((item, index) => {
                    const programCounts = valueObject(item.counts);
                    return (
                      <DashboardTableRow key={item.programme_id} index={index}>
                        <th scope="row">
                          {programmeNames.get(item.programme_id) ??
                            item.programme_code}
                        </th>
                        <td>{item.programme_code}</td>
                        <td>
                          {item.has_current_snapshot ? (
                            <span className="status-badge active">
                              Current declaration
                            </span>
                          ) : (
                            <span className="status-badge neutral">
                              No declaration
                            </span>
                          )}
                        </td>
                        <td className="numeral-strong">
                          {item.has_current_snapshot
                            ? displayCount(programCounts?.declared_records)
                            : "—"}
                        </td>
                        <td>
                          {item.has_current_snapshot
                            ? displayCount(programCounts?.demo_active_records)
                            : "—"}
                        </td>
                      </DashboardTableRow>
                    );
                  })}
                  {summaryPrograms.length === 0 && (
                    <tr>
                      <td colSpan={5}>No programmes match this filter.</td>
                    </tr>
                  )}
                </tbody>
              </DashboardTable>
            </section>
          </div>
          <section className="panel" aria-labelledby="intake-comparison-title">
            <header className="panel-heading">
              <div>
                <p className="eyebrow">CONFIGURED RULE COMPARISON</p>
                <h2 id="intake-comparison-title">
                  Category counts and configured intake
                </h2>
              </div>
              <span className="status-badge warning">
                Local rules · not official determinations
              </span>
            </header>
            {intake.isPending ? (
              <Loading label="Loading configured intake rules…" />
            ) : intake.isError ? (
              <ErrorPanel
                error={intake.error}
                retry={() => void intake.refetch()}
              />
            ) : intakeRows.length === 0 ? (
              <div className="empty-state compact">
                <h3>No intake configuration</h3>
                <p>
                  No configured rule was returned for this academic year and
                  programme selection.
                </p>
              </div>
            ) : (
              <DashboardTable label="Current category records compared with configured intake">
                <thead>
                  <tr>
                    <th scope="col">Programme</th>
                    <th scope="col">Category</th>
                    <th scope="col">Current declared</th>
                    <th scope="col">Active</th>
                    <th scope="col">Configured seats</th>
                    <th scope="col">Configured rule</th>
                  </tr>
                </thead>
                <tbody>
                  {intakeRows.map((rule) => {
                    const currentProgram = programById.get(rule.programme_id);
                    const category = valueObject(
                      valueObject(currentProgram?.counts)?.categories,
                    )?.[rule.category];
                    const declared = currentProgram?.has_current_snapshot
                      ? countValue(valueObject(category)?.declared_records)
                      : null;
                    const active = currentProgram?.has_current_snapshot
                      ? countValue(valueObject(category)?.demo_active_records)
                      : null;
                    return (
                      <tr key={rule.id}>
                        <th scope="row">
                          {programmeNames.get(rule.programme_id) ??
                            rule.programme_id}
                        </th>
                        <td>{prettyLabel(rule.category)}</td>
                        <td>
                          {currentProgram?.has_current_snapshot
                            ? displayCount(declared)
                            : "No current declaration"}
                        </td>
                        <td>
                          {currentProgram?.has_current_snapshot
                            ? displayCount(active)
                            : "No current declaration"}
                        </td>
                        <td>{rule.approved_seats.toLocaleString()}</td>
                        <td>
                          {rule.rule_version} · {rule.source_label}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </DashboardTable>
            )}
            <p className="data-note">
              These comparisons show declared records against configured
              capacities by programme and category. They do not establish an
              official AICTE violation.
            </p>
          </section>
          <section className="panel" aria-labelledby="recent-submissions-title">
            <header className="panel-heading">
              <div>
                <p className="eyebrow">TRACEABLE HISTORY</p>
                <h2 id="recent-submissions-title">Recent submissions</h2>
                <p className="cell-note">
                  Candidate uploads are not current until explicitly activated.
                </p>
              </div>
              <Link className="button secondary" href="/submissions">
                View submission history
              </Link>
            </header>
            {submissions.isPending ? (
              <Loading label="Loading recent submissions…" />
            ) : submissions.isError ? (
              <ErrorPanel
                error={submissions.error}
                retry={() => void submissions.refetch()}
              />
            ) : submissions.data.data.length === 0 ? (
              <div className="empty-state compact">
                <h3>No submissions for this filter</h3>
                <p>
                  Upload a complete candidate snapshot for the selected academic
                  year.
                </p>
              </div>
            ) : (
              <DashboardTable label="Recent institution submissions">
                <thead>
                  <tr>
                    <th scope="col">Received</th>
                    <th scope="col">Programme</th>
                    <th scope="col">Snapshot state</th>
                    <th scope="col">Processing</th>
                    <th scope="col">Next action</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.data.data.map((batch) => (
                    <tr key={batch.id}>
                      <td>
                        <time dateTime={batch.received_at}>
                          {new Date(batch.received_at).toLocaleString()}
                        </time>
                      </td>
                      <td>
                        {programmeNames.get(batch.programme_id) ??
                          batch.programme_id}
                        <small>{batch.academic_year}</small>
                      </td>
                      <td>
                        <span
                          className={`status-badge ${batch.snapshot_state === "CURRENT" ? "active" : batch.snapshot_state === "PREVIOUS" ? "neutral" : "warning"}`}
                        >
                          {prettyLabel(batch.snapshot_state)}
                        </span>
                      </td>
                      <td>{prettyLabel(batch.status)}</td>
                      <td>
                        <Link href={`/submissions/${batch.id}`}>
                          {batch.snapshot_state === "CANDIDATE"
                            ? "Continue candidate review"
                            : batch.snapshot_state === "CURRENT"
                              ? "View current declaration"
                              : "View previous version"}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </DashboardTable>
            )}
          </section>
        </>
      )}
      {valid && (
        <>
          <IntegritySignalsPanel
            institutionId={institutionId}
            canDecide={false}
          />
          <DeclaredTotalsPanel institutionId={institutionId} />
          <SimulatorPanel institutionId={institutionId} />
        </>
      )}
      <p className="data-note">
        All dashboard values come from the authenticated API and synthetic
        records. Historical uploads and unactivated candidates are excluded from
        current enrolment metrics.
      </p>
    </div>
  );
}
