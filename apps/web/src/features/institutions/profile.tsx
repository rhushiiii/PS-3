"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { useSession } from "@/features/auth/session";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import type { components, paths } from "@/lib/api/generated";
import { isUUID } from "@/lib/api/client";
import { DeclaredTotalsPanel } from "@/features/intake/declarations-panel";
import { IntegritySignalsPanel } from "@/features/integrity/panel";
import { IntakeRulesPanel } from "@/features/intake/rules-panel";
import { SimulatorPanel } from "@/features/intake/simulator-panel";

type Institution = components["schemas"]["InstitutionResponse"];
type Programmes =
  paths["/api/v1/institutions/{institution_id}/programmes"]["get"]["responses"][200]["content"]["application/json"];

export function InstitutionProfile({
  institutionId,
}: {
  institutionId: string;
}) {
  const { session, request } = useSession();
  const [page, setPage] = useState(1);
  const valid = isUUID(institutionId);
  const key = [
    "private",
    session?.generation,
    session?.user.id,
    "institution",
    institutionId,
  ];
  const institution = useQuery({
    queryKey: key,
    enabled: !!session && valid,
    queryFn: ({ signal }) =>
      request<Institution>(
        `/institutions/${encodeURIComponent(institutionId)}`,
        { signal },
      ),
  });
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
      {institution.isPending ? (
        <Loading label="Loading institution…" />
      ) : institution.isError ? (
        <ErrorPanel
          error={institution.error}
          retry={() => void institution.refetch()}
        />
      ) : (
        <>
          <section className="profile-card" aria-labelledby="institution-name">
            <div className="institution-emblem" aria-hidden="true">
              {institution.data.name
                .replace("Demo ", "")
                .slice(0, 2)
                .toUpperCase()}
            </div>
            <div className="profile-identity">
              <p className="tiny-label">SYNTHETIC INSTITUTION</p>
              <h2 id="institution-name">{institution.data.name}</h2>
              <p>{institution.data.permanent_id}</p>
            </div>
            <span
              className={`status-badge ${institution.data.active ? "active" : "inactive"}`}
            >
              <span aria-hidden="true" />
              {institution.data.active
                ? "Active institution"
                : "Inactive institution"}
            </span>
          </section>
          <div className="metadata-grid">
            <section className="metadata-item">
              <span className="tiny-label">PERMANENT INSTITUTION ID</span>
              <strong>{institution.data.permanent_id}</strong>
            </section>
            <section className="metadata-item">
              <span className="tiny-label">REGION</span>
              <strong>{institution.data.region.replaceAll("_", " ")}</strong>
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
              <div className="empty-state">
                <h3>No programmes found</h3>
                <p>No programme records are available for this institution.</p>
              </div>
            ) : (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Programme table, scroll horizontally on small screens"
              >
                <table>
                  <caption className="sr-only">
                    Programmes belonging to {institution.data.name}
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
            {programmes.data && (
              <Pagination
                page={page}
                pageSize={10}
                total={programmes.data.pagination.total}
                busy={programmes.isFetching}
                change={setPage}
              />
            )}
          </section>
          {session?.user.role !== "AICTE_MANAGER" && (
            <IntakeRulesPanel
              institutionId={institutionId}
              canEdit={session?.user.role === "AICTE_OFFICER"}
            />
          )}
          {session?.user.role === "AICTE_OFFICER" && (
            <>
              <IntegritySignalsPanel institutionId={institutionId} canDecide />
              <DeclaredTotalsPanel institutionId={institutionId} />
              <SimulatorPanel institutionId={institutionId} />
            </>
          )}
          <p className="data-note">
            These are local synthetic institution records. They do not establish
            official approval, enrolment totals or government verification.
          </p>
        </>
      )}
    </>
  );
}
