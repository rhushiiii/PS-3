import type { components } from "@/lib/api/generated";

type Finding = components["schemas"]["FindingResponse"];

const guidance: Record<string, { what: string; next: string }> = {
  REQUIRED_FIELD_MISSING: {
    what: "A required value is missing from this submitted record.",
    next: "Check the source record and include the correct value in a new complete CSV submission.",
  },
  INVALID_ACADEMIC_YEAR: {
    what: "The row's academic year does not match this candidate snapshot.",
    next: "Confirm the intended year and correct the source CSV before creating a replacement submission.",
  },
  PROGRAMME_MISMATCH: {
    what: "The row programme does not match the programme selected for this snapshot.",
    next: "Check the programme in the source system and submit a corrected complete CSV if needed.",
  },
  INVALID_ADMISSION_CATEGORY: {
    what: "The admission category is outside the supported categories.",
    next: "Confirm the category in the source record. Supported categories are illustrative configuration.",
  },
  INVALID_ENROLLMENT_STATUS: {
    what: "The enrolment status is outside the supported statuses.",
    next: "Confirm the student's current status in the source system and correct the next CSV if needed.",
  },
  INVALID_ENROLLMENT_DATE: {
    what: "The date is missing or could not be read as a calendar date.",
    next: "Check the date in the source system. This is a reviewable data-quality finding.",
  },
  INVALID_APAAR_FORMAT: {
    what: "The nonempty APAAR value does not match the configured local format.",
    next: "Check the source value and correct it if appropriate. This local syntax check does not verify identity.",
  },
  DUPLICATE_COLLEGE_STUDENT_ID: {
    what: "The same college student identifier appears more than once in this candidate.",
    next: "Check whether the rows refer to separate people or a repeated entry. Do not merge records automatically.",
  },
  DUPLICATE_IN_BATCH: {
    what: "A structurally matching APAAR token appears on another row in this candidate.",
    next: "Review both source records. This is a possible overlap, not proof of fraud or identity verification.",
  },
  POTENTIAL_CROSS_INSTITUTION_DUPLICATE: {
    what: "A matching token was found in another institution's records.",
    next: "Treat this as a possible overlap; transfers or withdrawals may explain it. Officer review may be needed.",
  },
  INTAKE_EXCEEDED: {
    what: "The candidate count exceeds the configured capacity for this year and category.",
    next: "Compare the candidate with the institution's configured intake rule. This is not an official AICTE violation.",
  },
  MISSING_INTAKE_RULE: {
    what: "No configured capacity was available for this year and category.",
    next: "Ask an administrator to review the intake configuration; no official capacity conclusion is implied.",
  },
};

export function findingGuidance(finding: Finding) {
  return (
    guidance[finding.rule_code] ?? {
      what: finding.explanation,
      next: "Review the evidence with your data administrator. Submitted rows are immutable; corrections use a new complete CSV.",
    }
  );
}

const safeEvidenceKeys = new Set([
  "source_row_number",
  "field_name",
  "observed",
  "expected",
  "programme_code",
  "academic_year",
  "admission_category",
  "enrollment_status",
  "configured_capacity",
  "reported_count",
  "matched_record_count",
  "assessment_label",
  "match_kind",
  "current_active",
  "match_context",
]);

export function safeEvidence(
  evidence: Finding["evidence"],
): [string, string][] {
  return Object.entries(evidence)
    .filter(([key, value]) => safeEvidenceKeys.has(key) && value !== null)
    .filter(([, value]) =>
      ["string", "number", "boolean"].includes(typeof value),
    )
    .map(([key, value]) => [key.replaceAll("_", " "), String(value)]);
}
