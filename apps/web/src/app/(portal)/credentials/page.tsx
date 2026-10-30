import { Protected } from "@/components/app-shell";
import { CredentialList } from "@/features/credentials/manage";

export default function CredentialsPage() {
  return (
    <Protected roles={["INSTITUTION_ADMIN", "AICTE_OFFICER"]}>
      <CredentialList />
    </Protected>
  );
}
