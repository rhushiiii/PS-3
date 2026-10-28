import { Protected } from "@/components/app-shell";
import { InstitutionProfile } from "@/features/institutions/profile";

export default async function ProfilePage({
  params,
}: {
  params: Promise<{ institutionId: string }>;
}) {
  const { institutionId } = await params;
  return (
    <Protected roles={["AICTE_OFFICER", "AICTE_MANAGER"]}>
      <InstitutionProfile institutionId={institutionId} />
    </Protected>
  );
}
