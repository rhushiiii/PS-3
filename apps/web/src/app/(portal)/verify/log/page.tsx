import { Protected } from "@/components/app-shell";
import { VerificationLog } from "@/features/credentials/log";

export default function VerificationLogPage() {
  return (
    <Protected roles={["AUTHORIZED_VERIFIER", "AICTE_OFFICER"]}>
      <VerificationLog />
    </Protected>
  );
}
