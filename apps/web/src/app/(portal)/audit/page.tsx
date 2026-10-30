import { Protected } from "@/components/app-shell";
import { AuditExplorer } from "@/features/audit/explorer";

export default function AuditPage() {
  return (
    <Protected roles={["AICTE_OFFICER"]}>
      <AuditExplorer />
    </Protected>
  );
}
