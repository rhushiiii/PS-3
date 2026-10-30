"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import {
  useSubmissionContext,
  validAcademicYear,
} from "@/features/submissions/data";
import type { components } from "@/lib/api/generated";
import {
  CATEGORIES,
  DEFAULT_YEAR,
  DemoRuleNotice,
  ScrollTable,
  categoryLabel,
  intakeMessage,
  type Category,
} from "./shared";

type Simulation = components["schemas"]["SimulationResponse"];
type Line = {
  category: string;
  approved_seats: number | null;
  rule_version: string | null;
  before_active_count: number;
  added_count: number;
  after_active_count: number;
  remaining_capacity: number | null;
  would_exceed: boolean;
  excess: number;
  calculation: string;
};
type Row = { id: number; category: Category; count: string };

export function SimulatorPanel({ institutionId }: { institutionId: string }) {
  const { request } = useSession();
  const { options } = useSubmissionContext(institutionId);
  const [programmeId, setProgrammeId] = useState("");
  const [year, setYear] = useState(DEFAULT_YEAR);
  const [rows, setRows] = useState<Row[]>([
    { id: 1, category: "REGULAR", count: "" },
  ]);
  const [nextId, setNextId] = useState(2);
  const [error, setError] = useState("");
  const run = useMutation({
    mutationFn: (body: {
      programme_id: string;
      academic_year: string;
      additions: { category: Category; count: number }[];
    }) =>
      request<Simulation>(`/institutions/${institutionId}/intake/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    onError: (e) => setError(intakeMessage(e)),
  });
  const update = (id: number, change: Partial<Row>) =>
    setRows((current) =>
      current.map((r) => (r.id === id ? { ...r, ...change } : r)),
    );
  const lines = (run.data?.categories ?? []) as unknown as Line[];
  return (
    <section
      className="panel"
      aria-labelledby="simulator-title"
      aria-busy={run.isPending}
    >
      <header className="panel-heading">
        <div>
          <p className="eyebrow">WHAT-IF · DEMO RULES</p>
          <h2 id="simulator-title">What-if simulator</h2>
        </div>
        <span className="quiet-label">Simulation only</span>
      </header>
      <div className="panel-padding">
        <DemoRuleNotice />
        <p className="form-help">
          Simulation only — no data was changed. Enter hypothetical additions to
          see them against the current snapshot and the DEMO rules.
        </p>
        <form
          className="intake-sim-form"
          onSubmit={(e) => {
            e.preventDefault();
            const additions = rows.map((r) => ({
              category: r.category,
              count: Number(r.count),
            }));
            if (!programmeId) return setError("Choose a programme.");
            if (!validAcademicYear(year))
              return setError("Use an academic year such as 2026-27.");
            if (
              rows.some(
                (r) =>
                  !/^\d+$/.test(r.count) ||
                  Number(r.count) < 1 ||
                  Number(r.count) > 1_000_000,
              )
            )
              return setError(
                "Each addition needs a whole number count of at least 1.",
              );
            setError("");
            run.mutate({
              programme_id: programmeId,
              academic_year: year,
              additions,
            });
          }}
        >
          <div className="validation-filters">
            <label>
              Programme
              <select
                value={programmeId}
                onChange={(e) => setProgrammeId(e.target.value)}
              >
                <option value="">Choose programme</option>
                {options.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Academic year
              <input value={year} onChange={(e) => setYear(e.target.value)} />
            </label>
          </div>
          <fieldset className="intake-additions">
            <legend>Hypothetical additions</legend>
            {rows.map((row, index) => (
              <div className="validation-filters" key={row.id}>
                <label>
                  Category
                  <select
                    value={row.category}
                    onChange={(e) =>
                      update(row.id, { category: e.target.value as Category })
                    }
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {categoryLabel(c)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Count
                  <input
                    inputMode="numeric"
                    value={row.count}
                    onChange={(e) => update(row.id, { count: e.target.value })}
                  />
                </label>
                {rows.length > 1 && (
                  <button
                    type="button"
                    className="button ghost small"
                    onClick={() =>
                      setRows((c) => c.filter((r) => r.id !== row.id))
                    }
                  >
                    Remove<span className="sr-only"> addition {index + 1}</span>
                  </button>
                )}
              </div>
            ))}
            <div className="button-row">
              <button
                type="button"
                className="button secondary small"
                disabled={rows.length >= 20}
                onClick={() => {
                  setRows((c) => [
                    ...c,
                    { id: nextId, category: "REGULAR", count: "" },
                  ]);
                  setNextId(nextId + 1);
                }}
              >
                Add row
              </button>
              <button
                className="button primary"
                type="submit"
                disabled={run.isPending}
              >
                {run.isPending ? "Simulating…" : "Run simulation"}
              </button>
            </div>
          </fieldset>
        </form>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </div>
      {run.data && (
        <div className="panel-padding" aria-live="polite">
          <h3>Simulation result</h3>
          <p className="form-help">
            Simulation only — no data was changed. Rule version{" "}
            {run.data.rule_version} · {run.data.source_label}.{" "}
            {run.data.has_current_snapshot
              ? "“Before” counts are ACTIVE records in the current snapshot."
              : "No current snapshot exists, so “before” counts are 0."}
          </p>
          <ScrollTable label="Simulated ACTIVE records against DEMO approved seats by category">
            <thead>
              <tr>
                <th scope="col">Category</th>
                <th scope="col">Before</th>
                <th scope="col">Added</th>
                <th scope="col">After</th>
                <th scope="col">Approved</th>
                <th scope="col">Remaining</th>
                <th scope="col">Outcome</th>
                <th scope="col">Calculation</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((l) => (
                <tr key={l.category}>
                  <td>{categoryLabel(l.category)}</td>
                  <td>{l.before_active_count}</td>
                  <td>{l.added_count}</td>
                  <td>{l.after_active_count}</td>
                  <td>{l.approved_seats ?? "No rule"}</td>
                  <td>{l.remaining_capacity ?? "—"}</td>
                  <td>
                    {l.approved_seats === null ? (
                      <span className="status-badge neutral">
                        No conclusion
                      </span>
                    ) : l.would_exceed ? (
                      <span className="status-badge warning">
                        Would exceed by {l.excess}
                      </span>
                    ) : (
                      <span className="status-badge active">
                        Within capacity
                      </span>
                    )}
                  </td>
                  <td>
                    <code>{l.calculation}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </ScrollTable>
          <p className="data-note">{run.data.notice}</p>
        </div>
      )}
    </section>
  );
}
