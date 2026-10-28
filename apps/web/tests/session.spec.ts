import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { API_URL } from "./setup";
import { cors, fail, signIn } from "./helpers";
import type { components } from "../src/lib/api/generated";

test("real administrator sign-in, programmes, logout and storage isolation", async ({
  page,
}) => {
  const identity = await signIn(page);
  expect(identity.role).toBe("INSTITUTION_ADMIN");
  await expect(page).toHaveURL(/\/institution$/);
  await expect(
    page.getByRole("heading", { name: "Demo Cedar Institute", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "DEMO-COMP", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "DEMO-ELEC", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("complementary", { name: "Demo data notice" }),
  ).toContainText("synthetic data only");
  expect(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
  ).toBe(0);
  expect(
    (await page.context().cookies()).some((cookie) =>
      /bearer|access_token|eyJ/.test(cookie.value),
    ),
  ).toBe(false);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: "Institution profile", exact: true }),
  ).toHaveCount(0);
  await signIn(page, "Demo Maple Institute");
  await expect(
    page.getByRole("heading", { name: "Demo Maple Institute", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Demo Cedar Institute", exact: true }),
  ).toHaveCount(0);
});

test("refresh and direct private navigation require sign-in", async ({
  page,
}) => {
  await signIn(page);
  await expect(page).toHaveURL(/\/institution$/);
  await page.reload();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/aicte/institutions");
  await expect(page).toHaveURL(/\/login$/);
});

for (const role of ["officer", "manager"]) {
  test(`real ${role} directory and scoped metadata`, async ({ page }) => {
    const identity = await signIn(page, `Demo AICTE ${role}`);
    expect(identity.institution_id).toBeNull();
    await expect(page).toHaveURL(/\/aicte$/);
    await page.getByRole("link", { name: "Institutions", exact: true }).click();
    await expect(page).toHaveURL(/\/aicte\/institutions$/);
    await expect(
      page.getByRole("heading", { name: "Institutions", exact: true }),
    ).toBeVisible();
    await page
      .getByRole("link", { name: "View Demo Maple Institute", exact: true })
      .click();
    await expect(
      page.getByRole("heading", { name: "Demo Maple Institute", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("cell", { name: "DEMO-COMP", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /activate|upload/i }),
    ).toHaveCount(0);
  });
}

test("altering presented identity never grants backend permissions", async ({
  page,
}) => {
  await page.route(API_URL + "/me", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({
      response,
      json: { ...body, role: "AICTE_OFFICER", institution_id: null },
    });
  });
  await signIn(page);
  await expect(page).toHaveURL(/\/aicte$/);
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "permission",
  );
  await expect(
    page.getByRole("link", { name: "View Demo Cedar Institute", exact: true }),
  ).toHaveCount(0);
});

test("directory search uses real API results and honest pagination", async ({
  page,
}) => {
  await signIn(page, "Demo AICTE officer");
  await page.getByRole("link", { name: "Institutions", exact: true }).click();
  const search = page.getByRole("searchbox", { name: "Search institutions" });
  await expect(
    page.getByRole("link", { name: "View Demo Cedar Institute", exact: true }),
  ).toBeVisible();
  await search.fill("Maple");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "View Demo Maple Institute", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "View Demo Cedar Institute", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Next", exact: true }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Previous", exact: true }),
  ).toBeDisabled();
  await search.fill("NoSuchSyntheticInstitution");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "No matching institutions",
      exact: true,
    }),
  ).toBeVisible();
  await search.fill("");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(
    page.getByRole("link", { name: "View Demo Cedar Institute", exact: true }),
  ).toBeVisible();
});

test("backend independently denies cross-institution and privileged access", async ({
  request,
}) => {
  const login = await request.post(API_URL + "/auth/demo-login", {
    data: { demo_alias: "cedar_admin" },
  });
  expect(login.status()).toBe(200);
  const credential: components["schemas"]["TokenResponse"] = await login.json();
  const headers = { Authorization: `Bearer ${credential.access_token}` };
  expect(
    (await request.get(API_URL + "/institutions", { headers })).status(),
  ).toBe(403);
  expect(
    (
      await request.get(
        API_URL + "/institutions/00000000-0000-4000-8000-000000000001",
        { headers },
      )
    ).status(),
  ).toBe(404);
  expect(
    (
      await request.post(API_URL + "/auth/demo-login", {
        data: { demo_alias: "cedar_admin", role: "AICTE_OFFICER" },
      })
    ).status(),
  ).toBe(422);
});

test("client expiry clears session and explains next action", async ({
  page,
}) => {
  await page.clock.install();
  await signIn(page);
  await expect(
    page.getByRole("cell", { name: "DEMO-COMP", exact: true }),
  ).toBeVisible();
  await page.clock.fastForward(901_000);
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Your demo session expired. Select a demo account to continue.",
  );
  expect(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
  ).toBe(0);
});

