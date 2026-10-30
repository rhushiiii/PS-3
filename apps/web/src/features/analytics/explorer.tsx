"use client";

import Link from "next/link";
import { useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { validAcademicYear } from "@/features/submissions/data";
import type { components } from "@/lib/api/generated";
import {
  CategoryBars,
  DashboardTable,
  MetricCard,
  prettyLabel,
} from "@/features/dashboards/components";
import { useInstitutionOptions } from "@/features/institutions/options";

type Schemas = components["schemas"];
type Trends = Schemas["TrendsResponse"];
type Completeness = Schemas["CompletenessResponse"];
type Utilisation = Schemas["UtilisationResponse"];
type CasePerf = Schemas["CasePerformanceResponse"];
type Common = {
  as_of: string;
  coverage: Schemas["CoverageCounts"];
  notice: string;
  source_label: "DEMO";
  pagination: Schemas["Pagination"];
};

const TABS = [
  { id: "trends", label: "Enrolment trends" },
  { id: "completeness", label: "Completeness & freshness" },
  { id: "utilisation", label: "Intake utilisation" },
  { id: "cases", label: "Case performance" },
] as const;
type TabId = (typeof TABS)[number]["id"];
type GroupBy = Trends["group_by"];
const PAGE_SIZE = 25;
const NO_DATA = "No data";

type Filters = {
  year: string;
  institution: string;
  region: string;
  priority: string;
  severity: string;
};
const EMPTY: Filters = {
  year: "",
  institution: "",
  region: "",
  priority: "",
  severity: "",
};

function num(value: number | null | undefined, suffix = ""): string {
  return value === null || value === undefined
    ? NO_DATA
    : `${value.toLocaleString()}${suffix}`;
}

function when(value: string): string {
  return new Date(value).toLocaleString();
}

function Frame({
  query,
  page,
  setPage,
  children,
}: {
  query: {
    isPending: boolean;
    isError: boolean;
    isFetching: boolean;
    error: unknown;
    data: Common | undefined;
    refetch: () => unknown;
  };
  page: number;
  setPage: (page: number) => void;
  children: (data: Common) => ReactNode;
}) {
  const data = query.data;
  if (query.isPending) return <Loading label="Loading analytics…" />;
  if (query.isError || !data)
    return (
      <ErrorPanel error={query.error} retry={() => void query.refetch()} />
    );
  const { coverage } = data;
  return (
    <div className="analytics-stack">
      <div aria-live="polite">
        <p className="analytics-meta">
          <span>
            {coverage.institutions_with_current_snapshot} of{" "}
            {coverage.institutions_total} institutions have a current snapshot
          </span>
          <span>
            {coverage.programmes_with_current_snapshot} of{" "}
            {coverage.programmes_total} programmes
          </span>
          <span>
            As of <time dateTime={data.as_of}>{when(data.as_of)}</time>
          </span>
          <span>
            <span className="status-badge warning">
              {data.source_label === "DEMO" ? "SYNTHETIC / DEMO DATA" : ""}
            </span>
          </span>
        </p>
        <p className="data-note">{data.notice}</p>
      </div>
      {children(data)}
      {data.pagination.total > data.pagination.page_size && (
        <Pagination
          page={page}
          pageSize={data.pagination.page_size}
          total={data.pagination.total}
          busy={query.isFetching}
          change={setPage}
          label="Analytics pagination"
        />
      )}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="empty-state">
      <h3>No rows</h3>
      <p>{text}</p>
    </div>
  );
}

function InstitutionCell({
  id,
  name,
  officer,
}: {
  id: string;
  name: string;
  officer: boolean;
}) {
  // Managers keep an aggregate-only boundary: plain text, no drill-down.
  return officer ? (
    <Link href={`/aicte/institutions/${id}`}>{name}</Link>
  ) : (
    <>{name}</>
  );
}

export function AnalyticsExplorer() {
  const { session, request } = useSession();
  const officer = session?.user.role === "AICTE_OFFICER";
  const [tab, setTab] = useState<TabId>("trends");
  const [groupBy, setGroupBy] = useState<GroupBy>("academic_year");
  const [draft, setDraft] = useState<Filters>(EMPTY);
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [error, setError] = useState("");
  const [pages, setPages] = useState<Record<string, number>>({});
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const scope = ["private", session?.generation, session?.user.id, "analytics"];

  const institutions = useInstitutionOptions(
    [...scope, "institutions"],
    !!session,
  );
  const regions = [
    ...new Set((institutions.data?.data ?? []).map((i) => i.region)),
  ].sort();

  const page = pages[tab] ?? 1;
  const setPage = (value: number) => setPages((p) => ({ ...p, [tab]: value }));

  function params(extra: Record<string, string>) {
    const query = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
      ...extra,
    });
    if (tab !== "cases" && filters.year)
      query.set("academic_year", filters.year);
    if (filters.institution) query.set("institution_id", filters.institution);
    if (filters.region) query.set("region", filters.region);
    if (tab === "cases") {
      if (filters.priority) query.set("priority", filters.priority);
      if (filters.severity) query.set("severity", filters.severity);
    }
    return query;
  }
  const paths: Record<TabId, string> = {
    trends: `/analytics/enrolment-trends?${params({ group_by: groupBy })}`,
    completeness: `/analytics/submission-completeness?${params({})}`,
    utilisation: `/analytics/intake-utilisation?${params({})}`,
    cases: `/analytics/case-performance?${params({})}`,
  };
  const query = useQuery({
    queryKey: [...scope, tab, paths[tab]],
    enabled: !!session,
    queryFn: ({ signal }) => request<Common>(paths[tab], { signal }),
    // Each tab's response has a different shape (Trends/Completeness/
    // Utilisation/CasePerf) cast via the shared `Common` type below, so a
    // placeholder must only carry over within the same tab (smooth
    // pagination/filter changes) — never across a tab switch, or the new
    // tab's view renders the previous tab's data under its own shape.
    placeholderData: (previous, previousQuery) =>
      previousQuery?.queryKey[4] === tab ? previous : undefined,
  });

  function onTabKey(event: KeyboardEvent, index: number) {
    const move =
      event.key === "ArrowRight"
        ? 1
        : event.key === "ArrowLeft"
          ? -1
          : event.key === "Home"
            ? -index
            : event.key === "End"
              ? TABS.length - 1 - index
              : null;
    if (move === null) return;
    event.preventDefault();
    const next = (index + move + TABS.length) % TABS.length;
    setTab(TABS[next].id);
    tabRefs.current[next]?.focus();
  }

  function apply() {
    if (draft.year && !validAcademicYear(draft.year)) {
      setError("Enter a consecutive academic year, for example 2026-27.");
      return;
    }
    setError("");
    setFilters(draft);
    setPages({});
  }

  return (
    <div className="dashboard-page">
      <header className="page-heading">
        <p className="eyebrow">AICTE ANALYTICS</p>
        <h1>Analytics</h1>
        <p>
          Aggregate views over current activated declarations. Missing snapshots
          are shown as “{NO_DATA}”, never as zero.{" "}
          {!officer && "Manager accounts see aggregates only."}
        </p>
      </header>

      <section className="panel dashboard-panel" aria-label="Analytics filters">
        <form
          className="dashboard-filters"
          onSubmit={(event) => {
            event.preventDefault();
            apply();
          }}
        >
          {tab === "trends" && (
            <label>
              Group by
              <select
                value={groupBy}
                onChange={(e) => {
                  setGroupBy(e.target.value as GroupBy);
                  setPages({});
                }}
              >
                <option value="academic_year">Academic year</option>
                <option value="institution">Institution</option>
                <option value="programme">Programme</option>
                <option value="region">Region</option>
              </select>
            </label>
          )}
          {tab !== "cases" && (
            <label>
              Academic year
              <input
                value={draft.year}
                onChange={(e) => setDraft({ ...draft, year: e.target.value })}
                placeholder="All years, or 2026-27"
              />
            </label>
          )}
          <label>
            Institution
            <select
              value={draft.institution}
              onChange={(e) =>
                setDraft({ ...draft, institution: e.target.value })
              }
            >
              <option value="">All institutions</option>
              {(institutions.data?.data ?? []).map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Region
            <select
              value={draft.region}
              onChange={(e) => setDraft({ ...draft, region: e.target.value })}
            >
              <option value="">All regions</option>
              {regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          {tab === "cases" && (
            <>
              <label>
                Priority
                <select
                  value={draft.priority}
                  onChange={(e) =>
                    setDraft({ ...draft, priority: e.target.value })
                  }
                >
                  <option value="">Any priority</option>
                  {["LOW", "MEDIUM", "HIGH", "URGENT"].map((v) => (
                    <option key={v} value={v}>
                      {prettyLabel(v)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Severity
                <select
                  value={draft.severity}
                  onChange={(e) =>
                    setDraft({ ...draft, severity: e.target.value })
                  }
                >
                  <option value="">Any severity</option>
                  {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((v) => (
                    <option key={v} value={v}>
                      {prettyLabel(v)}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
          <button className="button secondary" type="submit">
            Apply filters
          </button>
          <button
            className="button secondary"
            type="button"
            onClick={() => {
              setDraft(EMPTY);
              setFilters(EMPTY);
              setError("");
              setPages({});
            }}
          >
            Clear
          </button>
        </form>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {institutions.isError && (
          <p className="form-error" role="alert">
            Institution and region options could not be loaded.
          </p>
        )}
      </section>

      <section className="panel" aria-label="Analytics results">
        <p>
          <Link
            href={`/reports?${new URLSearchParams(
              Object.entries({
                academic_year: filters.year,
                institution_id: filters.institution,
                region: filters.region,
              }).filter(([, v]) => v),
            )}`}
          >
            Download report
          </Link>
        </p>
        <div className="tab-list" role="tablist" aria-label="Analytics views">
          {TABS.map((item, index) => (
            <button
              key={item.id}
              ref={(node) => {
                tabRefs.current[index] = node;
              }}
              role="tab"
              id={`tab-${item.id}`}
              aria-selected={tab === item.id}
              aria-controls="analytics-panel"
              tabIndex={tab === item.id ? 0 : -1}
              onClick={() => setTab(item.id)}
              onKeyDown={(e) => onTabKey(e, index)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div
          role="tabpanel"
          id="analytics-panel"
          aria-labelledby={`tab-${tab}`}
          tabIndex={0}
        >
          <Frame query={query} page={page} setPage={setPage}>
            {(data) => {
              switch (tab) {
                case "trends":
                  return <TrendsView data={data as Trends} officer={officer} />;
                case "completeness":
                  return (
                    <CompletenessView
                      data={data as Completeness}
                      officer={officer}
                    />
                  );
                case "utilisation":
                  return (
                    <UtilisationView
                      data={data as Utilisation}
                      officer={officer}
                    />
                  );
                case "cases":
                  return (
                    <CasesView data={data as CasePerf} officer={officer} />
                  );
              }
            }}
          </Frame>
        </div>
      </section>
      <p className="data-note">
        Analytics are computed from synthetic demo records. Figures are review
        aids, not fraud determinations or official APAAR verification.
      </p>
    </div>
  );
}

function trendLabel(row: Schemas["TrendRow"], by: GroupBy): string {
  switch (by) {
    case "institution":
      return `${row.institution_name ?? "Institution"} · ${row.academic_year}`;
    case "programme":
      return `${row.programme_code ?? "Programme"} · ${row.academic_year}`;
    case "region":
      return `${row.region ?? "Region"} · ${row.academic_year}`;
    default:
      return row.academic_year;
  }
}

function TrendsView({ data, officer }: { data: Trends; officer: boolean }) {
  if (data.data.length === 0)
    return <Empty text="No rows match these filters." />;
  return (
    <>
      <CategoryBars
        categories={data.data.map((row) => ({
          label: trendLabel(row, data.group_by),
          value: row.active_records,
        }))}
        emptyLabel="No current snapshots to chart. See the table for status."
      />
      <DashboardTable label="Enrolment trends table">
        <caption className="sr-only">
          Active records and declared totals by {data.group_by}. Rows without a
          current snapshot show “{NO_DATA}”.
        </caption>
        <thead>
          <tr>
            <th scope="col">Group</th>
            <th scope="col">Status</th>
            <th scope="col">Active records</th>
            <th scope="col">Declared</th>
            <th scope="col">Unclassified active</th>
            <th scope="col">Categories (active / declared)</th>
            <th scope="col">Programmes with snapshot</th>
          </tr>
        </thead>
        <tbody>
          {data.data.map((row, index) => (
            <tr key={`${trendLabel(row, data.group_by)}-${index}`}>
              <th scope="row">
                {row.institution_id && row.institution_name ? (
                  <>
                    <InstitutionCell
                      id={row.institution_id}
                      name={row.institution_name}
                      officer={officer}
                    />
                    <small> {row.academic_year}</small>
                  </>
                ) : (
                  trendLabel(row, data.group_by)
                )}
              </th>
              <td>
                <span
                  className={`status-badge ${row.status === "COMPLETE" ? "active" : row.status === "PARTIAL" ? "warning" : "neutral"}`}
                >
                  {row.status === "NO_CURRENT_SNAPSHOT"
                    ? "No current snapshot"
                    : prettyLabel(row.status)}
                </span>
              </td>
              <td>{num(row.active_records)}</td>
              <td>{num(row.declared_records)}</td>
              <td>{num(row.unclassified_active_records)}</td>
              <td>
                {row.categories
                  ? Object.entries(row.categories)
                      .map(
                        ([k, v]) =>
                          `${prettyLabel(k)} ${v.active_records}/${v.declared_records}`,
                      )
                      .join(", ") || NO_DATA
                  : NO_DATA}
              </td>
              <td>
                {row.programmes_with_current_snapshot} of {row.programmes_total}
              </td>
            </tr>
          ))}
        </tbody>
      </DashboardTable>
    </>
  );
}

function CompletenessView({
  data,
  officer,
}: {
  data: Completeness;
  officer: boolean;
}) {
  const tone = {
    FRESH: "active",
    STALE: "warning",
    NO_CURRENT_SNAPSHOT: "neutral",
  };
  const text = {
    FRESH: "Fresh",
    STALE: "Stale",
    NO_CURRENT_SNAPSHOT: "Missing",
  };
  return (
    <>
      <p className="data-note">
        A snapshot is stale after {data.stale_after_days} days without
        activation.
      </p>
      {data.data.length === 0 ? (
        <Empty text="No rows match these filters." />
      ) : (
        <DashboardTable label="Submission completeness table">
          <caption className="sr-only">
            Declared versus current records and freshness per institution
            programme.
          </caption>
          <thead>
            <tr>
              <th scope="col">Institution</th>
              <th scope="col">Programme</th>
              <th scope="col">Freshness</th>
              <th scope="col">Declared total</th>
              <th scope="col">Current records</th>
              <th scope="col">Shortfall</th>
              <th scope="col">Pending candidates</th>
              <th scope="col">Last activated</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((row) => (
              <tr
                key={`${row.institution_id}-${row.programme_id}-${row.academic_year}`}
              >
                <th scope="row">
                  <InstitutionCell
                    id={row.institution_id}
                    name={row.institution_name}
                    officer={officer}
                  />
                  <small> {row.region}</small>
                </th>
                <td>
                  {row.programme_code}
                  <small> {row.academic_year ?? ""}</small>
                </td>
                <td>
                  <span
                    className={`status-badge ${tone[row.freshness_status]}`}
                  >
                    {text[row.freshness_status]}
                  </span>
                  {row.freshness_days !== null && (
                    <small> {row.freshness_days} days</small>
                  )}
                </td>
                <td>
                  {row.has_declaration ? num(row.declared_total) : NO_DATA}
                </td>
                <td>
                  {row.has_current_snapshot
                    ? num(row.current_declared_records)
                    : NO_DATA}
                </td>
                <td>{row.shortfall === null ? "—" : num(row.shortfall)}</td>
                <td>{row.pending_candidate_count}</td>
                <td>
                  {row.last_activated_at
                    ? when(row.last_activated_at)
                    : NO_DATA}
                </td>
              </tr>
            ))}
          </tbody>
        </DashboardTable>
      )}
      <h3>Region rollup</h3>
      {data.rollups_by_region.length === 0 ? (
        <Empty text="No regional rollup available." />
      ) : (
        <DashboardTable label="Region rollup table">
          <thead>
            <tr>
              <th scope="col">Region</th>
              <th scope="col">Institutions</th>
              <th scope="col">Programme-years</th>
              <th scope="col">With declaration</th>
              <th scope="col">With current snapshot</th>
              <th scope="col">Stale</th>
              <th scope="col">With shortfall</th>
              <th scope="col">Pending candidates</th>
            </tr>
          </thead>
          <tbody>
            {data.rollups_by_region.map((row) => (
              <tr key={row.region}>
                <th scope="row">{row.region}</th>
                <td>{row.institutions_total}</td>
                <td>{row.programme_years_total}</td>
                <td>{row.with_declaration}</td>
                <td>{row.with_current_snapshot}</td>
                <td>{row.stale}</td>
                <td>{row.with_shortfall}</td>
                <td>{row.pending_candidates}</td>
              </tr>
            ))}
          </tbody>
        </DashboardTable>
      )}
    </>
  );
}

function UtilisationView({
  data,
  officer,
}: {
  data: Utilisation;
  officer: boolean;
}) {
  const statusText = {
    OK: "Rule applied",
    NO_RULE: "No intake rule",
    NO_CURRENT_SNAPSHOT: "No current snapshot",
  };
  return (
    <>
      <p className="data-note">
        {data.pooling_note} Rule version in use: {data.rule_version_in_use}.
      </p>
      {data.data.length === 0 ? (
        <Empty text="No rows match these filters." />
      ) : (
        <DashboardTable label="Intake utilisation table">
          <caption className="sr-only">
            Approved capacity versus current records per programme and seat
            category.
          </caption>
          <thead>
            <tr>
              <th scope="col">Institution</th>
              <th scope="col">Programme / category</th>
              <th scope="col">Status</th>
              <th scope="col">Approved</th>
              <th scope="col">Current</th>
              <th scope="col">Utilisation</th>
              <th scope="col">Remaining</th>
              <th scope="col">Exceeded</th>
              <th scope="col">Calculation</th>
            </tr>
          </thead>
          <tbody>
            {data.data.map((row) => (
              <tr
                key={`${row.institution_id}-${row.programme_id}-${row.academic_year}-${row.category}`}
              >
                <th scope="row">
                  <InstitutionCell
                    id={row.institution_id}
                    name={row.institution_name}
                    officer={officer}
                  />
                </th>
                <td>
                  {row.programme_code} · {prettyLabel(row.category)}
                  <small> {row.academic_year}</small>
                </td>
                <td>
                  <span
                    className={`status-badge ${row.status === "OK" ? "active" : "neutral"}`}
                  >
                    {statusText[row.status]}
                  </span>
                </td>
                <td>{num(row.approved_seats)}</td>
                <td>{num(row.current_active)}</td>
                <td>{num(row.utilisation_pct, "%")}</td>
                <td>{num(row.remaining_capacity)}</td>
                <td>
                  {row.exceeded === null ? (
                    "—"
                  ) : row.exceeded ? (
                    <span className="status-badge warning">
                      Exceeded by {row.excess ?? 0}
                    </span>
                  ) : (
                    <span className="status-badge active">Within capacity</span>
                  )}
                </td>
                <td>{row.calculation}</td>
              </tr>
            ))}
          </tbody>
        </DashboardTable>
      )}
    </>
  );
}

function CasesView({ data, officer }: { data: CasePerf; officer: boolean }) {
  const { totals } = data;
  return (
    <>
      <div className="dashboard-metrics">
        <MetricCard label="All cases" value={totals.all} note="In scope" />
        <MetricCard label="Open" value={totals.open} note="Not yet closed" />
        <MetricCard
          label="Overdue"
          value={totals.overdue}
          note="Past due date"
        />
        <MetricCard
          label="Escalated"
          value={totals.escalated}
          note="Escalated cases"
        />
      </div>

      <h3>Ageing of open cases</h3>
      <CategoryBars
        categories={data.ageing.map((b) => ({
          label: `${b.bucket} days`,
          value: b.count,
        }))}
        emptyLabel="No open cases to chart."
      />
      <DashboardTable label="Ageing buckets table">
        <caption className="sr-only">Open cases by age in days.</caption>
        <thead>
          <tr>
            <th scope="col">Age (days)</th>
            <th scope="col">Cases</th>
            {officer && <th scope="col">Queue</th>}
          </tr>
        </thead>
        <tbody>
          {data.ageing.map((b) => (
            <tr key={b.bucket}>
              <th scope="row">{b.bucket}</th>
              <td>{b.count}</td>
              {officer && (
                <td>
                  <Link href={`/cases?min_age_days=${b.min_days}`}>
                    Cases aged {b.min_days}+ days
                  </Link>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </DashboardTable>

      <h3>By status</h3>
      <DashboardTable label="Cases by status table">
        <thead>
          <tr>
            <th scope="col">Status</th>
            <th scope="col">Total</th>
            <th scope="col">Overdue</th>
            <th scope="col">Escalated</th>
          </tr>
        </thead>
        <tbody>
          {data.by_status.map((s) => (
            <tr key={s.status}>
              <th scope="row">
                {officer ? (
                  <Link href={`/cases?status=${s.status}`}>
                    {prettyLabel(s.status)}
                  </Link>
                ) : (
                  prettyLabel(s.status)
                )}
              </th>
              <td>{s.total}</td>
              <td>{s.overdue}</td>
              <td>{s.escalated}</td>
            </tr>
          ))}
        </tbody>
      </DashboardTable>

      <h3>Resolution time by priority</h3>
      <p className="data-note">{data.p90_method}</p>
      <DashboardTable label="Resolution statistics table">
        <thead>
          <tr>
            <th scope="col">Priority</th>
            <th scope="col">Resolved</th>
            <th scope="col">Mean days</th>
            <th scope="col">Median days</th>
            <th scope="col">P90 days</th>
          </tr>
        </thead>
        <tbody>
          {data.resolution_days.map((r) => (
            <tr key={r.priority}>
              <th scope="row">{prettyLabel(r.priority)}</th>
              <td>{r.resolved_count}</td>
              <td>{num(r.mean_days)}</td>
              <td>{num(r.median_days)}</td>
              <td>{num(r.p90_days)}</td>
            </tr>
          ))}
        </tbody>
      </DashboardTable>

      <h3>By institution</h3>
      {data.data.length === 0 ? (
        <Empty text="No institutions match these filters." />
      ) : (
        <DashboardTable label="Cases by institution table">
          <thead>
            <tr>
              <th scope="col">Institution</th>
              <th scope="col">Region</th>
              <th scope="col">Open</th>
              <th scope="col">Overdue</th>
              <th scope="col">Resolved</th>
              {officer && <th scope="col">Queue</th>}
            </tr>
          </thead>
          <tbody>
            {data.data.map((row) => (
              <tr key={row.institution_id}>
                <th scope="row">
                  <InstitutionCell
                    id={row.institution_id}
                    name={row.institution_name}
                    officer={officer}
                  />
                </th>
                <td>{row.region}</td>
                <td>{row.open}</td>
                <td>{row.overdue}</td>
                <td>{row.resolved}</td>
                {officer && (
                  <td>
                    <Link href={`/cases?institution_id=${row.institution_id}`}>
                      View cases
                    </Link>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </DashboardTable>
      )}
    </>
  );
}
