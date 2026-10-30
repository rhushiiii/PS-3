import { Protected } from "@/components/app-shell";
import { AnalyticsExplorer } from "@/features/analytics/explorer";

export default function AnalyticsPage() {
  return (
    <Protected roles={["AICTE_OFFICER", "AICTE_MANAGER"]}>
      <AnalyticsExplorer />
    </Protected>
  );
}
