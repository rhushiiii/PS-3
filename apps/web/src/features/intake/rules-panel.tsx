"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import {
  useSubmissionContext,
  validAcademicYear,
} from "@/features/submissions/data";
import { ApiError } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";
import {
  DEFAULT_YEAR,
  DemoRuleNotice,
  ScrollTable,
  categoryLabel,
  intakeMessage,
} from "./shared";

type Rule = components["schemas"]["IntakeRuleResponse"];
type RulePage = components["schemas"]["Page_IntakeRuleResponse_"];
type ChangePage = components["schemas"]["Page_RuleChangeResponse_"];

const jsonHeaders = { "Content-Type": "application/json" };

function EditRuleDialog({
  rule,
  institutionId,
  programmeName,
  onClose,
  onSaved,
}: {
  rule: Rule;
  institutionId: string;
  programmeName: string;
  onClose: () => void;
  onSaved: (message: string) => void;
}) {
  const { request } = useSession();
  const [seats, setSeats] = useState(String(rule.approved_seats));
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const save = useMutation({
    mutationFn: (body: { approved_seats: number; reason: string }) =>
      request(`/institutions/${institutionId}/intake/${rule.id}`, {
        method: "PATCH",
        headers: jsonHeaders,
        body: JSON.stringify(body),
      }),
    onSuccess: () =>
      onSaved(
        `${programmeName} · ${categoryLabel(rule.category)} DEMO approved seats updated.`,
      ),
    onError: (e) => setError(intakeMessage(e)),
  });
  const submit = () => {
    const value = Number(seats);
    const trimmed = reason.trim();
    if (!/^\d+$/.test(seats) || value > 1_000_000)
      return setError(
        "Enter approved seats as a whole number up to 1,000,000.",
      );
    if (value === rule.approved_seats)
      return setError("Approved seats already have this value.");
    if (trimmed.length < 3 || trimmed.length > 500)
      return setError("Give a reason between 3 and 500 characters.");
    setError("");
    save.mutate({ approved_seats: value, reason: trimmed });
  };
  return (
    <ConfirmDialog
      open
      title="Change DEMO approved seats"
      confirmLabel="Confirm change"
      busy={save.isPending}
      onCancel={onClose}
      onConfirm={submit}
    >
      <p>
        {programmeName} · {categoryLabel(rule.category)} · {rule.academic_year}{" "}
        · rule {rule.rule_version}. This changes a DEMO value only and is
        recorded in the change history.
      </p>
      <div className="dialog-fields">
        <label>
          Approved seats
          <input
            inputMode="numeric"
            value={seats}
            onChange={(e) => setSeats(e.target.value)}
          />
        </label>
        <label>
          Reason (required)
          <input
            value={reason}
            maxLength={500}
            onChange={(e) => setReason(e.target.value)}
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
      </div>
    </ConfirmDialog>
  );
}

