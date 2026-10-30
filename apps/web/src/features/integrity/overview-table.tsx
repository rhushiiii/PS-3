"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useSession } from "@/features/auth/session";
import { ScrollTable } from "@/features/intake/shared";
import type { components } from "@/lib/api/generated";
import { FAMILIES, bandTone } from "./panel";

type Overview = components["schemas"]["OverviewResponse"];
const BANDS = ["LOW", "MEDIUM", "HIGH"] as const;
const PAGE_SIZE = 10;

/** Aggregate review prioritisation; officers get links, managers get names only. */
export function InstitutionsRequiringReview({
  canOpenInstitution,
  initialYear,
}: {
  canOpenInstitution: boolean;
  initialYear: string;
}) {
  const { session, request } = useSession();
  const [yearDraft, setYearDraft] = useState(initialYear);
  const [year, setYear] = useState(initialYear);
  const [bandDraft, setBandDraft] = useState("");
  const [band, setBand] = useState("");
  const [yearError, setYearError] = useState("");
  const [page, setPage] = useState(1);
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(PAGE_SIZE),
  });
  if (year) params.set("academic_year", year);
  if (band) params.set("band", band);
  const overview = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "integrity-overview",
      year,
      band,
      page,
    ],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<Overview>(`/integrity/overview?${params}`, { signal }),
  });
  return (
    <section
      className="panel"
      aria-labelledby="review-title"
      aria-busy={overview.isFetching}
    >
      <header className="panel-heading">
        <div>
          <p className="eyebrow">REVIEW PRIORITISATION</p>
          <h2 id="review-title">Institutions requiring review</h2>
        </div>
        <span className="quiet-label">Aggregates only</span>
      </header>
      <div className="panel-padding">
        <aside className="demo-banner" aria-label="Prioritisation notice">
          <span className="demo-dot" aria-hidden="true" />
          Prioritisation, not a finding
          <span className="banner-detail">
            {overview.data?.disclaimer ??
              "Rule-based review prompts from DEMO data. They are not fraud findings or compliance determinations; officers decide."}
          </span>
        </aside>
        <form
          className="dashboard-filters"
          onSubmit={(e) => {
            e.preventDefault();
            if (yearDraft && !/^\d{4}-\d{2}$/.test(yearDraft))
              return setYearError("Use an academic year such as 2026-27.");
            setYearError("");
            setYear(yearDraft);
            setBand(bandDraft);
            setPage(1);
          }}
        >
          <label>
            Academic year
            <input
              value={yearDraft}
              placeholder="2026-27"
              onChange={(e) => setYearDraft(e.target.value)}
            />
          </label>
          <label>
            Review band
            <select
              value={bandDraft}
              onChange={(e) => setBandDraft(e.target.value)}
            >
              <option value="">All bands</option>
              {BANDS.map((b) => (
                <option key={b} value={b}>
                  {b.charAt(0) + b.slice(1).toLowerCase()}
                </option>
              ))}
            </select>
          </label>
          <button className="button secondary" type="submit">
            Apply filters
          </button>
        </form>
        {yearError && (
          <p className="form-error" role="alert">
            {yearError}
          </p>
        )}
      </div>
      {overview.isPending ? (
        <Loading label="Loading review overview…" />
      ) : overview.isError ? (
        <ErrorPanel
          error={overview.error}
          retry={() => void overview.refetch()}
        />
      ) : overview.data.data.length === 0 ? (
        <div className="empty-state compact">
          <h3>No institutions to show</h3>
          <p>No institutions match these filters.</p>
        </div>
      ) : (
        <>
          <ScrollTable label="Institutions by review priority">
            <thead>
              <tr>
                <th scope="col">Institution</th>
                <th scope="col">Band</th>
                {FAMILIES.map((f) => (
                  <th scope="col" key={f.id}>
                    {f.label} points
                  </th>
                ))}
                <th scope="col">Total</th>
                <th scope="col">Signals (active / dismissed)</th>
              </tr>
            </thead>
            <tbody>
              {overview.data.data.map((item) => (
                <tr key={item.institution_id}>
                  <th scope="row">
                    {canOpenInstitution ? (
                      <Link
                        href={`/aicte/institutions/${encodeURIComponent(item.institution_id)}`}
                      >
                        {item.institution_name}
                      </Link>
                    ) : (
                      item.institution_name
                    )}
                  </th>
                  <td>
                    <span
                      className={`status-badge ${bandTone(item.score.band)}`}
                    >
                      {item.score.band.charAt(0) +
                        item.score.band.slice(1).toLowerCase()}
                    </span>
                  </td>
                  {FAMILIES.map((f) => (
                    <td key={f.id}>
                      {item.score.components.find((c) => c.family === f.id)
                        ?.weighted_points ?? 0}
                    </td>
                  ))}
                  <td>
                    <strong>{item.score.total_points}</strong>
                  </td>
                  <td>
                    {item.signal_count} total · {item.active_count} active ·{" "}
                    {item.dismissed_count} dismissed
                  </td>
                </tr>
              ))}
            </tbody>
          </ScrollTable>
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={overview.data.pagination.total}
            busy={overview.isFetching}
            change={setPage}
            label="Review overview pagination"
          />
          <p className="data-note">
            Points = {overview.data.data[0].score.formula}. Bands order review
            work; they do not indicate wrongdoing.
          </p>
        </>
      )}
    </section>
  );
}
