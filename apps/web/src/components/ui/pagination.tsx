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
