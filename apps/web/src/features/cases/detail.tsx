"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { useSession } from "@/features/auth/session";
import { errorMessage, isUUID } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";
import { RecordVerification } from "./record-verification";
import {
  CASE_PRIORITIES,
  CASE_SEVERITIES,
  CaseBadges,
  eventLabel,
  eventTone,
  legalActions,
  statusLabel,
  statusTone,
  titleCase,
  type CaseAction,
  type CasePriority,
  type CaseSeverity,
} from "./shared";

type Case = components["schemas"]["CaseResponse"];
type Assignee = components["schemas"]["AssigneeResponse"];
type ActionBody = components["schemas"]["CaseActionRequest"];

const CONFIRM: Partial<
  Record<CaseAction, { title: string; text: string; button: string }>
> = {
  RESOLVED: {
    title: "Mark this case resolved?",
    text: "The resolution reason is recorded in the append-only history and the institution is notified.",
    button: "Mark resolved",
  },
  REJECTED: {
    title: "Mark this case rejected?",
    text: "The reason is recorded in the append-only history and the institution is notified. This is a review outcome, not a fraud determination.",
    button: "Mark rejected",
  },
  CLOSED: {
    title: "Close this case?",
    text: "A closed case accepts no further actions.",
    button: "Close case",
  },
  RESPONSE_SUBMITTED: {
    title: "Submit your response?",
    text: "This tells the reviewing officer your response is ready for another look.",
    button: "Submit response",
  },
};

const BUTTON_LABELS: Partial<Record<CaseAction, string>> = {
  START_REVIEW: "Start review",
  REQUEST_CORRECTION: "Request correction",
  RESOLVED: "Mark resolved",
  REJECTED: "Mark rejected",
  CLOSED: "Close case",
  RESPONSE_SUBMITTED: "Submit response",
};

function toLocalInput(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  const shifted = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return shifted.toISOString().slice(0, 16);
}

