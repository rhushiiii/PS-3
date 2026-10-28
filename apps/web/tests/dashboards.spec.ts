import {
  expect,
  test,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { API_URL } from "./setup";
import { signIn } from "./helpers";

const initialCsv = readFileSync(
  resolve("../../samples/synthetic_snapshot_initial.csv"),
);

async function account(request: APIRequestContext, alias: string) {
  const login = await request.post(`${API_URL}/auth/demo-login`, {
    data: { demo_alias: alias },
  });
  const headers = {
    Authorization: `Bearer ${(await login.json()).access_token}`,
  };
  const identity = await (
    await request.get(`${API_URL}/me`, { headers })
  ).json();
  const programmeResponse = await request.get(
    `${API_URL}/institutions/${identity.institution_id}/programmes?page=1&page_size=100`,
    { headers },
  );
  const programmes = await programmeResponse.json();
  return {
    headers,
    institutionId: identity.institution_id as string,
    programmeId: programmes.data.find(
      (item: { code: string }) => item.code === "DEMO-COMP",
    ).id as string,
  };
}

async function activateSnapshot(
  request: APIRequestContext,
  alias: string,
  year: string,
) {
  const owner = await account(request, alias);
  const response = await request.post(`${API_URL}/submissions`, {
    headers: owner.headers,
    multipart: {
      institution_id: owner.institutionId,
      programme_id: owner.programmeId,
      academic_year: year,
      schema_version: "v1",
      file: {
        name: "synthetic_dashboard.csv",
        mimeType: "text/csv",
        buffer: Buffer.from(initialCsv.toString().replaceAll("2026-27", year)),
      },
    },
  });
  expect(response.status()).toBe(201);
  const batchId = (await response.json()).id as string;
  const validation = await request.post(
    `${API_URL}/submissions/${batchId}/validate`,
    { headers: owner.headers },
  );
  expect(validation.status()).toBe(201);
  const runId = (await validation.json()).id as string;
  const reviewResponse = await request.post(
    `${API_URL}/submissions/${batchId}/reviews`,
    { headers: owner.headers, data: { validation_run_id: runId } },
  );
  expect(reviewResponse.status()).toBe(201);
  const review = await reviewResponse.json();
  const activated = await request.post(
    `${API_URL}/submissions/${batchId}/activate`,
    {
      headers: owner.headers,
      data: {
        review_id: review.id,
        expected_scope_revision: review.expected_scope_revision,
        confirm_complete_replacement: true,
        acknowledge_review_warnings: true,
        acknowledge_omissions: true,
      },
    },
  );
  expect(activated.status()).toBe(200);
  return { ...owner, batchId, runId };
}

async function applyYear(page: Page, year: string) {
  await page.getByRole("textbox", { name: "Academic year" }).fill(year);
  await page.getByRole("button", { name: "Apply filters" }).click();
}

test("institution dashboard uses activated counts, keeps candidates out, and shows partial coverage", async ({
  page,
  request,
}) => {
  const year = "2026-27";
  await activateSnapshot(request, "cedar_admin", year);
  const owner = await account(request, "cedar_admin");
  const candidateResponse = await request.post(`${API_URL}/submissions`, {
    headers: owner.headers,
    multipart: {
      institution_id: owner.institutionId,
      programme_id: owner.programmeId,
      academic_year: year,
      schema_version: "v1",
      file: {
        name: "synthetic_candidate.csv",
        mimeType: "text/csv",
        buffer: Buffer.from(initialCsv.toString().replaceAll("2026-27", year)),
      },
    },
  });
  expect(candidateResponse.status()).toBe(201);
  await signIn(page);
  await applyYear(page, year);
  await expect(
    page.getByRole("heading", { name: "Institution dashboard" }),
  ).toBeVisible();
  await expect(
    page.getByText("Current declared records").locator(".."),
  ).toContainText("3");
  await expect(
    page.getByText("Demo ACTIVE enrolments").locator(".."),
  ).toContainText("3");
  await expect(page.getByText("1 / 2")).toBeVisible();
  await expect(
    page.locator(".dashboard-metric").filter({ hasText: "Programme coverage" }),
  ).toContainText("Partial");
  await expect(
    page.getByRole("row").filter({ hasText: "DEMO-ELEC" }),
  ).toContainText("No declaration");
  const recent = page.getByRole("region", {
    name: "Recent institution submissions",
  });
  await expect(recent).toContainText("Candidate");
  await expect(recent).toContainText("Continue candidate review");
  await expect(
    page.getByText("Candidate", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByText("Current declared records").locator(".."),
  ).toContainText("3");
  await expect(
    page.getByText("official AICTE compliance", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("Configured DEMO intake comparisons").locator(".."),
  ).toContainText("10");
  const programme = await page
    .locator(".dashboard-filters")
    .getByLabel("Programme")
    .locator("option")
    .filter({ hasText: "DEMO-COMP" })
    .getAttribute("value");
  expect(programme).toBeTruthy();
  await page
    .locator(".dashboard-filters")
    .getByLabel("Programme")
    .selectOption(programme!);
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.getByText("1 / 1")).toBeVisible();
  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);
});

test("institution dashboard distinguishes no declaration from a zero count", async ({
  page,
}) => {
  await signIn(page);
  await applyYear(page, "2099-00");
  await expect(page.getByText("No declaration").first()).toBeVisible();
  await expect(
    page.getByText("No current declarations are available for this scope."),
  ).toBeVisible();
  await expect(
    page.getByRole("row").filter({ hasText: "DEMO-COMP" }),
  ).toContainText("No declaration");
});

test("officer dashboard filters institutions and reports freshness as stale after another scope activates", async ({
  page,
  request,
}) => {
  const year = "2100-01";
  const cedar = await activateSnapshot(request, "cedar_admin", year);
  const officerLogin = await request.post(`${API_URL}/auth/demo-login`, {
    data: { demo_alias: "demo_officer" },
  });
  const officerHeaders = {
    Authorization: `Bearer ${(await officerLogin.json()).access_token}`,
  };
  const revalidated = await request.post(
    `${API_URL}/submissions/${cedar.batchId}/revalidate`,
    { headers: officerHeaders },
  );
  expect(revalidated.status()).toBe(201);
  const run = await revalidated.json();
  expect(run.cross_current_freshness).toBe("FRESH");
  await activateSnapshot(request, "maple_admin", year);

  await signIn(page, "Demo AICTE officer");
  await applyYear(page, year);
  await expect(
    page.getByRole("heading", { name: "Institution dashboard" }),
  ).toBeVisible();
  await expect(
    page.getByRole("row").filter({ hasText: "Demo Cedar Institute" }),
  ).toContainText("Stale");
  await expect(page.getByText("overlap metrics are never zero")).toBeVisible();
  await page.getByLabel("Region").selectOption({ index: 1 });
  const institutionOptions = await page
    .getByLabel("Institution")
    .locator("option")
    .allTextContents();
  expect(institutionOptions.length).toBeGreaterThan(1);
  const cedarOption = await page
    .getByLabel("Institution")
    .locator("option")
    .filter({ hasText: "Cedar" })
    .getAttribute("value");
  expect(cedarOption).toBeTruthy();
  await page
    .locator(".dashboard-filters")
    .getByLabel("Institution")
    .selectOption(cedarOption!);
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(
    page.getByRole("row").filter({ hasText: "Demo Cedar Institute" }),
  ).toBeVisible();
  await expect(
    page.getByRole("row").filter({ hasText: "Demo Maple Institute" }),
  ).toHaveCount(0);
});

test("manager dashboard uses aggregate APIs only and never requests submissions", async ({
  page,
}) => {
  let submissionRequests = 0;
  await page.route("**/api/v1/submissions**", async (route) => {
    submissionRequests += 1;
    await route.abort();
  });
  await signIn(page, "Demo AICTE manager");
  await applyYear(page, "2026-27");
  await expect(
    page.getByRole("heading", { name: "Aggregate overview" }),
  ).toBeVisible();
  await expect(page.getByText("Aggregate access boundary")).toBeVisible();
  await expect(page.getByText("Fictional Student One")).toHaveCount(0);
  await expect(page.getByRole("link", { name: /submission/i })).toHaveCount(0);
  await page.getByLabel("Region").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.getByRole("row").first()).toBeVisible();
  expect(submissionRequests).toBe(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", 390);
  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);
});
