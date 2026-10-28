"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { homeFor, useSession } from "@/features/auth/session";
import { ApiError, errorMessage } from "@/lib/api/client";
import { DemoBanner } from "@/components/ui/feedback";
import { Icon } from "@/components/ui/icon";

const accounts = [
  {
    alias: "cedar_admin",
    label: "Demo Cedar Institute",
    role: "Institution administrator",
    monogram: "CE",
  },
  {
    alias: "maple_admin",
    label: "Demo Maple Institute",
    role: "Institution administrator",
    monogram: "MA",
  },
  {
    alias: "willow_admin",
    label: "Demo Willow Institute",
    role: "Institution administrator",
    monogram: "WI",
  },
  {
    alias: "demo_officer",
    label: "Demo AICTE officer",
    role: "Institution review access",
    monogram: "OF",
  },
  {
    alias: "demo_manager",
    label: "Demo AICTE manager",
    role: "Institution metadata access",
    monogram: "MG",
  },
];

export function Login() {
  const { session, reason, signingIn, signIn } = useSession();
  const [alias, setAlias] = useState("cedar_admin");
  const [error, setError] = useState<unknown>(null);
  const router = useRouter();
  const enabled = process.env.NEXT_PUBLIC_DEMO_UI_ENABLED === "true";
  useEffect(() => {
    if (session) router.replace(homeFor(session.user.role));
  }, [session, router]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      const identity = await signIn(alias);
      router.replace(homeFor(identity.role));
    } catch (failure) {
      if (!(failure instanceof DOMException && failure.name === "AbortError"))
        setError(failure);
    }
  }

  return (
    <div className="login-page">
      <header className="login-header">
        <div className="brand">
          <span className="brand-mark">
            S<span>26</span>
          </span>
          <span>
            SIH26263<small>Admissions workspace</small>
          </span>
        </div>
        <span className="local-tag">Local prototype</span>
      </header>
      <main className="login-main">
        <section className="login-card" aria-labelledby="login-title">
          <p className="eyebrow">A CLEAR START</p>
          <h1 id="login-title">Sign in to the prototype</h1>
          <p className="intro">
            Choose a synthetic account to open its permitted workspace. Access
            is resolved by the backend.
          </p>
          <DemoBanner />
          {reason && (
            <p className="session-notice" role="alert">
              {reason === "expired"
                ? "Your demo session expired. Select a demo account to continue."
                : "Your session is no longer valid. Select a demo account to continue."}
            </p>
          )}
          {!enabled ? (
            <section className="disabled-notice" role="status">
              <h2>Demo sign-in is disabled</h2>
              <p>
                The local demo interface must be explicitly enabled by the
                operator. Backend demo authentication must also be configured
                for direct local access.
              </p>
            </section>
          ) : (
            <form onSubmit={submit} aria-busy={signingIn}>
              <fieldset className="account-options" disabled={signingIn}>
                <legend>Select a demo account</legend>
                {accounts.map((account) => (
                  <label
                    key={account.alias}
                    className={`account-option ${alias === account.alias ? "selected" : ""}`}
                  >
                    <input
                      type="radio"
                      name="demo-account"
                      value={account.alias}
                      checked={alias === account.alias}
                      onChange={() => setAlias(account.alias)}
                    />
                    <span className="account-monogram" aria-hidden="true">
                      {account.monogram}
                    </span>
                    <span className="account-copy">
                      <strong>{account.label}</strong>
                      <small>{account.role}</small>
                    </span>
                    <span className="radio-indicator" aria-hidden="true" />
                  </label>
                ))}
              </fieldset>
              {error !== null && (
                <div className="login-error" role="alert">
                  <p>
                    {error instanceof ApiError && error.status === 404
                      ? "Demo sign-in is unavailable. Check that the local API has demo authentication enabled."
                      : errorMessage(error)}
                  </p>
                  {error instanceof ApiError && error.requestId && (
                    <small>Request reference: {error.requestId}</small>
                  )}
                </div>
              )}
              <button
                className="button primary login-submit"
                disabled={signingIn}
                type="submit"
              >
                {signingIn
                  ? "Opening your workspace…"
                  : "Continue with demo account"}
                <Icon name="arrow" />
              </button>
            </form>
          )}
          <p className="session-hint">
            Your session stays in this tab’s memory. Refreshing the page
            requires signing in again. If a session ended during an upload,
            check your own submission history after signing in; the upload may
            still have completed.
          </p>
        </section>
        <p className="login-footnote">
          Synthetic data only. No APAAR identity or government verification is
          performed.
        </p>
      </main>
    </div>
  );
}
