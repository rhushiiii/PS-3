/** Locale timestamp wrapped in a machine-readable <time> element. */
export const when = (value: string) => (
  <time dateTime={value}>{new Date(value).toLocaleString()}</time>
);

/** "NEEDS_REVIEW" -> "Needs review". */
export function humanize(value: string): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^./, (first) => first.toUpperCase());
}

/** "ACTIVATION_BLOCKING" -> "ACTIVATION BLOCKING" (case preserved). */
export function plain(value: string): string {
  return value.replaceAll("_", " ");
}

/** The single wording for simulated provenance labels. */
export const DEMO_TAG = "SIMULATED / DEMO DATA";

/** Unknown -> object | null; the shared defensive reader for loose payloads. */
export function valueObject(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

/** Unknown -> finite number | null. */
export function countValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/** Count display: localized digits, or the fallback when nothing was reported. */
export function displayCount(
  value: unknown,
  suffix = "",
  empty = "Unavailable",
): string {
  const count = countValue(value);
  return count === null ? empty : count.toLocaleString() + suffix;
}

/** Snapshot badge wording, shared by history, records and dashboards. */
export function snapshotLabel(state: string): string {
  switch (state) {
    case "CURRENT":
      return "Current";
    case "CANDIDATE":
      return "Candidate";
    case "PREVIOUS":
      return "Previous";
    case "SUPERSEDED":
      return "Superseded";
    default:
      return humanize(state);
  }
}

/** Snapshot badge tone: current stands out, candidates warn, the rest recede. */
export function snapshotTone(state: string): string {
  if (state === "CURRENT") return "active";
  if (state === "CANDIDATE") return "warning";
  return "neutral";
}

/** Sorted, deduplicated region list for filter dropdowns. */
export function regionsOf(institutions: Array<{ region: string }>): string[] {
  return [...new Set(institutions.map((institution) => institution.region))].sort();
}
