"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { demoAccounts as accounts } from "@/features/auth/accounts";
import { homeFor, useSession } from "@/features/auth/session";
import { ApiError, errorMessage } from "@/lib/api/client";
import { DataNotice } from "@/components/ui/feedback";
import { Icon } from "@/components/ui/icon";

export function Login() {
  const { session, reason, signingIn, signIn } = useSession();
  const searchParams = useSearchParams();
  const requested = searchParams.get("alias");
  const [alias, setAlias] = useState(
    accounts.some((account) => account.alias === requested)
      ? (requested as string)
      : "cedar_admin",
  );
  // Track the last-seen ?alias= and adjust selection during render (not in
  // an effect) when it changes — e.g. clicking a different account in the
  // nav dropdown while already on this page. See "Adjusting state when a
  // prop changes" in the React docs. The useState above already seeds the
  // correct value on first render, so this only reacts to later changes.
  const [seenRequested, setSeenRequested] = useState(requested);
  if (requested !== seenRequested) {
    setSeenRequested(requested);
    if (requested && accounts.some((account) => account.alias === requested))
      setAlias(requested);
  }
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
      <main className="login-main">
        <section className="login-card" aria-labelledby="login-title">
          <p className="eyebrow">A CLEAR START</p>
          <h1 id="login-title">Sign in to PRAVYA</h1>
          <p className="intro">
            Choose an account to open its permitted workspace. Access is
            resolved by the backend.
          </p>
          <DataNotice />
          {reason && (
            <p className="session-notice" role="alert">
              {reason === "expired"
                ? "Your session expired. Select an account to continue."
                : "Your session is no longer valid. Select an account to continue."}
            </p>
          )}
          {!enabled ? (
            <section className="disabled-notice" role="status">
              <h2>Sign-in is disabled</h2>
              <p>
                Demo sign-in must be explicitly enabled by the operator. Backend
                demo authentication must also be configured.
              </p>
            </section>
          ) : (
            <form onSubmit={submit} aria-busy={signingIn}>
              <fieldset className="account-options" disabled={signingIn}>
                <legend>Select an account</legend>
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
                      ? "Sign-in is unavailable. Check that the API has demo authentication enabled."
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
                {signingIn ? "Opening your workspace…" : "Continue"}
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
