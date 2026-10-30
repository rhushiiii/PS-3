"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Icon } from "@/components/ui/icon";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import type { components } from "@/lib/api/generated";
import {
  CASE_PRIORITIES,
  CASE_SEVERITIES,
  CASE_STATUSES,
  CaseBadges,
  statusLabel,
  statusTone,
  titleCase,
  type CasePriority,
  type CaseSeverity,
  type CaseStatus,
} from "./shared";

type CasePage = components["schemas"]["Page_CaseResponse_"];
type Assignee = components["schemas"]["AssigneeResponse"];
type InstitutionPage = components["schemas"]["Page_InstitutionResponse_"];

type Filters = {
  status: CaseStatus | "";
  priority: CasePriority | "";
  severity: CaseSeverity | "";
  overdue: boolean;
  assignee: string;
  institution: string;
  minAge: string;
};
const NO_FILTERS: Filters = {
  status: "",
  priority: "",
  severity: "",
  overdue: false,
  assignee: "",
  institution: "",
  minAge: "",
};

/** Minimal deep-link support: ?status=&overdue=true&institution_id=. */
function initialFilters(search: URLSearchParams): Filters {
  const status = search.get("status");
  const institution = search.get("institution_id") ?? "";
  return {
    ...NO_FILTERS,
    status: (CASE_STATUSES as readonly string[]).includes(status ?? "")
      ? (status as CaseStatus)
      : "",
    overdue: search.get("overdue") === "true",
    minAge: /^\d{1,4}$/.test(search.get("min_age_days") ?? "")
      ? (search.get("min_age_days") as string)
      : "",
    institution: /^[0-9a-f-]{36}$/i.test(institution) ? institution : "",
  };
}

