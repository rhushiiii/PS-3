import { Protected } from "@/components/app-shell";
import { CaseQueue } from "@/features/cases/queue";

export default function CasesPage() {
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <CaseQueue />
    </Protected>
  );
}
