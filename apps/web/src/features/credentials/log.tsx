"use client";

import { useState } from "react";
import { EmptyState, QueryBoundary } from "@/components/ui/feedback";
import { QueryPagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { useApiQuery, useScope } from "@/lib/api/hooks";
import { DEMO_TAG } from "@/lib/format";
import type { components } from "@/lib/api/generated";
import { outcomeLabel, outcomeTone, when } from "./shared";

type LogPage = components["schemas"]["Page_VerificationLogEntry_"];
const PAGE_SIZE = 20;

export function VerificationLog() {
  const { session } = useSession();
  const [page, setPage] = useState(1);
  const officer = session?.user.role === "AICTE_OFFICER";
  const log = useApiQuery<LogPage>(
    useScope("vlog", page),
    `/credentials/verifications?page=${page}&page_size=${PAGE_SIZE}`,
  );
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">{`AUDIT · ${DEMO_TAG}`}</p>
        <h1>Verification log</h1>
        <p>
          {officer
            ? "All credential verifications."
            : "Your credential verifications."}{" "}
          Tokens are never stored or shown here.
        </p>
      </div>
      <section className="panel" aria-labelledby="log-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">LOG</p>
            <h2 id="log-title">Verifications</h2>
          </div>
        </header>
        <QueryBoundary query={log} loading="Loading verification log…">
          {(data) =>
            data.data.length === 0 ? (
              <EmptyState title="No verifications yet">
                Checks you run appear here.
              </EmptyState>
            ) : (
              <div
                className="table-scroll"
                tabIndex={0}
                role="region"
                aria-label="Verification log"
              >
                <table className="review-table">
                  <caption>Credential verifications</caption>
                  <thead>
                    <tr>
                      <th scope="col">Time</th>
                      <th scope="col">Outcome</th>
                      <th scope="col">Purpose</th>
                      <th scope="col">Consent reference</th>
                      {officer && <th scope="col">Verifier</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {data.data.map((e) => (
                      <tr key={e.id}>
                        <td>{when(e.verified_at)}</td>
                        <td>
                          <span
                            className={`status-badge ${outcomeTone[e.outcome]}`}
                          >
                            {outcomeLabel[e.outcome]}
                          </span>
                        </td>
                        <td>{e.purpose}</td>
                        <td>{e.consent_ref}</td>
                        {officer && (
                          <td>
                            <code>{e.verifier_user_id.slice(0, 8)}</code>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        </QueryBoundary>
        <QueryPagination
          query={log}
          page={page}
          pageSize={PAGE_SIZE}
          change={setPage}
        />
      </section>
    </>
  );
}
