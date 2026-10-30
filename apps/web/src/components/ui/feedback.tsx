import type { ReactNode } from "react";
import type { UseQueryResult } from "@tanstack/react-query";
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

/** Demo/synthetic-data banner: dot, headline and a detail line. */
export function DemoBanner({
  label,
  title,
  children,
}: {
  label: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <aside className="demo-banner" aria-label={label}>
      <span className="demo-dot" aria-hidden="true" />
      {title}
      <span className="banner-detail">{children}</span>
    </aside>
  );
}

export function DataNotice() {
  return (
    <DemoBanner label="Synthetic data notice" title="Synthetic data only">
      Local validation is not government identity verification.
    </DemoBanner>
  );
}

/** Loading, then error-with-retry, then children once the query has data. */
export function QueryBoundary<T>({
  query,
  loading,
  children,
}: {
  query: UseQueryResult<T>;
  loading?: string;
  children: (data: T) => ReactNode;
}) {
  if (query.isPending) return <Loading label={loading} />;
  if (query.isError)
    return (
      <ErrorPanel error={query.error} retry={() => void query.refetch()} />
    );
  return <>{children(query.data)}</>;
}

/** Alert shown when optional filter dropdown data failed to load. */
export function FilterOptionsError() {
  return (
    <p className="form-error" role="alert">
      Some filter options could not be loaded. Other filters still work.
    </p>
  );
}
