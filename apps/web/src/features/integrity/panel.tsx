"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  ErrorPanel,
  Loading,
  DemoBanner,
  QueryBoundary,
} from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { ScrollTable } from "@/features/intake/shared";
import { ApiError, errorMessage } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";

type Signals = components["schemas"]["SignalsResponse"];
type Signal = components["schemas"]["Signal"];
type Family = Signal["family"];
type Decision = components["schemas"]["DecisionRequest"]["decision"];
type DecisionPage = components["schemas"]["Page_DecisionResponse_"];
type ScoreSummary = components["schemas"]["ScoreSummary"];

export const FAMILIES: { id: Family; label: string; hint: string }[] = [
  {
    id: "DATA_QUALITY",
    label: "Data quality",
    hint: "Completeness and format of submitted data.",
  },
  {
    id: "IDENTITY_UNCERTAINTY",
    label: "Identity uncertainty",
    hint: "Potential overlaps and identifier questions that need a human look.",
  },
  {
    id: "COMPLIANCE",
    label: "Compliance",
    hint: "Comparisons against configured demo intake rules.",
  },
];
export const familyLabel = (id: string) =>
  FAMILIES.find((f) => f.id === id)?.label ?? id;

const DECISIONS: { id: Decision; label: string }[] = [
  { id: "FALSE_POSITIVE", label: "False positive (dismiss)" },
  { id: "NEEDS_FOLLOW_UP", label: "Needs follow-up" },
  { id: "CONFIRMED_CONCERN", label: "Confirmed concern for review" },
];
const decisionLabel = (id: string) =>
  DECISIONS.find((d) => d.id === id)?.label ?? id;

export function severityTone(severity: string): string {
  return severity === "HIGH"
    ? "danger"
    : severity === "MEDIUM"
      ? "warning"
      : "neutral";
}
export const bandTone = severityTone;
const title = (value: string) => value.charAt(0) + value.slice(1).toLowerCase();

export function Disclaimer({ text }: { text: string }) {
  return (
    <DemoBanner label="Review prompt disclaimer" title="Review prompts only">
      {text}
    </DemoBanner>
  );
}

function decisionMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 403)
    return "Only AICTE officers can record decisions.";
  return errorMessage(error);
}

