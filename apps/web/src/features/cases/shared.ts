import type { components } from "@/lib/api/generated";

export type CaseStatus = components["schemas"]["CaseResponse"]["status"];
export type CaseEventAction =
  components["schemas"]["CaseEventResponse"]["action"];

export const CASE_STATUSES: CaseStatus[] = [
  "OPEN",
  "AWAITING_CORRECTION",
  "UNDER_REVIEW",
  "RESOLVED",
  "CLOSED",
];

export function statusLabel(status: CaseStatus): string {
  return status.replaceAll("_", " ");
}

export function statusTone(
  status: CaseStatus,
): "warning" | "active" | "neutral" {
  if (status === "AWAITING_CORRECTION") return "warning";
  if (status === "OPEN" || status === "UNDER_REVIEW") return "active";
  return "neutral";
}

export function eventTone(
  action: CaseEventAction,
): "warning" | "active" | "neutral" {
  if (action === "REQUEST_CORRECTION") return "warning";
  if (action === "RESOLVED" || action === "CORRECTION_RECEIVED")
    return "active";
  return "neutral";
}

export function eventLabel(action: CaseEventAction): string {
  switch (action) {
    case "OPENED":
      return "Case opened";
    case "COMMENT":
      return "Comment";
    case "REQUEST_CORRECTION":
      return "Correction requested";
    case "CORRECTION_RECEIVED":
      return "Correction received (automatic)";
    case "ASSIGNED":
      return "Assigned";
    case "RESOLVED":
      return "Marked resolved";
    case "CLOSED":
      return "Case closed";
    default:
      return action;
  }
}
