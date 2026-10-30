import { Protected } from "@/components/app-shell";
import { RecordRegistry } from "@/features/records/registry";

export default function RecordsPage() {
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <RecordRegistry />
    </Protected>
  );
}
