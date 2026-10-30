import { Suspense } from "react";
import { Protected } from "@/components/app-shell";
import { CaseQueue } from "@/features/cases/queue";

export default function CasesPage() {
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <Suspense>
        <CaseQueue />
      </Suspense>
    </Protected>
  );
}
