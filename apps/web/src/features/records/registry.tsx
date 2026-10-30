"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { QueryBoundary, FilterOptionsError } from "@/components/ui/feedback";
import { QueryPagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
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
  const { session, request } = useSession();
  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  const [page, setPage] = useState(1);
  const officer = session?.user.role === "AICTE_OFFICER";
  const scope = ["private", session?.generation, session?.user.id];
  const hasFilters = JSON.stringify(filters) !== JSON.stringify(NO_FILTERS);
  const update = <K extends keyof Filters>(key: K, value: Filters[K]) => {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  };
  const programmeInstitution = officer
    ? filters.institution
    : (session?.user.institution_id ?? "");

  const institutions = useInstitutionOptions(
    [...scope, "institutions", "filter-options"],
    !!session && officer,
  );
  const programmes = useQuery({
    queryKey: [...scope, "programmes", programmeInstitution],
    enabled: !!session && !!programmeInstitution,
    queryFn: ({ signal }) =>
      request<ProgrammePage>(
        `/institutions/${programmeInstitution}/programmes?page=1&page_size=100`,
        { signal },
      ),
  });

  const records = useQuery({
    queryKey: [...scope, "records", filters, page],
    enabled: !!session,
    queryFn: ({ signal }) => {
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
      if (filters.validation)
        params.set("validation_status", filters.validation);
      if (filters.candidates) params.set("include_candidates", "true");
      return request<RecordPage>(`/records?${params}`, { signal });
    },
  });

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">STUDENT REGISTRY</p>
        <h1>Student registry</h1>
        <p>
          Student records from received submissions, with masked APAAR values.
          SIMULATED / DEMO DATA: records are synthetic and local validation is
          not official APAAR verification.
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
            <label className="inline-filter">
              Institution
              <select
                value={filters.institution}
                disabled={institutions.isPending}
                onChange={(e) => {
                  setFilters((c) => ({
                    ...c,
                    institution: e.target.value,
                    programme: "",
                  }));
                  setPage(1);
                }}
              >
                <option value="">All institutions</option>
                {institutions.data?.data.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.name}
                  </option>
                ))}
              </select>
            </label>
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
              setFilters(NO_FILTERS);
              setPage(1);
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
              <div className="empty-state">
                {hasFilters ? (
                  <>
                    <h3>No records match these filters</h3>
                    <p>Try removing a filter or clear all filters.</p>
                  </>
                ) : (
                  <>
                    <h3>No records yet</h3>
                    <p>
                      Records appear here once a submission has been received
                      and its rows processed.
                    </p>
                  </>
                )}
              </div>
            ) : (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Student records"
              >
                <table className="review-table">
                  <caption>Student records · SIMULATED / DEMO DATA</caption>
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
