"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  useIsMutating,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { ErrorPanel, Loading } from "@/components/ui/feedback";
import { Icon } from "@/components/ui/icon";
import { ApiError, isUUID } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";
import { useSubmissionContext, validAcademicYear } from "./data";
import { templateCSV, uploadError } from "./upload-state";

type Policy = components["schemas"]["UploadPolicyResponse"];
type UploadResult = components["schemas"]["UploadResponse"];

export function CandidateUpload() {
  const { session, request } = useSession();
  const institutionId = session?.user.institution_id ?? "";
  const { institution, programmes, options } =
    useSubmissionContext(institutionId);
  const queryClient = useQueryClient();
  const [programme, setProgramme] = useState("");
  const [year, setYear] = useState("");
  const [formError, setFormError] = useState("");
  const [synthetic, setSynthetic] = useState(false);
  const file = useRef<HTMLInputElement>(null);
  const attempting = useRef(false);
  const policy = useQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "upload-policy",
    ],
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<Policy>("/submissions/upload-policy", { signal }),
  });
  const mutation = useMutation({
    mutationKey: [
      "private",
      session?.generation,
      session?.user.id,
      "candidate-upload",
    ],
    retry: false,
    networkMode: "always", // Never queue an offline upload for automatic later execution.
    gcTime: 0,
    mutationFn: async (): Promise<UploadResult> => {
      const selectedFile = file.current?.files?.[0];
      if (!selectedFile) throw new ApiError(422, "INVALID_REQUEST");
      const body = new FormData();
      body.append("file", selectedFile);
      body.append("institution_id", institutionId);
      body.append("programme_id", programme);
      body.append("academic_year", year);
      body.append("schema_version", "v1");
      const result = await request<UploadResult>("/submissions", {
        method: "POST",
        body,
      });
      if (
        !result ||
        !isUUID(result.id) ||
        result.status !== "COMPLETED" ||
        result.validation_performed !== false ||
        !Array.isArray(result.warnings) ||
        !result.warnings.every((warning) => typeof warning === "string")
      )
        throw new ApiError(201, "INVALID_RESPONSE");
      return result;
    },
  });
  const pendingUploads = useIsMutating({
    mutationKey: [
      "private",
      session?.generation,
      session?.user.id,
      "candidate-upload",
    ],
  });
  const otherPending = pendingUploads > 0 && !mutation.isPending;
  useEffect(() => {
    if (!mutation.isPending && !otherPending) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [mutation.isPending, otherPending]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      attempting.current ||
      otherPending ||
      mutation.isSuccess ||
      (mutation.isError && uploadError(mutation.error).uncertain)
    )
      return;
    const selectedFile = file.current?.files?.[0];
    let issue = "";
    if (!policy.data || policy.isError)
      issue =
        "Upload policy is unavailable. Retry loading it before uploading.";
    else if (
      !institution.data?.active ||
      !options.some((item) => item.id === programme && item.active)
    )
      issue =
        "Choose an active programme belonging to your active institution.";
    else if (!validAcademicYear(year))
      issue = "Use consecutive academic years, for example 2026-27.";
    else if (!selectedFile || selectedFile.size === 0)
      issue = "Choose a non-empty synthetic student CSV.";
    else if (selectedFile.size > policy.data.max_file_bytes)
      issue =
        "The selected file exceeds the configured file-size limit. It has not been sent.";
    else if (!synthetic)
      issue = "Confirm that the file contains synthetic student records only.";
    setFormError(issue);
    if (issue) return;
    attempting.current = true;
    mutation.mutate(undefined, {
      onSuccess: () => {
        if (file.current) file.current.value = "";
        void queryClient.invalidateQueries({
          queryKey: [
            "private",
            session?.generation,
            session?.user.id,
            "submissions",
            institutionId,
          ],
        });
      },
      onSettled: () => {
        attempting.current = false;
      },
    });
  }

  function prepareAnother() {
    mutation.reset();
    setFormError("");
    setSynthetic(false);
    if (file.current) file.current.value = "";
  }

  function downloadTemplate() {
    if (!policy.data) return;
    const url = URL.createObjectURL(
      new Blob([templateCSV(policy.data.required_headers)], {
        type: "text/csv;charset=utf-8",
      }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "pravya-students-v1.csv";
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  const outcome = mutation.isError ? uploadError(mutation.error) : null;
  const locked =
    otherPending ||
    mutation.isPending ||
    mutation.isSuccess ||
    !!outcome?.uncertain;
  return (
    <>
      <div className="page-heading heading-actions">
        <div>
          <p className="eyebrow">INSTITUTION DECLARATIONS</p>
          <h1>Upload candidate CSV</h1>
          <p>Store a complete synthetic snapshot, with history preserved.</p>
        </div>
        <Link className="button secondary" href="/submissions">
          Submission history
        </Link>
      </div>
      <section className="snapshot-explainer" aria-labelledby="snapshot-intent">
        <Icon name="upload" />
        <div>
          <h2 id="snapshot-intent">
            One CSV. One complete candidate snapshot.
          </h2>
          <p>
            Include every declared record across all admission categories for
            exactly one institution, programme and academic year. A future
            activation would replace that scope’s current snapshot. Uploading
            here never activates it or changes current enrolment totals.
          </p>
        </div>
      </section>
      {institution.isPending ? (
        <Loading label="Loading institution…" />
      ) : institution.isError ? (
        <ErrorPanel
          error={institution.error}
          retry={() => void institution.refetch()}
        />
      ) : (
        <div className="scope-notice">
          <strong>{institution.data.name}</strong>
          <span>
            Synthetic records only · institution is set by your authenticated
            account
          </span>
        </div>
      )}
      <div className="upload-layout">
        <section className="panel" aria-labelledby="upload-title">
          <header className="panel-heading">
            <div>
              <p className="eyebrow">CANDIDATE INGESTION</p>
              <h2 id="upload-title">Upload details</h2>
            </div>
            <span className="quiet-label">Not an activation</span>
          </header>
          {programmes.isError && (
            <ErrorPanel
              error={programmes.error}
              retry={() => void programmes.refetch()}
            />
          )}
          {institution.isSuccess && programmes.isPending && (
            <Loading label="Loading permitted programmes…" />
          )}
          {programmes.isSuccess &&
            !options.some((item) => item.active) &&
            !programmes.hasNextPage && (
              <div className="empty-state">
                <h3>No active programmes</h3>
                <p>
                  An active programme is required before uploading. No upload is
                  available for this institution.
                </p>
              </div>
            )}
          <form
            className="upload-form"
            onSubmit={submit}
            noValidate
            aria-busy={mutation.isPending}
          >
            <fieldset disabled={locked}>
              <legend className="sr-only">
                Candidate upload context and synthetic CSV
              </legend>
              <div className="upload-fields">
                <label>
                  Programme
                  <select
                    value={programme}
                    onChange={(event) => setProgramme(event.target.value)}
                    disabled={programmes.isPending || programmes.isError}
                  >
                    <option value="">Select a permitted programme</option>
                    {options
                      .filter((item) => item.active)
                      .map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.code} — {item.name}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Academic year
                  <input
                    value={year}
                    onChange={(event) => setYear(event.target.value)}
                    placeholder="2026-27"
                    maxLength={7}
                    aria-describedby="upload-year-help"
                  />
                  <span id="upload-year-help" className="form-help">
                    Consecutive years, YYYY-YY. This must match the CSV records.
                  </span>
                </label>
                <label className="file-field">
                  Synthetic student CSV
                  <input
                    ref={file}
                    type="file"
                    accept=".csv,text/csv"
                    aria-describedby="file-help"
                    onChange={() => {
                      setFormError("");
                      if (mutation.isError && !outcome?.uncertain)
                        mutation.reset();
                    }}
                  />
                  <span id="file-help" className="form-help">
                    CSV only. Contents are checked by the server; no student
                    preview is displayed here.
                  </span>
                </label>
                <label className="confirmation">
                  <input
                    type="checkbox"
                    checked={synthetic}
                    onChange={(event) => setSynthetic(event.target.checked)}
                  />
                  <span>
                    I confirm that this file contains synthetic student records
                    only.
                  </span>
                </label>
              </div>
            </fieldset>
            {programmes.hasNextPage && (
              <button
                type="button"
                className="button secondary small"
                disabled={programmes.isFetchingNextPage || locked}
                onClick={() => void programmes.fetchNextPage()}
              >
                Load more programme options
              </button>
            )}
            {formError && (
              <p className="form-error" role="alert">
                {formError}
              </p>
            )}
            {!mutation.isSuccess && !outcome?.uncertain && (
              <button
                className="button primary"
                type="submit"
                disabled={
                  mutation.isPending ||
                  otherPending ||
                  !policy.data ||
                  policy.isError ||
                  !institution.data?.active ||
                  programmes.isPending ||
                  programmes.isError ||
                  !options.some((item) => item.active)
                }
              >
                <Icon name="upload" />
                {mutation.isPending
                  ? "Uploading and processing…"
                  : "Upload candidate"}
              </button>
            )}
            <p className="form-help">
              No automatic retries. Each accepted upload creates a separate
              version, including repeated files.
            </p>
          </form>
          {mutation.isPending && (
            <Loading label="Uploading and processing. Keep this page open; the result is not yet confirmed." />
          )}
          {otherPending && (
            <Loading label="Another upload is still awaiting a response in this session. Check submission history; do not submit it again while it is pending." />
          )}
          {mutation.isSuccess && (
            <section className="upload-outcome success-state" role="status">
              <h3>Candidate stored</h3>
              <p>
                Submission{" "}
                <span className="code-label">{mutation.data.id}</span> was
                parsed and stored. It is unvalidated and has not been activated.
                Current enrolment totals are unchanged.
              </p>
              {mutation.data.warnings?.includes("DUPLICATE_UPLOAD") && (
                <p className="warning-text">
                  Repeated file detected. This is a separate candidate; earlier
                  uploads remain unchanged.
                </p>
              )}
              <div className="outcome-actions">
                <Link className="button secondary" href="/submissions">
                  View submission history
                </Link>
                <button className="button secondary" onClick={prepareAnother}>
                  Prepare another upload
                </button>
              </div>
            </section>
          )}
          {outcome && (
            <section className="upload-outcome error-state" role="alert">
              <h3>
                {outcome.uncertain
                  ? "Upload outcome unknown"
                  : "Upload not accepted"}
              </h3>
              <p>{outcome.message}</p>
              {mutation.error instanceof ApiError &&
                mutation.error.requestId && (
                  <p className="request-id">
                    Request reference: {mutation.error.requestId}
                  </p>
                )}
              {outcome.uncertain && (
                <>
                  <p>
                    No retry was sent. Re-uploading may create another
                    candidate. Check your own history after any interrupted
                    upload or session expiry.
                  </p>
                  <div className="outcome-actions">
                    <Link className="button secondary" href="/submissions">
                      Check submission history
                    </Link>
                    <button
                      className="button secondary"
                      onClick={prepareAnother}
                    >
                      I checked history; prepare another upload
                    </button>
                  </div>
                </>
              )}
            </section>
          )}
        </section>
        <aside className="panel upload-policy" aria-labelledby="policy-title">
          <header className="panel-heading">
            <div>
              <p className="eyebrow">STRICT V1</p>
              <h2 id="policy-title">CSV requirements</h2>
            </div>
          </header>
          {policy.isPending ? (
            <Loading label="Loading configured upload policy…" />
          ) : policy.isError ? (
            <ErrorPanel
              error={policy.error}
              retry={() => void policy.refetch()}
            />
          ) : (
            <div className="panel-padding">
              <dl className="policy-values">
                <dt>File-size limit</dt>
                <dd>{policy.data.max_file_bytes.toLocaleString()} bytes</dd>
                <dt>Data-record limit</dt>
                <dd>
                  {policy.data.max_rows.toLocaleString()} records, excluding the
                  header
                </dd>
                <dt>Encoding</dt>
                <dd>
                  {policy.data.encoding}
                  {policy.data.accepts_utf8_bom ? ", optional BOM" : ""}
                </dd>
                <dt>Schema</dt>
                <dd>
                  {policy.data.schema_version} · comma-delimited, exact header
                  order
                </dd>
              </dl>
              <button className="button secondary" onClick={downloadTemplate}>
                Download strict-v1 template
              </button>
              <h3>Required headers, in order</h3>
              <ol className="csv-headers">
                {policy.data.required_headers.map((header) => (
                  <li key={header}>
                    <code>{header}</code>
                  </li>
                ))}
              </ol>
              <p className="form-help">
                The template contains headers only. Add synthetic student
                records; an empty template cannot be uploaded. Do not rename or
                reorder columns.
              </p>
              <p className="form-help">
                Logical CSV records are counted, not physical lines. A quoted
                multiline field remains part of one record.
              </p>
              <p className="form-help">
                Server receive/processing budgets:{" "}
                {policy.data.receive_timeout_seconds}s /{" "}
                {policy.data.processing_timeout_seconds}s. These are not
                guaranteed HTTP completion deadlines.
              </p>
            </div>
          )}
        </aside>
      </div>
      <p className="data-note">
        Processing is separate from student validation, snapshot activation and
        government verification. Only synthetic data is permitted on this
        platform.
      </p>
    </>
  );
}
