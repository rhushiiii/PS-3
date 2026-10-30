"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import { isUUID } from "@/lib/api/client";
import { useApiQuery, useScope } from "@/lib/api/hooks";
import type { components, paths } from "@/lib/api/generated";

export type Batch = components["schemas"]["BatchResponse"];
export type History =
  paths["/api/v1/submissions"]["get"]["responses"][200]["content"]["application/json"];
export type Programmes =
  paths["/api/v1/institutions/{institution_id}/programmes"]["get"]["responses"][200]["content"]["application/json"];

export function useSubmissionContext(institutionId: string) {
  const { session, request } = useSession();
  const valid = isUUID(institutionId);
  const scope = useScope("institution", institutionId);
  const institution = useApiQuery<components["schemas"]["InstitutionResponse"]>(
    scope,
    `/institutions/${institutionId}`,
    { enabled: valid },
  );
  const programmes = useInfiniteQuery({
    queryKey: [
      "private",
      session?.generation,
      session?.user.id,
      "submission-programmes",
      institutionId,
    ],
    enabled: valid && !!session && !!institution.data,
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
