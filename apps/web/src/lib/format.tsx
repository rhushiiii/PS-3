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
