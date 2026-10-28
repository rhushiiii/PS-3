"use client";

import { useSession } from "@/features/auth/session";
import { SubmissionHistory } from "./history";

export function ScopedSubmissionHistory({
  institutionId,
}: {
  institutionId: string;
}) {
  const { session } = useSession();
  const scope =
    session?.user.role === "INSTITUTION_ADMIN"
      ? (session.user.institution_id ?? "")
      : institutionId;
  return (
    <SubmissionHistory
      key={`${session?.generation}:${scope}`}
      institutionId={scope}
    />
  );
}
