"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { QueryBoundary } from "@/components/ui/feedback";
import { Icon } from "@/components/ui/icon";
import { QueryPagination } from "@/components/ui/pagination";
import type { paths } from "@/lib/api/generated";

type Institutions =
  paths["/api/v1/institutions"]["get"]["responses"][200]["content"]["application/json"];

export function InstitutionDirectory() {
  const { session, request } = useSession();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);
  const institutions = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "institutions",
      filter,
      page,
    ],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<Institutions>(
        `/institutions?${new URLSearchParams({ q: filter, page: String(page), page_size: "10" })}`,
        { signal },
      ),
  });
  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">INSTITUTION DIRECTORY</p>
        <h1>Institutions</h1>
        <p>
          Explore institution information within your permitted review
          workspace.
        </p>
      </div>
      <section className="panel" aria-labelledby="directory-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">LOCAL RECORDS</p>
            <h2 id="directory-title">Institution information</h2>
          </div>
          <span className="quiet-label">Synthetic data only</span>
        </header>
        <form
          className="search-form"
          onSubmit={(event) => {
            event.preventDefault();
            setPage(1);
            setFilter(search.trim());
          }}
        >
          <label htmlFor="institution-search">Search institutions</label>
          <div>
            <input
              id="institution-search"
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by institution name"
              maxLength={200}
            />
            <button className="button secondary" type="submit">
              Search
            </button>
          </div>
        </form>
        <QueryBoundary query={institutions} loading="Loading institutions…">
          {(data) =>
            data.data.length === 0 ? (
              <div className="empty-state">
                <h3>No matching institutions</h3>
                <p>Try a different institution name.</p>
              </div>
            ) : (
              <div className="institution-list">
                {data.data.map((institution) => (
                  <article key={institution.id} className="directory-item">
                    <span className="directory-icon" aria-hidden="true">
                      <Icon name="building" />
                    </span>
                    <div>
                      <h3>
                        <Link href={`/aicte/institutions/${institution.id}`}>
                          {institution.name}
                        </Link>
                      </h3>
                      <p>
                        {institution.permanent_id}{" "}
                        <span aria-hidden="true">·</span>{" "}
                        {institution.region.replaceAll("_", " ")}
                      </p>
                    </div>
                    <Link
                      className="view-link"
                      href={`/aicte/institutions/${institution.id}`}
                      aria-label={`View ${institution.name}`}
                    >
                      View institution
                      <Icon name="arrow" />
                    </Link>
                  </article>
                ))}
              </div>
            )
          }
        </QueryBoundary>
        <QueryPagination
          query={institutions}
          page={page}
          pageSize={10}
          change={setPage}
        />
      </section>
      <p className="data-note">
        Institution and programme metadata only. This view makes no claim of
        official APAAR verification.
      </p>
    </>
  );
}