test("server SESSION_EXPIRED response clears private UI", async ({ page }) => {
  await signIn(page, "Demo AICTE officer");
  await expect(
    page.getByRole("heading", { name: "Institution dashboard", exact: true }),
  ).toBeVisible();
  await page.route(API_URL + "/institutions?*", (route) =>
    fail(route, 401, "SESSION_EXPIRED"),
  );
  await page.getByRole("link", { name: "Institutions", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Your demo session expired",
  );
  await expect(
    page.getByRole("heading", { name: "Institution dashboard", exact: true }),
  ).toHaveCount(0);
});

test("database failure shows a real error and retry, never fake data", async ({
  page,
}) => {
  await page.route(API_URL + "/institutions/*", (route) =>
    fail(route, 503, "DATABASE_UNAVAILABLE"),
  );
  await signIn(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "database is unavailable",
  );
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "synthetic-request-reference",
  );
  await expect(
    page.getByRole("heading", { name: "Demo Cedar Institute", exact: true }),
  ).toHaveCount(0);
  await page.unroute(API_URL + "/institutions/*");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(
    page.getByRole("cell", { name: "DEMO-COMP", exact: true }),
  ).toBeVisible();
});

test("empty programme response remains an honest empty state", async ({
  page,
}) => {
  await page.route(API_URL + "/institutions/*/programmes?*", (route) =>
    route.fulfill({
      status: 200,
      headers: cors,
      json: { data: [], pagination: { page: 1, page_size: 10, total: 0 } },
    }),
  );
  await signIn(page);
  await expect(
    page.getByRole("heading", { name: "No programmes found", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "DEMO-COMP", exact: true }),
  ).toHaveCount(0);
});

test("unavailable demo login is explained without a fallback identity", async ({
  page,
}) => {
  await page.route(API_URL + "/auth/demo-login", (route) =>
    fail(route, 404, "RESOURCE_NOT_FOUND"),
  );
  await page.goto("/login");
  await page
    .getByRole("button", { name: "Continue with demo account" })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Demo sign-in is unavailable",
  );
  await expect(page).toHaveURL(/\/login$/);
});

test("late old-account query cannot populate a new session", async ({
  page,
}) => {
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let signalIntercepted: () => void = () => {};
  const intercepted = new Promise<void>((resolve) => {
    signalIntercepted = resolve;
  });
  let first = true;
  await page.route(
    (url) =>
      url.origin === new URL(API_URL).origin &&
      url.pathname.includes("/api/v1/institutions/") &&
      url.pathname.endsWith("/programmes"),
    async (route) => {
      if (!first) {
        await route.continue();
        return;
      }
      first = false;
      const response = await route.fetch();
      const body = await response.json();
      body.data[0].name = "Old Cedar response must not appear";
      signalIntercepted();
      await gate;
      try {
        await route.fulfill({ response, json: body });
      } catch {
        /* The logged-out request may already be aborted. */
      }
    },
  );
  await signIn(page);
  await intercepted;
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await signIn(page, "Demo Maple Institute");
  await expect(
    page
      .getByRole("region", { name: "Programme declaration coverage" })
      .getByRole("cell", { name: "DEMO-COMP", exact: true }),
  ).toBeVisible();
  release();
  await expect(
    page.getByRole("heading", { name: "Demo Maple Institute", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Old Cedar response must not appear"),
  ).toHaveCount(0);
});

test("accessible login and authenticated desktop shell", async ({ page }) => {
  await page.goto("/login");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await signIn(page);
  await expect(
    page
      .getByRole("region", { name: "Programme declaration coverage" })
      .getByRole("cell", { name: "DEMO-COMP", exact: true }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test("mobile navigation supports keyboard escape and has no page overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  await expect(
    page
      .getByRole("region", { name: "Programme declaration coverage" })
      .getByRole("cell", { name: "DEMO-COMP", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  const opener = page.getByRole("button", { name: "Open navigation" });
  await opener.click();
  await expect(
    page.getByRole("dialog", { name: "Workspace navigation" }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("dialog", { name: "Workspace navigation" }),
  ).not.toBeVisible();
  await expect(opener).toBeFocused();
  await opener.click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("malformed identity never establishes a session", async ({ page }) => {
  await page.route(API_URL + "/me", (route) =>
    route.fulfill({
      status: 200,
      headers: cors,
      json: {
        id: "not-a-uuid",
        institution_id: null,
        role: "INSTITUTION_ADMIN",
        demo_mode: true,
      },
    }),
  );
  await page.goto("/login");
  await page
    .getByRole("button", { name: "Continue with demo account" })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "unexpected response",
  );
  await expect(page).toHaveURL(/\/login$/);
});
