import { useApiQuery, useScope } from "@/lib/api/hooks";
import type { components } from "@/lib/api/generated";

export type InstitutionPage =
  components["schemas"]["Page_InstitutionResponse_"];

/** Up to 100 institutions for filter dropdowns. */
export function useInstitutionOptions(enabled: boolean) {
  const scope = useScope("institutions");
  return useApiQuery<InstitutionPage>(
    scope,
    "/institutions?page=1&page_size=100",
    { enabled },
  );
}
