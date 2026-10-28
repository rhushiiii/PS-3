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
import { fail, signIn } from "./helpers";

const fixture = readFileSync(resolve("../../samples/synthetic_validation.csv"));
const cleanFixture = readFileSync(
  resolve("../../samples/synthetic_snapshot_initial.csv"),
);

async function adminContext(request: APIRequestContext) {
  const login = await request.post(API_URL + "/auth/demo-login", {
    data: { demo_alias: "cedar_admin" },
  });
  const headers = {
    Authorization: `Bearer ${(await login.json()).access_token}`,
  };
  const identity = await (
    await request.get(API_URL + "/me", { headers })
  ).json();
  const programmes = await (
    await request.get(
      API_URL + `/institutions/${identity.institution_id}/programmes`,
      { headers },
    )
  ).json();
  const programme = programmes.data.find(
    (item: { code: string }) => item.code === "DEMO-COMP",
  );
  return {
    headers,
    institutionId: identity.institution_id as string,
    programmeId: programme.id as string,
  };
}

async function uploadCandidate(
  request: APIRequestContext,
  year: string,
  source = fixture,
) {
  const account = await adminContext(request);
  const content = Buffer.from(source.toString().replaceAll("2026-27", year));
  const response = await request.post(API_URL + "/submissions", {
    headers: account.headers,
    multipart: {
      institution_id: account.institutionId,
      programme_id: account.programmeId,
      academic_year: year,
      schema_version: "v1",
      file: {
        name: "synthetic_validation.csv",
        mimeType: "text/csv",
        buffer: content,
      },
    },
  });
  expect(response.status()).toBe(201);
  return { ...account, batchId: (await response.json()).id as string };
}

async function openCandidate(
  page: Page,
  batchId: string,
  year: string,
  role: "admin" | "officer",
) {
  if (role === "officer") {
    await page
      .getByRole("link", { name: "View Demo Cedar Institute", exact: true })
      .click();
    await page
      .getByRole("link", { name: "View submission history", exact: true })
      .click();
  } else {
    const mobile = (await page.evaluate(() => window.innerWidth)) <= 760;
    if (mobile)
      await page.getByRole("button", { name: "Open navigation" }).click();
    const navigation = mobile ? page.getByRole("dialog") : page;
    await navigation
      .getByRole("link", { name: "Submissions", exact: true })
      .click();
  }
  await page
    .getByRole("textbox", { name: "Academic year", exact: true })
    .fill(year);
  await page.getByRole("button", { name: "Apply filters" }).click();
  const row = page.getByRole("row").filter({ hasText: batchId.slice(0, 8) });
  await expect(row).toBeVisible();
  await row
    .getByRole("link", { name: /Open candidate|View validation/ })
    .click();
}

