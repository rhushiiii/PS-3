import { Protected } from "@/components/app-shell";
import { InstitutionDirectory } from "@/features/institutions/directory";

export default function DirectoryPage() {
  return (
    <Protected roles={["AICTE_OFFICER", "AICTE_MANAGER"]}>
      <InstitutionDirectory />
    </Protected>
  );
}
