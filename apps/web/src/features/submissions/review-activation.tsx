"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { ApiError, errorMessage, isUUID } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";

type Batch = components["schemas"]["BatchResponse"];
type Run = components["schemas"]["RunResponse"];
type Review = components["schemas"]["ReviewResponse"];
type Activation = components["schemas"]["ActivationResponse"];
type ObjectValue = Record<string, unknown>;

const omissionPageSize = 20;

function object(value: unknown): ObjectValue | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as ObjectValue)
    : null;
}

function integer(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) ? value : null;
}

function count(value: unknown): string {
  const result = integer(value);
  return result === null ? "Unavailable" : result.toLocaleString();
}

function label(value: string): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (c) => c.toUpperCase());
}

function nestedCount(value: unknown, key: string): unknown {
  return object(value)?.[key];
}

function valueString(value: unknown): string {
  if (typeof value === "string" || typeof value === "number")
    return String(value);
  return "Unavailable";
}

function activationError(error: unknown): string {
  if (!(error instanceof ApiError))
    return "The activation result is uncertain. We are checking the candidate and review status before allowing another attempt.";
  switch (error.code) {
    case "SCOPE_REVISION_CONFLICT":
      return "The current snapshot changed since this review. This receipt is no longer usable; create a fresh review before activating.";
    case "ACTIVATION_CONFLICT":
      return "Another activation is using this scope. Confirm the latest candidate and review state, then create a fresh review.";
    case "REVALIDATION_REQUIRED":
    case "REVIEW_POLICY_CHANGED":
      return "The selected run or review policy is no longer compatible. Select a current validation run and create a new review.";
    case "CANDIDATE_INELIGIBLE":
      return "The candidate has activation-blocking structural issues. Review the blocking rules and correct the source in a new CSV.";
    case "ALREADY_ACTIVATED":
      return "This candidate was already activated. Refresh its provenance to confirm the current state.";
    case "OMISSIONS_ACKNOWLEDGMENT_REQUIRED":
      return "This replacement omits earlier records. Check the omission acknowledgment and try again.";
    default:
      return error.status >= 500 || error.status === 0
        ? "The activation result is uncertain. We are checking the candidate and review status before allowing another attempt."
        : errorMessage(error);
  }
}

function CountCard({
  title,
  value,
  note,
}: {
  title: string;
  value: unknown;
  note?: string;
}) {
  return (
    <div className="review-count-card">
      <span>{title}</span>
      <strong>{count(value)}</strong>
      {note && <small>{note}</small>}
    </div>
  );
}

