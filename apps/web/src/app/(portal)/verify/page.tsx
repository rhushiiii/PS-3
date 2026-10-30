import { Protected } from "@/components/app-shell";
import { VerifyCredential } from "@/features/credentials/verify";

export default function VerifyPage() {
  return (
    <Protected roles={["AUTHORIZED_VERIFIER", "AICTE_OFFICER"]}>
      <VerifyCredential />
    </Protected>
  );
}
