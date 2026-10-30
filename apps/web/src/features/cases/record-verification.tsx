"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { useApiQuery, useScope } from "@/lib/api/hooks";
import { ApiError, errorMessage, wasReplayed } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";
import { DEMO_TAG, when } from "@/lib/format";

type VerificationPage = components["schemas"]["Page_VerificationResponse_"];
type Verification = components["schemas"]["VerificationResponse"];

export const SIM_LABEL = `${DEMO_TAG} — not an official government verification`;

const RETRYABLE: Verification["status"][] = [
  "PENDING",
  "SOURCE_UNAVAILABLE",
  "SOURCE_TIMEOUT",
];

const statusText: Record<Verification["status"], string> = {
  SIMULATED_MATCH: "Simulated match",
  SIMULATED_MISMATCH: "Simulated mismatch",
  PENDING: "Pending — no answer yet",
  SOURCE_UNAVAILABLE: "Source unavailable — no answer",
  SOURCE_TIMEOUT: "Source timed out — no answer",
};

function statusTone(
  status: Verification["status"],
): "active" | "warning" | "inconclusive" {
  if (status === "SIMULATED_MATCH") return "active";
  if (status === "SIMULATED_MISMATCH") return "warning";
  return "inconclusive";
}

function verificationError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 429)
      return "Retry limit reached for this verification. Wait before trying again.";
    if (error.code === "RETRY_NOT_ALLOWED")
      return "This result cannot be retried (only pending, unavailable or timed-out results can).";
    if (error.code === "IDEMPOTENCY_KEY_REUSED")
      return "This attempt key was already used for a different request. Submit again to start a new attempt.";
  }
  return errorMessage(error);
}

const newKey = () => crypto.randomUUID();

export function RecordVerification({
  recordVersionId,
  officer,
  index,
}: {
  recordVersionId: string;
  officer: boolean;
  index: number;
}) {
  const { request } = useSession();
  const queryClient = useQueryClient();
  const [purpose, setPurpose] = useState("AICTE_CASE_REVIEW");
  const [consentRef, setConsentRef] = useState("");
  const [error, setError] = useState("");
  const [replayed, setReplayed] = useState(false);
  // One Idempotency-Key per attempt: reused while the same request body is
  // re-sent (e.g. after a network error), replaced once it succeeds or changes.
  const attempt = useRef<{ key: string; body: string } | null>(null);
  const baseKey = useScope("apaar-verify", recordVersionId);
  const history = useApiQuery<VerificationPage>(
    baseKey,
    `/records/${recordVersionId}/apaar-verify?page=1&page_size=5`,
  );
  const verify = useMutation({
    mutationFn: (retryOf: string | null) => {
      const body = JSON.stringify({
        purpose: purpose.trim(),
        consent_ref: consentRef.trim(),
        ...(retryOf ? { retry_of: retryOf } : {}),
      });
      if (attempt.current?.body !== body)
        attempt.current = { key: newKey(), body };
      return request<Verification>(`/records/${recordVersionId}/apaar-verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": attempt.current.key,
        },
        body,
      });
    },
    retry: false,
    onSuccess: async (data) => {
      attempt.current = null;
      setReplayed(wasReplayed(data));
      setError("");
      setConsentRef("");
      await queryClient.invalidateQueries({ queryKey: baseKey });
    },
    onError: (mutationError) => {
      if (
        mutationError instanceof ApiError &&
        mutationError.code === "IDEMPOTENCY_KEY_REUSED"
      )
        attempt.current = null;
      setError(verificationError(mutationError));
    },
  });
  const latest = history.data?.data[0];
  const canRetry = !!latest && RETRYABLE.includes(latest.status);
  const ready = !!purpose.trim() && !!consentRef.trim();
  const submit = (retryOf: string | null) => {
    if (!ready) {
      setError(
        "Provide a purpose and consent reference before requesting a check.",
      );
      return;
    }
    setError("");
    verify.mutate(retryOf);
  };
  return (
    <article className="record-verification">
      <h3 className="sr-only">Linked record {index + 1}</h3>
      <p className="cell-note">
        Record <code>{recordVersionId}</code>
      </p>
      <p className="sim-label">{SIM_LABEL}</p>
      {latest ? (
        <div className={`verification-result ${statusTone(latest.status)}`}>
          <p>
            <span className={`status-badge ${statusTone(latest.status)}`}>
              {statusText[latest.status]}
            </span>{" "}
            <span className="cell-note">
              {latest.provenance_label} · {when(latest.requested_at)}
            </span>
          </p>
          <dl className="case-facts">
            <div>
              <dt>Format check (local)</dt>
              <dd>
                {latest.format_validation.valid
                  ? "Valid format"
                  : "Invalid format"}{" "}
                <span className="cell-note">
                  {latest.format_validation.note}
                </span>
              </dd>
            </div>
            <div>
              <dt>Identity check (simulated)</dt>
              <dd>{statusText[latest.identity_verification.status]}</dd>
            </div>
            <div>
              <dt>Provider request ID</dt>
              <dd>
                <code>
                  {latest.identity_verification.provider_request_id ??
                    "none issued"}
                </code>
              </dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>
                {new Date(
                  latest.identity_verification.completed_at,
                ).toLocaleString()}
              </dd>
            </div>
          </dl>
          {canRetry && (
            <p className="cell-note">
              This is not a match or a mismatch — the check did not finish. You
              can retry.
            </p>
          )}
        </div>
      ) : history.isError ? null : (
        <p className="cell-note">No APAAR verification requested yet.</p>
      )}
      {replayed && (
        <p className="data-note" role="status">
          The server returned the earlier result for this attempt (replay); no
          new check was run.
        </p>
      )}
      {officer && (
        <form
          className="verification-form"
          onSubmit={(event) => {
            event.preventDefault();
            submit(null);
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
            disabled={verify.isPending || !ready}
          >
            {verify.isPending
              ? "Requesting…"
              : "Request simulated APAAR verification"}
          </button>
          {canRetry && latest && (
            <button
              className="button secondary small"
              type="button"
              disabled={verify.isPending || !ready}
              onClick={() => submit(latest.id)}
            >
              Retry this check
            </button>
          )}
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
