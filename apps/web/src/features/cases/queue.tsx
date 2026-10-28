"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Icon } from "@/components/ui/icon";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import type { components } from "@/lib/api/generated";
import {
  CASE_STATUSES,
  statusLabel,
  statusTone,
  type CaseStatus,
} from "./shared";

type CasePage = components["schemas"]["Page_CaseResponse_"];

export function CaseQueue() {
  const { session, request } = useSession();
  const [status, setStatus] = useState<CaseStatus | "">("");
  const [page, setPage] = useState(1);
  const officer = session?.user.role === "AICTE_OFFICER";
  const cases = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "cases",
      status,
      page,
    ],
    enabled: !!session,
    queryFn: ({ signal }) => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20",
      });
      if (status) params.set("status", status);
      return request<CasePage>(`/cases?${params}`, { signal });
    },
  });
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">EVIDENCE-LINKED REVIEW</p>
        <h1>Officer cases</h1>
        <p>
          {officer
            ? "Open and manage cases investigating potential overlaps or mismatches. Opening a case is not a fraud determination."
            : "Cases referencing your institution's records. You may read the timeline and add comments."}
        </p>
      </div>
      <section className="panel" aria-labelledby="case-queue-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">CASE QUEUE</p>
            <h2 id="case-queue-title">
              {officer ? "All cases" : "Cases for your institution"}
            </h2>
          </div>
          <label className="inline-filter">
            Status
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as CaseStatus | "");
                setPage(1);
              }}
            >
              <option value="">All statuses</option>
              {CASE_STATUSES.map((item) => (
                <option key={item} value={item}>
                  {statusLabel(item)}
                </option>
              ))}
            </select>
          </label>
        </header>
        {cases.isPending ? (
          <Loading label="Loading cases…" />
        ) : cases.isError ? (
          <ErrorPanel error={cases.error} retry={() => void cases.refetch()} />
        ) : cases.data.data.length === 0 ? (
          <div className="empty-state">
            <h3>No cases match this view</h3>
            <p>
              {officer
                ? "Open a case from a flagged finding to begin an investigation."
                : "No officer has opened a case against your institution's records."}
            </p>
          </div>
        ) : (
          <div className="institution-list">
            {cases.data.data.map((item) => (
              <article key={item.id} className="directory-item">
                <span className="directory-icon" aria-hidden="true">
                  <Icon name="flag" />
                </span>
                <div>
                  <h3>
                    <Link href={`/cases/${item.id}`}>
                      {item.category.replaceAll("_", " ")}
                    </Link>
                  </h3>
                  <p>
                    {item.summary.length > 140
                      ? `${item.summary.slice(0, 140)}…`
                      : item.summary}
                  </p>
                  <p className="cell-note">
                    Opened{" "}
                    <time dateTime={item.opened_at}>
                      {new Date(item.opened_at).toLocaleString()}
                    </time>{" "}
                    · {item.record_version_ids.length} linked record
                    {item.record_version_ids.length === 1 ? "" : "s"}
                  </p>
                </div>
                <span className={`status-badge ${statusTone(item.status)}`}>
                  {statusLabel(item.status)}
                </span>
              </article>
            ))}
          </div>
        )}
        {cases.data && (
          <Pagination
            page={page}
            pageSize={20}
            total={cases.data.pagination.total}
            busy={cases.isFetching}
            change={setPage}
          />
        )}
      </section>
      <p className="data-note">
        Cases reference synthetic records only. A case is a review lead, not a
        fraud determination or official APAAR identity verification.
      </p>
    </>
  );
}
