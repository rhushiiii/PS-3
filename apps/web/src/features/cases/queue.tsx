"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import {
  QueryBoundary,
  EmptyState,
  FilterOptionsError,
} from "@/components/ui/feedback";
import { EnumSelect, InstitutionSelect } from "@/components/ui/filters";
import { Icon } from "@/components/ui/icon";
import { QueryPagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { useApiQuery, useFilterState, useScope } from "@/lib/api/hooks";
import { plain, when } from "@/lib/format";
import type { components } from "@/lib/api/generated";
import {
  CASE_PRIORITIES,
  CASE_SEVERITIES,
  CASE_STATUSES,
  CaseBadges,
  statusLabel,
  statusTone,
  type CasePage,
  type CasePriority,
  type CaseSeverity,
  type CaseStatus,
} from "./shared";
import { useInstitutionOptions } from "@/features/institutions/options";

type Assignee = components["schemas"]["AssigneeResponse"];

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
  const { session } = useSession();
  const search = useSearchParams();
  const [page, setPage] = useState(1);
  const { filters, update, reset } = useFilterState(
    initialFilters(search),
    () => setPage(1),
  );
  const officer = session?.user.role === "AICTE_OFFICER";
  const hasFilters = JSON.stringify(filters) !== JSON.stringify(NO_FILTERS);

  const assignees = useApiQuery<Assignee[]>(
    useScope("cases", "assignees"),
    "/cases/assignees",
    { enabled: officer },
  );
  const institutions = useInstitutionOptions(!!session && officer);

  const casesPath = (() => {
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
    return `/cases?${params}`;
  })();
  const cases = useApiQuery<CasePage>(
    useScope("cases", filters, page),
    casesPath,
  );
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
          <EnumSelect
            className="inline-filter"
            label="Priority"
            values={CASE_PRIORITIES}
            value={filters.priority}
            onChange={(value) => update("priority", value as CasePriority | "")}
            allLabel="Any priority"
          />
          <EnumSelect
            className="inline-filter"
            label="Severity"
            values={CASE_SEVERITIES}
            value={filters.severity}
            onChange={(value) => update("severity", value as CaseSeverity | "")}
            allLabel="Any severity"
          />
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
              <InstitutionSelect
                className="inline-filter"
                institutions={institutions.data?.data ?? []}
                value={filters.institution}
                disabled={institutions.isPending}
                onChange={(value) => update("institution", value)}
              />
            </>
          )}
          <button
            type="button"
            className="button secondary small"
            disabled={!hasFilters}
            onClick={reset}
          >
            Clear filters
          </button>
          {officer && (assignees.isError || institutions.isError) && (
            <FilterOptionsError />
          )}
        </form>
        <p className="sr-only" role="status" aria-live="polite">
          {cases.data ? `${cases.data.pagination.total} cases found` : ""}
        </p>
        <QueryBoundary query={cases} loading="Loading cases…">
          {(data) =>
            data.data.length === 0 ? (
              hasFilters ? (
                <EmptyState title="No cases match these filters">
                  Try removing a filter or clear all filters.
                </EmptyState>
              ) : (
                <EmptyState title="No cases yet">
                  {officer
                    ? "Open a case from a flagged finding to begin an investigation."
                    : "No officer has opened a case against your institution's records."}
                </EmptyState>
              )
            ) : (
              <div className="institution-list">
                {data.data.map((item) => (
                  <article key={item.id} className="directory-item">
                    <span className="directory-icon" aria-hidden="true">
                      <Icon name="flag" />
                    </span>
                    <div>
                      <h3>
                        <Link href={`/cases/${item.id}`}>
                          {plain(item.category)}
                        </Link>
                      </h3>
                      <p>
                        {item.summary.length > 140
                          ? `${item.summary.slice(0, 140)}…`
                          : item.summary}
                      </p>
                      <p className="cell-note">
                        Opened {when(item.opened_at)} ·{" "}
                        {item.record_version_ids.length} linked record
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
            )
          }
        </QueryBoundary>
        <QueryPagination
          query={cases}
          page={page}
          pageSize={20}
          change={setPage}
        />
      </section>
      <p className="data-note">
        Cases reference synthetic records only. A case is a review lead, not a
        fraud determination or official APAAR identity verification.
      </p>
    </>
  );
}
