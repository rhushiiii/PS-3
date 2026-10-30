"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { useSession } from "@/features/auth/session";
import { CaseBadges, statusLabel, statusTone } from "@/features/cases/shared";
import { RecordCredentialCard } from "@/features/credentials/manage";
import { isUUID } from "@/lib/api/client";
import { when } from "@/lib/format";
import { StatusBadges, snapshotLabel, type RecordDetail } from "./shared";

const verificationText: Record<string, string> = {
  SIMULATED_MATCH: "Simulated match",
  SIMULATED_MISMATCH: "Simulated mismatch",
  PENDING: "Pending",
  SOURCE_UNAVAILABLE: "Source unavailable",
  SOURCE_TIMEOUT: "Source timeout",
};

export function RecordDetailView({
  recordVersionId,
}: {
  recordVersionId: string;
}) {
  const { session, request } = useSession();
  const officer = session?.user.role === "AICTE_OFFICER";
  const valid = isUUID(recordVersionId);
  const query = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "record",
      recordVersionId,
    ],
    enabled: !!session && valid,
    queryFn: ({ signal }) =>
      request<RecordDetail>(`/records/${recordVersionId}`, { signal }),
  });

  if (!valid)
    return (
      <div className="empty-state">
        <h3>Record not found</h3>
        <p>
          <Link href="/records">Back to student registry</Link>
        </p>
      </div>
    );
  if (query.isPending) return <Loading label="Loading record…" />;
  if (query.isError)
    return (
      <ErrorPanel error={query.error} retry={() => void query.refetch()} />
    );
  const r = query.data;
  const p = r.provenance;

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">
          <Link href="/records">STUDENT REGISTRY</Link> · SIMULATED / DEMO DATA
        </p>
        <h1>{r.student_name}</h1>
        <p>
          {r.college_student_id} · {r.institution_name} · {r.programme_name} (
          {r.programme_code}) · {r.academic_year}
        </p>
        <StatusBadges
          snapshot={r.snapshot_state}
          validation={r.validation_status}
        />
      </div>

      <section className="panel" aria-labelledby="summary-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">SUMMARY</p>
            <h2 id="summary-title">Record summary</h2>
          </div>
        </header>
        <dl className="case-facts">
          <div>
            <dt>Masked APAAR</dt>
            <dd>{r.masked_apaar}</dd>
          </div>
          <div>
            <dt>Category</dt>
            <dd>{r.category}</dd>
          </div>
          <div>
            <dt>Enrollment status</dt>
            <dd>{r.enrollment_status}</dd>
          </div>
          <div>
            <dt>Enrollment date</dt>
            <dd>{r.enrollment_date ?? "Not provided"}</dd>
          </div>
          {officer && (
            <div>
              <dt>Validation workspace</dt>
              <dd>
                <Link href={`/submissions/${r.batch_id}`}>
                  Open from validation workspace
                </Link>
              </dd>
            </div>
          )}
        </dl>
      </section>

      <section className="panel" aria-labelledby="prov-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">PROVENANCE</p>
            <h2 id="prov-title">Provenance</h2>
          </div>
        </header>
        <dl className="case-facts">
          <div>
            <dt>Submission batch</dt>
            <dd>
              <Link href={`/submissions/${p.batch_id}`}>View batch</Link>
            </dd>
          </div>
          <div>
            <dt>Received</dt>
            <dd>{when(p.received_at)}</dd>
          </div>
          <div>
            <dt>Source</dt>
            <dd>{p.source}</dd>
          </div>
          <div>
            <dt>Snapshot state</dt>
            <dd>{p.snapshot_state}</dd>
          </div>
          <div>
            <dt>Activated</dt>
            <dd>{p.activated_at ? when(p.activated_at) : "Not activated"}</dd>
          </div>
          <div>
            <dt>Superseded by</dt>
            <dd>
              {p.superseded_by_batch_id ? (
                <Link href={`/submissions/${p.superseded_by_batch_id}`}>
                  View batch
                </Link>
              ) : (
                "Not superseded"
              )}
            </dd>
          </div>
        </dl>
        <p className="data-note" role="note">
          {r.presence_note ??
            (r.snapshot_presence === "NOT_IN_LATEST_SNAPSHOT"
              ? "Not present in the latest snapshot. Omission is not proof of withdrawal."
              : "")}
        </p>
      </section>

      <section className="panel" aria-labelledby="find-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">LOCAL VALIDATION</p>
            <h2 id="find-title">Validation findings</h2>
          </div>
          <span className="quiet-label">{r.findings.length}</span>
        </header>
        {r.findings.length === 0 ? (
          <div className="empty-state">
            <h3>No findings</h3>
            <p>No validation findings are recorded for this record version.</p>
          </div>
        ) : (
          <ul className="finding-list">
            {r.findings.map((f) => (
              <li key={f.id}>
                <strong>{f.rule_code}</strong>{" "}
                <span className="badge-row">
                  <span
                    className={`status-badge ${f.severity === "ERROR" ? "danger" : f.severity === "WARNING" ? "warning" : "neutral"}`}
                  >
                    {f.severity}
                  </span>
                  <span className="status-badge neutral">
                    {f.classification.replaceAll("_", " ")}
                  </span>
                </span>
                <p>{f.explanation}</p>
              </li>
            ))}
          </ul>
        )}
        <p className="data-note">
          Findings are review leads from configured rules, not fraud
          determinations.
        </p>
      </section>

      <section className="panel" aria-labelledby="ver-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">SIMULATED / DEMO DATA</p>
            <h2 id="ver-title">APAAR verification</h2>
          </div>
        </header>
        {r.verification ? (
          <dl className="case-facts">
            <div>
              <dt>Latest result</dt>
              <dd>
                <span className="status-badge neutral">
                  {verificationText[r.verification.status] ??
                    r.verification.status}
                </span>
              </dd>
            </div>
            <div>
              <dt>Source</dt>
              <dd>
                {r.verification.source_type} · {r.verification.adapter_type}
              </dd>
            </div>
            <div>
              <dt>Provenance</dt>
              <dd>{r.verification.provenance_label}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>{when(r.verification.completed_at)}</dd>
            </div>
          </dl>
        ) : (
          <div className="empty-state">
            <h3>None requested</h3>
            <p>No simulated verification has been requested for this record.</p>
          </div>
        )}
        <p className="data-note">
          This is a simulated result, not official APAAR verification.
        </p>
      </section>

      {r.snapshot_state === "CURRENT" &&
        r.enrollment_status.trim().toUpperCase() === "ACTIVE" && (
          <RecordCredentialCard recordVersionId={r.record_version_id} />
        )}

      <section className="panel" aria-labelledby="cases-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">REVIEW</p>
            <h2 id="cases-title">Related cases</h2>
          </div>
          <span className="quiet-label">{r.cases.length}</span>
        </header>
        {r.cases.length === 0 ? (
          <div className="empty-state">
            <h3>No related cases</h3>
          </div>
        ) : (
          <ul className="finding-list">
            {r.cases.map((c) => (
              <li key={c.id}>
                <Link href={`/cases/${c.id}`}>
                  Case opened {new Date(c.opened_at).toLocaleDateString()}
                </Link>{" "}
                <span className={`status-badge ${statusTone(c.status)}`}>
                  {statusLabel(c.status)}
                </span>
                <CaseBadges
                  item={
                    { ...c, is_escalated: false } as Parameters<
                      typeof CaseBadges
                    >[0]["item"]
                  }
                />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="panel" aria-labelledby="hist-title">
        <header className="panel-heading">
          <div>
            <p className="eyebrow">IMMUTABLE VERSIONS</p>
            <h2 id="hist-title">Version history</h2>
          </div>
        </header>
        <ol className="case-timeline">
          {r.history.map((h) => (
            <li key={h.record_version_id}>
              <header>
                <span className="status-badge neutral">
                  {snapshotLabel(h.snapshot_state)}
                </span>
                {when(h.received_at)}
                {h.record_version_id === r.record_version_id && (
                  <span className="quiet-label"> · This version</span>
                )}
              </header>
              {h.apaar_changed && (
                <p>
                  <span className="status-badge warning">APAAR changed</span>
                </p>
              )}
              {h.changes.length === 0 ? (
                <p className="cell-note">
                  No field changes from previous version.
                </p>
              ) : (
                <ul>
                  {h.changes.map((c) => (
                    <li key={c.field}>
                      <strong>{c.field.replaceAll("_", " ")}</strong>:{" "}
                      {c.previous ?? "empty"} → {c.current ?? "empty"}
                    </li>
                  ))}
                </ul>
              )}
              {h.record_version_id !== r.record_version_id && (
                <Link href={`/records/${h.record_version_id}`}>
                  Open this version
                </Link>
              )}
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}
