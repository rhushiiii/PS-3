import { Protected } from "@/components/app-shell";
import { CaseDetail } from "@/features/cases/detail";

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ caseId: string }>;
}) {
  const { caseId } = await params;
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <CaseDetail caseId={caseId} />
    </Protected>
  );
}
