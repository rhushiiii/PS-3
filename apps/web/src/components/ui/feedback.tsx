import { ApiError, errorMessage } from "@/lib/api/client";

export function Loading({
  label = "Loading information…",
}: {
  label?: string;
}) {
  return (
    <div className="feedback loading-state" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorPanel({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => void;
}) {
  return (
    <section className="feedback error-state" role="alert">
      <div>
        <h2>Unable to load this information</h2>
        <p>{errorMessage(error)}</p>
        {error instanceof ApiError && error.requestId && (
          <p className="request-id">Request reference: {error.requestId}</p>
        )}
      </div>
      {retry && (
        <button className="button secondary" onClick={retry}>
          Try again
        </button>
      )}
    </section>
  );
}

export function DemoBanner() {
  return (
    <aside className="demo-banner" aria-label="Demo data notice">
      <span className="demo-dot" aria-hidden="true" />
      DEMO — synthetic data only
      <span className="banner-detail">
        Local validation is not government identity verification.
      </span>
    </aside>
  );
}
