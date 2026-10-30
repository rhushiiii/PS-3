import type { components } from "@/lib/api/generated";

type Schemas = components["schemas"];
export type RecordRow = Schemas["RecordRow"];
export type RecordDetail = Schemas["RecordDetail"];
export type SnapshotState = RecordRow["snapshot_state"];
export type ValidationStatus = NonNullable<RecordRow["validation_status"]>;

export const VALIDATION_STATUSES: ValidationStatus[] = [
  "VALID",
  "FLAGGED",
  "INCOMPLETE",
];

export function snapshotLabel(state: SnapshotState): string {
  if (state === "CURRENT") return "Current";
  return state === "CANDIDATE" ? "Candidate" : "Superseded";
}

export function validationTone(status: RecordRow["validation_status"]) {
  if (status === "VALID") return "active";
  if (status === "FLAGGED") return "warning";
  return "neutral";
}

export function validationLabel(status: RecordRow["validation_status"]) {
  return status ? status.charAt(0) + status.slice(1).toLowerCase() : "Not run";
}

export function StatusBadges({
  snapshot,
  validation,
}: {
  snapshot: SnapshotState;
  validation: RecordRow["validation_status"];
}) {
  return (
    <span className="badge-row">
      <span
        className={`status-badge ${snapshot === "CURRENT" ? "active" : "neutral"}`}
      >
        {snapshotLabel(snapshot)}
      </span>
      <span className={`status-badge ${validationTone(validation)}`}>
        Validation: {validationLabel(validation)}
      </span>
    </span>
  );
}