async function validateInUi(page: Page, batchId: string, year: string) {
  await openCandidate(page, batchId, year, "admin");
  await expect(
    page.getByRole("heading", { name: "Student validation" }),
  ).toBeVisible();
  const post = page.waitForResponse(
    (response) =>
      response.url() === `${API_URL}/submissions/${batchId}/validate` &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Run Validation" }).click();
  const response = await post;
  expect(response.status()).toBe(201);
  return (await response.json()).id as string;
}

test("institution admin runs local validation, selects it in URL and downloads masked feedback", async ({
  page,
  request,
}) => {
  const { batchId } = await uploadCandidate(request, "2041-42");
  await signIn(page);
  const runId = await validateInUi(page, batchId, "2041-42");
  await expect(page).toHaveURL(new RegExp(`run_id=${runId}`));
  await expect(
    page.getByRole("heading", { name: "Run summary" }),
  ).toBeVisible();
  await expect(page.getByText("LOCAL-DEMO-v1").first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Student records" }),
  ).toBeVisible();
  await expect(page.getByRole("table").getByText("Record 2")).toBeVisible();
  await expect(
    page
      .getByRole("table")
      .getByText(/\*+0001/)
      .first(),
  ).toBeVisible();
  await expect(page.getByRole("main")).not.toContainText("900000000001");
  await expect(page.getByRole("main")).toContainText(
    "not government identity verification",
  );
  await expect(page.getByRole("heading", { name: "Findings" })).toBeVisible();
  const blockingFinding = page
    .locator(".finding-card")
    .filter({
      hasText: "Activation-blocking",
    })
    .first();
  await expect(blockingFinding).toBeVisible();

  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download masked feedback CSV" })
    .click();
  const file = await download;
  expect(file.suggestedFilename()).toMatch(
    /^(feedback-[a-f0-9-]+|validation-feedback)\.csv$/i,
  );
  const stream = await file.createReadStream();
  if (!stream) throw new Error("Feedback export stream was unavailable");
  let csv = "";
  for await (const chunk of stream) csv += chunk.toString();
  expect(csv).toContain("apaar_id_masked");
  expect(csv).not.toContain("900000000001");

  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await signIn(page, "Demo AICTE manager");
  await expect(page.getByRole("main")).not.toContainText(
    "Fictional Student One",
  );
  await expect(
    page.getByRole("link", { name: "Submissions", exact: true }),
  ).toHaveCount(0);
});

test("officer appends a new run, history selection is immutable and filters stay in the URL", async ({
  page,
  request,
}) => {
  const { batchId, headers } = await uploadCandidate(request, "2042-43");
  const initialResponse = await request.post(
    API_URL + `/submissions/${batchId}/validate`,
    { headers },
  );
  expect(initialResponse.status()).toBe(201);
  const initial = await initialResponse.json();
  await signIn(page, "Demo AICTE officer");
  await openCandidate(page, batchId, "2042-43", "officer");
  await expect(page).toHaveURL(new RegExp(`run_id=${initial.id}`));
  await expect(
    page.getByRole("button", { name: "Run officer revalidation" }),
  ).toBeVisible();
  const revalidate = page.waitForResponse(
    (response) =>
      response.url() === `${API_URL}/submissions/${batchId}/revalidate` &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Run officer revalidation" }).click();
  expect((await revalidate).status()).toBe(201);
  await expect(page).toHaveURL(/run_id=/);
  const oldRun = page
    .getByRole("button", { name: /Initial validation/ })
    .first();
  await expect(oldRun).toBeVisible();
  await oldRun.click();
  await expect(page).toHaveURL(new RegExp(`run_id=${initial.id}`));
  await page.getByLabel("Filter by rule code").fill("INVALID_APAAR_FORMAT");
  await page.getByRole("button", { name: "Apply rule filter" }).click();
  await expect(page).toHaveURL(/finding_rule=INVALID_APAAR_FORMAT/);
  await page.getByLabel("Severity").selectOption("WARNING");
  await expect(page).toHaveURL(/finding_severity=WARNING/);
  await page.getByLabel("Issue type").selectOption("REVIEWABLE");
  await expect(page).toHaveURL(/finding_classification=REVIEWABLE/);
  await expect(page.getByRole("heading", { name: "Findings" })).toBeVisible();
  await expect(page.getByText("Potential current ACTIVE overlap")).toHaveCount(
    0,
  );
});

test("manager cannot inspect student validation via the interface or API", async ({
  page,
  request,
}) => {
  const { batchId } = await uploadCandidate(request, "2043-44");
  const admin = await request.post(API_URL + "/auth/demo-login", {
    data: { demo_alias: "cedar_admin" },
  });
  const token = (await admin.json()).access_token as string;
  const validation = await request.post(
    API_URL + `/submissions/${batchId}/validate`,
    {
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  expect(validation.status()).toBe(201);
  const manager = await request.post(API_URL + "/auth/demo-login", {
    data: { demo_alias: "demo_manager" },
  });
  const managerHeaders = {
    Authorization: `Bearer ${(await manager.json()).access_token}`,
  };
  const denied = await request.get(
    API_URL + `/submissions/${batchId}/validation-runs`,
    { headers: managerHeaders },
  );
  expect(denied.status()).toBe(403);
  await signIn(page, "Demo AICTE manager");
  await page.goto(`/submissions/${batchId}`);
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByText("Fictional Student One")).toHaveCount(0);
});

test("validation network uncertainty is not retried and remains explicit on mobile", async ({
  page,
  request,
}) => {
  const { batchId } = await uploadCandidate(request, "2044-45");
  await signIn(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await openCandidate(page, batchId, "2044-45", "admin");
  let postCount = 0;
  await page.route(`**/submissions/${batchId}/validate`, async (route) => {
    postCount += 1;
    await route.abort("failed");
  });
  await page.getByRole("button", { name: "Run Validation" }).click();
  await expect(page.getByRole("status")).toContainText("outcome is unknown");
  expect(postCount).toBe(1);
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", 390);
  await expect(page.getByRole("main")).not.toContainText("900000000001");
});

test("controlled validation configuration rejection is distinct from an unknown outcome", async ({
  page,
  request,
}) => {
  const { batchId } = await uploadCandidate(request, "2046-47");
  await signIn(page);
  await openCandidate(page, batchId, "2046-47", "admin");
  let postCount = 0;
  await page.route(`**/submissions/${batchId}/validate`, async (route) => {
    postCount += 1;
    await fail(route, 422, "MATCHING_CONFIGURATION_UNAVAILABLE");
  });
  await page.getByRole("button", { name: "Run Validation" }).click();
  await expect(
    page.locator(".validation-action").getByRole("alert"),
  ).toContainText("server's APAAR matching configuration is unavailable");
  await expect(page.getByRole("status")).not.toContainText(
    "outcome is unknown",
  );
  expect(postCount).toBe(1);
});

test("stale cross-institution assessment is unavailable, never shown as zero", async ({
  page,
  request,
}) => {
  const account = await adminContext(request);
  const first = await uploadCandidate(request, "2045-46", cleanFixture);
  const validateAndActivate = async (batchId: string) => {
    const runResponse = await request.post(
      API_URL + `/submissions/${batchId}/validate`,
      { headers: account.headers },
    );
    expect(runResponse.status()).toBe(201);
    const run = await runResponse.json();
    const reviewResponse = await request.post(
      API_URL + `/submissions/${batchId}/reviews`,
      {
        headers: account.headers,
        data: { validation_run_id: run.id },
      },
    );
    expect(reviewResponse.status()).toBe(201);
    const receipt = await reviewResponse.json();
    const activation = await request.post(
      API_URL + `/submissions/${batchId}/activate`,
      {
        headers: account.headers,
        data: {
          review_id: receipt.id,
          expected_scope_revision: receipt.expected_scope_revision,
          confirm_complete_replacement: true,
          acknowledge_review_warnings: true,
          acknowledge_omissions: true,
        },
      },
    );
    expect(activation.status()).toBe(200);
    return run.id as string;
  };

  const firstRun = await validateAndActivate(first.batchId);
  const second = await uploadCandidate(request, "2045-46", cleanFixture);
  await validateAndActivate(second.batchId);
  const currentState = await request.get(
    API_URL + `/submissions/${first.batchId}/validation-runs/${firstRun}`,
    { headers: account.headers },
  );
  expect(currentState.status()).toBe(200);
  expect((await currentState.json()).current_overlap_records).toBeNull();

  await signIn(page, "Demo AICTE officer");
  await openCandidate(page, first.batchId, "2045-46", "officer");
  await expect(page).toHaveURL(new RegExp(`run_id=${firstRun}`));
  await expect(page.locator(".validation-metrics")).toContainText(
    "Assessment is stale; this is not zero.",
  );
  await expect(page.getByText("Unavailable", { exact: true })).toBeVisible();
});
