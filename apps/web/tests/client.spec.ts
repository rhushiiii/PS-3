import { expect, test } from "@playwright/test";
import { ApiError, errorMessage } from "../src/lib/api/client";
import { homeFor } from "../src/features/auth/session";

test("error presentation is controlled and does not echo server payloads", () => {
  expect(errorMessage(new Error("secret token or CSV content"))).not.toContain(
    "secret",
  );
  expect(errorMessage(new ApiError(503, "DATABASE_UNAVAILABLE"))).toContain(
    "database is unavailable",
  );
  expect(errorMessage(new ApiError(403, "FORBIDDEN_ROLE"))).toContain(
    "permission",
  );
  expect(errorMessage(new ApiError(404, "RESOURCE_NOT_FOUND"))).toContain(
    "unavailable",
  );
});

test("role destinations contain no impersonation parameters", () => {
  expect(homeFor("INSTITUTION_ADMIN")).toBe("/institution");
  expect(homeFor("AICTE_OFFICER")).toBe("/aicte");
  expect(homeFor("AICTE_MANAGER")).toBe("/aicte");
  expect(homeFor("AUTHORIZED_VERIFIER")).toBe("/access-denied");
});
