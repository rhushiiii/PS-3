import { Protected } from "@/components/app-shell";
import { ScopedSubmissionHistory } from "@/features/submissions/scoped-history";

export default async function SubmissionsPage({
  searchParams,
}: {
  searchParams: Promise<{ institution_id?: string | string[] }>;
}) {
  const context = await searchParams;
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <ScopedSubmissionHistory
        institutionId={
          typeof context.institution_id === "string"
            ? context.institution_id
            : ""
        }
      />
    </Protected>
  );
}
