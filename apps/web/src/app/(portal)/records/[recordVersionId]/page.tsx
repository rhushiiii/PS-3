import { Protected } from "@/components/app-shell";
import { RecordDetailView } from "@/features/records/detail";

export default async function RecordDetailPage({
  params,
}: {
  params: Promise<{ recordVersionId: string }>;
}) {
  const { recordVersionId } = await params;
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <RecordDetailView recordVersionId={recordVersionId} />
    </Protected>
  );
}
