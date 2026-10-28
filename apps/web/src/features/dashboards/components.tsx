import type { CSSProperties } from "react";

export type CountMap = Record<string, unknown>;

export function valueObject(value: unknown): CountMap | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as CountMap)
    : null;
}

export function countValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function displayCount(value: unknown): string {
  const count = countValue(value);
  return count === null ? "Unavailable" : count.toLocaleString();
}

export function prettyLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (first) => first.toUpperCase());
}

export function MetricCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string | number;
  note: string;
}) {
  return (
    <article className="dashboard-metric">
      <span>{label}</span>
      <strong>
        {typeof value === "number" ? value.toLocaleString() : value}
      </strong>
      <small>{note}</small>
    </article>
  );
}

export function CategoryBars({
  categories,
  emptyLabel = "No current declared records to chart.",
}: {
  categories: Array<{ label: string; value: number | null }>;
  emptyLabel?: string;
}) {
  const max = Math.max(0, ...categories.map((item) => item.value ?? 0));
  if (!categories.some((item) => item.value !== null)) {
    return <p className="chart-empty">{emptyLabel}</p>;
  }
  return (
    <div
      className="category-bars"
      aria-label="Current declared records by category"
    >
      {categories.map((item) => {
        const value = item.value;
        const width = max > 0 && value !== null ? (value / max) * 100 : 0;
        const style = { "--bar-width": `${width}%` } as CSSProperties;
        return (
          <div className="category-bar-row" key={item.label}>
            <span>{item.label}</span>
            <div
              className="category-bar-track"
              role="img"
              aria-label={`${item.label}: ${value === null ? "no current declaration" : value.toLocaleString()}`}
            >
              <span style={style} />
            </div>
            <strong>{value === null ? "—" : value.toLocaleString()}</strong>
          </div>
        );
      })}
    </div>
  );
}

export function CoverageBadge({ status }: { status: string }) {
  const tone =
    status === "COMPLETE"
      ? "active"
      : status === "PARTIAL"
        ? "warning"
        : "neutral";
  const text = status === "NONE" ? "No declarations" : prettyLabel(status);
  return <span className={`status-badge ${tone}`}>{text}</span>;
}

export function DashboardFilters({
  year,
  setYear,
  onApply,
  children,
}: {
  year: string;
  setYear: (value: string) => void;
  onApply: () => void;
  children?: React.ReactNode;
}) {
  return (
    <form
      className="dashboard-filters"
      onSubmit={(event) => {
        event.preventDefault();
        onApply();
      }}
    >
      <label>
        Academic year
        <input
          value={year}
          onChange={(event) => setYear(event.target.value)}
          aria-label="Academic year"
          placeholder="2026-27"
          inputMode="numeric"
          pattern="[0-9]{4}-[0-9]{2}"
        />
      </label>
      {children}
      <button className="button secondary" type="submit">
        Apply filters
      </button>
    </form>
  );
}

export function DashboardTable({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="table-scroll dashboard-table"
      role="region"
      tabIndex={0}
      aria-label={label}
    >
      <table>{children}</table>
    </div>
  );
}
