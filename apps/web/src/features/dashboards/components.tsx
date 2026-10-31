import { motion, useReducedMotion } from "framer-motion";
import { humanize } from "@/lib/format";

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

export const prettyLabel = humanize;

export function MetricCard({
  label,
  value,
  note,
  tone = "neutral",
}: {
  label: string;
  value: string | number;
  note: string;
  tone?: "neutral" | "warning" | "critical" | "success";
}) {
  const reduce = useReducedMotion();
  const toneClass =
    tone === "critical"
      ? "dashboard-metric-critical"
      : tone === "warning"
        ? "dashboard-metric-warning"
        : tone === "success"
          ? "dashboard-metric-success"
          : "dashboard-metric-neutral";

  return (
    <motion.article
      className={`dashboard-metric ${toneClass}`}
      initial={reduce ? undefined : { opacity: 0, scale: 0.94, y: 8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      whileHover={reduce ? undefined : { y: -3, scale: 1.012 }}
      transition={
        reduce
          ? { duration: 0.15 }
          : { type: "spring", stiffness: 420, damping: 28 }
      }
    >
      <span className="metric-label">{label}</span>
      <strong className="metric-value">
        {typeof value === "number" ? value.toLocaleString() : value}
      </strong>
      <small className="metric-note">{note}</small>
    </motion.article>
  );
}

export function CategoryBars({
  categories,
  emptyLabel = "No current declared records to chart.",
}: {
  categories: Array<{ label: string; value: number | null }>;
  emptyLabel?: string;
}) {
  const reduce = useReducedMotion();
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
        const isWinner = value !== null && value === max && max > 0;
        return (
          <div
            className={`category-bar-row ${isWinner ? "category-bar-winner" : ""}`}
            key={item.label}
          >
            <span className={isWinner ? "bar-label-winner" : undefined}>
              {item.label}
              {isWinner && <span className="winner-indicator" aria-hidden="true">★</span>}
            </span>
            <div
              className={`category-bar-track ${isWinner ? "track-winner" : ""}`}
              role="img"
              aria-label={`${item.label}: ${value === null ? "no current declaration" : value.toLocaleString()}${isWinner ? " (highest)" : ""}`}
            >
              <motion.span
                className={isWinner ? "bar-span-winner" : undefined}
                initial={reduce ? undefined : { width: 0 }}
                animate={{ width: `${width}%` }}
                transition={
                  reduce
                    ? { duration: 0.1 }
                    : { duration: 0.65, ease: [0.16, 1, 0.3, 1] }
                }
              />
            </div>
            <strong className={isWinner ? "bar-val-winner" : undefined}>
              {value === null ? "—" : value.toLocaleString()}
            </strong>
          </div>
        );
      })}
    </div>
  );
}

const statusTone: Record<string, string> = {
  ACTIVE: "#15803d",
  INACTIVE: "#b45309",
  UNSUPPORTED: "#6b7280",
};
const donutPalette = ["#15803d", "#3b82f6", "#b45309", "#d97706", "#6b7280"];

export function StatusDonut({
  statuses,
  total,
}: {
  statuses: Array<{ label: string; value: number }>;
  total: number;
}) {
  const reduce = useReducedMotion();
  const nonZero = statuses.filter((item) => item.value > 0);
  if (total <= 0 || nonZero.length === 0)
    return <p className="chart-empty">No current records to chart.</p>;
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const maxVal = Math.max(0, ...nonZero.map((item) => item.value));
  const lengths = nonZero.map((item) => (item.value / total) * circumference);
  const offsets = lengths.map((_, index) =>
    lengths.slice(0, index).reduce((sum, value) => sum + value, 0),
  );
  const segments = nonZero.map((item, index) => ({
    ...item,
    isWinner: item.value === maxVal && maxVal > 0,
    length: lengths[index],
    offset: offsets[index],
    color:
      statusTone[item.label.toUpperCase()] ??
      donutPalette[index % donutPalette.length],
  }));
  return (
    <div className="status-donut">
      <svg
        viewBox="0 0 140 140"
        width="140"
        height="140"
        role="img"
        aria-label="Current records by status"
      >
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="#eceae3"
          strokeWidth="16"
        />
        {segments.map((segment) => (
          <motion.circle
            key={segment.label}
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke={segment.color}
            strokeWidth={segment.isWinner ? "18" : "15"}
            strokeDasharray={`${segment.length} ${circumference - segment.length}`}
            initial={
              reduce
                ? undefined
                : { strokeDashoffset: circumference, opacity: 0 }
            }
            animate={{
              strokeDashoffset: circumference - segment.offset,
              opacity: 1,
            }}
            transition={
              reduce
                ? { duration: 0.1 }
                : { duration: 0.7, ease: [0.16, 1, 0.3, 1] }
            }
            transform="rotate(-90 70 70)"
            strokeLinecap="butt"
          />
        ))}
        <text x="70" y="65" textAnchor="middle" className="status-donut-total">
          {total.toLocaleString()}
        </text>
        <text x="70" y="82" textAnchor="middle" className="status-donut-label">
          records
        </text>
      </svg>
      <ul className="status-donut-legend">
        {segments.map((segment) => (
          <li
            key={segment.label}
            className={segment.isWinner ? "status-legend-winner" : undefined}
          >
            <span
              style={{ background: segment.color }}
              aria-hidden="true"
              className={segment.isWinner ? "legend-dot-winner" : undefined}
            />
            {prettyLabel(segment.label)} · {segment.value.toLocaleString()}
            {segment.isWinner && (
              <span className="legend-winner-badge">Majority</span>
            )}
          </li>
        ))}
      </ul>
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

export function DashboardTableRow({
  index = 0,
  children,
  className = "",
  ...props
}: {
  index?: number;
  children: React.ReactNode;
  className?: string;
} & React.HTMLAttributes<HTMLTableRowElement>) {
  const reduce = useReducedMotion();
  return (
    <motion.tr
      className={`dashboard-table-row ${className}`}
      initial={reduce ? undefined : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={
        reduce
          ? { duration: 0.05 }
          : {
              duration: 0.28,
              delay: Math.min(index * 0.032, 0.35),
              ease: "easeOut",
            }
      }
      {...(props as any)}
    >
      {children}
    </motion.tr>
  );
}
