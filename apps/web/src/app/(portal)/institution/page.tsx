"use client";

import { Protected } from "@/components/app-shell";
import { useSession } from "@/features/auth/session";
import { InstitutionDashboard } from "@/features/dashboards/institution-dashboard";

export default function InstitutionPage() {
  const { session } = useSession();
  return (
    <Protected roles={["INSTITUTION_ADMIN"]}>
      <InstitutionDashboard
        institutionId={session?.user.institution_id || ""}
      />
    </Protected>
  );
}
