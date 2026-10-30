import type { ReactNode } from "react";
import { humanize } from "@/lib/format";

/**
 * The shared institution dropdown. Dependent resets (e.g. clearing the
 * programme filter) stay with the caller via `onChange`.
 */
export function InstitutionSelect({
  institutions,
  value,
  onChange,
  disabled,
  className,
  allLabel = "All institutions",
}: {
  institutions: Array<{ id: string; name: string }>;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  className?: string;
  allLabel?: string;
}) {
  return (
    <label className={className}>
      Institution
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{allLabel}</option>
        {institutions.map((institution) => (
          <option key={institution.id} value={institution.id}>
            {institution.name}
          </option>
        ))}
      </select>
    </label>
  );
}

/** The shared region dropdown over a sorted region list. */
export function RegionSelect({
  regions,
  value,
  onChange,
  className,
  allLabel = "All regions",
}: {
  regions: readonly string[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
  allLabel?: string;
}) {
  return (
    <label className={className}>
      Region
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{allLabel}</option>
        {regions.map((region) => (
          <option key={region} value={region}>
            {region}
          </option>
        ))}
      </select>
    </label>
  );
}

/** A labeled single-value select over an enum-ish value list. */
export function EnumSelect({
  label,
  values,
  value,
  onChange,
  allLabel,
  className,
  format = humanize,
}: {
  label: string;
  values: readonly string[];
  value: string;
  onChange: (value: string) => void;
  allLabel: string;
  className?: string;
  format?: (value: string) => string;
}) {
  return (
    <label className={className}>
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{allLabel}</option>
        {values.map((item) => (
          <option key={item} value={item}>
            {format(item)}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Optional children rendered after the selects (extra inputs, errors). */
export function FilterField({
  label,
  children,
  className,
}: {
  label: string;
  children: ReactNode;
  className?: string;
}) {
  return <label className={className}>{label}{children}</label>;
}
