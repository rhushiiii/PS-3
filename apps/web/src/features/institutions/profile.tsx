"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import {
  EmptyState,
  ErrorPanel,
  Loading,
  QueryBoundary,
} from "@/components/ui/feedback";
import { QueryPagination } from "@/components/ui/pagination";
import type { components } from "@/lib/api/generated";
import { isUUID } from "@/lib/api/client";
import { useApiQuery, useScope } from "@/lib/api/hooks";
import { plain } from "@/lib/format";
import { DeclaredTotalsPanel } from "@/features/intake/declarations-panel";
import { IntegritySignalsPanel } from "@/features/integrity/panel";
import { IntakeRulesPanel } from "@/features/intake/rules-panel";
import { SimulatorPanel } from "@/features/intake/simulator-panel";
import type { Programmes } from "@/features/submissions/data";

type Institution = components["schemas"]["InstitutionResponse"];

export function InstitutionProfile({
  institutionId,
}: {
  institutionId: string;
}) {
  const { session, request } = useSession();
  const [page, setPage] = useState(1);
  const valid = isUUID(institutionId);
  const key = useScope("institution", institutionId);
  const institution = useApiQuery<Institution>(
    key,
    `/institutions/${encodeURIComponent(institutionId)}`,
    { enabled: valid },
  );
  const programmes = useQuery({
    queryKey: [...key, "programmes", page],
    enabled: !!session && valid && !!institution.data,
    queryFn: ({ signal }) =>
      request<Programmes>(
        `/institutions/${encodeURIComponent(institutionId)}/programmes?page=${page}&page_size=10`,
        { signal },
      ),
  });
  if (!valid)
    return (
      <section className="feedback">
        <h1>Institution unavailable</h1>
        <p>The institution reference is invalid.</p>
      </section>
    );
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">INSTITUTION INFORMATION</p>
        <h1>Institution profile</h1>
        <p>A clear view of your institution and its programme records.</p>
        {session?.user.role === "AICTE_OFFICER" && (
          <Link
            className="button secondary"
            href={`/submissions?institution_id=${encodeURIComponent(institutionId)}`}
          >
            View submission history
          </Link>
        )}
      </div>
      <QueryBoundary query={institution} loading="Loading institution…">
        {(data) => (
          <>
            <section
              className="profile-card"
              aria-labelledby="institution-name"
            >
              <div className="institution-emblem" aria-hidden="true">
                {data.name.replace("Demo ", "").slice(0, 2).toUpperCase()}
              </div>
              <div className="profile-identity">
                <p className="tiny-label">SYNTHETIC INSTITUTION</p>
                <h2 id="institution-name">{data.name}</h2>
                <p>{data.permanent_id}</p>
              </div>
              <span
                className={`status-badge ${data.active ? "active" : "inactive"}`}
              >
                <span aria-hidden="true" />
                {data.active ? "Active institution" : "Inactive institution"}
              </span>
            </section>
            <div className="metadata-grid">
              <section className="metadata-item">
                <span className="tiny-label">PERMANENT INSTITUTION ID</span>
                <strong>{data.permanent_id}</strong>
              </section>
              <section className="metadata-item">
                <span className="tiny-label">REGION</span>
                <strong>{plain(data.region)}</strong>
              </section>
              <section className="metadata-item">
                <span className="tiny-label">DATA CONTEXT</span>
                <strong>Synthetic records</strong>
              </section>
            </div>
            <section
              className="panel"
              aria-labelledby="programmes-title"
              aria-busy={programmes.isFetching}
            >
              <header className="panel-heading">
                <div>
                  <p className="eyebrow">ACADEMIC STRUCTURE</p>
                  <h2 id="programmes-title">
                    Programmes{" "}
                    {programmes.data && (
                      <span className="count-pill">
                        {programmes.data.pagination.total}
                      </span>
                    )}
                  </h2>
                </div>
                <span className="quiet-label">Institution-scoped records</span>
              </header>
              {programmes.isPending ? (
                <Loading label="Loading programmes…" />
              ) : programmes.isError ? (
                <ErrorPanel
                  error={programmes.error}
                  retry={() => void programmes.refetch()}
                />
              ) : programmes.data.data.length === 0 ? (
                <EmptyState title="No programmes found">
                  No programme records are available for this institution.
                </EmptyState>
              ) : (
                <div
                  className="table-scroll"
                  tabIndex={0}
                  role="region"
                  aria-label="Programme table, scroll horizontally on small screens"
                >
                  <table>
                    <caption className="sr-only">
                      Programmes belonging to {data.name}
                    </caption>
                    <thead>
                      <tr>
                        <th scope="col">Programme</th>
                        <th scope="col">Programme code</th>
                        <th scope="col">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {programmes.data.data.map((programme) => (
                        <tr key={programme.id}>
                          <td>
                            <strong>{programme.name}</strong>
                          </td>
                          <td>
                            <span className="code-label">{programme.code}</span>
                          </td>
                          <td>
                            <span
                              className={`status-badge ${programme.active ? "active" : "inactive"}`}
                            >
                              {programme.active ? "Active" : "Inactive"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <QueryPagination
                query={programmes}
                page={page}
                pageSize={10}
                change={setPage}
              />
            </section>
            {session?.user.role !== "AICTE_MANAGER" && (
              <IntakeRulesPanel
                institutionId={institutionId}
                canEdit={session?.user.role === "AICTE_OFFICER"}
              />
            )}
            {session?.user.role === "AICTE_OFFICER" && (
              <>
                <IntegritySignalsPanel
                  institutionId={institutionId}
                  canDecide
                />
                <DeclaredTotalsPanel institutionId={institutionId} />
                <SimulatorPanel institutionId={institutionId} />
              </>
            )}
            <p className="data-note">
              These are local synthetic institution records. They do not
              establish official approval, enrolment totals or government
              verification.
            </p>
          </>
        )}
      </QueryBoundary>
    </>
  );
}
