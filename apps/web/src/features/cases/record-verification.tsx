"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { errorMessage } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";

type VerificationPage = components["schemas"]["Page_VerificationResponse_"];
type Verification = components["schemas"]["VerificationResponse"];

function statusTone(
  status: Verification["status"],
): "active" | "warning" | "neutral" {
  if (status === "SIMULATED_MATCH") return "active";
  if (status === "SIMULATED_MISMATCH") return "warning";
  return "neutral";
}

export function RecordVerification({
  recordVersionId,
  officer,
  index,
}: {
  recordVersionId: string;
  officer: boolean;
  index: number;
}) {
  const { session, request } = useSession();
  const queryClient = useQueryClient();
  const [purpose, setPurpose] = useState("AICTE_CASE_REVIEW");
  const [consentRef, setConsentRef] = useState("");
  const [error, setError] = useState("");
  const baseKey = [
    "private",
    session?.generation,
    session?.user.id,
    "apaar-verify",
    recordVersionId,
  ];
  const history = useQuery({
    queryKey: baseKey,
    enabled: !!session,
    queryFn: ({ signal }) =>
      request<VerificationPage>(
        `/records/${recordVersionId}/apaar-verify?page=1&page_size=5`,
        { signal },
      ),
  });
  const verify = useMutation({
    mutationFn: () =>
      request<Verification>(`/records/${recordVersionId}/apaar-verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          purpose,
          consent_ref: consentRef,
        }),
      }),
    retry: false,
    onSuccess: async () => {
      setError("");
      setConsentRef("");
      await queryClient.invalidateQueries({ queryKey: baseKey });
    },
    onError: (mutationError) => setError(errorMessage(mutationError)),
  });
  const latest = history.data?.data[0];
  return (
    <article className="record-verification">
      <h3 className="sr-only">Linked record {index + 1}</h3>
      <p className="cell-note">
        Record <code>{recordVersionId}</code>
      </p>
      {latest ? (
        <p>
          <span className={`status-badge ${statusTone(latest.status)}`}>
            {latest.status.replaceAll("_", " ")}
          </span>{" "}
          <span className="cell-note">
            {latest.provenance_label} ·{" "}
            <time dateTime={latest.requested_at}>
              {new Date(latest.requested_at).toLocaleString()}
            </time>
          </span>
        </p>
      ) : history.isError ? null : (
        <p className="cell-note">No APAAR verification requested yet.</p>
      )}
      {officer && (
        <form
          className="verification-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!consentRef.trim()) {
              setError(
                "Provide a consent reference before requesting a check.",
              );
              return;
            }
            verify.mutate();
          }}
        >
          <label>
            Purpose
            <input
              value={purpose}
              onChange={(event) => setPurpose(event.target.value)}
              maxLength={120}
              required
            />
          </label>
          <label>
            Consent reference
            <input
              value={consentRef}
              onChange={(event) => setConsentRef(event.target.value)}
              maxLength={64}
              placeholder="consent-demo-1"
              required
            />
          </label>
          <button
            className="button secondary small"
            type="submit"
            disabled={verify.isPending}
          >
            {verify.isPending
              ? "Requesting…"
              : "Request simulated APAAR verification"}
          </button>
        </form>
      )}
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
    </article>
  );
}
