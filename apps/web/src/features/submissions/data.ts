"use client";

import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { isUUID } from "@/lib/api/client";
import type { components, paths } from "@/lib/api/generated";

export type Batch = components["schemas"]["BatchResponse"];
export type History =
  paths["/api/v1/submissions"]["get"]["responses"][200]["content"]["application/json"];
type Programmes =
  paths["/api/v1/institutions/{institution_id}/programmes"]["get"]["responses"][200]["content"]["application/json"];

export function useSubmissionContext(institutionId: string) {
  const { session, request } = useSession();
  const key = ["private", session?.generation, session?.user.id];
  const enabled = !!session && isUUID(institutionId);
  const institution = useQuery({
    queryKey: [...key, "institution", institutionId],
    enabled,
    queryFn: ({ signal }) =>
      request<components["schemas"]["InstitutionResponse"]>(
        `/institutions/${institutionId}`,
        { signal },
      ),
  });
  const programmes = useInfiniteQuery({
    queryKey: [...key, "submission-programmes", institutionId],
    enabled: enabled && !!institution.data,
    initialPageParam: 1,
    queryFn: ({ signal, pageParam }) =>
      request<Programmes>(
        `/institutions/${institutionId}/programmes?page=${pageParam}&page_size=100`,
        { signal },
      ),
    getNextPageParam: (last) =>
      last.pagination.page * last.pagination.page_size < last.pagination.total
        ? last.pagination.page + 1
        : undefined,
  });
  return {
    institution,
    programmes,
    options: programmes.data?.pages.flatMap((page) => page.data) ?? [],
  };
}

export { validAcademicYear } from "@/lib/academic-year";

export const snapshotLabels = {
  CANDIDATE: "Candidate",
  CURRENT: "Current",
  PREVIOUS: "Previous",
} as const;
