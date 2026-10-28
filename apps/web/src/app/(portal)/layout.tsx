import type { ReactNode } from "react";
import { AppShell, Protected } from "@/components/app-shell";

export default function PortalLayout({ children }: { children: ReactNode }) {
  return (
    <Protected
      roles={[
        "INSTITUTION_ADMIN",
        "AICTE_OFFICER",
        "AICTE_MANAGER",
        "AUTHORIZED_VERIFIER",
      ]}
    >
      <AppShell>{children}</AppShell>
    </Protected>
  );
}
