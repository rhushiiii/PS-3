"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { isUUID } from "@/lib/api/client";
import {
  snapshotLabels,
  useSubmissionContext,
  validAcademicYear,
  type History,
} from "./data";

export function SubmissionHistory({
  institutionId,
}: {
  institutionId: string;
}) {
  const { session, request } = useSession();
  const { institution, programmes, options } =
    useSubmissionContext(institutionId);
  const [programme, setProgramme] = useState("");
  const [year, setYear] = useState("");
  const [filters, setFilters] = useState({ programme: "", year: "" });
  const [page, setPage] = useState(1);
  const [formError, setFormError] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const admin = session?.user.role === "INSTITUTION_ADMIN";
  const history = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "submissions",
      institutionId,
      filters,
      page,
    ],
    enabled: !!session && isUUID(institutionId) && !!institution.data,
    queryFn: ({ signal }) => {
      const query = new URLSearchParams({
        institution_id: institutionId,
        page: String(page),
        page_size: "10",
      });
      if (filters.programme) query.set("programme_id", filters.programme);
      if (filters.year) query.set("academic_year", filters.year);
      return request<History>(`/submissions?${query}`, { signal });
    },
  });
  if (!isUUID(institutionId))
    return (
      <section className="feedback">
        <h1>Choose an institution</h1>
        <p>
          Open an institution from the directory to browse its permitted
          submission history.
        </p>
        <Link className="button secondary" href="/aicte/institutions">
          Browse institutions
        </Link>
      </section>
    );
  return (
    <>
      <div className="page-heading heading-actions">
        <div>
          <p className="eyebrow">IMMUTABLE HISTORY</p>
          <h1>Submissions</h1>
          <p>
            Candidate uploads and activated snapshots, kept as separate
            versions.
          </p>
        </div>
        {admin && (
          <Link className="button primary" href="/institution/upload">
            Upload candidate CSV
          </Link>
        )}
      </div>
      {institution.isPending ? (
        <Loading label="Loading institution…" />
      ) : institution.isError ? (
        <ErrorPanel
          error={institution.error}
          retry={() => void institution.refetch()}
        />
      ) : (
        <>
          <div className="scope-notice">
            <strong>{institution.data.name}</strong>
            <span>
              Synthetic declarations · history is never added to current
              enrolment totals.
            </span>
          </div>
          <section className="panel" aria-labelledby="history-title">
            <header className="panel-heading">
              <div>
                <p className="eyebrow">SUBMISSION REGISTER</p>
                <h2 id="history-title">Upload history</h2>
              </div>
              <button
                className="button secondary small"
                disabled={history.isFetching}
                onClick={() => void history.refetch()}
              >
                Refresh history
              </button>
            </header>
            <form
              className="submission-filters"
              onSubmit={(event) => {
                event.preventDefault();
                if (year && !validAcademicYear(year)) {
                  setFormError("Use consecutive years, for example 2026-27.");
                  return;
                }
                setFormError("");
                setFilters({ programme, year });
                setPage(1);
                setExpanded(null);
              }}
            >
              <label>
                Programme
                <select
                  value={programme}
                  onChange={(event) => setProgramme(event.target.value)}
                  disabled={programmes.isPending || programmes.isError}
                >
                  <option value="">All programmes</option>
                  {options.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.code} — {item.name}
                      {!item.active ? " (inactive)" : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Academic year
                <input
                  value={year}
                  onChange={(event) => setYear(event.target.value)}
                  placeholder="All years"
                  maxLength={7}
                  aria-describedby="history-year-help"
                />
              </label>
              <button className="button secondary" type="submit">
                Apply filters
              </button>
              <button
                className="button secondary"
                type="button"
                onClick={() => {
                  setProgramme("");
                  setYear("");
                  setFilters({ programme: "", year: "" });
                  setPage(1);
                  setFormError("");
                  setExpanded(null);
                }}
              >
                Clear filters
              </button>
              <p id="history-year-help" className="form-help">
                Year format: YYYY-YY, for example 2026-27.
              </p>
              {formError && (
                <p className="form-error" role="alert">
                  {formError}
                </p>
              )}
            </form>
            {programmes.isError && (
              <ErrorPanel
                error={programmes.error}
                retry={() => void programmes.refetch()}
              />
            )}
            {programmes.hasNextPage && (
              <div className="panel-padding">
                <button
                  className="button secondary small"
                  disabled={programmes.isFetchingNextPage}
                  onClick={() => void programmes.fetchNextPage()}
                >
                  Load more programme options
                </button>
              </div>
            )}
            {history.isPending ? (
              <Loading label="Loading submissions…" />
            ) : history.isError ? (
              <ErrorPanel
                error={history.error}
                retry={() => void history.refetch()}
              />
            ) : history.data.data.length === 0 ? (
              <div className="empty-state">
                <h3>No submissions found</h3>
                <p>
                  No stored uploads match these filters. An empty history does
                  not establish current enrolment.
                </p>
              </div>
            ) : (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Submission history, scroll horizontally on small screens"
              >
                <table className="history-table">
                  <caption className="sr-only">
                    Submission history for {institution.data.name}
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Submission</th>
                      <th scope="col">Programme / year</th>
                      <th scope="col">Records</th>
                      <th scope="col">Processing</th>
                      <th scope="col">Snapshot</th>
                      <th scope="col">Provenance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.data.data.map((batch) => (
                      <tr key={batch.id}>
                        <td>
                          <span className="code-label">
                            {batch.id.slice(0, 8)}
                          </span>
                          <small className="cell-note">
                            <Link href={`/submissions/${batch.id}`}>
                              {batch.validation_performed
                                ? "View validation"
                                : "Open candidate"}
                            </Link>
                          </small>
                          <small className="cell-note">
                            <time dateTime={batch.received_at}>
                              {new Date(batch.received_at).toLocaleString()}
                            </time>
                          </small>
                          {batch.warnings?.includes("DUPLICATE_UPLOAD") && (
                            <span className="cell-note warning-text">
                              Repeated file · separate upload
                            </span>
                          )}
                        </td>
                        <td>
                          {options.find(
                            (item) => item.id === batch.programme_id,
                          )?.code ?? batch.programme_id}
                          <small className="cell-note">
                            {batch.academic_year}
                          </small>
                        </td>
                        <td>
                          {batch.row_count}
                          <small className="cell-note">
                            Declared rows, not active enrolments
                          </small>
                        </td>
                        <td>
                          <span className="status-badge neutral">
                            {batch.status === "COMPLETED"
                              ? "Processed"
                              : batch.status === "FAILED"
                                ? "Processing failed"
                                : "Processing"}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`status-badge ${batch.snapshot_state === "CURRENT" ? "active" : "neutral"}`}
                          >
                            {snapshotLabels[batch.snapshot_state]}
                          </span>
                          <small className="cell-note">
                            {batch.snapshot_state === "CURRENT"
                              ? "Activated declaration"
                              : batch.snapshot_state === "PREVIOUS"
                                ? "Historical snapshot"
                                : "Not activated"}
                          </small>
                        </td>
                        <td>
                          <button
                            className="button secondary small"
                            aria-expanded={expanded === batch.id}
                            aria-controls={`provenance-${batch.id}`}
                            onClick={() =>
                              setExpanded(
                                expanded === batch.id ? null : batch.id,
                              )
                            }
                          >
                            {expanded === batch.id ? "Hide" : "Show"} provenance
                            <span className="sr-only">
                              {" "}
                              for {batch.id.slice(0, 8)}
                            </span>
                          </button>
                          {expanded === batch.id && (
                            <dl
                              id={`provenance-${batch.id}`}
                              className="batch-provenance"
                            >
                              <dt>Submission ID</dt>
                              <dd>{batch.id}</dd>
                              <dt>Source / schema</dt>
                              <dd>
                                {batch.source} / {batch.schema_version}
                              </dd>
                              <dt>File size</dt>
                              <dd>
                                {batch.file_size_bytes.toLocaleString()} bytes
                              </dd>
                              <dt>Uploader reference</dt>
                              <dd>{batch.uploaded_by}</dd>
                              <dt>Base scope revision</dt>
                              <dd>{batch.base_scope_revision}</dd>
                              <dt>Completed</dt>
                              <dd>
                                {batch.completed_at
                                  ? new Date(
                                      batch.completed_at,
                                    ).toLocaleString()
                                  : "Not completed"}
                              </dd>
                            </dl>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {history.data && !history.isError && (
              <Pagination
                page={page}
                pageSize={10}
                total={history.data.pagination.total}
                busy={history.isFetching}
                change={(next) => {
                  setPage(next);
                  setExpanded(null);
                }}
              />
            )}
          </section>
          <p className="data-note">
            Processed means CSV parsing and storage completed. It does not mean
            local validation passed, a snapshot was approved or APAAR was
            verified. Candidate uploads never become current automatically.
          </p>
        </>
      )}
    </>
  );
}
