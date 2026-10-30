"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import type { components } from "@/lib/api/generated";
import {
  DemoRuleNotice,
  ScrollTable,
  categoryLabel,
  intakeMessage,
  severityClass,
} from "./shared";

type Assessment = components["schemas"]["AssessmentResponse"];
type AssessmentPage = components["schemas"]["Page_AssessmentSummary_"];

// The API types `result` as a free-form object; these mirror its documented shape.
type CategoryLine = {
  category: string;
  approved_seats: number | null;
  rule_version: string | null;
  current_active_count: number | null;
  candidate_active_count: number;
  remaining_capacity: number | null;
  excess: number;
  exceeded: boolean;
  calculation: string;
};
type DiffChange = {
  college_student_id: string;
  change_type: string;
  changed_fields: string[];
};
type Diff = {
  status: string;
  added_count?: number;
  removed_count?: number;
  changed_count?: number;
  retained_unchanged_count?: number;
  changes_total?: number;
  changes_truncated?: boolean;
  changes?: DiffChange[];
  omission_meaning?: string;
  removed_conclusion?: string;
};
type Population = {
  status: string;
  declared_total?: number;
  candidate_record_count?: number;
  shortfall?: number;
  discrepancy?: boolean;
  calculation?: string;
};
type FindingLine = {
  rule_id: string;
  severity: string;
  category?: string;
  calculation: string;
};
type Result = {
  notice: string;
  is_current_snapshot: boolean;
  categories: CategoryLine[];
  snapshot_diff: Diff;
  missing_population: Population;
  findings: FindingLine[];
};

const diffUnavailable: Record<string, string> = {
  NO_CURRENT_SNAPSHOT:
    "No current snapshot exists, so there is nothing to compare against.",
  UNAVAILABLE_AMBIGUOUS_IDENTIFIERS:
    "Comparison unavailable: college student identifiers are blank or repeated.",
};

