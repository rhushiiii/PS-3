import type { components } from "@/lib/api/generated";
import { humanize } from "@/lib/format";

type Schemas = components["schemas"];
export type CaseStatus = Schemas["CaseResponse"]["status"];
export type CasePriority = Schemas["CaseResponse"]["priority"];
export type CaseSeverity = Schemas["CaseResponse"]["severity"];
export type CaseEventAction = Schemas["CaseEventResponse"]["action"];
export type CaseAction = Schemas["CaseActionRequest"]["action"];
export type CaseSummary = Schemas["CaseResponse"];
export type CasePage = Schemas["Page_CaseResponse_"];

export const CASE_STATUSES: CaseStatus[] = [
  "OPEN",
  "ASSIGNED",
  "UNDER_REVIEW",
  "AWAITING_CORRECTION",
  "RESPONSE_SUBMITTED",
  "RESOLVED",
  "REJECTED",
  "CLOSED",
];
export const CASE_PRIORITIES: CasePriority[] = [
  "LOW",
  "MEDIUM",
  "HIGH",
  "URGENT",
];
export const CASE_SEVERITIES: CaseSeverity[] = [
  "LOW",
  "MEDIUM",
  "HIGH",
  "CRITICAL",
];

type Tone = "warning" | "active" | "neutral" | "danger";

/** Mirror of the backend transition table, used only to hide illegal actions. */
const BASE_ACTIONS: Record<CaseStatus, CaseAction[]> = {
  OPEN: ["COMMENT", "ASSIGNED", "START_REVIEW", "REQUEST_CORRECTION"],
  ASSIGNED: ["COMMENT", "ASSIGNED", "START_REVIEW", "REQUEST_CORRECTION"],
  UNDER_REVIEW: [
    "COMMENT",
    "ASSIGNED",
    "REQUEST_CORRECTION",
    "RESOLVED",
    "REJECTED",
  ],
  AWAITING_CORRECTION: ["COMMENT", "ASSIGNED", "RESPONSE_SUBMITTED"],
  RESPONSE_SUBMITTED: [
    "COMMENT",
    "ASSIGNED",
    "START_REVIEW",
    "REQUEST_CORRECTION",
  ],
  RESOLVED: ["COMMENT", "CLOSED"],
  REJECTED: ["COMMENT", "CLOSED"],
  CLOSED: [],
};
const TERMINAL: CaseStatus[] = ["RESOLVED", "REJECTED", "CLOSED"];

export function legalActions(
  status: CaseStatus,
  role: string | undefined,
): CaseAction[] {
  const base = BASE_ACTIONS[status];
  if (role === "INSTITUTION_ADMIN")
    return base.filter((a) => a === "COMMENT" || a === "RESPONSE_SUBMITTED");
  if (role !== "AICTE_OFFICER") return [];
  const officer = base.filter((a) => a !== "RESPONSE_SUBMITTED");
  return TERMINAL.includes(status) ? officer : [...officer, "UPDATED"];
}

export const titleCase = humanize;

export function statusLabel(status: CaseStatus): string {
  return status.replaceAll("_", " ");
}

export function statusTone(status: CaseStatus): Tone {
  if (status === "AWAITING_CORRECTION") return "warning";
  if (
    status === "OPEN" ||
    status === "ASSIGNED" ||
    status === "UNDER_REVIEW" ||
    status === "RESPONSE_SUBMITTED"
  )
    return "active";
  return "neutral";
}

export function priorityTone(priority: CasePriority): Tone {
  if (priority === "URGENT") return "danger";
  return priority === "HIGH" ? "warning" : "neutral";
}

export function severityTone(severity: CaseSeverity): Tone {
  if (severity === "CRITICAL") return "danger";
  return severity === "HIGH" ? "warning" : "neutral";
}

export function eventTone(action: CaseEventAction): Tone {
  if (action === "REQUEST_CORRECTION") return "warning";
  if (
    action === "RESOLVED" ||
    action === "CORRECTION_RECEIVED" ||
    action === "RESPONSE_SUBMITTED"
  )
    return "active";
  if (action === "REJECTED") return "danger";
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
    case "START_REVIEW":
      return "Review started";
    case "RESPONSE_SUBMITTED":
      return "Response submitted";
    case "UPDATED":
      return "Details updated";
    case "RESOLVED":
      return "Marked resolved";
    case "REJECTED":
      return "Marked rejected";
    case "CLOSED":
      return "Case closed";
    default:
      return action;
  }
}

/** Priority, severity, overdue and escalated badges for a case. */
export function CaseBadges({ item }: { item: CaseSummary }) {
  return (
    <span className="badge-row">
      <span className={`status-badge ${priorityTone(item.priority)}`}>
        Priority: {titleCase(item.priority)}
      </span>
      <span className={`status-badge ${severityTone(item.severity)}`}>
        Severity: {titleCase(item.severity)}
      </span>
      {item.is_overdue && <span className="status-badge danger">Overdue</span>}
      {item.is_escalated && (
        <span className="status-badge danger">Escalated</span>
      )}
    </span>
  );
}