export function ScoreTable({ score }: { score: ScoreSummary }) {
  return (
    <>
      <ScrollTable label="Score components by signal family">
        <thead>
          <tr>
            <th scope="col">Family</th>
            <th scope="col">Signals</th>
            <th scope="col">Active</th>
            <th scope="col">Points</th>
            <th scope="col">Max severity</th>
          </tr>
        </thead>
        <tbody>
          {FAMILIES.map((f) => {
            const c = score.components.find((x) => x.family === f.id);
            return (
              <tr key={f.id}>
                <th scope="row">{f.label}</th>
                <td>{c?.signal_count ?? 0}</td>
                <td>{c?.active_count ?? 0}</td>
                <td>{c?.weighted_points ?? 0}</td>
                <td>{c?.max_severity ? title(c.max_severity) : "None"}</td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">Total</th>
            <td colSpan={2} />
            <td>
              <strong>{score.total_points}</strong>
            </td>
            <td />
          </tr>
        </tfoot>
      </ScrollTable>
      <p className="cell-note">
        Review priority band:{" "}
        <span className={`status-badge ${bandTone(score.band)}`}>
          {title(score.band)}
        </span>{" "}
        Formula: {score.formula}. Severity weights:{" "}
        {Object.entries(score.severity_weights)
          .map(([k, v]) => `${title(k)} ${v}`)
          .join(", ")}
        . Band thresholds:{" "}
        {Object.entries(score.band_thresholds)
          .map(([k, v]) => `${title(k)} ${v}`)
          .join(", ")}
        . A prioritisation aid, not a finding.
      </p>
    </>
  );
}

function Evidence({ signal }: { signal: Signal }) {
  const e = signal.evidence;
  const MAX = 5;
  const groups: { label: string; items: React.ReactNode[] }[] = [
    {
      label: "Batches",
      items: e.batch_ids.map((id) => (
        <Link key={id} href={`/submissions/${id}`}>
          {id.slice(0, 8)}
        </Link>
      )),
    },
    {
      label: "Cases",
      items: e.case_ids.map((id) => (
        <Link key={id} href={`/cases/${id}`}>
          {id.slice(0, 8)}
        </Link>
      )),
    },
    {
      label: "Records",
      items: e.record_version_ids.map((id) => (
        <Link key={id} href={`/records/${id}`}>
          {id.slice(0, 8)}
        </Link>
      )),
    },
  ].filter((g) => g.items.length > 0);
  const counts = Object.entries(e.finding_rule_counts);
  if (!groups.length && !e.assessment_id && !counts.length)
    return <p className="cell-note">No linked evidence references.</p>;
  return (
    <dl className="cell-note">
      {groups.map((g) => (
        <div key={g.label}>
          <dt style={{ display: "inline" }}>{g.label}: </dt>
          <dd style={{ display: "inline", margin: 0 }}>
            {g.items.slice(0, MAX).map((item, i) => (
              <span key={i}>
                {i > 0 && ", "}
                {item}
              </span>
            ))}
            {g.items.length > MAX && ` and ${g.items.length - MAX} more`}
          </dd>
        </div>
      ))}
      {e.assessment_id && (
        <div>
          <dt style={{ display: "inline" }}>Assessment: </dt>
          <dd style={{ display: "inline", margin: 0 }}>
            <span className="code-label">{e.assessment_id.slice(0, 8)}</span>
          </dd>
        </div>
      )}
      {counts.length > 0 && (
        <div>
          <dt style={{ display: "inline" }}>Findings by rule: </dt>
          <dd style={{ display: "inline", margin: 0 }}>
            {counts.map(([rule, n]) => `${rule} × ${n}`).join(", ")}
          </dd>
        </div>
      )}
      {e.record_version_total > e.record_version_ids.length && (
        <div>
          {e.record_version_total.toLocaleString()} record versions in total;
          the list above is capped.
        </div>
      )}
    </dl>
  );
}

function SignalItem({
  signal,
  onDecide,
}: {
  signal: Signal;
  onDecide?: (s: Signal) => void;
}) {
  return (
    <li className="panel-padding" style={{ borderTop: "1px solid #0001" }}>
      <p>
        <span className={`status-badge ${severityTone(signal.severity)}`}>
          {title(signal.severity)}
        </span>{" "}
        <strong>{signal.title}</strong>{" "}
        <span className="code-label">{signal.rule_id}</span>
        {signal.dismissed && (
          <>
            {" "}
            <span className="status-badge neutral">Dismissed</span>
          </>
        )}
      </p>
      <p>{signal.calculation}</p>
      <Evidence signal={signal} />
      <p>
        <strong>Suggested next step:</strong> {signal.recommended_next_action}
      </p>
      {signal.decision && (
        <p className="cell-note">
          Latest decision: {decisionLabel(signal.decision)}
          {signal.decision_at && (
            <>
              {" "}
              on{" "}
              <time dateTime={signal.decision_at}>
                {new Date(signal.decision_at).toLocaleString()}
              </time>
            </>
          )}
        </p>
      )}
      {onDecide && (
        <button
          type="button"
          className="button secondary small"
          onClick={() => onDecide(signal)}
        >
          Record decision
        </button>
      )}
    </li>
  );
}

function DecisionHistory({ institutionId }: { institutionId: string }) {
  const { session, request } = useSession();
  const [page, setPage] = useState(1);
  const list = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "integrity-decisions",
      institutionId,
      page,
    ],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<DecisionPage>(
        `/integrity/institutions/${institutionId}/decisions?page=${page}&page_size=10`,
        { signal },
      ),
  });
  return (
    <div className="panel-padding">
      <h3>Decision history</h3>
      <QueryBoundary query={list} loading="Loading decisions…">
        {(data) =>
          data.data.length === 0 ? (
            <div className="empty-state compact">
              <p>No decisions recorded yet.</p>
            </div>
          ) : (
            <>
              <ScrollTable label="Integrity signal decisions, newest first">
                <thead>
                  <tr>
                    <th scope="col">Recorded</th>
                    <th scope="col">Signal</th>
                    <th scope="col">Decision</th>
                    <th scope="col">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {data.data.map((d) => (
                    <tr key={d.id}>
                      <td>
                        <time dateTime={d.created_at}>
                          {new Date(d.created_at).toLocaleString()}
                        </time>
                      </td>
                      <td>
                        <span className="code-label">{d.signal_key}</span>
                      </td>
                      <td>{decisionLabel(d.decision)}</td>
                      <td>{d.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </ScrollTable>
              <Pagination
                page={page}
                pageSize={10}
                total={data.pagination.total}
                busy={list.isFetching}
                change={setPage}
                label="Decision history pagination"
              />
            </>
          )
        }
      </QueryBoundary>
    </div>
  );
}

/** Institution-level review prompts. Officers may record decisions; admins are read-only. */
export function IntegritySignalsPanel({
  institutionId,
  canDecide,
}: {
  institutionId: string;
  canDecide: boolean;
}) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const [target, setTarget] = useState<Signal | null>(null);
  const [decision, setDecision] = useState<Decision>("NEEDS_FOLLOW_UP");
  const [reason, setReason] = useState("");
  const [dialogError, setDialogError] = useState("");
  const [notice, setNotice] = useState("");
  const key = [
    "private",
    session?.generation,
    session?.user.id,
    "integrity",
    institutionId,
  ];
  const signals = useQuery({
    queryKey: [...key, "signals"],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<Signals>(`/integrity/institutions/${institutionId}/signals`, {
        signal,
      }),
  });
  const close = () => {
    setTarget(null);
    setReason("");
    setDialogError("");
  };
  const record = useMutation({
    mutationFn: (body: components["schemas"]["DecisionRequest"]) =>
      request(`/integrity/institutions/${institutionId}/decisions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    onSuccess: async (_saved, body) => {
      setNotice(`Decision recorded: ${decisionLabel(body.decision)}.`);
      close();
      await queryClient.invalidateQueries({ queryKey: key });
    },
    onError: (e) => setDialogError(decisionMessage(e)),
  });
  const submit = () => {
    const trimmed = reason.trim();
    if (trimmed.length < 3 || trimmed.length > 500)
      return setDialogError("Give a reason of 3 to 500 characters.");
    if (!target) return;
    setDialogError("");
    record.mutate({
      signal_key: target.signal_key,
      decision,
      reason: trimmed,
    });
  };
  return (
    <section
      className="panel"
      aria-labelledby="integrity-title"
      aria-busy={signals.isFetching}
    >
      <header className="panel-heading">
        <div>
          <p className="eyebrow">REVIEW PROMPTS</p>
          <h2 id="integrity-title">Integrity signals</h2>
        </div>
        <span className="quiet-label">
          {canDecide ? "Officers record decisions" : "Read-only"}
        </span>
      </header>
      {signals.isPending ? (
        <Loading label="Loading integrity signals…" />
      ) : signals.isError ? (
        <ErrorPanel
          error={signals.error}
          retry={() => void signals.refetch()}
        />
      ) : (
        <>
          <div className="panel-padding">
            <Disclaimer text={signals.data.disclaimer} />
            <p className="cell-note">
              Source: {signals.data.source_label}. Verification-related inputs
              are SIMULATED / DEMO DATA.
            </p>
            <div aria-live="polite">
              {notice && <p className="form-success">{notice}</p>}
            </div>
          </div>
          <div className="panel-padding">
            <h3>Score components</h3>
            <ScoreTable score={signals.data.score} />
          </div>
          {signals.data.signals.length === 0 && (
            <div className="empty-state compact">
              <h3>No signals</h3>
              <p>
                No review prompts were raised from the stored data. This does
                not confirm compliance.
              </p>
            </div>
          )}
          {FAMILIES.map((f) => {
            const items = signals.data.signals.filter((s) => s.family === f.id);
            if (!items.length) return null;
            return (
              <section key={f.id} aria-labelledby={`fam-${f.id}`}>
                <div className="panel-padding">
                  <h3 id={`fam-${f.id}`}>
                    {f.label} <span className="count-pill">{items.length}</span>
                  </h3>
                  <p className="cell-note">{f.hint}</p>
                </div>
                <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                  {items.map((s) => (
                    <SignalItem
                      key={s.signal_key}
                      signal={s}
                      onDecide={
                        canDecide
                          ? (picked) => {
                              setNotice("");
                              setDecision("NEEDS_FOLLOW_UP");
                              setTarget(picked);
                            }
                          : undefined
                      }
                    />
                  ))}
                </ul>
              </section>
            );
          })}
          {canDecide && <DecisionHistory institutionId={institutionId} />}
        </>
      )}
      {target && (
        <ConfirmDialog
          open
          title="Record decision"
          confirmLabel="Record decision"
          busy={record.isPending}
          onCancel={close}
          onConfirm={submit}
        >
          <p>
            <strong>{target.title}</strong>
          </p>
          <p className="cell-note">
            Decisions are appended to the audit history and are made by the
            officer. They are not fraud findings.
          </p>
          <label>
            Decision
            <select
              value={decision}
              onChange={(e) => setDecision(e.target.value as Decision)}
            >
              {DECISIONS.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Reason (required)
            <textarea
              value={reason}
              maxLength={500}
              rows={3}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          {dialogError && (
            <p className="form-error" role="alert">
              {dialogError}
            </p>
          )}
        </ConfirmDialog>
      )}
    </section>
  );
}
