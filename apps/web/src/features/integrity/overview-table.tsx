"use client";

import Link from "next/link";
import { useState } from "react";
import { DemoBanner, QueryBoundary } from "@/components/ui/feedback";
import { Pagination } from "@/components/ui/pagination";
import { useApiQuery, useScope } from "@/lib/api/hooks";
import { validAcademicYear } from "@/lib/academic-year";
import { ScrollTable } from "@/features/intake/shared";
import type { components } from "@/lib/api/generated";
import { humanize } from "@/lib/format";
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
  const overview = useApiQuery<Overview>(
    useScope("integrity-overview", year, band, page),
    `/integrity/overview?${params}`,
  );
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
        <DemoBanner
          label="Prioritisation notice"
          title="Prioritisation, not a finding"
        >
          {overview.data?.disclaimer ??
            "Rule-based review prompts from DEMO data. They are not fraud findings or compliance determinations; officers decide."}
        </DemoBanner>
        <form
          className="dashboard-filters"
          onSubmit={(e) => {
            e.preventDefault();
            if (yearDraft && !validAcademicYear(yearDraft))
              return setYearError(
                "Use a consecutive academic year such as 2026-27.",
              );
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
                  {humanize(b)}
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
      <QueryBoundary query={overview} loading="Loading review overview…">
        {(data) =>
          data.data.length === 0 ? (
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
                  {data.data.map((item) => (
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
                          {humanize(item.score.band)}
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
                total={data.pagination.total}
                busy={overview.isFetching}
                change={setPage}
                label="Review overview pagination"
              />
              <p className="data-note">
                Points = {data.data[0].score.formula}. Bands order review work;
                they do not indicate wrongdoing.
              </p>
            </>
          )
        }
      </QueryBoundary>
    </section>
  );
}
