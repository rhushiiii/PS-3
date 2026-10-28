import { Protected } from "@/components/app-shell";
import { AicteDashboard } from "@/features/dashboards/aicte-dashboard";

export default function AicteDashboardPage() {
  return (
    <Protected roles={["AICTE_OFFICER", "AICTE_MANAGER"]}>
      <AicteDashboard />
    </Protected>
  );
}
