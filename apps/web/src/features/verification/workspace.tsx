"use client";

import { useState } from "react";
import { EmptyState, QueryBoundary } from "@/components/ui/feedback";
import { InstitutionSelect } from "@/components/ui/filters";
import { useSession } from "@/features/auth/session";
import { useApiQuery, useScope } from "@/lib/api/hooks";
import {
  RecordVerification,
  SIM_LABEL,
} from "@/features/cases/record-verification";
import type { components } from "@/lib/api/generated";
import { DEMO_TAG } from "@/lib/format";
import { useInstitutionOptions } from "@/features/institutions/options";

type RecordPage = components["schemas"]["Page_RecordRow_"];

export function VerificationWorkspace() {
  const { session } = useSession();
  const [q, setQ] = useState("");
  const [institution, setInstitution] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const term = q.trim();

  const institutions = useInstitutionOptions(!!session);
  const recordsPath = (() => {
    const params = new URLSearchParams({ page: "1", page_size: "10" });
    if (term) params.set("q", term);
    if (institution) params.set("institution_id", institution);
    return `/records?${params}`;
  })();
  const records = useApiQuery<RecordPage>(
    useScope("verification-search", term, institution),
    recordsPath,
    { enabled: !!term || !!institution },
  );

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">{`APAAR VERIFICATION · ${DEMO_TAG}`}</p>
        <h1>APAAR verification</h1>
        <p className="sim-label">{SIM_LABEL}</p>
        <p>
          Find a record by college student ID or name (APAAR values are never
          searchable), then request a simulated check. A valid format is not
          identity verification.
        </p>
      </div>
      <section className="panel" aria-labelledby="find-rec-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">FIND RECORD</p>
            <h2 id="find-rec-title">Search records</h2>
          </div>
        </header>
        <form
          className="case-filters"
          aria-label="Find a record"
          onSubmit={(e) => e.preventDefault()}
        >
          <label className="inline-filter">
            Student ID or name
            <input
              type="search"
              value={q}
              maxLength={100}
              onChange={(e) => {
                setQ(e.target.value);
                setSelected(null);
              }}
            />
          </label>
          <InstitutionSelect
            className="inline-filter"
            institutions={institutions.data?.data ?? []}
            value={institution}
            disabled={institutions.isPending}
            onChange={(value) => {
              setInstitution(value);
              setSelected(null);
            }}
          />
        </form>
        {!term && !institution ? (
          <EmptyState title="Search to begin">
            Enter a student ID or name, or choose an institution.
          </EmptyState>
        ) : (
          <QueryBoundary query={records} loading="Searching records…">
            {(data) =>
              data.data.length === 0 ? (
                <EmptyState title="No records match" />
              ) : (
                <ul className="finding-list" aria-label="Search results">
                  {data.data.map((r) => (
                    <li key={r.record_version_id}>
                      <button
                        type="button"
                        className="button secondary small"
                        aria-pressed={selected === r.record_version_id}
                        onClick={() => setSelected(r.record_version_id)}
                      >
                        {selected === r.record_version_id
                          ? "Selected"
                          : "Select"}
                      </button>{" "}
                      <strong>{r.student_name}</strong>{" "}
                      <span className="cell-note">
                        {r.college_student_id} · {r.institution_name} ·{" "}
                        {r.programme_name} · {r.academic_year} ·{" "}
                        {r.masked_apaar} · {r.snapshot_state}
                      </span>
                    </li>
                  ))}
                </ul>
              )
            }
          </QueryBoundary>
        )}
      </section>
      {selected && (
        <section className="panel panel-padding" aria-labelledby="ver-ws-title">
          <h2 id="ver-ws-title">Verification</h2>
          <RecordVerification
            key={selected}
            recordVersionId={selected}
            officer
            index={0}
          />
        </section>
      )}
    </>
  );
}
