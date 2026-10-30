"use client";

import type { ReactNode } from "react";
import { ApiError, errorMessage } from "@/lib/api/client";
import type { components } from "@/lib/api/generated";

export type Category = components["schemas"]["AdmissionCategory"];
export const CATEGORIES: Category[] = [
  "REGULAR",
  "SUPERNUMERARY",
  "NRI",
  "OCI",
  "FOREIGN_NATIONAL",
];
export const DEFAULT_YEAR = "2026-27";

export function categoryLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^\w/, (c) => c.toUpperCase());
}

/** Plain-language message for intake mutations; never exposes raw server text. */
export function intakeMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "NO_CHANGE")
      return "Approved seats already have this value. Enter a different number.";
    if (error.code === "SUBMISSION_NOT_PROCESSED")
      return "This submission has not finished processing, so it cannot be assessed yet.";
    if (error.status === 403)
      return "Your role is not permitted to use this intake function.";
  }
  return errorMessage(error);
}

/** DEMO labelling: intake values are illustrative, never official AICTE values. */
export function DemoRuleNotice() {
  return (
    <aside className="demo-banner" aria-label="Demo intake rules notice">
      <span className="demo-dot" aria-hidden="true" />
      DEMO intake rules
      <span className="banner-detail">
        Illustrative values, not official AICTE determinations. Flags are review
        signals, not fraud findings; officers decide.
      </span>
    </aside>
  );
}

export function ScrollTable({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div
      className="table-scroll"
      tabIndex={0}
      role="region"
      aria-label={`${label}, scroll horizontally on small screens`}
    >
      <table>
        <caption className="sr-only">{label}</caption>
        {children}
      </table>
    </div>
  );
}

export function severityClass(severity: string): string {
  return severity === "ERROR"
    ? "danger"
    : severity === "WARNING"
      ? "warning"
      : "neutral";
}
