"use client";

import { Fragment, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { DashboardTable, prettyLabel } from "@/features/dashboards/components";
import type { components } from "@/lib/api/generated";

type AuditPage = components["schemas"]["Page_AuditEventResponse_"];
type Actions = components["schemas"]["AuditActionsResponse"];
type InstitutionPage = components["schemas"]["Page_InstitutionResponse_"];

type Filters = {
  action: string;
  entityType: string;
  institution: string;
  actor: string;
  from: string;
  to: string;
};
const EMPTY: Filters = {
  action: "",
  entityType: "",
  institution: "",
  actor: "",
  from: "",
  to: "",
};
const PAGE_SIZE = 25;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** datetime-local has no zone; new Date() interprets it as local time. */
function toIso(value: string): string | null {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function show(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function AuditExplorer() {
  const { session, request } = useSession();
  const [draft, setDraft] = useState<Filters>(EMPTY);
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const scope = ["private", session?.generation, session?.user.id, "audit"];

  const actions = useQuery({
    queryKey: [...scope, "actions"],
    enabled: !!session,
    queryFn: ({ signal }) => request<Actions>("/audit/actions", { signal }),
  });
  const institutions = useQuery({
    queryKey: [...scope, "institutions"],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<InstitutionPage>("/institutions?page=1&page_size=100", {
        signal,
      }),
  });
  const institutionNames = new Map(
    (institutions.data?.data ?? []).map((i) => [i.id, i.name]),
  );

  const events = useQuery<AuditPage>({
    queryKey: [...scope, "events", filters, page],
    enabled: !!session,
    placeholderData: (previous) => previous,
    queryFn: ({ signal }) => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
      });
      if (filters.action) params.set("action", filters.action);
      if (filters.entityType) params.set("entity_type", filters.entityType);
      if (filters.institution)
        params.set("institution_id", filters.institution);
      if (filters.actor) params.set("actor_user_id", filters.actor);
      if (filters.from) params.set("from", filters.from);
      if (filters.to) params.set("to", filters.to);
      return request<AuditPage>(`/audit/events?${params}`, { signal });
    },
  });

  function apply() {
    const actor = draft.actor.trim();
    if (actor && !UUID.test(actor)) {
      setError("Actor id must be a user id in UUID format.");
      return;
    }
    const from = draft.from ? toIso(draft.from) : "";
    const to = draft.to ? toIso(draft.to) : "";
    if (from === null || to === null) {
      setError("Enter valid from and to dates.");
      return;
    }
    if (from && to && from > to) {
      setError("The from date must be before the to date.");
      return;
    }
    setError("");
    setFilters({ ...draft, actor, from, to });
    setPage(1);
    setExpanded(null);
  }

  return (
    <div className="dashboard-page">
      <header className="page-heading">
        <p className="eyebrow">OFFICER AUDIT TRAIL</p>
        <h1>Audit explorer</h1>
        <p>
          Newest events first. Event details are redacted: APAAR numbers and
          access tokens are never shown here.
        </p>
      </header>

      <section className="panel dashboard-panel" aria-label="Audit filters">
        <form
          className="dashboard-filters"
          onSubmit={(event) => {
            event.preventDefault();
            apply();
          }}
        >
          <label>
            Action
            <select
              value={draft.action}
              onChange={(e) => setDraft({ ...draft, action: e.target.value })}
              disabled={actions.isPending}
            >
              <option value="">All actions</option>
              {(actions.data?.data ?? []).map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </label>
          <label>
            Entity type
            <input
              value={draft.entityType}
              onChange={(e) =>
                setDraft({ ...draft, entityType: e.target.value })
              }
              placeholder="e.g. case"
            />
          </label>
          <label>
            Institution
            <select
              value={draft.institution}
              onChange={(e) =>
                setDraft({ ...draft, institution: e.target.value })
              }
            >
              <option value="">All institutions</option>
              {(institutions.data?.data ?? []).map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Actor id
            <input
              value={draft.actor}
              onChange={(e) => setDraft({ ...draft, actor: e.target.value })}
              placeholder="User id (UUID)"
              autoComplete="off"
            />
          </label>
          <label>
            From
            <input
              type="datetime-local"
              value={draft.from}
              onChange={(e) => setDraft({ ...draft, from: e.target.value })}
            />
          </label>
          <label>
            To
            <input
              type="datetime-local"
              value={draft.to}
              onChange={(e) => setDraft({ ...draft, to: e.target.value })}
            />
          </label>
          <button className="button secondary" type="submit">
            Apply filters
          </button>
          <button
            className="button secondary"
            type="button"
            onClick={() => {
              setDraft(EMPTY);
              setFilters(EMPTY);
              setPage(1);
              setError("");
              setExpanded(null);
            }}
          >
            Clear
          </button>
        </form>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {(actions.isError || institutions.isError) && (
          <p className="form-error" role="alert">
            Some filter options could not be loaded. Other filters still work.
          </p>
        )}
      </section>

      <section className="panel" aria-label="Audit events">
        <p className="sr-only" role="status" aria-live="polite">
          {events.data ? `${events.data.pagination.total} events found` : ""}
        </p>
        {events.isPending ? (
          <Loading label="Loading audit events…" />
        ) : events.isError ? (
          <ErrorPanel
            error={events.error}
            retry={() => void events.refetch()}
          />
        ) : events.data.data.length === 0 ? (
          <div className="empty-state">
            <h3>No audit events</h3>
            <p>No events match these filters.</p>
          </div>
        ) : (
          <DashboardTable label="Audit events table">
            <caption className="sr-only">
              Audit events, newest first. Use Details to view redacted event
              details.
            </caption>
            <thead>
              <tr>
                <th scope="col">Time</th>
                <th scope="col">Action</th>
                <th scope="col">Actor</th>
                <th scope="col">Entity</th>
                <th scope="col">Institution</th>
                <th scope="col">
                  <span className="sr-only">Details</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {events.data.data.map((event) => {
                const open = expanded === event.id;
                const entries = Object.entries(event.details);
                return (
                  <Fragment key={event.id}>
                    <tr>
                      <td>
                        <time dateTime={event.occurred_at}>
                          {new Date(event.occurred_at).toLocaleString()}
                        </time>
                      </td>
                      <td>{event.action}</td>
                      <td>
                        {event.actor ? (
                          <>
                            {event.actor.display_name}
                            <small>
                              {" "}
                              {event.actor.role
                                ? prettyLabel(event.actor.role)
                                : "No role"}
                            </small>
                          </>
                        ) : (
                          "System"
                        )}
                      </td>
                      <td>
                        {prettyLabel(event.entity_type)}
                        <small> {event.entity_id}</small>
                      </td>
                      <td>
                        {event.institution_id
                          ? (institutionNames.get(event.institution_id) ??
                            event.institution_id)
                          : "—"}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="button secondary small"
                          aria-expanded={open}
                          aria-controls={`audit-detail-${event.id}`}
                          onClick={() => setExpanded(open ? null : event.id)}
                        >
                          {open ? "Hide details" : "Details"}
                        </button>
                      </td>
                    </tr>
                    {open && (
                      <tr id={`audit-detail-${event.id}`}>
                        <td colSpan={6}>
                          <p className="data-note">
                            Redacted details. APAAR numbers and tokens are never
                            shown.
                          </p>
                          {entries.length === 0 ? (
                            <p>No additional details were recorded.</p>
                          ) : (
                            <dl className="kv-list">
                              {entries.map(([key, value]) => (
                                <Fragment key={key}>
                                  <dt>{key}</dt>
                                  <dd>{show(value)}</dd>
                                </Fragment>
                              ))}
                            </dl>
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </DashboardTable>
        )}
        {events.data && events.data.pagination.total > PAGE_SIZE && (
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={events.data.pagination.total}
            busy={events.isFetching}
            change={(next) => {
              setPage(next);
              setExpanded(null);
            }}
            label="Audit pagination"
          />
        )}
      </section>
    </div>
  );
}
