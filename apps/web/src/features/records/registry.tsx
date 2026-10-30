"use client";

import Link from "next/link";
import { useState } from "react";
import {
  EmptyState,
  QueryBoundary,
  FilterOptionsError,
} from "@/components/ui/feedback";
import { InstitutionSelect } from "@/components/ui/filters";
import { QueryPagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { useApiQuery, useFilterState, useScope } from "@/lib/api/hooks";
import { DEMO_TAG } from "@/lib/format";
import type { components } from "@/lib/api/generated";
import {
  StatusBadges,
  VALIDATION_STATUSES,
  validationLabel,
  type RecordRow,
  type ValidationStatus,
} from "./shared";
import { useInstitutionOptions } from "@/features/institutions/options";

type RecordPage = components["schemas"]["Page_RecordRow_"];
type ProgrammePage = components["schemas"]["Page_ProgrammeResponse_"];

type Filters = {
  q: string;
  institution: string;
  programme: string;
  year: string;
  enrollment: string;
  validation: ValidationStatus | "";
  candidates: boolean;
};
const NO_FILTERS: Filters = {
  q: "",
  institution: "",
  programme: "",
  year: "",
  enrollment: "",
  validation: "",
  candidates: false,
};
const PAGE_SIZE = 20;

export function RecordRegistry() {
  const { session } = useSession();
  const [page, setPage] = useState(1);
  const officer = session?.user.role === "AICTE_OFFICER";
  const { filters, setFilters, update, reset } = useFilterState<Filters>(
    NO_FILTERS,
    () => setPage(1),
  );
  const hasFilters = JSON.stringify(filters) !== JSON.stringify(NO_FILTERS);
  const programmeInstitution = officer
    ? filters.institution
    : (session?.user.institution_id ?? "");

  const institutions = useInstitutionOptions(!!session && officer);
  const programmes = useApiQuery<ProgrammePage>(
    useScope("programmes", programmeInstitution),
    `/institutions/${programmeInstitution}/programmes?page=1&page_size=100`,
    { enabled: !!programmeInstitution },
  );

  const recordsPath = (() => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(PAGE_SIZE),
    });
    const q = filters.q.trim();
    if (q) params.set("q", q);
    if (officer && filters.institution)
      params.set("institution_id", filters.institution);
    if (filters.programme) params.set("programme_id", filters.programme);
    if (filters.year.trim()) params.set("academic_year", filters.year.trim());
    if (filters.enrollment.trim())
      params.set("enrollment_status", filters.enrollment.trim());
    if (filters.validation) params.set("validation_status", filters.validation);
    if (filters.candidates) params.set("include_candidates", "true");
    return `/records?${params}`;
  })();
  const records = useApiQuery<RecordPage>(
    useScope("records", filters, page),
    recordsPath,
  );

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">STUDENT REGISTRY</p>
        <h1>Student registry</h1>
        <p>
          Student records from received submissions, with masked APAAR values.{" "}
          {DEMO_TAG}: records are synthetic and local validation is not official
          APAAR verification.
        </p>
      </div>
      <section className="panel" aria-labelledby="registry-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">RECORDS</p>
            <h2 id="registry-title">
              {officer ? "All institutions" : "Your institution"}
            </h2>
          </div>
        </header>
        <form
          className="case-filters"
          aria-label="Filter student records"
          onSubmit={(event) => event.preventDefault()}
        >
          <label className="inline-filter">
            Search
            <input
              type="search"
              value={filters.q}
              maxLength={100}
              placeholder="College student ID or name"
              onChange={(e) => update("q", e.target.value)}
            />
          </label>
          {officer && (
            <InstitutionSelect
              className="inline-filter"
              institutions={institutions.data?.data ?? []}
              value={filters.institution}
              disabled={institutions.isPending}
              onChange={(value) => {
                setFilters((c) => ({
                  ...c,
                  institution: value,
                  programme: "",
                }));
                setPage(1);
              }}
            />
          )}
          <label className="inline-filter">
            Programme
            <select
              value={filters.programme}
              disabled={!programmeInstitution || programmes.isPending}
              onChange={(e) => update("programme", e.target.value)}
            >
              <option value="">
                {programmeInstitution
                  ? "All programmes"
                  : "Select an institution first"}
              </option>
              {programmes.data?.data.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>
          <label className="inline-filter">
            Academic year
            <input
              value={filters.year}
              maxLength={20}
              placeholder="e.g. 2025-26"
              onChange={(e) => update("year", e.target.value)}
            />
          </label>
          <label className="inline-filter">
            Enrollment status
            <input
              value={filters.enrollment}
              maxLength={40}
              onChange={(e) => update("enrollment", e.target.value)}
            />
          </label>
          <label className="inline-filter">
            Validation status
            <select
              value={filters.validation}
              onChange={(e) =>
                update("validation", e.target.value as ValidationStatus | "")
              }
            >
              <option value="">Any status</option>
              {VALIDATION_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {validationLabel(s)}
                </option>
              ))}
            </select>
          </label>
          <label className="inline-filter">
            <span>
              <input
                type="checkbox"
                checked={filters.candidates}
                onChange={(e) => update("candidates", e.target.checked)}
              />{" "}
              Include candidate records
            </span>
          </label>
          <button
            type="button"
            className="button secondary small"
            disabled={!hasFilters}
            onClick={() => {
              reset();
            }}
          >
            Clear filters
          </button>
          {(institutions.isError || programmes.isError) && (
            <FilterOptionsError />
          )}
        </form>
        <p className="sr-only" role="status" aria-live="polite">
          {records.data ? `${records.data.pagination.total} records found` : ""}
        </p>
        <QueryBoundary query={records} loading="Loading records…">
          {(data) =>
            data.data.length === 0 ? (
              hasFilters ? (
                <EmptyState title="No records match these filters">
                  Try removing a filter or clear all filters.
                </EmptyState>
              ) : (
                <EmptyState title="No records yet">
                  Records appear here once a submission has been received and
                  its rows processed.
                </EmptyState>
              )
            ) : (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Student records"
              >
                <table className="review-table">
                  <caption>Student records · {DEMO_TAG}</caption>
                  <thead>
                    <tr>
                      <th scope="col">Student</th>
                      <th scope="col">Masked APAAR</th>
                      {officer && <th scope="col">Institution</th>}
                      <th scope="col">Programme</th>
                      <th scope="col">Year</th>
                      <th scope="col">Enrollment</th>
                      <th scope="col">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.data.map((row: RecordRow) => (
                      <tr key={row.record_version_id}>
                        <th scope="row">
                          <Link href={`/records/${row.record_version_id}`}>
                            {row.student_name}
                          </Link>
                          <span className="cell-note">
                            {row.college_student_id}
                          </span>
                        </th>
                        <td>{row.masked_apaar}</td>
                        {officer && <td>{row.institution_name}</td>}
                        <td>{row.programme_name}</td>
                        <td>{row.academic_year}</td>
                        <td>{row.enrollment_status}</td>
                        <td>
                          <StatusBadges
                            snapshot={row.snapshot_state}
                            validation={row.validation_status}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        </QueryBoundary>
        <QueryPagination
          query={records}
          page={page}
          pageSize={PAGE_SIZE}
          change={setPage}
        />
      </section>
      <p className="data-note">
        Search matches college student ID or name only; APAAR values are never
        searchable. Candidate records are not yet active.
      </p>
    </>
  );
}
