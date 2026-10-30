"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { errorMessage } from "@/lib/api/client";
import { DEMO_TAG } from "@/lib/format";
import type { components } from "@/lib/api/generated";
import { DEMO_LABEL, outcomeLabel, when } from "./shared";

type VerifyResponse = components["schemas"]["VerifyResponse"];

const outcomeMessage: Record<VerifyResponse["outcome"], string> = {
  VALID:
    "The signature and issuer checks passed and the credential is current. Only the permitted claims below are shown.",
  EXPIRED:
    "The signature is genuine but this credential has expired. It is NOT currently valid.",
  REVOKED:
    "The signature is genuine but the issuer has revoked this credential. It is NOT currently valid.",
  INVALID:
    "Signature or issuer check failed — do not rely on this credential. No claims are shown.",
  UNAVAILABLE:
    "Verification service unavailable — this is NOT a finding that the credential is invalid. Try again later.",
};

function Claims({ result }: { result: VerifyResponse }) {
  const c = result.claims;
  if (!c) return null;
  const notCurrent = result.outcome !== "VALID";
  return (
    <>
      {notCurrent && (
        <p className="data-note" role="note">
          Claims below are limited to what the server returned and describe a
          credential that is not currently valid.
        </p>
      )}
      <dl className="case-facts">
        <div>
          <dt>Institution</dt>
          <dd>{c.institution_name}</dd>
        </div>
        <div>
          <dt>Programme code</dt>
          <dd>{c.programme_code}</dd>
        </div>
        <div>
          <dt>Academic year</dt>
          <dd>{c.academic_year}</dd>
        </div>
        <div>
          <dt>Admission category</dt>
          <dd>{c.admission_category}</dd>
        </div>
        <div>
          <dt>Enrollment status</dt>
          <dd>{c.enrollment_status}</dd>
        </div>
        <div>
          <dt>Issued</dt>
          <dd>{when(c.issued_at)}</dd>
        </div>
        <div>
          <dt>Expires</dt>
          <dd>{when(c.expires_at)}</dd>
        </div>
      </dl>
    </>
  );
}

export function VerifyCredential() {
  const { request } = useSession();
  const [token, setToken] = useState("");
  const [purpose, setPurpose] = useState("");
  const [consentRef, setConsentRef] = useState("");
  const verify = useMutation({
    mutationFn: (body: {
      token: string;
      purpose: string;
      consent_ref: string;
    }) =>
      request<VerifyResponse>("/credentials/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    // The pasted token is cleared as soon as the server has answered.
    onSettled: () => setToken(""),
  });
  const ready = !!token.trim() && !!purpose.trim() && !!consentRef.trim();
  const result = verify.data;

  return (
    <>
      <div className="page-heading">
        <p className="eyebrow">{`CREDENTIAL VERIFICATION · ${DEMO_TAG}`}</p>
        <h1>Verify credential</h1>
        <p>
          Paste the credential token. A QR scanner usually outputs this text; a
          QR code is only a carrier. A scan, a QR image or a database value is
          never proof by itself. Only the server-side signature check is.
        </p>
      </div>
      <section className="panel panel-padding" aria-labelledby="vf-title">
        <h2 id="vf-title" className="sr-only">
          Verification request
        </h2>
        <form
          className="verify-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!ready || verify.isPending) return;
            verify.mutate({
              token: token.trim(),
              purpose: purpose.trim(),
              consent_ref: consentRef.trim(),
            });
          }}
        >
          <label>
            Credential token
            <textarea
              value={token}
              rows={5}
              spellCheck={false}
              autoComplete="off"
              maxLength={8000}
              onChange={(e) => setToken(e.target.value)}
              required
            />
          </label>
          <label>
            Purpose
            <input
              value={purpose}
              maxLength={120}
              onChange={(e) => setPurpose(e.target.value)}
              required
            />
          </label>
          <label>
            Consent reference
            <input
              value={consentRef}
              maxLength={64}
              onChange={(e) => setConsentRef(e.target.value)}
              required
            />
          </label>
          <p className="form-help">
            Verification is denied unless a purpose and consent reference are
            both provided. Every check is logged with your account, purpose and
            consent reference (never the token).
          </p>
          <button
            className="button primary"
            type="submit"
            disabled={!ready || verify.isPending}
          >
            {verify.isPending ? "Verifying…" : "Verify credential"}
          </button>
        </form>
        {verify.isError && (
          <p className="form-error" role="alert">
            {errorMessage(verify.error)} No result was produced; this is not a
            finding about the credential.
          </p>
        )}
      </section>
      {result && (
        <section
          className={`outcome-panel outcome-${result.outcome.toLowerCase()}`}
          aria-labelledby="outcome-title"
          role="status"
        >
          <p className="eyebrow">{DEMO_LABEL}</p>
          <h2 id="outcome-title">{outcomeLabel[result.outcome]}</h2>
          <p className="outcome-message">{outcomeMessage[result.outcome]}</p>
          <Claims result={result} />
          <p className="data-note">
            Logged as verification <code>{result.verification_id}</code>. The
            token has been cleared from this page.
          </p>
        </section>
      )}
    </>
  );
}