function CountComparison({
  current,
  candidate,
  delta,
}: {
  current: ObjectValue | null;
  candidate: ObjectValue | null;
  delta: ObjectValue | null;
}) {
  if (!candidate) return <p>Candidate comparison is unavailable.</p>;
  const categoriesCurrent = object(current?.categories);
  const categoriesCandidate = object(candidate.categories);
  const categoryDeltas = object(delta?.categories);
  const categories = Object.keys(categoriesCandidate ?? {});
  const statusesCurrent = object(current?.statuses);
  const statusesCandidate = object(candidate.statuses);
  const statuses = Object.keys(statusesCandidate ?? {});
  return (
    <>
      {categories.length > 0 && (
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Category count differences"
        >
          <table className="review-table">
            <caption>
              Candidate and current category counts · local accounting
            </caption>
            <thead>
              <tr>
                <th scope="col">Category</th>
                <th scope="col">Current declared</th>
                <th scope="col">Candidate declared</th>
                <th scope="col">Current active</th>
                <th scope="col">Candidate active</th>
                <th scope="col">Declared change</th>
                <th scope="col">ACTIVE change</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((key) => {
                const before = object(categoriesCurrent?.[key]);
                const after = object(categoriesCandidate?.[key]);
                const change = object(categoryDeltas?.[key]);
                return (
                  <tr key={key}>
                    <th scope="row">{label(key)}</th>
                    <td>
                      {current
                        ? count(before?.declared_records)
                        : "No current snapshot"}
                    </td>
                    <td>{count(after?.declared_records)}</td>
                    <td>
                      {current
                        ? count(before?.demo_active_records)
                        : "No current snapshot"}
                    </td>
                    <td>{count(after?.demo_active_records)}</td>
                    <td>{count(change?.declared_records)}</td>
                    <td>{count(change?.demo_active_records)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {statuses.length > 0 && (
        <div
          className="table-scroll review-status-table"
          tabIndex={0}
          role="region"
          aria-label="Enrolment status differences"
        >
          <table className="review-table">
            <caption>
              Declared enrolment status counts · not official regulatory
              accounting
            </caption>
            <thead>
              <tr>
                <th scope="col">Status</th>
                <th scope="col">Current</th>
                <th scope="col">Candidate</th>
                <th scope="col">Change</th>
              </tr>
            </thead>
            <tbody>
              {statuses.map((key) => (
                <tr key={key}>
                  <th scope="row">{label(key)}</th>
                  <td>
                    {current
                      ? count(statusesCurrent?.[key])
                      : "No current snapshot"}
                  </td>
                  <td>{count(statusesCandidate?.[key])}</td>
                  <td>{count(nestedCount(delta?.statuses, key))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

export function ReviewActivation({
  batch,
  run,
  institutionName,
  programmeName,
  reviewId,
  omissionPage,
  onReviewChange,
  onRunChange,
}: {
  batch: Batch;
  run: Run;
  institutionName: string;
  programmeName: string;
  reviewId?: string;
  omissionPage: number;
  onReviewChange: (reviewId: string | undefined, page?: number) => void;
  onRunChange: (runId: string) => void;
}) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const admin = session?.user.role === "INSTITUTION_ADMIN";
  const officer = session?.user.role === "AICTE_OFFICER";
  const [completeReplacement, setCompleteReplacement] = useState(false);
  const [reviewWarnings, setReviewWarnings] = useState(false);
  const [omissionsAcknowledged, setOmissionsAcknowledged] = useState(false);
  const [status, setStatus] = useState("");
  const [uncertain, setUncertain] = useState(false);
  const [statusCheckFailed, setStatusCheckFailed] = useState(false);
  const [retryAllowed, setRetryAllowed] = useState(false);
  const [requiresFreshReview, setRequiresFreshReview] = useState(false);
  const [activationResult, setActivationResult] = useState<Activation | null>(
    null,
  );
  const [copyMessage, setCopyMessage] = useState("");
  const page = Math.max(1, omissionPage);
  const baseKey = [
    "private",
    session?.generation,
    session?.user.id,
    "validation",
    batch.id,
  ];
  const receiptKey = [...baseKey, "review", reviewId, page];
  const receipt = useQuery({
    queryKey: receiptKey,
    enabled: !!session && isUUID(batch.id) && isUUID(reviewId),
    queryFn: ({ signal }) =>
      request<Review>(
        `/submissions/${batch.id}/reviews/${reviewId}?page=${page}&page_size=${omissionPageSize}`,
        { signal },
      ),
  });
  const pinnedRunId = receipt.data?.validation_run_id ?? run.id;
  const runFindings = useQuery({
    queryKey: [...baseKey, "review-findings", pinnedRunId],
    enabled: !!session && !!receipt.data && isUUID(pinnedRunId),
    queryFn: ({ signal }) =>
      request<components["schemas"]["Page_FindingResponse_"]>(
        `/submissions/${batch.id}/findings?run_id=${pinnedRunId}&page=1&page_size=100`,
        { signal },
      ),
  });

  const createReview = useMutation({
    mutationFn: () =>
      request<Review>(`/submissions/${batch.id}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ validation_run_id: run.id }),
      }),
    retry: false,
    networkMode: "always",
    onSuccess: (created) => {
      setStatus(
        "A new immutable review receipt is saved. Activation has not occurred.",
      );
      setRequiresFreshReview(false);
      setUncertain(false);
      setRetryAllowed(false);
      setCompleteReplacement(false);
      setReviewWarnings(false);
      setOmissionsAcknowledged(false);
      onReviewChange(created.id, 1);
    },
    onError: (error) => {
      setStatus(
        error instanceof ApiError && error.status >= 400 && error.status < 500
          ? `Review was not accepted. ${errorMessage(error)}`
          : "Review creation outcome is unknown. No activation occurred and the request was not retried. Refresh candidate history before deliberately creating another review.",
      );
    },
  });

  const clearAcknowledgments = () => {
    setCompleteReplacement(false);
    setReviewWarnings(false);
    setOmissionsAcknowledged(false);
  };

  const confirmActivation = useMutation({
    mutationFn: () => {
      if (!receipt.data)
        throw new Error("A selected review receipt is required");
      return request<Activation>(`/submissions/${batch.id}/activate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          review_id: receipt.data.id,
          expected_scope_revision: receipt.data.expected_scope_revision,
          confirm_complete_replacement: true,
          acknowledge_review_warnings: true,
          acknowledge_omissions:
            integer(receipt.data.snapshot.omitted_record_count)! > 0
              ? omissionsAcknowledged
              : false,
        }),
      });
    },
    retry: false,
    networkMode: "always",
    onSuccess: async (result) => {
      setUncertain(false);
      setRetryAllowed(false);
      setRequiresFreshReview(false);
      setActivationResult(result);
      setStatus(
        "Activation confirmed by the API. This candidate is now the current snapshot.",
      );
      await queryClient.invalidateQueries({ queryKey: [...baseKey, "batch"] });
      await queryClient.invalidateQueries({ queryKey: [...baseKey, "review"] });
      await queryClient.invalidateQueries({ queryKey: ["private"] });
    },
    onError: async (error) => {
      clearAcknowledgments();
      if (error instanceof ApiError && error.status === 409) {
        setRequiresFreshReview(
          error.code === "SCOPE_REVISION_CONFLICT" ||
            error.code === "ACTIVATION_CONFLICT" ||
            error.code === "REVIEW_POLICY_CHANGED",
        );
        setUncertain(false);
        setRetryAllowed(false);
        setStatus(activationError(error));
        await queryClient.invalidateQueries({
          queryKey: [...baseKey, "batch"],
        });
        await queryClient.invalidateQueries({
          queryKey: [...baseKey, "review"],
        });
        return;
      }
      if (
        error instanceof ApiError &&
        error.status >= 400 &&
        error.status < 500
      ) {
        setStatus(activationError(error));
        return;
      }
      setUncertain(true);
      setRetryAllowed(false);
      setStatus(activationError(error));
      await reconcileActivation();
    },
  });

  async function reconcileActivation() {
    if (!receipt.data) return;
    setStatusCheckFailed(false);
    try {
      const [freshBatch, freshReceipt] = await Promise.all([
        request<Batch>(`/submissions/${batch.id}`),
        request<Review>(
          `/submissions/${batch.id}/reviews/${receipt.data.id}?page=${page}&page_size=${omissionPageSize}`,
        ),
      ]);
      queryClient.setQueryData([...baseKey, "batch"], freshBatch);
      queryClient.setQueryData(receiptKey, freshReceipt);
      const provenance = object(freshBatch.activation_provenance);
      const activatedByThisReceipt =
        freshBatch.activation_review_id === receipt.data.id ||
        provenance?.review_id === receipt.data.id ||
        freshReceipt.review_state === "CONSUMED";
      if (activatedByThisReceipt && freshBatch.activated_at) {
        setUncertain(false);
        setRetryAllowed(false);
        setActivationResult({
          batch_id: freshBatch.id,
          scope_id: freshBatch.scope_id,
          review_id: receipt.data.id,
          validation_run_id: freshReceipt.validation_run_id,
          previous_batch_id: freshReceipt.expected_current_batch_id,
          scope_revision:
            integer(provenance?.scope_revision) ??
            freshReceipt.expected_scope_revision + 1,
          activated_by: freshReceipt.reviewed_by,
          activated_at: freshBatch.activated_at,
          counts: object(freshReceipt.snapshot.candidate_counts) ?? {},
          source_label: "DEMO",
        });
        setStatus(
          "Activation is confirmed in candidate provenance. No second activation was sent.",
        );
        return;
      }
      if (
        freshBatch.activated_at === null &&
        freshBatch.snapshot_state === "CANDIDATE" &&
        freshReceipt.review_state === "READY"
      ) {
        setUncertain(true);
        setRetryAllowed(true);
        setStatus(
          "Status checked: no activation is recorded and this review is still READY. Review the details and acknowledgments again before a deliberate new attempt.",
        );
        return;
      }
      setUncertain(true);
      setRetryAllowed(false);
      setRequiresFreshReview(freshReceipt.review_state === "STALE");
      setStatus(
        `Status checked. The batch is ${freshBatch.snapshot_state.toLowerCase()} and the receipt is ${freshReceipt.review_state.toLowerCase()}; another activation is not available from this receipt.`,
      );
    } catch {
      setUncertain(true);
      setRetryAllowed(false);
      setStatusCheckFailed(true);
      setStatus(
        "Activation remains uncertain because status could not be checked. Retry status checking; do not send another activation request yet.",
      );
    }
  }

  const batchIsActivated =
    !!batch.activation_review_id && batch.activation_review_id === reviewId;
  const activated = batchIsActivated || !!activationResult;
  const canCreateReceipt =
    admin && !batch.activated_at && batch.status === "COMPLETED";
  const freshReview = useMutation({
    mutationFn: () =>
      request<Review>(`/submissions/${batch.id}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ validation_run_id: run.id }),
      }),
    retry: false,
    networkMode: "always",
    onSuccess: (created) => {
      setRequiresFreshReview(false);
      setUncertain(false);
      setRetryAllowed(false);
      clearAcknowledgments();
      setStatus(
        "A fresh immutable review was created for the selected validation run. Check its new comparison before activation.",
      );
      onReviewChange(created.id, 1);
    },
    onError: (error) =>
      setStatus(`A fresh review could not be created. ${errorMessage(error)}`),
  });

  if (!isUUID(reviewId)) {
    return (
      <section
        className="panel review-entry"
        aria-labelledby="review-entry-title"
      >
        <div>
          <p className="eyebrow">SNAPSHOT REPLACEMENT</p>
          <h2 id="review-entry-title">Review candidate snapshot</h2>
          <p>
            Compare this completed validation run with the current declaration.
            Creating a review does not activate the candidate.
          </p>
        </div>
        {canCreateReceipt ? (
          <button
            className="button primary"
            disabled={createReview.isPending}
            onClick={() => createReview.mutate()}
          >
            {createReview.isPending
              ? "Preparing immutable review…"
              : "Create review receipt"}
          </button>
        ) : officer ? (
          <p className="form-help">
            Officers may inspect a permitted receipt by opening its review link.
            Only the institution administrator can create or activate.
          </p>
        ) : (
          <span className="status-badge neutral">
            This snapshot is not eligible for a new review
          </span>
        )}
        {createReview.isError && (
          <p className="form-error" role="alert">
            {status}
          </p>
        )}
      </section>
    );
  }

  if (receipt.isPending)
    return (
      <section className="panel">
        <Loading label="Loading immutable review receipt…" />
      </section>
    );
  if (receipt.isError)
    return (
      <section className="panel">
        <ErrorPanel
          error={receipt.error}
          retry={() => void receipt.refetch()}
        />
      </section>
    );

  const data = receipt.data;
  const snapshot = data.snapshot;
  const current = object(snapshot.current_counts);
  const candidate = object(snapshot.candidate_counts);
  const delta = object(snapshot.delta_counts);
  const eligibility = object(data.eligibility);
  const blockingRules = Array.isArray(eligibility?.structural_blocking_rules)
    ? eligibility.structural_blocking_rules.filter(
        (item): item is string => typeof item === "string",
      )
    : [];
  const blockingReasons = Array.isArray(eligibility?.blocking_reasons)
    ? eligibility.blocking_reasons.filter(
        (item): item is string => typeof item === "string",
      )
    : [];
  const comparisonComplete = snapshot.identifier_comparison === "COMPLETE";
  const omittedCount = integer(snapshot.omitted_record_count);
  const activeOmittedCount = integer(
    snapshot.previously_active_omitted_record_count,
  );
  const hasOmissions = omittedCount !== null && omittedCount > 0;
  const receiptReady =
    data.review_state === "READY" &&
    eligibility?.eligible === true &&
    data.validation_run_id === run.id &&
    !requiresFreshReview;
  const acknowledged =
    completeReplacement &&
    reviewWarnings &&
    (!hasOmissions || omissionsAcknowledged);
  const activationDisabled =
    !admin ||
    !receiptReady ||
    !acknowledged ||
    confirmActivation.isPending ||
    activated ||
    (uncertain && !retryAllowed);
  const transitions = (key: string) => {
    const rows = snapshot[key];
    return Array.isArray(rows)
      ? rows.flatMap((entry) => {
          const item = object(entry);
          if (
            !item ||
            typeof item.from !== "string" ||
            typeof item.to !== "string"
          )
            return [];
          return [
            `${item.from} → ${item.to}: ${count(item.records)} record${item.records === 1 ? "" : "s"}`,
          ];
        })
      : [];
  };
  const assessment = object(data.assessment_now);
  const overlap = assessment?.current_overlap_records;
  const crossFreshness = assessment?.cross_current_freshness;
  const matchingAssessment = assessment?.matching_assessment;

  return (
    <section className="panel review-workspace" aria-labelledby="review-title">
      <header className="panel-heading review-heading">
        <div>
          <p className="eyebrow">
            IMMUTABLE REVIEW RECEIPT · {data.review_policy_version}
          </p>
          <h2 id="review-title">Review replacement snapshot</h2>
          <p>{data.receipt_label}</p>
        </div>
        <span
          className={`status-badge ${data.review_state === "READY" ? "active" : data.review_state === "STALE" || data.review_state === "BLOCKED" ? "warning" : "neutral"}`}
        >
          {data.review_state}
        </span>
      </header>

      <div className="review-scope-grid">
        <div>
          <span>Institution</span>
          <strong>{institutionName}</strong>
          <small>{data.institution_id}</small>
        </div>
        <div>
          <span>Programme</span>
          <strong>{programmeName}</strong>
          <small>{data.programme_id}</small>
        </div>
        <div>
          <span>Academic year</span>
          <strong>{data.academic_year}</strong>
        </div>
        <div>
          <span>Candidate</span>
          <strong>{data.batch_id}</strong>
          <small>Complete replacement snapshot</small>
        </div>
        <div>
          <span>Selected validation run</span>
          <strong>{data.validation_run_id}</strong>
          <small>
            {data.validation_run_id === run.id
              ? "Matches selected run"
              : "Receipt is pinned to a different run"}
          </small>
        </div>
        <div>
          <span>Scope revision reviewed</span>
          <strong>{data.expected_scope_revision}</strong>
          <small>
            {data.expected_current_batch_id
              ? `Current candidate ${data.expected_current_batch_id}`
              : "No current snapshot at review time"}
          </small>
        </div>
        <div>
          <span>Review created</span>
          <strong>
            <time dateTime={data.created_at}>
              {new Date(data.created_at).toLocaleString()}
            </time>
          </strong>
          <small>Reviewer {data.reviewed_by}</small>
        </div>
        <div>
          <span>Current assessment</span>
          <strong>
            {crossFreshness === "STALE"
              ? "Stale"
              : crossFreshness === "FRESH"
                ? "Fresh"
                : "Unavailable"}
          </strong>
          <small>
            {typeof overlap === "number" &&
            crossFreshness === "FRESH" &&
            matchingAssessment === "COMPLETE"
              ? `${overlap} current potential overlaps at this assessment`
              : "Current overlap count unavailable; this is not zero."}
          </small>
        </div>
      </div>

      <div className="review-callout">
        <strong>Candidate totals are separate from current enrolment.</strong>
        <span>
          Only activation changes the current reference. Omitted records mean
          absent from this replacement; they are not automatically withdrawals
          or transfers.
        </span>
        <span>
          All capacities and active-status counts shown here are configured
          local comparisons, not official AICTE policy.
        </span>
      </div>

      <div className="review-count-grid">
        <CountCard
          title="Current declared records"
          value={current?.declared_records}
          note={current ? "Activated snapshot only" : "No current snapshot"}
        />
        <CountCard
          title="Candidate declared records"
          value={candidate?.declared_records}
          note="This candidate only"
        />
        <CountCard
          title="Current active enrolments"
          value={current?.demo_active_records}
          note={current ? "Activated snapshot only" : "No current snapshot"}
        />
        <CountCard
          title="Candidate active enrolments"
          value={candidate?.demo_active_records}
          note="Internal status rule; not official policy"
        />
        <CountCard
          title="Added identifiers"
          value={snapshot.added_record_count}
        />
        <CountCard
          title="Retained identifiers"
          value={snapshot.retained_record_count}
        />
        <CountCard
          title="Omitted records"
          value={snapshot.omitted_record_count}
          note="Absence does not infer withdrawal"
        />
        <CountCard
          title="Previously ACTIVE omissions"
          value={snapshot.previously_active_omitted_record_count}
          note="Require explicit acknowledgment"
        />
      </div>

      <div className="review-subsection">
        <h3>Category and status comparison</h3>
        <CountComparison
          current={current}
          candidate={candidate}
          delta={delta}
        />
        <div className="transition-grid">
          <div>
            <strong>Category changes among retained records</strong>
            {transitions("category_transitions").length ? (
              <ul>
                {transitions("category_transitions").map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p>
                {snapshot.category_transitions === null
                  ? "Unavailable because identifier comparison is ambiguous."
                  : "No category changes."}
              </p>
            )}
          </div>
          <div>
            <strong>Enrolment status changes among retained records</strong>
            {transitions("status_transitions").length ? (
              <ul>
                {transitions("status_transitions").map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p>
                {snapshot.status_transitions === null
                  ? "Unavailable because identifier comparison is ambiguous."
                  : "No status changes."}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="review-subsection">
        <div className="section-inline-heading">
          <div>
            <h3>Omitted identifiers</h3>
            <p>
              Previously declared identifiers missing from this candidate. They
              are not treated as withdrawn or transferred.
            </p>
          </div>
          {data.omission_pagination && (
            <span>
              {data.omission_pagination.total} total ·{" "}
              {activeOmittedCount ?? "Unavailable"} previously ACTIVE
            </span>
          )}
        </div>
        {!comparisonComplete ||
        data.omitted_records === null ||
        data.omission_pagination === null ? (
          <div className="empty-state compact">
            <h4>Omission comparison unavailable</h4>
            <p>
              Ambiguous identifiers prevent a reliable comparison. Unavailable
              does not mean zero; structural eligibility blocks activation.
            </p>
          </div>
        ) : data.omitted_records.length === 0 ? (
          <div className="empty-state compact">
            <h4>No omitted identifiers</h4>
            <p>
              The complete identifier comparison found no records from the
              current declaration missing in the candidate.
            </p>
          </div>
        ) : (
          <>
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="Omitted student identifiers"
            >
              <table className="review-table">
                <caption>
                  Omitted identifiers from the previously current snapshot
                </caption>
                <thead>
                  <tr>
                    <th scope="col">College student ID</th>
                    <th scope="col">Prior CSV record</th>
                    <th scope="col">Prior status</th>
                    <th scope="col">Prior category</th>
                    <th scope="col">Interpretation</th>
                  </tr>
                </thead>
                <tbody>
                  {data.omitted_records.map((item) => (
                    <tr key={item.record_version_id}>
                      <th scope="row">
                        {item.college_student_id || "Missing identifier"}
                      </th>
                      <td>{item.source_row_number}</td>
                      <td>
                        <span
                          className={`status-badge ${item.previous_enrollment_status === "ACTIVE" ? "warning" : "neutral"}`}
                        >
                          {item.previous_enrollment_status}
                        </span>
                      </td>
                      <td>{item.previous_admission_category}</td>
                      <td>
                        {item.previous_enrollment_status === "ACTIVE"
                          ? "Previously ACTIVE; omission acknowledgment required"
                          : "Absent from replacement; not an inferred withdrawal"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              label="Omitted records pagination"
              page={data.omission_pagination.page}
              pageSize={data.omission_pagination.page_size}
              total={data.omission_pagination.total}
              busy={receipt.isFetching}
              change={(next) => onReviewChange(data.id, next)}
            />
          </>
        )}
      </div>

      <div className="review-subsection">
        <div className="section-inline-heading">
          <div>
            <h3>Eligibility and validation findings</h3>
            <p>
              Structural issues block activation. Reviewable APAAR, duplicate
              and intake findings stay visible but do not automatically block
              when rows remain countable.
            </p>
          </div>
          <Link
            className="button secondary small"
            href={`/submissions/${batch.id}?run_id=${data.validation_run_id}#findings`}
          >
            Open selected run findings
          </Link>
        </div>
        <div className="finding-classifications">
          <div className="finding-classification blocking">
            <strong>Activation-blocking structural findings</strong>
            <span>
              {Array.isArray(snapshot.blocking_finding_ids)
                ? snapshot.blocking_finding_ids.length
                : "Unavailable"}{" "}
              at review · {blockingRules.length} current structural rule
              {blockingRules.length === 1 ? "" : "s"}
            </span>
            {blockingRules.length > 0 ? (
              <ul>
                {blockingRules.map((rule) => (
                  <li key={rule}>{rule}</li>
                ))}
              </ul>
            ) : (
              <p>
                {blockingReasons.includes("STRUCTURAL_BLOCKERS")
                  ? "Inspect the selected validation run for blocker evidence."
                  : "No current structural blocker was reported."}
              </p>
            )}
          </div>
          <div className="finding-classification reviewable">
            <strong>Reviewable findings</strong>
            <span>
              {count(snapshot.reviewable_finding_count)} findings pinned to this
              run
            </span>
            <p>
              Missing or malformed APAAR, possible overlaps, and comparisons
              against configured intake rules are not official identity
              verification, proof of fraud, or official AICTE violations.
            </p>
          </div>
        </div>
        {runFindings.isError && (
          <ErrorPanel
            error={runFindings.error}
            retry={() => void runFindings.refetch()}
          />
        )}
        {runFindings.data && runFindings.data.data.length > 0 && (
          <div
            className="review-findings-list"
            aria-label="Selected run evidence summary"
          >
            {runFindings.data.data.map((finding) => (
              <article key={finding.id}>
                <span
                  className={`status-badge ${finding.classification === "ACTIVATION_BLOCKING" ? "warning" : "neutral"}`}
                >
                  {finding.classification === "ACTIVATION_BLOCKING"
                    ? "Activation-blocking"
                    : "Reviewable"}
                </span>
                <code>{finding.rule_code}</code>
                <span>{finding.explanation}</span>
              </article>
            ))}
            {runFindings.data.pagination.total >
              runFindings.data.data.length && (
              <p>
                Showing {runFindings.data.data.length} of{" "}
                {runFindings.data.pagination.total} findings. Open the selected
                run for the full paginated evidence list.
              </p>
            )}
          </div>
        )}
      </div>

      <div className="review-subsection">
        <h3>Final activation confirmation</h3>
        <p>
          This receipt records the comparison presented; it is not proof that it
          was read. Confirm the exact scope and review above before activation.
          The API will recheck permissions, structural eligibility and scope
          revision in one transaction.
        </p>
        {data.review_state === "STALE" && (
          <p className="form-error" role="alert">
            This review is stale because its scope revision changed. It cannot
            be activated.
          </p>
        )}
        {data.review_state === "BLOCKED" && (
          <p className="form-error" role="alert">
            This candidate is blocked. Resolve structural issues in a new CSV or
            create a compatible new validation run and review.
          </p>
        )}
        {activated || data.review_state === "CONSUMED" ? (
          <div className="activation-confirmed" role="status">
            <strong>
              {batch.snapshot_state === "CANDIDATE" && activationResult
                ? "Activation confirmed · refreshing current state"
                : batch.snapshot_state === "CURRENT"
                  ? "Current snapshot activated"
                  : "Snapshot was activated and is now historical"}
            </strong>
            <span>
              {batch.activated_at
                ? new Date(batch.activated_at).toLocaleString()
                : activationResult
                  ? new Date(activationResult.activated_at).toLocaleString()
                  : "Activation time unavailable"}{" "}
              · scope revision{" "}
              {activationResult?.scope_revision ??
                valueString(
                  object(batch.activation_provenance)?.scope_revision,
                )}
            </span>
            <span>
              Current status: {batch.snapshot_state}. Historical batches and
              submitted rows remain preserved.
            </span>
          </div>
        ) : admin && canCreateReceipt ? (
          <>
            <div className="activation-checklist">
              <label>
                <input
                  type="checkbox"
                  checked={completeReplacement}
                  onChange={(event) =>
                    setCompleteReplacement(event.target.checked)
                  }
                />
                I confirm this CSV is the complete replacement declaration for
                this institution, programme, academic year and all configured
                admission categories.
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={reviewWarnings}
                  onChange={(event) => setReviewWarnings(event.target.checked)}
                />
                I reviewed the APAAR, possible duplicate and configured local
                intake findings. I understand these are review signals, not
                official verification or fraud determinations.
              </label>
              {hasOmissions && (
                <label>
                  <input
                    type="checkbox"
                    checked={omissionsAcknowledged}
                    onChange={(event) =>
                      setOmissionsAcknowledged(event.target.checked)
                    }
                  />
                  I acknowledge {omittedCount} omitted record
                  {omittedCount === 1 ? "" : "s"}, including{" "}
                  {activeOmittedCount ?? "an unavailable number of"} previously
                  ACTIVE record{activeOmittedCount === 1 ? "" : "s"}. Absence is
                  not automatically a withdrawal or transfer.
                </label>
              )}
            </div>
            <div
              className="final-scope-confirmation"
              aria-label="Exact activation target"
            >
              <strong>Activation target</strong>
              <span>
                {institutionName} · {programmeName} · {data.academic_year}
              </span>
              <span>Candidate {data.batch_id}</span>
              <span>Validation run {data.validation_run_id}</span>
              <span>
                Scope {data.scope_id} · revision {data.expected_scope_revision}
              </span>
              <span>Review {data.id}</span>
            </div>
            {officer ? (
              <p className="form-help">
                Officer access is read-only. The institution administrator who
                created this receipt must perform activation.
              </p>
            ) : (
              <button
                className="button primary activation-button"
                disabled={activationDisabled}
                onClick={() => {
                  setStatus("");
                  confirmActivation.mutate();
                }}
              >
                {confirmActivation.isPending
                  ? "Activating…"
                  : uncertain && retryAllowed
                    ? "Retry activation after status check"
                    : "Activate this snapshot"}
              </button>
            )}
            {uncertain && (
              <div className="uncertain-activation" role="status">
                <strong>Activation outcome is being reconciled.</strong>
                <p>{status}</p>
                {statusCheckFailed && (
                  <button
                    className="button secondary"
                    disabled={receipt.isFetching}
                    onClick={() => void reconcileActivation()}
                  >
                    Check candidate and review status again
                  </button>
                )}
              </div>
            )}
          </>
        ) : (
          <p className="form-help">
            Only the institution administrator who created this receipt may
            activate it. Managers and verifiers cannot access student-level
            review information.
          </p>
        )}
        {status && !uncertain && !activated && (
          <p
            className={
              confirmActivation.isError || requiresFreshReview
                ? "form-error"
                : "form-help"
            }
            role={
              confirmActivation.isError || requiresFreshReview
                ? "alert"
                : "status"
            }
          >
            {status}
          </p>
        )}
        {requiresFreshReview && admin && !batch.activated_at && (
          <button
            className="button secondary"
            disabled={freshReview.isPending}
            onClick={() => freshReview.mutate()}
          >
            {freshReview.isPending
              ? "Creating new review…"
              : "Create a fresh review from the selected run"}
          </button>
        )}
        {freshReview.isError && (
          <p className="form-error" role="alert">
            {status}
          </p>
        )}
      </div>

      <footer className="review-receipt-footer">
        <span>Receipt ID {data.id}</span>
        <button
          className="button secondary small"
          type="button"
          onClick={() => {
            void navigator.clipboard.writeText(window.location.href).then(
              () =>
                setCopyMessage(
                  "Review link copied; the receiving user must sign in with an authorized account.",
                ),
              () =>
                setCopyMessage(
                  "Could not access clipboard. Share the review ID with an authorized officer.",
                ),
            );
          }}
        >
          Copy review link
        </button>
        {copyMessage && <span role="status">{copyMessage}</span>}
        {data.validation_run_id !== run.id && (
          <button
            className="button secondary small"
            type="button"
            onClick={() => onRunChange(data.validation_run_id)}
          >
            Open this receipt’s selected run
          </button>
        )}
      </footer>
    </section>
  );
}
