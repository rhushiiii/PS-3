"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { useSession } from "@/features/auth/session";
import {
  RecordVerification,
  SIM_LABEL,
} from "@/features/cases/record-verification";
import type { components } from "@/lib/api/generated";

type RecordPage = components["schemas"]["Page_RecordRow_"];
type InstitutionPage = components["schemas"]["Page_InstitutionResponse_"];

export function VerificationWorkspace() {
  const { session, request } = useSession();
  const scope = ["private", session?.generation, session?.user.id];
  const [q, setQ] = useState("");
  const [institution, setInstitution] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const term = q.trim();

  const institutions = useQuery({
    queryKey: [...scope, "institutions", "filter-options"],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<InstitutionPage>("/institutions?page=1&page_size=100", {
        signal,
      }),
  });
  const records = useQuery({
    queryKey: [...scope, "verification-search", term, institution],
    enabled: !!session && (!!term || !!institution),
    queryFn: ({ signal }) => {
      const params = new URLSearchParams({ page: "1", page_size: "10" });
      if (term) params.set("q", term);
      if (institution) params.set("institution_id", institution);
      return request<RecordPage>(`/records?${params}`, { signal });
    },
  });

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">APAAR VERIFICATION · SIMULATED / DEMO DATA</p>
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
          <label className="inline-filter">
            Institution
            <select
              value={institution}
              disabled={institutions.isPending}
              onChange={(e) => {
                setInstitution(e.target.value);
                setSelected(null);
              }}
            >
              <option value="">All institutions</option>
              {institutions.data?.data.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </select>
          </label>
        </form>
        {!term && !institution ? (
          <div className="empty-state">
            <h3>Search to begin</h3>
            <p>Enter a student ID or name, or choose an institution.</p>
          </div>
        ) : records.isPending ? (
          <Loading label="Searching records…" />
        ) : records.isError ? (
          <ErrorPanel
            error={records.error}
            retry={() => void records.refetch()}
          />
        ) : records.data.data.length === 0 ? (
          <div className="empty-state">
            <h3>No records match</h3>
          </div>
        ) : (
          <ul className="finding-list" aria-label="Search results">
            {records.data.data.map((r) => (
              <li key={r.record_version_id}>
                <button
                  type="button"
                  className="button secondary small"
                  aria-pressed={selected === r.record_version_id}
                  onClick={() => setSelected(r.record_version_id)}
                >
                  {selected === r.record_version_id ? "Selected" : "Select"}
                </button>{" "}
                <strong>{r.student_name}</strong>{" "}
                <span className="cell-note">
                  {r.college_student_id} · {r.institution_name} ·{" "}
                  {r.programme_name} · {r.academic_year} · {r.masked_apaar} ·{" "}
                  {r.snapshot_state}
                </span>
              </li>
            ))}
          </ul>
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