export function CaseDetail({ caseId }: { caseId: string }) {
  const { session, request } = useSession();
  const role = session?.user.role;
  const officer = role === "AICTE_OFFICER";
  const scope = ["private", session?.generation, session?.user.id];
  const caseKey = [...scope, "cases", caseId];
  const caseQuery = useQuery({
    queryKey: caseKey,
    enabled: !!session && isUUID(caseId),
    queryFn: ({ signal }) => request<Case>(`/cases/${caseId}`, { signal }),
  });
  const assignees = useQuery({
    queryKey: [...scope, "cases", "assignees"],
    enabled: !!session && officer,
    queryFn: ({ signal }) =>
      request<Assignee[]>("/cases/assignees", { signal }),
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
  const assigneeName = item.assigned_to
    ? (assignees.data?.find((a) => a.id === item.assigned_to)?.display_name ??
      "Assigned officer")
    : "Unassigned";

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
          <CaseBadges item={item} />
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

      <section className="panel" aria-labelledby="facts-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">CASE DETAILS</p>
            <h2 id="facts-title">Priority and due date</h2>
          </div>
        </header>
        <dl className="case-facts">
          <div>
            <dt>Priority</dt>
            <dd>{titleCase(item.priority)}</dd>
          </div>
          <div>
            <dt>Severity</dt>
            <dd>{titleCase(item.severity)}</dd>
          </div>
          <div>
            <dt>Due</dt>
            <dd>
              {item.due_at ? (
                <time dateTime={item.due_at}>
                  {new Date(item.due_at).toLocaleString()}
                </time>
              ) : (
                "No due date"
              )}
              {item.is_overdue ? " (overdue)" : ""}
            </dd>
          </div>
          <div>
            <dt>Age</dt>
            <dd>
              {item.age_days} day{item.age_days === 1 ? "" : "s"}
            </dd>
          </div>
          <div>
            <dt>Escalated</dt>
            <dd>{item.is_escalated ? "Yes" : "No"}</dd>
          </div>
          {officer && (
            <div>
              <dt>Assigned to</dt>
              <dd>{assigneeName}</dd>
            </div>
          )}
          {item.resolution_reason && (
            <div>
              <dt>Resolution reason</dt>
              <dd>{item.resolution_reason}</dd>
            </div>
          )}
        </dl>
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

      <CaseActions
        item={item}
        caseKey={caseKey}
        scopeKey={[...scope, "cases"]}
        assignees={assignees.data}
        assigneesError={assignees.isError}
      />
    </div>
  );
}

function CaseActions({
  item,
  caseKey,
  scopeKey,
  assignees,
  assigneesError,
}: {
  item: Case;
  caseKey: unknown[];
  scopeKey: unknown[];
  assignees: Assignee[] | undefined;
  assigneesError: boolean;
}) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const role = session?.user.role;
  const officer = role === "AICTE_OFFICER";
  const actions = legalActions(item.status, role);
  const can = (action: CaseAction) => actions.includes(action);

  const [comment, setComment] = useState("");
  const [reason, setReason] = useState("");
  const [assignee, setAssignee] = useState(item.assigned_to ?? "");
  const [priority, setPriority] = useState<CasePriority>(item.priority);
  const [severity, setSeverity] = useState<CaseSeverity>(item.severity);
  const [due, setDue] = useState(toLocalInput(item.due_at));
  const [confirming, setConfirming] = useState<CaseAction | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const act = useMutation({
    mutationFn: (body: ActionBody) =>
      request<Case>(`/cases/${item.id}/actions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    onSuccess: async (_data, body) => {
      setConfirming(null);
      setError("");
      setComment("");
      setReason("");
      setNotice(
        `Saved: ${(BUTTON_LABELS[body.action] ?? titleCase(body.action)).toLowerCase()}.`,
      );
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: caseKey }),
        queryClient.invalidateQueries({ queryKey: scopeKey }),
        queryClient.invalidateQueries({
          queryKey: [scopeKey[0], scopeKey[1], scopeKey[2], "notifications"],
        }),
      ]);
    },
    onError: (mutationError) => {
      setConfirming(null);
      setNotice("");
      setError(errorMessage(mutationError));
    },
  });

  const submit = (action: CaseAction) => {
    setError("");
    setNotice("");
    const note = comment.trim() || undefined;
    const body: ActionBody = { action, comment: note };
    if (action === "ASSIGNED") body.assigned_to = assignee;
    if (action === "RESOLVED" || action === "REJECTED")
      body.resolution_reason = reason.trim();
    act.mutate(body);
  };
  const begin = (action: CaseAction) => {
    setError("");
    setNotice("");
    if (action === "COMMENT" && !comment.trim()) {
      setError("Enter a comment first.");
      return;
    }
    if ((action === "RESOLVED" || action === "REJECTED") && !reason.trim()) {
      setError("A resolution reason is required.");
      return;
    }
    if (CONFIRM[action]) setConfirming(action);
    else submit(action);
  };
  const saveDetails = () => {
    setError("");
    setNotice("");
    const body: ActionBody = { action: "UPDATED" };
    if (priority !== item.priority) body.priority = priority;
    if (severity !== item.severity) body.severity = severity;
    if (due && due !== toLocalInput(item.due_at))
      body.due_at = new Date(due).toISOString();
    if (!body.priority && !body.severity && !body.due_at) {
      setError("Change the priority, severity or due date first.");
      return;
    }
    if (comment.trim()) body.comment = comment.trim();
    act.mutate(body);
  };

  if (actions.length === 0)
    return (
      <p className="data-note">
        This case is closed. No further actions are accepted.
      </p>
    );

  const workflow = actions.filter(
    (a) => a in BUTTON_LABELS && a !== "RESPONSE_SUBMITTED",
  );
  const resolving = can("RESOLVED") || can("REJECTED");
  const busy = act.isPending;

  return (
    <>
      {officer && (
        <section className="panel" aria-labelledby="manage-title">
          <header className="panel-heading">
            <div>
              <p className="eyebrow">OFFICER CONTROLS</p>
              <h2 id="manage-title">Assignment and priority</h2>
            </div>
          </header>
          <div className="case-form">
            {can("ASSIGNED") && (
              <div className="case-form-row">
                <label>
                  Assign to officer
                  <select
                    value={assignee}
                    onChange={(e) => setAssignee(e.target.value)}
                    disabled={!assignees}
                  >
                    <option value="">Select an officer</option>
                    {assignees?.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.display_name}
                      </option>
                    ))}
                  </select>
                </label>
                <div style={{ alignSelf: "end" }}>
                  <button
                    type="button"
                    className="button secondary"
                    disabled={
                      busy || !assignee || assignee === item.assigned_to
                    }
                    onClick={() => begin("ASSIGNED")}
                  >
                    Assign
                  </button>
                </div>
              </div>
            )}
            {assigneesError && (
              <p className="form-error" role="alert">
                The officer list could not be loaded, so assignment is
                unavailable.
              </p>
            )}
            {can("UPDATED") && (
              <>
                <h3>Priority, severity and due date</h3>
                <div className="case-form-row">
                  <label>
                    Priority
                    <select
                      value={priority}
                      onChange={(e) =>
                        setPriority(e.target.value as CasePriority)
                      }
                    >
                      {CASE_PRIORITIES.map((p) => (
                        <option key={p} value={p}>
                          {titleCase(p)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Severity
                    <select
                      value={severity}
                      onChange={(e) =>
                        setSeverity(e.target.value as CaseSeverity)
                      }
                    >
                      {CASE_SEVERITIES.map((p) => (
                        <option key={p} value={p}>
                          {titleCase(p)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Due date (local time)
                    <input
                      type="datetime-local"
                      value={due}
                      onChange={(e) => setDue(e.target.value)}
                    />
                  </label>
                </div>
                <div>
                  <button
                    type="button"
                    className="button secondary"
                    disabled={busy}
                    onClick={saveDetails}
                  >
                    Save details
                  </button>
                </div>
              </>
            )}
          </div>
        </section>
      )}

      <section className="panel" aria-labelledby="actions-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">EXPLICIT ACTION</p>
            <h2 id="actions-title">Record an action</h2>
          </div>
        </header>
        <div className="case-form">
          {!officer && item.status === "AWAITING_CORRECTION" && (
            <p className="data-note">
              An officer has asked for a correction. Upload a corrected
              submission &mdash; activating it records your response
              automatically &mdash; or add a comment and use &ldquo;Submit
              response&rdquo; to tell the officer you have responded.
            </p>
          )}
          <label>
            Comment
            <textarea
              value={comment}
              onChange={(event) => setComment(event.target.value)}
              maxLength={2000}
              rows={3}
              placeholder={
                officer
                  ? "Optional note recorded with the action"
                  : "Describe the correction or context for the officer"
              }
            />
          </label>
          {resolving && (
            <label>
              Resolution reason (required to resolve or reject)
              <textarea
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                maxLength={2000}
                rows={3}
              />
            </label>
          )}
          <div className="case-action-buttons">
            {can("COMMENT") && (
              <button
                type="button"
                className="button secondary small"
                disabled={busy}
                onClick={() => begin("COMMENT")}
              >
                Add comment
              </button>
            )}
            {!officer && can("RESPONSE_SUBMITTED") && (
              <button
                type="button"
                className="button primary small"
                disabled={busy}
                onClick={() => begin("RESPONSE_SUBMITTED")}
              >
                Submit response
              </button>
            )}
            {officer &&
              workflow.map((action) => (
                <button
                  key={action}
                  type="button"
                  className="button secondary small"
                  disabled={busy}
                  onClick={() => begin(action)}
                >
                  {BUTTON_LABELS[action]}
                </button>
              ))}
          </div>
          <div aria-live="polite">
            {notice && <p className="form-success">{notice}</p>}
          </div>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
        </div>
      </section>

      {confirming && CONFIRM[confirming] && (
        <ConfirmDialog
          open
          title={CONFIRM[confirming].title}
          confirmLabel={CONFIRM[confirming].button}
          busy={busy}
          onCancel={() => setConfirming(null)}
          onConfirm={() => submit(confirming)}
        >
          <p>{CONFIRM[confirming].text}</p>
        </ConfirmDialog>
      )}
    </>
  );
}
