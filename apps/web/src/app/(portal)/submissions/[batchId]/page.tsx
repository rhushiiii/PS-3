import { Protected } from "@/components/app-shell";
import { ValidationWorkspace } from "@/features/validation/workspace";

type SearchValue = string | string[] | undefined;

export default async function SubmissionDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ batchId: string }>;
  searchParams: Promise<Record<string, SearchValue>>;
}) {
  const [{ batchId }, search] = await Promise.all([params, searchParams]);
  const one = (value: SearchValue) =>
    typeof value === "string" ? value : undefined;
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <ValidationWorkspace
        batchId={batchId}
        query={{
          run_id: one(search.run_id),
          run_page: one(search.run_page),
          row_page: one(search.row_page),
          row_status: one(search.row_status),
          finding_page: one(search.finding_page),
          finding_rule: one(search.finding_rule),
          finding_severity: one(search.finding_severity),
          finding_classification: one(search.finding_classification),
          review_id: one(search.review_id),
          omission_page: one(search.omission_page),
        }}
      />
    </Protected>
  );
}