export function IntakeRulesPanel({
  institutionId,
  canEdit,
}: {
  institutionId: string;
  canEdit: boolean;
}) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const { options } = useSubmissionContext(institutionId);
  const [yearDraft, setYearDraft] = useState(DEFAULT_YEAR);
  const [year, setYear] = useState(DEFAULT_YEAR);
  const [yearError, setYearError] = useState("");
  const [editing, setEditing] = useState<Rule | null>(null);
  const [notice, setNotice] = useState("");
  const [historyPage, setHistoryPage] = useState(1);
  const key = [
    "private",
    session?.generation,
    session?.user.id,
    "intake-rules",
    institutionId,
  ];
  const names = new Map(options.map((p) => [p.id, p.name]));
  const rules = useQuery({
    queryKey: [...key, "rules", year],
    enabled: !!session,
    retry: false,
    queryFn: ({ signal }) =>
      request<RulePage>(
        `/institutions/${institutionId}/intake?academic_year=${year}&page=1&page_size=100`,
        { signal },
      ),
  });
  const changes = useQuery({
    queryKey: [...key, "changes", historyPage],
    enabled: !!session && canEdit,
    retry: false,
    queryFn: ({ signal }) =>
      request<ChangePage>(
        `/institutions/${institutionId}/intake/changes?page=${historyPage}&page_size=5`,
        { signal },
      ),
  });
  const forbidden =
    rules.error instanceof ApiError && rules.error.status === 403;
  const ruleById = new Map((rules.data?.data ?? []).map((r) => [r.id, r]));
  const sorted = [...(rules.data?.data ?? [])].sort(
    (a, b) =>
      (names.get(a.programme_id) ?? "").localeCompare(
        names.get(b.programme_id) ?? "",
      ) || a.category.localeCompare(b.category),
  );
  return (
    <section
      className="panel"
      aria-labelledby="intake-rules-title"
      aria-busy={rules.isFetching}
    >
      <header className="panel-heading">
        <div>
          <p className="eyebrow">DEMO INTAKE CONFIGURATION</p>
          <h2 id="intake-rules-title">Intake rules</h2>
        </div>
        <span className="quiet-label">Per programme and seat category</span>
      </header>
      <div className="panel-padding">
        <DemoRuleNotice />
        <form
          className="validation-filters"
          onSubmit={(e) => {
            e.preventDefault();
            if (!validAcademicYear(yearDraft))
              return setYearError("Use an academic year such as 2026-27.");
            setYearError("");
            setYear(yearDraft);
          }}
        >
          <label>
            Academic year
            <input
              value={yearDraft}
              onChange={(e) => setYearDraft(e.target.value)}
            />
          </label>
          <button className="button secondary" type="submit">
            Show rules
          </button>
          {yearError && (
            <p className="form-error" role="alert">
              {yearError}
            </p>
          )}
        </form>
        <div aria-live="polite">
          {notice && <p className="form-success">{notice}</p>}
        </div>
      </div>
      {rules.isPending ? (
        <Loading label="Loading intake rules…" />
      ) : forbidden ? (
        <div className="empty-state compact">
          <h3>Intake rules not available for your role</h3>
          <p>
            Your account does not have permission to view intake configuration.
          </p>
        </div>
      ) : rules.isError ? (
        <ErrorPanel error={rules.error} retry={() => void rules.refetch()} />
      ) : sorted.length === 0 ? (
        <div className="empty-state compact">
          <h3>No intake rules for {year}</h3>
          <p>No DEMO intake rules are configured for this academic year.</p>
        </div>
      ) : (
        <ScrollTable label={`DEMO intake rules for ${year}`}>
          <thead>
            <tr>
              <th scope="col">Programme</th>
              <th scope="col">Category</th>
              <th scope="col">Approved seats</th>
              <th scope="col">Rule version</th>
              {canEdit && <th scope="col">Action</th>}
            </tr>
          </thead>
          <tbody>
            {sorted.map((rule) => (
              <tr key={rule.id}>
                <td>{names.get(rule.programme_id) ?? "Programme"}</td>
                <td>{categoryLabel(rule.category)}</td>
                <td>
                  <strong>{rule.approved_seats.toLocaleString()}</strong>{" "}
                  <span className="status-badge neutral">
                    {rule.source_label}
                  </span>
                </td>
                <td>{rule.rule_version}</td>
                {canEdit && (
                  <td>
                    <button
                      className="button secondary small"
                      onClick={() => {
                        setNotice("");
                        setEditing(rule);
                      }}
                    >
                      Edit
                      <span className="sr-only">
                        {" "}
                        {names.get(rule.programme_id)}{" "}
                        {categoryLabel(rule.category)}
                      </span>
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </ScrollTable>
      )}
      {canEdit && (
        <div className="panel-padding">
          <h3>Change history</h3>
          {changes.isPending ? (
            <Loading label="Loading change history…" />
          ) : changes.isError ? (
            <ErrorPanel
              error={changes.error}
              retry={() => void changes.refetch()}
            />
          ) : changes.data.data.length === 0 ? (
            <p className="form-help">No rule changes have been recorded.</p>
          ) : (
            <>
              <ScrollTable label="DEMO intake rule change history">
                <thead>
                  <tr>
                    <th scope="col">When</th>
                    <th scope="col">Rule</th>
                    <th scope="col">Seats</th>
                    <th scope="col">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {changes.data.data.map((change) => {
                    const rule = ruleById.get(change.intake_rule_id);
                    return (
                      <tr key={change.id}>
                        <td>
                          <time dateTime={change.created_at}>
                            {new Date(change.created_at).toLocaleString()}
                          </time>
                        </td>
                        <td>
                          {rule
                            ? `${names.get(rule.programme_id) ?? "Programme"} · ${categoryLabel(rule.category)}`
                            : "Rule in another academic year"}
                        </td>
                        <td>
                          {change.old_approved_seats} →{" "}
                          {change.new_approved_seats}
                          <small>
                            {" "}
                            version {change.new_rule_version} ·{" "}
                            {change.source_label}
                          </small>
                        </td>
                        <td>{change.reason}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </ScrollTable>
              <Pagination
                page={historyPage}
                pageSize={5}
                total={changes.data.pagination.total}
                busy={changes.isFetching}
                change={setHistoryPage}
                label="Change history pagination"
              />
            </>
          )}
        </div>
      )}
      {editing && (
        <EditRuleDialog
          key={editing.id}
          rule={editing}
          institutionId={institutionId}
          programmeName={names.get(editing.programme_id) ?? "Programme"}
          onClose={() => setEditing(null)}
          onSaved={(message) => {
            setEditing(null);
            setNotice(message);
            void queryClient.invalidateQueries({ queryKey: key });
          }}
        />
      )}
    </section>
  );
}
