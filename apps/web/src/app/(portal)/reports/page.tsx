import { Suspense } from "react";
import { Protected } from "@/components/app-shell";
import { ReportCenter } from "@/features/reports/center";

export default function ReportsPage() {
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER", "AICTE_MANAGER"]}>
      <Suspense>
        <ReportCenter />
      </Suspense>
    </Protected>
  );
}