export function CaseQueue() {
  const { session, request } = useSession();
  const search = useSearchParams();
  const [filters, setFilters] = useState<Filters>(() => initialFilters(search));
  const [page, setPage] = useState(1);
  const officer = session?.user.role === "AICTE_OFFICER";
  const scope = ["private", session?.generation, session?.user.id];
  const hasFilters = JSON.stringify(filters) !== JSON.stringify(NO_FILTERS);
  const update = <K extends keyof Filters>(key: K, value: Filters[K]) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  };

  const assignees = useQuery({
    queryKey: [...scope, "cases", "assignees"],
    enabled: !!session && officer,
    queryFn: ({ signal }) =>
      request<Assignee[]>("/cases/assignees", { signal }),
  });
  const institutions = useQuery({
    queryKey: [...scope, "institutions", "filter-options"],
    enabled: !!session && officer,
    queryFn: ({ signal }) =>
      request<InstitutionPage>("/institutions?page=1&page_size=100", {
        signal,
      }),
  });

  const cases = useQuery({
    queryKey: [...scope, "cases", filters, page],
    enabled: !!session,
    queryFn: ({ signal }) => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20",
      });
      if (filters.status) params.set("status", filters.status);
      if (filters.priority) params.set("priority", filters.priority);
      if (filters.severity) params.set("severity", filters.severity);
      if (filters.overdue) params.set("overdue", "true");
      const minAge = Number.parseInt(filters.minAge, 10);
      if (Number.isInteger(minAge) && minAge >= 0)
        params.set("min_age_days", String(minAge));
      if (officer && filters.assignee)
        params.set("assigned_to", filters.assignee);
      if (officer && filters.institution)
        params.set("institution_id", filters.institution);
      return request<CasePage>(`/cases?${params}`, { signal });
    },
  });
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">EVIDENCE-LINKED REVIEW</p>
        <h1>{officer ? "Officer cases" : "Cases"}</h1>
        <p>
          {officer
            ? "Open and manage cases investigating potential overlaps or mismatches. Opening a case is not a fraud determination."
            : "Cases referencing your institution's records. You may read the timeline, comment, and respond to correction requests."}
        </p>
      </div>
      <section className="panel" aria-labelledby="case-queue-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">CASE QUEUE</p>
            <h2 id="case-queue-title">
              {officer ? "All cases" : "Cases for your institution"}
            </h2>
          </div>
        </header>
        <form
          className="case-filters"
          aria-label="Filter cases"
          onSubmit={(event) => event.preventDefault()}
        >
          <label className="inline-filter">
            Status
            <select
              value={filters.status}
              onChange={(e) =>
                update("status", e.target.value as CaseStatus | "")
              }
            >
              <option value="">All statuses</option>
              {CASE_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {statusLabel(item)}
                </option>
              ))}
            </select>
          </label>
          <label className="inline-filter">
            Priority
            <select
              value={filters.priority}
              onChange={(e) =>
                update("priority", e.target.value as CasePriority | "")
              }
            >
              <option value="">Any priority</option>
              {CASE_PRIORITIES.map((item) => (
                <option key={item} value={item}>
                  {titleCase(item)}
                </option>
              ))}
            </select>
          </label>
          <label className="inline-filter">
            Severity
            <select
              value={filters.severity}
              onChange={(e) =>
                update("severity", e.target.value as CaseSeverity | "")
              }
            >
              <option value="">Any severity</option>
              {CASE_SEVERITIES.map((item) => (
                <option key={item} value={item}>
                  {titleCase(item)}
                </option>
              ))}
            </select>
          </label>
          <label className="inline-filter">
            Overdue
            <select
              value={filters.overdue ? "yes" : ""}
              onChange={(e) => update("overdue", e.target.value === "yes")}
            >
              <option value="">Any due date</option>
              <option value="yes">Overdue only</option>
            </select>
          </label>
          <label className="inline-filter">
            Minimum age (days)
            <input
              type="number"
              min={0}
              max={3650}
              inputMode="numeric"
              value={filters.minAge}
              onChange={(e) => update("minAge", e.target.value)}
            />
          </label>
          {officer && (
            <>
              <label className="inline-filter">
                Assignee
                <select
                  value={filters.assignee}
                  onChange={(e) => update("assignee", e.target.value)}
                  disabled={assignees.isPending}
                >
                  <option value="">Anyone</option>
                  {assignees.data?.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.display_name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="inline-filter">
                Institution
                <select
                  value={filters.institution}
                  onChange={(e) => update("institution", e.target.value)}
                  disabled={institutions.isPending}
                >
                  <option value="">All institutions</option>
                  {institutions.data?.data.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.name}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
          <button
            type="button"
            className="button secondary small"
            disabled={!hasFilters}
            onClick={() => {
              setFilters(NO_FILTERS);
              setPage(1);
            }}
          >
            Clear filters
          </button>
          {officer && (assignees.isError || institutions.isError) && (
            <p className="form-error" role="alert">
              Some filter options could not be loaded. Other filters still work.
            </p>
          )}
        </form>
        <p className="sr-only" role="status" aria-live="polite">
          {cases.data ? `${cases.data.pagination.total} cases found` : ""}
        </p>
        {cases.isPending ? (
          <Loading label="Loading cases…" />
        ) : cases.isError ? (
          <ErrorPanel error={cases.error} retry={() => void cases.refetch()} />
        ) : cases.data.data.length === 0 ? (
          <div className="empty-state">
            {hasFilters ? (
              <>
                <h3>No cases match these filters</h3>
                <p>Try removing a filter or clear all filters.</p>
              </>
            ) : (
              <>
                <h3>No cases yet</h3>
                <p>
                  {officer
                    ? "Open a case from a flagged finding to begin an investigation."
                    : "No officer has opened a case against your institution's records."}
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="institution-list">
            {cases.data.data.map((item) => (
              <article key={item.id} className="directory-item">
                <span className="directory-icon" aria-hidden="true">
                  <Icon name="flag" />
                </span>
                <div>
                  <h3>
                    <Link href={`/cases/${item.id}`}>
                      {item.category.replaceAll("_", " ")}
                    </Link>
                  </h3>
                  <p>
                    {item.summary.length > 140
                      ? `${item.summary.slice(0, 140)}…`
                      : item.summary}
                  </p>
                  <p className="cell-note">
                    Opened{" "}
                    <time dateTime={item.opened_at}>
                      {new Date(item.opened_at).toLocaleString()}
                    </time>{" "}
                    · {item.record_version_ids.length} linked record
                    {item.record_version_ids.length === 1 ? "" : "s"} · Age{" "}
                    {item.age_days} day{item.age_days === 1 ? "" : "s"}
                    {item.due_at && (
                      <>
                        {" "}
                        · Due{" "}
                        <time dateTime={item.due_at}>
                          {new Date(item.due_at).toLocaleDateString()}
                        </time>
                      </>
                    )}
                  </p>
                  <CaseBadges item={item} />
                </div>
                <span className={`status-badge ${statusTone(item.status)}`}>
                  {statusLabel(item.status)}
                </span>
              </article>
            ))}
          </div>
        )}
        {cases.data && (
          <Pagination
            page={page}
            pageSize={20}
            total={cases.data.pagination.total}
            busy={cases.isFetching}
            change={setPage}
          />
        )}
      </section>
      <p className="data-note">
        Cases reference synthetic records only. A case is a review lead, not a
        fraud determination or official APAAR identity verification.
      </p>
    </>
  );
}
