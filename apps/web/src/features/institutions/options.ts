import { useQuery } from "@tanstack/react-query";
import { useSession } from "@/features/auth/session";
import type { components } from "@/lib/api/generated";

export type InstitutionPage =
  components["schemas"]["Page_InstitutionResponse_"];

/** Up to 100 institutions for filter dropdowns; callers own the cache key. */
export function useInstitutionOptions(
  queryKey: readonly unknown[],
  enabled: boolean,
) {
  const { request } = useSession();
  return useQuery({
    queryKey,
    enabled,
    queryFn: ({ signal }) =>
      request<InstitutionPage>("/institutions?page=1&page_size=100", {
        signal,
      }),
  });
}