function AssessmentDetail({ assessment }: { assessment: Assessment }) {
  const result = assessment.result as unknown as Result;
  const diff = result.snapshot_diff;
  const population = result.missing_population;
  return (
    <div className="intake-assessment">
      <p className="form-help">
        Assessed{" "}
        <time dateTime={assessment.computed_at}>
          {new Date(assessment.computed_at).toLocaleString()}
        </time>{" "}
        · rule version {assessment.rule_version} · {assessment.source_label} ·{" "}
        {result.is_current_snapshot
          ? "this batch is the current snapshot"
          : "this batch is not the current snapshot"}
        . Read-only record.
      </p>

      <h4>Per-category capacity (candidate ACTIVE records)</h4>
      <ScrollTable label="Per-category intake assessment">
        <thead>
          <tr>
            <th scope="col">Category</th>
            <th scope="col">Approved</th>
            <th scope="col">Current active</th>
            <th scope="col">Candidate active</th>
            <th scope="col">Remaining</th>
            <th scope="col">Excess</th>
            <th scope="col">Calculation</th>
            <th scope="col">Rule version</th>
          </tr>
        </thead>
        <tbody>
          {result.categories.map((c) => (
            <tr key={c.category}>
              <td>{categoryLabel(c.category)}</td>
              <td>{c.approved_seats ?? "No rule"}</td>
              <td>{c.current_active_count ?? "No current snapshot"}</td>
              <td>{c.candidate_active_count}</td>
              <td>{c.remaining_capacity ?? "—"}</td>
              <td>
                {c.exceeded ? (
                  <span className="status-badge warning">{c.excess}</span>
                ) : (
                  c.excess
                )}
              </td>
              <td>
                <code>{c.calculation}</code>
              </td>
              <td>{c.rule_version ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </ScrollTable>
      <p className="form-help">
        Categories are compared separately and never pooled into one cap.
      </p>

      <h4>Snapshot difference</h4>
      {diff.status !== "COMPARED" ? (
        <p>
          {diffUnavailable[diff.status] ?? "Snapshot comparison unavailable."}
        </p>
      ) : (
        <>
          <p>
            Added {diff.added_count} · Removed {diff.removed_count} · Changed{" "}
            {diff.changed_count} · Unchanged {diff.retained_unchanged_count}
          </p>
          {diff.omission_meaning && (
            <p className="form-help">{diff.omission_meaning}</p>
          )}
          {(diff.changes ?? []).length === 0 ? (
            <p className="form-help">No added, removed or changed records.</p>
          ) : (
            <>
              <p className="form-help">
                Showing {(diff.changes ?? []).length} of {diff.changes_total}{" "}
                differences{diff.changes_truncated ? " (list capped)" : ""}.
                Field names only; no personal values are shown.
              </p>
              <div className="intake-diff-list">
                <ScrollTable label="Snapshot differences by college student ID">
                  <thead>
                    <tr>
                      <th scope="col">College student ID</th>
                      <th scope="col">Change</th>
                      <th scope="col">Changed fields</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(diff.changes ?? []).map((c) => (
                      <tr key={c.college_student_id}>
                        <td>{c.college_student_id}</td>
                        <td>{categoryLabel(c.change_type)}</td>
                        <td>{c.changed_fields.join(", ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </ScrollTable>
              </div>
            </>
          )}
        </>
      )}

      <h4>Missing population</h4>
      {population.status === "NO_REFERENCE" ? (
        <p>No reference total declared — no conclusion.</p>
      ) : (
        <p>
          {population.discrepancy ? (
            <span className="status-badge warning">Discrepancy</span>
          ) : (
            <span className="status-badge active">No shortfall</span>
          )}{" "}
          <code>{population.calculation}</code>
        </p>
      )}

      <h4>Findings</h4>
      {result.findings.length === 0 ? (
        <p>No findings raised by the DEMO rules.</p>
      ) : (
        <ul className="intake-findings">
          {result.findings.map((f, index) => (
            <li key={`${f.rule_id}-${index}`}>
              <span className={`status-badge ${severityClass(f.severity)}`}>
                {f.severity}
              </span>{" "}
              <strong>{f.rule_id}</strong>
              {f.category ? ` · ${categoryLabel(f.category)}` : ""}
              <br />
              <code>{f.calculation}</code>
            </li>
          ))}
        </ul>
      )}
      <p className="data-note">{result.notice}</p>
    </div>
  );
}

export function IntakeAssessmentPanel({
  batchId,
  processed,
}: {
  batchId: string;
  processed: boolean;
}) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const key = [
    "private",
    session?.generation,
    session?.user.id,
    "intake-assessment",
    batchId,
  ];
  const history = useQuery({
    queryKey: [...key, "list", page],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<AssessmentPage>(
        `/submissions/${batchId}/intake-assessments?page=${page}&page_size=5`,
        { signal },
      ),
  });
  const newest = history.data?.data[0]?.id ?? "";
  const activeId = selected || (page === 1 ? newest : "");
  const detail = useQuery({
    queryKey: [...key, "detail", activeId],
    enabled: !!session && !!activeId,
    queryFn: ({ signal }) =>
      request<Assessment>(
        `/submissions/${batchId}/intake-assessments/${activeId}`,
        { signal },
      ),
  });
  const run = useMutation({
    mutationFn: () =>
      request<Assessment>(`/submissions/${batchId}/intake-assessments`, {
        method: "POST",
      }),
    onSuccess: async (created) => {
      setError("");
      setPage(1);
      setSelected(created.id);
      queryClient.setQueryData([...key, "detail", created.id], created);
      setNotice("Assessment recorded. Earlier assessments are kept unchanged.");
      await queryClient.invalidateQueries({ queryKey: [...key, "list"] });
    },
    onError: (e) => {
      setNotice("");
      setError(intakeMessage(e));
    },
  });
  return (
    <section
      className="panel"
      aria-labelledby="assessment-title"
      aria-busy={run.isPending}
    >
      <header className="panel-heading">
        <div>
          <p className="eyebrow">DEMO INTAKE CHECK</p>
          <h2 id="assessment-title">Intake assessment</h2>
        </div>
        <button
          className="button primary"
          disabled={run.isPending || !processed}
          onClick={() => {
            setNotice("");
            run.mutate();
          }}
        >
          {run.isPending ? "Running assessment…" : "Run intake assessment"}
        </button>
      </header>
      <div className="panel-padding">
        <DemoRuleNotice />
        {!processed && (
          <p className="form-help">
            This submission has not finished processing, so it cannot be
            assessed yet.
          </p>
        )}
        <div aria-live="polite">
          {notice && <p className="form-success">{notice}</p>}
        </div>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {run.isPending && <Loading label="Running intake assessment…" />}
      </div>
      <div className="panel-padding">
        <h3>Past assessments</h3>
        {history.isPending ? (
          <Loading label="Loading assessment history…" />
        ) : history.isError ? (
          <ErrorPanel
            error={history.error}
            retry={() => void history.refetch()}
          />
        ) : history.data.data.length === 0 ? (
          <div className="empty-state compact">
            <h3>No assessments yet</h3>
            <p>
              Run an intake assessment to compare this batch with DEMO intake
              rules.
            </p>
          </div>
        ) : (
          <>
            <ul className="intake-history">
              {history.data.data.map((a) => (
                <li key={a.id}>
                  <button
                    className={`button small ${a.id === activeId ? "primary" : "secondary"}`}
                    aria-pressed={a.id === activeId}
                    onClick={() => setSelected(a.id)}
                  >
                    {new Date(a.computed_at).toLocaleString()} · rule{" "}
                    {a.rule_version}
                  </button>
                </li>
              ))}
            </ul>
            <Pagination
              page={page}
              pageSize={5}
              total={history.data.pagination.total}
              busy={history.isFetching}
              change={setPage}
              label="Assessment history pagination"
            />
          </>
        )}
        {activeId &&
          (detail.isPending ? (
            <Loading label="Loading assessment…" />
          ) : detail.isError ? (
            <ErrorPanel
              error={detail.error}
              retry={() => void detail.refetch()}
            />
          ) : (
            <AssessmentDetail assessment={detail.data} />
          ))}
      </div>
    </section>
  );
}
