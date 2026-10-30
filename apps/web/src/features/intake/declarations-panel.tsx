"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import {
  useSubmissionContext,
  validAcademicYear,
} from "@/features/submissions/data";
import { useApiQuery, useScope } from "@/lib/api/hooks";
import type { components } from "@/lib/api/generated";
import { when } from "@/lib/format";
import {
  DEFAULT_YEAR,
  DemoRuleNotice,
  ScrollTable,
  intakeMessage,
} from "./shared";

type Declaration = components["schemas"]["DeclarationResponse"];
type DeclarationPage = components["schemas"]["Page_DeclarationResponse_"];
type Draft = {
  programme_id: string;
  academic_year: string;
  declared_total: number;
  basis: string;
};

export function DeclaredTotalsPanel({
  institutionId,
}: {
  institutionId: string;
}) {
  const { request } = useSession();
  const queryClient = useQueryClient();
  const { options } = useSubmissionContext(institutionId);
  const [page, setPage] = useState(1);
  const [programmeId, setProgrammeId] = useState("");
  const [year, setYear] = useState(DEFAULT_YEAR);
  const [total, setTotal] = useState("");
  const [basis, setBasis] = useState("");
  const [formError, setFormError] = useState("");
  const [pending, setPending] = useState<Draft | null>(null);
  const [notice, setNotice] = useState("");
  const key = useScope("declarations", institutionId);
  const names = new Map(options.map((p) => [p.id, p.name]));
  const list = useApiQuery<DeclarationPage>(
    [...key, page],
    `/institutions/${institutionId}/declarations?page=${page}&page_size=10`,
  );
  const create = useMutation({
    mutationFn: (body: Draft) =>
      request<Declaration>(`/institutions/${institutionId}/declarations`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    onSuccess: async (saved) => {
      setPending(null);
      setFormError("");
      setTotal("");
      setBasis("");
      setPage(1);
      setNotice(
        `Declared total ${saved.declared_total.toLocaleString()} recorded for ${names.get(saved.programme_id) ?? "programme"}, ${saved.academic_year}.`,
      );
      await queryClient.invalidateQueries({ queryKey: key });
    },
    onError: (e) => {
      setPending(null);
      setNotice("");
      setFormError(intakeMessage(e));
    },
  });
  // Rows arrive newest first per the API; mark the first seen per programme and year.
  const seen = new Set<string>();
  const rows = [...(list.data?.data ?? [])]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .map((d) => {
      const id = `${d.programme_id}:${d.academic_year}`;
      const latest = !seen.has(id);
      seen.add(id);
      return { d, latest };
    });
  return (
    <section
      className="panel"
      aria-labelledby="declared-title"
      aria-busy={list.isFetching}
    >
      <header className="panel-heading">
        <div>
          <p className="eyebrow">DEMO REFERENCE TOTALS</p>
          <h2 id="declared-title">Declared totals</h2>
        </div>
        <span className="quiet-label">Append-only declarations</span>
      </header>
      <div className="panel-padding">
        <DemoRuleNotice />
        <form
          className="validation-filters"
          onSubmit={(e) => {
            e.preventDefault();
            const value = Number(total);
            if (!programmeId) return setFormError("Choose a programme.");
            if (!validAcademicYear(year))
              return setFormError("Use an academic year such as 2026-27.");
            if (!/^\d+$/.test(total) || value > 10_000_000)
              return setFormError(
                "Enter the declared total as a whole number.",
              );
            if (!basis.trim() || basis.trim().length > 500)
              return setFormError(
                "Give the basis of the declaration (up to 500 characters).",
              );
            setFormError("");
            setNotice("");
            setPending({
              programme_id: programmeId,
              academic_year: year,
              declared_total: value,
              basis: basis.trim(),
            });
          }}
        >
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
          <label>
            Declared total
            <input
              inputMode="numeric"
              value={total}
              onChange={(e) => setTotal(e.target.value)}
            />
          </label>
          <label>
            Basis
            <input
              value={basis}
              maxLength={500}
              onChange={(e) => setBasis(e.target.value)}
            />
          </label>
          <button
            className="button primary"
            type="submit"
            disabled={create.isPending}
          >
            Declare total
          </button>
        </form>
        <div aria-live="polite">
          {notice && <p className="form-success">{notice}</p>}
        </div>
        {formError && (
          <p className="form-error" role="alert">
            {formError}
          </p>
        )}
      </div>
      {list.isPending ? (
        <Loading label="Loading declared totals…" />
      ) : list.isError ? (
        <ErrorPanel error={list.error} retry={() => void list.refetch()} />
      ) : rows.length === 0 ? (
        <div className="empty-state compact">
          <h3>No declared totals</h3>
          <p>
            Without a declared total, assessments report “No reference total
            declared” and draw no missing-population conclusion.
          </p>
        </div>
      ) : (
        <>
          <ScrollTable label="Declared totals, newest first">
            <thead>
              <tr>
                <th scope="col">Programme</th>
                <th scope="col">Year</th>
                <th scope="col">Declared total</th>
                <th scope="col">Basis</th>
                <th scope="col">Recorded</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ d, latest }) => (
                <tr key={d.id}>
                  <td>{names.get(d.programme_id) ?? "Programme"}</td>
                  <td>{d.academic_year}</td>
                  <td>
                    <strong>{d.declared_total.toLocaleString()}</strong>{" "}
                    <span
                      className={`status-badge ${latest ? "active" : "neutral"}`}
                    >
                      {latest ? "Latest on page" : "Superseded"}
                    </span>{" "}
                    <span className="status-badge neutral">
                      {d.source_label}
                    </span>
                  </td>
                  <td>{d.basis}</td>
                  <td>{when(d.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </ScrollTable>
          <Pagination
            page={page}
            pageSize={10}
            total={list.data.pagination.total}
            busy={list.isFetching}
            change={setPage}
            label="Declared totals pagination"
          />
        </>
      )}
      {pending && (
        <ConfirmDialog
          open
          title="Record declared total"
          confirmLabel="Record declaration"
          busy={create.isPending}
          onCancel={() => setPending(null)}
          onConfirm={() => create.mutate(pending)}
        >
          <p>
            Declare {pending.declared_total.toLocaleString()} for{" "}
            {names.get(pending.programme_id) ?? "the programme"},{" "}
            {pending.academic_year}. Declarations are never overwritten; a newer
            one supersedes this value in future assessments. It is a DEMO
            reference, not an official figure.
          </p>
        </ConfirmDialog>
      )}
    </section>
  );
}
