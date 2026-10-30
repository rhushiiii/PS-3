import type { UseQueryResult } from "@tanstack/react-query";

export function Pagination({
  page,
  total,
  pageSize,
  busy,
  change,
  label = "Pagination",
}: {
  page: number;
  total: number;
  pageSize: number;
  busy: boolean;
  change: (page: number) => void;
  label?: string;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <nav className="pagination" aria-label={label}>
      <span aria-live="polite">
        Page {page} of {pages}
      </span>
      <div>
        <button
          className="button secondary small"
          disabled={page <= 1 || busy}
          onClick={() => change(page - 1)}
        >
          Previous
        </button>
        <button
          className="button secondary small"
          disabled={page >= pages || busy}
          onClick={() => change(page + 1)}
        >
          Next
        </button>
      </div>
    </nav>
  );
}

/** Pagination bar for a paged query; renders nothing until data exists. */
export function QueryPagination<T extends { pagination: { total: number } }>({
  query,
  page,
  pageSize,
  change,
  label,
}: {
  query: UseQueryResult<T>;
  page: number;
  pageSize: number;
  change: (page: number) => void;
  label?: string;
}) {
  if (!query.data) return null;
  return (
    <Pagination
      page={page}
      pageSize={pageSize}
      total={query.data.pagination.total}
      busy={query.isFetching}
      change={change}
      label={label}
    />
  );
}
