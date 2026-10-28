import { type Page, type Route } from "@playwright/test";
import { API_URL, WEB_URL } from "./setup";
import type { components } from "../src/lib/api/generated";

export const cors = {
  "access-control-allow-origin": WEB_URL,
  "content-type": "application/json",
};

export async function signIn(
  page: Page,
  label = "Demo Cedar Institute",
): Promise<components["schemas"]["CurrentUserResponse"]> {
  if (!page.url().endsWith("/login")) await page.goto("/login");
  await page.getByRole("radio", { name: new RegExp(label) }).check();
  const identity = page.waitForResponse(
    (response) => response.url() === API_URL + "/me",
  );
  await page
    .getByRole("button", { name: "Continue with demo account" })
    .click();
  return (await (
    await identity
  ).json()) as components["schemas"]["CurrentUserResponse"];
}

export async function fail(route: Route, status: number, code: string) {
  await route.fulfill({
    status,
    headers: cors,
    json: {
      error: {
        code,
        message: "Redacted test error",
        request_id: "synthetic-request-reference",
      },
    },
  });
}
