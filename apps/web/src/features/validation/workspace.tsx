"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { useSubmissionContext } from "@/features/submissions/data";
import { ReviewActivation } from "@/features/submissions/review-activation";
import { ApiError, errorMessage, isUUID } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";
import { findingGuidance, safeEvidence } from "./guidance";

type Run = components["schemas"]["RunResponse"];
type RunPage = components["schemas"]["Page_RunResponse_"];
type Finding = components["schemas"]["FindingResponse"];
type FindingPage = components["schemas"]["Page_FindingResponse_"];
type RowPage = components["schemas"]["Page_RowResponse_"];
type Batch = components["schemas"]["BatchResponse"];
type Status = "VALID" | "FLAGGED" | "INCOMPLETE";
type QueryState = {
  run_id?: string;
  run_page?: string;
  row_page?: string;
  row_status?: string;
  finding_page?: string;
  finding_rule?: string;
  finding_severity?: string;
  finding_classification?: string;
  review_id?: string;
  omission_page?: string;
};

const pageSize = 10;
const validStatuses: Status[] = ["VALID", "FLAGGED", "INCOMPLETE"];
const severityOptions = ["ERROR", "WARNING", "INFO"] as const;

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function runStatusLabel(status: Status | null | undefined) {
  if (!status) return "Not run";
  return status === "VALID" ? "Valid · local checks" : status;
}

function crossLabel(
  context: unknown,
  freshness: Finding["cross_current_freshness"],
): string {
  switch (context) {
    case "CURRENT_ACTIVE":
      return freshness === "STALE"
        ? "Potential current ACTIVE overlap identified as of a stale assessment"
        : "Potential current ACTIVE overlap";
    case "CURRENT_INACTIVE":
      return "Current but inactive match · informational";
    case "LOCAL_INACTIVE":
      return "Local inactive record · informational";
    case "HISTORICAL":
      return "Historical match as of this run · informational";
    case "DIFFERENT_YEAR":
      return "Different academic year · informational";
    case "UNACTIVATED_CANDIDATE":
      return "Unactivated candidate · informational";
    default:
      return "Potential match · review the evidence";
  }
}

function buildUrl(batchId: string, query: Record<string, string | undefined>) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query))
    if (value) params.set(key, value);
  const encoded = params.toString();
  return `/submissions/${batchId}${encoded ? `?${encoded}` : ""}`;
}

function stateNumber(value: string | undefined, fallback = 1): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

