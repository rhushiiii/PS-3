import { Protected } from "@/components/app-shell";
import { VerificationWorkspace } from "@/features/verification/workspace";

export default function VerificationPage() {
  return (
    <Protected roles={["AICTE_OFFICER"]}>
      <VerificationWorkspace />
    </Protected>
  );
}
