"use client";

import { Protected } from "@/components/app-shell";
import { useSession } from "@/features/auth/session";
import { CandidateUpload } from "@/features/submissions/upload";

export default function UploadPage() {
  const { session } = useSession();
  return (
    <Protected roles={["INSTITUTION_ADMIN"]}>
      <CandidateUpload key={session?.generation} />
    </Protected>
  );
}
