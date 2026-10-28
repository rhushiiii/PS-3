"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { useSession } from "@/features/auth/session";
import { errorMessage, isUUID } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";
import { RecordVerification } from "./record-verification";
import { eventLabel, eventTone, statusLabel, statusTone } from "./shared";

type Case = components["schemas"]["CaseResponse"];
type CaseAction = components["schemas"]["CaseActionRequest"]["action"];

const ACTIONS_BY_STATUS: Record<Case["status"], CaseAction[]> = {
  OPEN: ["COMMENT", "REQUEST_CORRECTION", "RESOLVED"],
  UNDER_REVIEW: ["COMMENT", "REQUEST_CORRECTION", "RESOLVED"],
  AWAITING_CORRECTION: ["COMMENT"],
  RESOLVED: ["COMMENT", "CLOSED"],
  CLOSED: [],
};

const actionLabels: Record<CaseAction, string> = {
  COMMENT: "Add comment",
  REQUEST_CORRECTION: "Request correction",
  ASSIGNED: "Assign",
  RESOLVED: "Mark resolved",
  CLOSED: "Close case",
};

export function CaseDetail({ caseId }: { caseId: string }) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const role = session?.user.role;
  const officer = role === "AICTE_OFFICER";
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");

  const baseKey = [
    "private",
    session?.generation,
    session?.user.id,
    "cases",
    caseId,
  ];
  const caseQuery = useQuery({
    queryKey: baseKey,
    enabled: !!session && isUUID(caseId),
    queryFn: ({ signal }) => request<Case>(`/cases/${caseId}`, { signal }),
  });

  const act = useMutation({
    mutationFn: (action: CaseAction) =>
      request<Case>(`/cases/${caseId}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          comment: comment.trim() || undefined,
        }),
      }),
    retry: false,
    onSuccess: async () => {
      setError("");
      setComment("");
      await queryClient.invalidateQueries({ queryKey: baseKey });
    },
    onError: (mutationError) => setError(errorMessage(mutationError)),
  });

  if (!isUUID(caseId))
    return (
      <section className="empty-state">
        <h1>Case unavailable</h1>
        <p>Choose a case from the queue.</p>
        <Link className="button secondary" href="/cases">
          Back to cases
        </Link>
      </section>
    );
  if (caseQuery.isPending) return <Loading label="Loading case…" />;
  if (caseQuery.isError)
    return (
      <ErrorPanel
        error={caseQuery.error}
        retry={() => void caseQuery.refetch()}
      />
    );

  const item = caseQuery.data;
  const legalActions = ACTIONS_BY_STATUS[item.status].filter(
    (action) => officer || action === "COMMENT",
  );

  return (
    <div className="case-detail-page">
      <div className="page-heading heading-actions">
        <div>
          <p className="eyebrow">{item.category.replaceAll("_", " ")}</p>
          <h1>
            Case review{" "}
            <span className={`status-badge ${statusTone(item.status)}`}>
              {statusLabel(item.status)}
            </span>
          </h1>
          <p>{item.summary}</p>
        </div>
        <Link className="button secondary" href="/cases">
          Back to cases
        </Link>
      </div>

      <section className="validation-notice" aria-label="Case meaning">
        <strong>Review lead, not a determination</strong>
        <p>
          A case is a lead for officer review. It does not imply fraud or an
          official APAAR identity verification. Correction requests never block
          the institution&rsquo;s ability to submit a new candidate.
        </p>
      </section>

      <section className="panel" aria-labelledby="records-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">LINKED EVIDENCE</p>
            <h2 id="records-title">Linked records</h2>
          </div>
          <span className="quiet-label">
            {item.record_version_ids.length} record
            {item.record_version_ids.length === 1 ? "" : "s"}
          </span>
        </header>
        {item.record_version_ids.map((recordId, index) => (
          <RecordVerification
            key={recordId}
            recordVersionId={recordId}
            officer={officer}
            index={index}
          />
        ))}
      </section>

      <section className="panel" aria-labelledby="timeline-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">APPEND-ONLY TIMELINE</p>
            <h2 id="timeline-title">Case history</h2>
          </div>
        </header>
        <ol className="case-timeline">
          {item.events.map((event) => (
            <li
              key={event.id}
              className={`timeline-${eventTone(event.action)}`}
            >
              <header>
                <span className={`status-badge ${eventTone(event.action)}`}>
                  {eventLabel(event.action)}
                </span>
                <time dateTime={event.created_at}>
                  {new Date(event.created_at).toLocaleString()}
                </time>
              </header>
              {event.comment && <p>{event.comment}</p>}
              {event.linked_batch_id && (
                <p className="cell-note">
                  Linked submission: {event.linked_batch_id}
                </p>
              )}
              {event.actor_id === null && (
                <p className="cell-note">
                  Recorded automatically by the system
                </p>
              )}
            </li>
          ))}
        </ol>
      </section>

      {legalActions.length > 0 && (
        <section className="panel" aria-labelledby="actions-title">
          <header className="panel-heading">
            <div>
              <p className="eyebrow">EXPLICIT ACTION</p>
              <h2 id="actions-title">Record an action</h2>
            </div>
          </header>
          <label>
            Comment
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              maxLength={2000}
              rows={3}
              placeholder={
                officer
                  ? "Optional comment for most actions"
                  : "Describe the correction or context for the officer"
              }
            />
          </label>
          <div className="case-action-buttons">
            {legalActions.map((action) => (
              <button
                key={action}
                className="button secondary small"
                disabled={act.isPending}
                onClick={() => act.mutate(action)}
              >
                {actionLabels[action]}
              </button>
            ))}
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
        </section>
      )}
      {legalActions.length === 0 && (
        <p className="data-note">
          This case is closed. No further actions are accepted.
        </p>
      )}
    </div>
  );
}