export function ValidationWorkspace({
  batchId,
  query,
}: {
  batchId: string;
  query: QueryState;
}) {
  const router = useRouter();
  const { session, request, download } = useSession();
  const queryClient = useQueryClient();
  const role = session?.user.role;
  const admin = role === "INSTITUTION_ADMIN";
  const officer = role === "AICTE_OFFICER";
  const [announcement, setAnnouncement] = useState("");
  const [filterError, setFilterError] = useState("");

  const runId = query.run_id ?? "";
  const runPageNumber = stateNumber(query.run_page);
  const rowPageNumber = stateNumber(query.row_page);
  const findingPageNumber = stateNumber(query.finding_page);
  const rowStatus = validStatuses.includes(query.row_status as Status)
    ? (query.row_status as Status)
    : "";
  const runFilters = {
    run_id: runId || undefined,
    run_page: runPageNumber > 1 ? String(runPageNumber) : undefined,
  };
  const findingFilters = {
    ...runFilters,
    finding_page: findingPageNumber > 1 ? String(findingPageNumber) : undefined,
    finding_rule: query.finding_rule || undefined,
    finding_severity: query.finding_severity || undefined,
    finding_classification: query.finding_classification || undefined,
  };
  const navigate = (changes: Partial<QueryState>, reset = false) => {
    const current: Record<string, string | undefined> = reset
      ? {}
      : {
          run_id: runId || undefined,
          run_page: query.run_page,
          row_page: query.row_page,
          row_status: query.row_status,
          finding_page: query.finding_page,
          finding_rule: query.finding_rule,
          finding_severity: query.finding_severity,
          finding_classification: query.finding_classification,
          review_id: query.review_id,
          omission_page: query.omission_page,
        };
    router.push(buildUrl(batchId, { ...current, ...changes }));
  };

  const baseKey = [
    "private",
    session?.generation,
    session?.user.id,
    "validation",
    batchId,
  ];
  const batchQuery = useQuery({
    queryKey: [...baseKey, "batch"],
    enabled: !!session && isUUID(batchId),
    queryFn: ({ signal }) =>
      request<Batch>(`/submissions/${batchId}`, { signal }),
  });
  const runs = useQuery({
    queryKey: [...baseKey, "runs", runPageNumber],
    enabled: !!session && isUUID(batchId),
    queryFn: ({ signal }) =>
      request<RunPage>(
        `/submissions/${batchId}/validation-runs?page=${runPageNumber}&page_size=${pageSize}`,
        { signal },
      ),
  });
  const selectedRun = useQuery({
    queryKey: [...baseKey, "run", runId],
    enabled: !!session && isUUID(batchId) && isUUID(runId),
    queryFn: ({ signal }) =>
      request<Run>(`/submissions/${batchId}/validation-runs/${runId}`, {
        signal,
      }),
  });
  const rows = useQuery({
    queryKey: [...baseKey, "rows", runId, rowPageNumber, rowStatus],
    enabled: !!session && isUUID(batchId) && isUUID(runId),
    queryFn: ({ signal }) => {
      const params = new URLSearchParams({
        run_id: runId,
        page: String(rowPageNumber),
        page_size: String(pageSize),
      });
      if (rowStatus) params.set("status", rowStatus);
      return request<RowPage>(`/submissions/${batchId}/rows?${params}`, {
        signal,
      });
    },
  });
  const findings = useQuery({
    queryKey: [...baseKey, "findings", runId, findingFilters],
    enabled: !!session && isUUID(batchId) && isUUID(runId),
    queryFn: ({ signal }) => {
      const params = new URLSearchParams({
        run_id: runId,
        page: String(findingPageNumber),
        page_size: String(pageSize),
      });
      if (findingFilters.finding_rule)
        params.set("rule_code", findingFilters.finding_rule);
      if (findingFilters.finding_severity)
        params.set("severity", findingFilters.finding_severity);
      if (findingFilters.finding_classification)
        params.set("classification", findingFilters.finding_classification);
      return request<FindingPage>(
        `/submissions/${batchId}/findings?${params}`,
        {
          signal,
        },
      );
    },
  });

  const validate = useMutation({
    mutationFn: () =>
      request<Run>(`/submissions/${batchId}/validate`, { method: "POST" }),
    retry: false,
    onSuccess: async (created) => {
      setAnnouncement(
        "Validation completed and was saved as a new immutable run.",
      );
      await queryClient.invalidateQueries({ queryKey: [...baseKey, "runs"] });
      await queryClient.invalidateQueries({ queryKey: [...baseKey, "batch"] });
      navigate({ run_id: created.id }, true);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        setAnnouncement(
          "A validation already completed or the candidate changed state. Refresh run history and select the saved run.",
        );
        void queryClient.invalidateQueries({ queryKey: [...baseKey, "runs"] });
        return;
      }
      if (
        error instanceof ApiError &&
        error.status >= 400 &&
        error.status < 500
      ) {
        setAnnouncement(
          error.code === "MATCHING_CONFIGURATION_UNAVAILABLE"
            ? "Validation was not started because the server's APAAR matching configuration is unavailable. Contact the local API operator."
            : `Validation was not accepted. ${errorMessage(error)}`,
        );
        return;
      }
      setAnnouncement(
        "Validation outcome is unknown. The request was not retried. Refresh run history before deciding what to do next.",
      );
    },
  });
  const revalidate = useMutation({
    mutationFn: () =>
      request<Run>(`/submissions/${batchId}/revalidate`, { method: "POST" }),
    retry: false,
    onSuccess: async (created) => {
      setAnnouncement("A new immutable revalidation run was saved.");
      await queryClient.invalidateQueries({ queryKey: [...baseKey, "runs"] });
      await queryClient.invalidateQueries({ queryKey: [...baseKey, "batch"] });
      navigate({ run_id: created.id }, true);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        setAnnouncement(
          "The candidate could not be revalidated in its current state. Refresh run history.",
        );
        void queryClient.invalidateQueries({ queryKey: [...baseKey, "runs"] });
      } else if (
        error instanceof ApiError &&
        error.status >= 400 &&
        error.status < 500
      ) {
        setAnnouncement(
          `Revalidation was not accepted. ${errorMessage(error)}`,
        );
      } else {
        setAnnouncement(
          "Revalidation outcome is unknown. The request was not retried. Refresh run history before deciding what to do next.",
        );
      }
    },
  });
  const exportFeedback = useMutation({
    mutationFn: (signal: AbortSignal) =>
      download(`/submissions/${batchId}/feedback.csv?run_id=${runId}`, signal),
    retry: false,
    onSuccess: ({ blob, filename }) => {
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
      setAnnouncement("Masked feedback CSV downloaded.");
    },
  });

  useEffect(() => {
    if (!query.run_id && runs.data?.data[0])
      router.replace(
        buildUrl(batchId, {
          run_id: runs.data.data[0].id,
          run_page: query.run_page,
          review_id: query.review_id,
          omission_page: query.omission_page,
        }),
      );
  }, [
    batchId,
    query.omission_page,
    query.review_id,
    query.run_id,
    query.run_page,
    router,
    runs.data,
  ]);

  useEffect(() => {
    const activatedReviewId = batchQuery.data?.activation_review_id;
    if (!query.review_id && activatedReviewId && runId) {
      router.replace(
        buildUrl(batchId, {
          run_id: runId || undefined,
          run_page: query.run_page,
          row_page: query.row_page,
          row_status: query.row_status,
          finding_page: query.finding_page,
          finding_rule: query.finding_rule,
          finding_severity: query.finding_severity,
          finding_classification: query.finding_classification,
          review_id: activatedReviewId,
          omission_page: query.omission_page,
        }),
      );
    }
  }, [
    batchId,
    batchQuery.data?.activation_review_id,
    query.finding_classification,
    query.finding_page,
    query.finding_rule,
    query.finding_severity,
    query.omission_page,
    query.review_id,
    query.row_page,
    query.row_status,
    query.run_page,
    router,
    runId,
  ]);

  const currentOverlaps = selectedRun.data?.current_overlap_records;
  const assessment = selectedRun.data?.summary.matching_assessment;
  const currentMetricAvailable =
    selectedRun.data?.cross_current_freshness === "FRESH" &&
    assessment === "COMPLETE" &&
    typeof currentOverlaps === "number";
  const findingCounts = useMemo(() => {
    const summary = selectedRun.data?.summary;
    const recordCounts = summary?.record_status_counts;
    const asRecord = (value: unknown): Record<string, unknown> | null =>
      typeof value === "object" && value !== null
        ? (value as Record<string, unknown>)
        : null;
    const counts = asRecord(recordCounts);
    return {
      valid: numberValue(counts?.VALID),
      flagged: numberValue(counts?.FLAGGED),
      incomplete: numberValue(counts?.INCOMPLETE),
    };
  }, [selectedRun.data]);
  const submissionContext = useSubmissionContext(
    batchQuery.data?.institution_id ?? "",
  );
  const { options: programmes } = submissionContext;
  const programme = programmes.find(
    (item) => item.id === batchQuery.data?.programme_id,
  );
  const pinnedSettings = selectedRun.data
    ? Object.entries(selectedRun.data.ruleset_snapshot).filter(
        ([key, value]) =>
          [
            "structural_ruleset_version",
            "intake_rule_version",
            "apaar_ascii_digit_length",
            "academic_year",
            "programme_code",
            "source_label",
          ].includes(key) && ["string", "number"].includes(typeof value),
      )
    : [];

  if (!isUUID(batchId))
    return (
      <section className="empty-state">
        <h1>Submission unavailable</h1>
        <p>Choose a stored submission from the permitted history list.</p>
        <Link className="button secondary" href="/submissions">
          Back to submissions
        </Link>
      </section>
    );

  if (batchQuery.isPending)
    return <Loading label="Loading candidate and validation history…" />;
  if (batchQuery.isError)
    return (
      <ErrorPanel
        error={batchQuery.error}
        retry={() => void batchQuery.refetch()}
      />
    );
  const batch = batchQuery.data;
  const hasInitial = batch.validation_performed;
  const isBusy = validate.isPending || revalidate.isPending;

  if (runId && !isUUID(runId))
    return (
      <section className="empty-state" role="alert">
        <h1>Validation run unavailable</h1>
        <p>
          The selected run reference is not valid. Choose a saved run from
          history.
        </p>
        <button className="button secondary" onClick={() => navigate({}, true)}>
          Clear selected run
        </button>
      </section>
    );

  return (
    <div className="validation-page">
      <div className="page-heading heading-actions">
        <div>
          <p className="eyebrow">SYNTHETIC DATA · IMMUTABLE CANDIDATE</p>
          <h1>Student validation</h1>
          <p>
            {programme?.code ?? "Programme"} · {batch.academic_year} ·{" "}
            {batch.row_count.toLocaleString()} submitted records
          </p>
        </div>
        <Link className="button secondary" href="/submissions">
          Back to submissions
        </Link>
      </div>

      <section className="validation-notice" aria-label="Validation meaning">
        <strong>Local rule checks only</strong>
        <p>
          APAAR format checks are local syntax checks, not government identity
          verification. Findings are review signals, not fraud decisions.
          Candidate rows cannot be edited; corrections use a new complete CSV.
        </p>
      </section>

      <section
        className="panel validation-action"
        aria-labelledby="validation-action-title"
      >
        <div>
          <p className="eyebrow">EXPLICIT ACTION</p>
          <h2 id="validation-action-title">Run checks for this candidate</h2>
          <p>
            Validation creates a new immutable result. It does not change the
            submitted rows or activate this candidate.
          </p>
        </div>
        {admin && !hasInitial && batch.status === "COMPLETED" && (
          <button
            className="button primary"
            disabled={isBusy}
            onClick={() => {
              setAnnouncement("");
              validate.mutate();
            }}
          >
            {validate.isPending ? "Validating…" : "Run Validation"}
          </button>
        )}
        {admin && !hasInitial && batch.status !== "COMPLETED" && (
          <span className="status-badge neutral">
            CSV processing is incomplete; validation is unavailable
          </span>
        )}
        {admin && hasInitial && (
          <span className="status-badge neutral">Initial run recorded</span>
        )}
        {officer && hasInitial && (
          <button
            className="button primary"
            disabled={isBusy}
            onClick={() => {
              setAnnouncement("");
              revalidate.mutate();
            }}
          >
            {revalidate.isPending
              ? "Revalidating…"
              : "Run officer revalidation"}
          </button>
        )}
        {officer && !hasInitial && (
          <span className="status-badge neutral">
            Waiting for institution validation
          </span>
        )}
        {announcement && (
          <p className="form-help validation-announcement" role="status">
            {announcement}
          </p>
        )}
        {(validate.isError || revalidate.isError || exportFeedback.isError) && (
          <p className="form-error" role="alert">
            {validate.isError || revalidate.isError
              ? announcement
              : errorMessage(exportFeedback.error)}
          </p>
        )}
      </section>

      <section className="panel" aria-labelledby="runs-heading">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">APPEND-ONLY HISTORY</p>
            <h2 id="runs-heading">Validation runs</h2>
          </div>
          {runs.data && (
            <span className="quiet-label">
              {runs.data.pagination.total} saved run
              {runs.data.pagination.total === 1 ? "" : "s"}
            </span>
          )}
        </header>
        {runs.isPending ? (
          <Loading label="Loading validation runs…" />
        ) : runs.isError ? (
          <ErrorPanel error={runs.error} retry={() => void runs.refetch()} />
        ) : runs.data.data.length === 0 ? (
          <div className="empty-state">
            <h3>No validation run yet</h3>
            <p>
              The uploaded candidate is stored, but has not been locally
              checked.
            </p>
          </div>
        ) : (
          <>
            <div className="run-list">
              {runs.data.data.map((run) => (
                <button
                  type="button"
                  key={run.id}
                  className={`run-option ${run.id === runId ? "selected" : ""}`}
                  aria-pressed={run.id === runId}
                  onClick={() =>
                    navigate(
                      {
                        run_id: run.id,
                        row_page: undefined,
                        row_status: undefined,
                        finding_page: undefined,
                      },
                      true,
                    )
                  }
                >
                  <span>
                    <strong>
                      {run.kind === "INITIAL"
                        ? "Initial validation"
                        : "Officer revalidation"}
                    </strong>
                    <small>
                      <time dateTime={run.completed_at}>
                        {new Date(run.completed_at).toLocaleString()}
                      </time>
                    </small>
                  </span>
                  <span className="run-rule">{run.ruleset_version}</span>
                  <span
                    className={`freshness ${run.cross_current_freshness.toLowerCase()}`}
                  >
                    {run.cross_current_freshness === "FRESH"
                      ? "Assessment fresh"
                      : "Assessment stale"}
                  </span>
                </button>
              ))}
            </div>
            <Pagination
              label="Validation run history pagination"
              page={runPageNumber}
              pageSize={pageSize}
              total={runs.data.pagination.total}
              busy={runs.isFetching}
              change={(next) =>
                navigate(
                  {
                    run_page: next === 1 ? undefined : String(next),
                    run_id: undefined,
                  },
                  true,
                )
              }
            />
          </>
        )}
      </section>

      {!runId ||
      (runs.data?.pagination.total === 0 &&
        !runs.isPending) ? null : selectedRun.isPending ? (
        <Loading label="Loading selected run…" />
      ) : selectedRun.isError ? (
        <ErrorPanel
          error={selectedRun.error}
          retry={() => void selectedRun.refetch()}
        />
      ) : (
        <>
          <section className="panel" aria-labelledby="run-summary-heading">
            <header className="panel-heading">
              <div>
                <p className="eyebrow">
                  SELECTED RUN · {selectedRun.data.kind}
                </p>
                <h2 id="run-summary-heading">Run summary</h2>
                <p className="cell-note">{selectedRun.data.validity_label}</p>
              </div>
              <button
                className="button secondary small"
                disabled={exportFeedback.isPending}
                onClick={() =>
                  exportFeedback.mutate(new AbortController().signal)
                }
              >
                {exportFeedback.isPending
                  ? "Preparing CSV…"
                  : "Download masked feedback CSV"}
              </button>
            </header>
            <div className="validation-metrics">
              <div>
                <span>Ruleset</span>
                <strong>{selectedRun.data.ruleset_version}</strong>
              </div>
              <div>
                <span>Evaluated</span>
                <strong>
                  <time dateTime={selectedRun.data.evaluated_at}>
                    {new Date(selectedRun.data.evaluated_at).toLocaleString()}
                  </time>
                </strong>
              </div>
              <div>
                <span>Candidate records</span>
                <strong>{batch.row_count.toLocaleString()}</strong>
                <small>Candidate rows · not current enrolment</small>
              </div>
              <div>
                <span>Candidate demo ACTIVE rows</span>
                <strong>
                  {numberValue(
                    selectedRun.data.summary.candidate_demo_active_records,
                  ) ?? "Unavailable"}
                </strong>
                <small>
                  Candidate-only count under demo statuses; not current totals.
                </small>
              </div>
              <div>
                <span>Local status</span>
                <strong>
                  VALID {findingCounts.valid ?? "—"} · FLAGGED{" "}
                  {findingCounts.flagged ?? "—"} · INCOMPLETE{" "}
                  {findingCounts.incomplete ?? "—"}
                </strong>
                <small>For this immutable run only</small>
              </div>
              <div>
                <span>Current potential ACTIVE overlaps</span>
                <strong>
                  {currentMetricAvailable ? currentOverlaps : "Unavailable"}
                </strong>
                <small>
                  {selectedRun.data.cross_current_freshness === "STALE"
                    ? "Assessment is stale; this is not zero."
                    : assessment !== "COMPLETE"
                      ? "Comparison incomplete; this is not zero."
                      : "Same-year current ACTIVE matches at this assessment."}
                </small>
              </div>
              <div>
                <span>Historical assessment</span>
                <strong>As of this run</strong>
                <small>Past evidence is not a current-overlap count.</small>
              </div>
            </div>
            {pinnedSettings.length > 0 && (
              <dl
                className="pinned-settings"
                aria-label="Validation configuration captured by this run"
              >
                {pinnedSettings.map(([key, value]) => (
                  <div key={key}>
                    <dt>{key.replaceAll("_", " ")}</dt>
                    <dd>{String(value)}</dd>
                  </div>
                ))}
              </dl>
            )}
          </section>

          <ReviewActivation
            key={`${batchId}:${query.review_id ?? batchQuery.data.activation_review_id ?? "new"}`}
            batch={batchQuery.data}
            run={selectedRun.data}
            institutionName={
              submissionContext.institution.data?.name ?? "Institution"
            }
            programmeName={programme?.name ?? batchQuery.data.programme_id}
            reviewId={
              query.review_id ??
              batchQuery.data.activation_review_id ??
              undefined
            }
            omissionPage={stateNumber(query.omission_page)}
            onReviewChange={(reviewId, page) =>
              navigate({
                review_id: reviewId,
                omission_page: page && page > 1 ? String(page) : undefined,
              })
            }
            onRunChange={(nextRunId) => navigate({ run_id: nextRunId })}
          />

          <section className="panel" aria-labelledby="records-heading">
            <header className="panel-heading">
              <div>
                <p className="eyebrow">READ-ONLY SOURCE ROWS</p>
                <h2 id="records-heading">Student records</h2>
              </div>
              <label className="inline-filter">
                Validation status
                <select
                  value={rowStatus}
                  onChange={(event) =>
                    navigate({
                      row_status: event.target.value || undefined,
                      row_page: undefined,
                    })
                  }
                >
                  <option value="">All statuses</option>
                  {validStatuses.map((status) => (
                    <option key={status} value={status}>
                      {runStatusLabel(status)}
                    </option>
                  ))}
                </select>
              </label>
            </header>
            {rows.isPending ? (
              <Loading label="Loading student rows…" />
            ) : rows.isError ? (
              <ErrorPanel
                error={rows.error}
                retry={() => void rows.refetch()}
              />
            ) : rows.data.data.length === 0 ? (
              <div className="empty-state">
                <h3>No records match this view</h3>
                <p>
                  Try another status filter. Original submitted rows remain
                  unchanged.
                </p>
              </div>
            ) : (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Student records; scroll horizontally on small screens"
              >
                <table className="validation-table">
                  <caption className="sr-only">
                    Read-only student records for the selected validation run
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">CSV record</th>
                      <th scope="col">Student</th>
                      <th scope="col">College ID</th>
                      <th scope="col">Programme / year</th>
                      <th scope="col">Category</th>
                      <th scope="col">Enrolment</th>
                      <th scope="col">APAAR (masked)</th>
                      <th scope="col">Run status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.data.data.map((row) => (
                      <tr key={row.id}>
                        <td>Record {row.source_row_number}</td>
                        <td>{row.student_name || "Name missing"}</td>
                        <td>{row.college_student_id || "Missing"}</td>
                        <td>
                          {row.programme_code}
                          <small className="cell-note">
                            {row.academic_year}
                          </small>
                        </td>
                        <td>{row.admission_category || "Missing"}</td>
                        <td>
                          {row.enrollment_status || "Missing"}
                          <small className="cell-note">
                            {row.enrollment_date ?? "Date unavailable"}
                          </small>
                        </td>
                        <td>
                          <span className="masked-value">
                            {row.apaar_id_masked}
                          </span>
                          <small className="cell-note">
                            {row.apaar_verification_status === "NOT_CHECKED"
                              ? "Not government verified"
                              : ""}
                          </small>
                        </td>
                        <td>
                          <span
                            className={`status-badge ${row.validation_status === "VALID" ? "active" : row.validation_status === "INCOMPLETE" ? "warning" : "neutral"}`}
                          >
                            {runStatusLabel(row.validation_status)}
                            {row.validation_status === "VALID"
                              ? " · local"
                              : ""}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {rows.data && (
              <Pagination
                label="Student records pagination"
                page={rowPageNumber}
                pageSize={pageSize}
                total={rows.data.pagination.total}
                busy={rows.isFetching}
                change={(next) =>
                  navigate({ row_page: next === 1 ? undefined : String(next) })
                }
              />
            )}
          </section>

          <section className="panel" aria-labelledby="findings-heading">
            <header className="panel-heading">
              <div>
                <p className="eyebrow">EVIDENCE-LINKED REVIEW SIGNALS</p>
                <h2 id="findings-heading">Findings</h2>
              </div>
              <span className="quiet-label">Not fraud determinations</span>
            </header>
            <form
              className="validation-filters"
              onSubmit={(event) => {
                event.preventDefault();
                const ruleInput = String(
                  new FormData(event.currentTarget).get("rule_code") ?? "",
                )
                  .trim()
                  .toUpperCase();
                if (ruleInput && !/^[A-Z0-9_]{1,64}$/.test(ruleInput)) {
                  setFilterError(
                    "Use an exact rule code with uppercase letters, digits or underscores.",
                  );
                  return;
                }
                setFilterError("");
                navigate({
                  finding_rule: ruleInput || undefined,
                  finding_page: undefined,
                });
              }}
            >
              <label>
                Rule code
                <input
                  key={query.finding_rule ?? "all"}
                  name="rule_code"
                  defaultValue={query.finding_rule ?? ""}
                  placeholder="All rule codes"
                  aria-label="Filter by rule code"
                />
              </label>
              <label>
                Severity
                <select
                  value={query.finding_severity ?? ""}
                  onChange={(event) =>
                    navigate({
                      finding_severity: event.target.value || undefined,
                      finding_page: undefined,
                    })
                  }
                >
                  <option value="">All severities</option>
                  {severityOptions.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                Issue type
                <select
                  value={query.finding_classification ?? ""}
                  onChange={(event) =>
                    navigate({
                      finding_classification: event.target.value || undefined,
                      finding_page: undefined,
                    })
                  }
                >
                  <option value="">All issue types</option>
                  <option value="ACTIVATION_BLOCKING">
                    Activation-blocking
                  </option>
                  <option value="REVIEWABLE">Reviewable</option>
                </select>
              </label>
              <button className="button secondary" type="submit">
                Apply rule filter
              </button>
              {(query.finding_rule ||
                query.finding_severity ||
                query.finding_classification) && (
                <button
                  className="button secondary"
                  type="button"
                  onClick={(event) => {
                    event.currentTarget.form?.reset();
                    navigate({
                      finding_rule: undefined,
                      finding_severity: undefined,
                      finding_classification: undefined,
                      finding_page: undefined,
                    });
                  }}
                >
                  Clear filters
                </button>
              )}
            </form>
            {filterError && (
              <p className="form-error" role="alert">
                {filterError}
              </p>
            )}
            {findings.isPending ? (
              <Loading label="Loading evidence-linked findings…" />
            ) : findings.isError ? (
              <ErrorPanel
                error={findings.error}
                retry={() => void findings.refetch()}
              />
            ) : findings.data.data.length === 0 ? (
              <div className="empty-state">
                <h3>No findings match these filters</h3>
                <p>
                  This means no findings were returned for the selected run and
                  filters. Valid means local checks only, never official
                  verification.
                </p>
              </div>
            ) : (
              <div className="finding-list">
                {findings.data.data.map((finding: Finding) => {
                  const copy = findingGuidance(finding);
                  const evidence = safeEvidence(finding.evidence);
                  const matchContext = finding.evidence.match_context;
                  return (
                    <article className="finding-card" key={finding.id}>
                      <header>
                        <div>
                          <span
                            className={`status-badge ${finding.classification === "ACTIVATION_BLOCKING" ? "warning" : "neutral"}`}
                          >
                            {finding.classification === "ACTIVATION_BLOCKING"
                              ? "Activation-blocking"
                              : "Reviewable"}
                          </span>
                          <span className="status-badge neutral">
                            {finding.severity}
                          </span>
                          {finding.cross_current_freshness === "STALE" && (
                            <span className="status-badge warning">
                              Assessment stale
                            </span>
                          )}
                        </div>
                        <code>{finding.rule_code}</code>
                      </header>
                      {finding.rule_code ===
                        "POTENTIAL_CROSS_INSTITUTION_DUPLICATE" && (
                        <p
                          className={`match-context ${matchContext === "CURRENT_ACTIVE" ? "current" : "informational"}`}
                        >
                          {crossLabel(
                            matchContext,
                            finding.cross_current_freshness,
                          )}
                        </p>
                      )}
                      <div className="finding-explanation">
                        <h3>What went wrong</h3>
                        <p>{copy.what}</p>
                        <h3>Why it was flagged</h3>
                        <p>{finding.explanation}</p>
                        <h3>What to do next</h3>
                        <p>{copy.next}</p>
                      </div>
                      {evidence.length > 0 && (
                        <dl className="evidence-list">
                          {evidence.map(([label, value]) => (
                            <div key={label}>
                              <dt>{label}</dt>
                              <dd>{value}</dd>
                            </div>
                          ))}
                        </dl>
                      )}
                      <footer>
                        <span>
                          {finding.field_name
                            ? `Field: ${finding.field_name}`
                            : "Batch-level evidence"}
                        </span>
                        <span>
                          CSV record{" "}
                          {typeof finding.evidence.source_row_number ===
                          "number"
                            ? finding.evidence.source_row_number
                            : "grouped"}
                        </span>
                        <time dateTime={finding.evaluated_at}>
                          {new Date(finding.evaluated_at).toLocaleString()}
                        </time>
                      </footer>
                    </article>
                  );
                })}
              </div>
            )}
            {findings.data && (
              <Pagination
                label="Finding results pagination"
                page={findingPageNumber}
                pageSize={pageSize}
                total={findings.data.pagination.total}
                busy={findings.isFetching}
                change={(next) =>
                  navigate({
                    finding_page: next === 1 ? undefined : String(next),
                  })
                }
              />
            )}
          </section>
        </>
      )}
      <p className="data-note">
        All candidate records and validation evidence are synthetic demo data.
        Historical uploads and previous validation runs remain preserved. A
        finding does not edit or remove the source row.
      </p>
    </div>
  );
}
