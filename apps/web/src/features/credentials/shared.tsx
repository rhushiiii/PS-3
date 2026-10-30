import type { components } from "@/lib/api/generated";
import { DEMO_TAG } from "@/lib/format";

type Schemas = components["schemas"];
export type CredentialSummary = Schemas["CredentialSummary"];
export type CredentialPage = Schemas["Page_CredentialSummary_"];
export type Outcome = Schemas["VerifyResponse"]["outcome"];

export const DEMO_LABEL = `${DEMO_TAG} — prototype key; not an official AICTE, APAAR or government document`;

export const outcomeLabel: Record<Outcome, string> = {
  VALID: "Valid",
  EXPIRED: "Expired",
  REVOKED: "Revoked",
  INVALID: "Invalid",
  UNAVAILABLE: "Service unavailable",
};

export const outcomeTone: Record<Outcome, string> = {
  VALID: "active",
  EXPIRED: "warning",
  REVOKED: "danger",
  INVALID: "danger",
  UNAVAILABLE: "neutral",
};

export { when } from "@/lib/format";

export function credentialState(c: CredentialSummary): {
  label: string;
  tone: string;
} {
  if (c.revoked) return { label: "Revoked", tone: "danger" };
  if (new Date(c.expires_at).getTime() <= Date.now())
    return { label: "Expired", tone: "warning" };
  return { label: "Active", tone: "active" };
}
