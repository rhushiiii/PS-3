import {
  expect,
  test,
  type APIRequestContext,
  type Page,
} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { API_URL, WEB_URL } from "./setup";
import { signIn } from "./helpers";

const initialCsv = readFileSync(
  resolve("../../samples/synthetic_snapshot_initial.csv"),
);
const replacementCsv = readFileSync(
  resolve("../../samples/synthetic_snapshot_replacement.csv"),
);
const blockedCsv = readFileSync(
  resolve("../../samples/synthetic_validation.csv"),
);

async function admin(request: APIRequestContext) {
  const login = await request.post(`${API_URL}/auth/demo-login`, {
    data: { demo_alias: "cedar_admin" },
  });
  const headers = {
    Authorization: `Bearer ${(await login.json()).access_token}`,
  };
  const identity = await (
    await request.get(`${API_URL}/me`, { headers })
  ).json();
  const programmes = await (
    await request.get(
      `${API_URL}/institutions/${identity.institution_id}/programmes`,
      { headers },
    )
  ).json();
  const programme = programmes.data.find(
    (entry: { code: string }) => entry.code === "DEMO-COMP",
  );
  return {
    headers,
    institutionId: identity.institution_id as string,
    programmeId: programme.id as string,
  };
}

async function upload(
  request: APIRequestContext,
  year: string,
  source: Buffer,
) {
  const account = await admin(request);
  const content = Buffer.from(source.toString().replaceAll("2026-27", year));
  const response = await request.post(`${API_URL}/submissions`, {
    headers: account.headers,
    multipart: {
      institution_id: account.institutionId,
      programme_id: account.programmeId,
      academic_year: year,
      schema_version: "v1",
      file: {
        name: "synthetic_snapshot.csv",
        mimeType: "text/csv",
        buffer: content,
      },
    },
  });
  expect(response.status()).toBe(201);
  return { ...account, batchId: (await response.json()).id as string };
}

async function validate(
  request: APIRequestContext,
  batchId: string,
  headers: Record<string, string>,
) {
  const response = await request.post(
    `${API_URL}/submissions/${batchId}/validate`,
    { headers },
  );
  expect(response.status()).toBe(201);
  return (await response.json()).id as string;
}

async function createReview(
  request: APIRequestContext,
  batchId: string,
  runId: string,
  headers: Record<string, string>,
) {
  const response = await request.post(
    `${API_URL}/submissions/${batchId}/reviews`,
    {
      headers,
      data: { validation_run_id: runId },
    },
  );
  expect(response.status()).toBe(201);
  return (await response.json()).id as string;
}

async function activate(
  request: APIRequestContext,
  batchId: string,
  runId: string,
  headers: Record<string, string>,
) {
  const reviewId = await createReview(request, batchId, runId, headers);
  const review = await (
    await request.get(`${API_URL}/submissions/${batchId}/reviews/${reviewId}`, {
      headers,
    })
  ).json();
  const response = await request.post(
    `${API_URL}/submissions/${batchId}/activate`,
    {
      headers,
      data: {
        review_id: reviewId,
        expected_scope_revision: review.expected_scope_revision,
        confirm_complete_replacement: true,
        acknowledge_review_warnings: true,
        acknowledge_omissions: true,
      },
    },
  );
  expect(response.status()).toBe(200);
  return reviewId;
}

async function openSubmission(page: Page, year: string, batchId: string) {
  const mobile = (await page.evaluate(() => innerWidth)) <= 760;
  if (mobile)
    await page.getByRole("button", { name: "Open navigation" }).click();
  const nav = mobile ? page.getByRole("dialog") : page;
  await nav.getByRole("link", { name: "Submissions", exact: true }).click();
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

test("institution completes upload, validation, review and current dashboard update", async ({
  page,
}) => {
  const year = "2095-96";
  await signIn(page);
  await page
    .getByRole("link", { name: "Upload candidate", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Programme", exact: true })
    .selectOption({ label: "DEMO-COMP — Demo Computing" });
  await page.getByRole("textbox", { name: /Academic year/ }).fill(year);
  await page.getByLabel("Synthetic student CSV").setInputFiles({
    name: "synthetic_snapshot.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(initialCsv.toString().replaceAll("2026-27", year)),
  });
  await page
    .getByRole("checkbox", { name: /synthetic student records only/ })
    .check();
  const uploadResponse = page.waitForResponse(
    (response) =>
      response.url() === `${API_URL}/submissions` &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Upload candidate" }).click();
  const stored = await uploadResponse;
  expect(stored.status()).toBe(201);
  const batchId = (await stored.json()).id as string;
  await expect(
    page.getByRole("heading", { name: "Candidate stored" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "View submission history", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Academic year", exact: true })
    .fill(year);
  await page.getByRole("button", { name: "Apply filters" }).click();
  const candidateRow = page
    .getByRole("row")
    .filter({ hasText: batchId.slice(0, 8) });
  await expect(candidateRow).toBeVisible();
  await candidateRow
    .getByRole("link", { name: /Open candidate|View validation/ })
    .click();
  await expect(
    page.getByRole("heading", { name: "Student validation" }),
  ).toBeVisible();
  const validationResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith("/validate") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Run Validation" }).click();
  expect((await validationResponse).status()).toBe(201);
  await expect(
    page.getByRole("heading", { name: "Review candidate snapshot" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Create review receipt" }).click();
  await expect(
    page.getByRole("heading", { name: "Review replacement snapshot" }),
  ).toBeVisible();
  await page.getByLabel(/complete replacement declaration/).check();
  const warningAcknowledgment = page.getByLabel(
    /reviewed the APAAR, possible duplicate/,
  );
  if (await warningAcknowledgment.isVisible())
    await warningAcknowledgment.check();
  const activation = page.waitForResponse(
    (response) =>
      response.url().endsWith("/activate") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Activate this snapshot" }).click();
  expect((await activation).status()).toBe(200);
  await expect(page.getByText("Current snapshot activated")).toBeVisible();
  await page.getByRole("link", { name: "Dashboard", exact: true }).click();
  await page.getByRole("textbox", { name: "Academic year" }).fill(year);
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(
    page.getByText("Current declared records").locator(".."),
  ).toContainText("3");
  await expect(
    page.getByText("Demo ACTIVE enrolments").locator(".."),
  ).toContainText("3");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test("institution admin reviews omissions and activates only after all explicit acknowledgments", async ({
  page,
  request,
}) => {
  const year = "2091-92";
  const account = await admin(request);
  const first = await upload(request, year, initialCsv);
  const firstRun = await validate(request, first.batchId, account.headers);
  await activate(request, first.batchId, firstRun, account.headers);

  const candidate = await upload(request, year, replacementCsv);
  const runId = await validate(request, candidate.batchId, candidate.headers);
  await signIn(page);
  await openSubmission(page, year, candidate.batchId);
  await expect(page).toHaveURL(new RegExp(`run_id=${runId}`));
  await expect(
    page.getByRole("heading", { name: "Review candidate snapshot" }),
  ).toBeVisible();

  const create = page.getByRole("button", { name: "Create review receipt" });
  const createdResponse = page.waitForResponse(
    (response) =>
      response.url() ===
        `${API_URL}/submissions/${candidate.batchId}/reviews` &&
      response.request().method() === "POST",
  );
  await create.click();
  expect((await createdResponse).status()).toBe(201);
  await expect(page).toHaveURL(/review_id=/);
  const reviewId = new URL(page.url()).searchParams.get("review_id");
  expect(reviewId).toBeTruthy();
  await expect(
    page.getByRole("heading", { name: "Review replacement snapshot" }),
  ).toBeVisible();
  await expect(page).toHaveURL(new RegExp(`review_id=${reviewId}`));
  await expect(page.getByText("Current declared records")).toBeVisible();
  await expect(page.getByText("Candidate declared records")).toBeVisible();
  await expect(page.getByText("Previously ACTIVE omissions")).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Omitted student identifiers" }),
  ).toContainText("DEMO-003");
  await expect(
    page.getByText("Category changes among retained records"),
  ).toBeVisible();
  await expect(
    page.getByText("Reviewable findings", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/not official identity verification/),
  ).toBeVisible();
  const action = page.getByRole("button", { name: "Activate this snapshot" });
  await expect(action).toBeDisabled();
  const complete = page.getByLabel(/complete replacement declaration/);
  const warnings = page.getByLabel(/reviewed the APAAR, possible duplicate/);
  const omissions = page.getByLabel(/I acknowledge 1 omitted record/);
  await expect(complete).not.toBeChecked();
  await expect(warnings).not.toBeChecked();
  await expect(omissions).not.toBeChecked();
  await complete.check();
  await warnings.check();
  await expect(action).toBeDisabled();
  await omissions.check();
  await expect(action).toBeEnabled();
  await expect(page.getByLabel("Exact activation target")).toContainText(runId);

  const activated = page.waitForResponse(
    (response) =>
      response.url() ===
        `${API_URL}/submissions/${candidate.batchId}/activate` &&
      response.request().method() === "POST",
  );
  await action.click();
  expect((await activated).status()).toBe(200);
  await expect(page.getByRole("status")).toContainText(
    "Current snapshot activated",
  );
  const batch = await (
    await request.get(`${API_URL}/submissions/${candidate.batchId}`, {
      headers: candidate.headers,
    })
  ).json();
  expect(batch.snapshot_state).toBe("CURRENT");
  const oldBatch = await (
    await request.get(`${API_URL}/submissions/${first.batchId}`, {
      headers: account.headers,
    })
  ).json();
  expect(oldBatch.snapshot_state).toBe("PREVIOUS");
  expect(batch.activation_provenance.review_id).toBe(reviewId);
  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);
});

test("structural blockers are visible and prevent activation", async ({
  page,
  request,
}) => {
  const year = "2092-93";
  const candidate = await upload(request, year, blockedCsv);
  const runId = await validate(request, candidate.batchId, candidate.headers);
  await signIn(page);
  await openSubmission(page, year, candidate.batchId);
  await page.getByRole("button", { name: "Create review receipt" }).click();
  await expect(
    page.getByRole("heading", { name: "Review replacement snapshot" }),
  ).toBeVisible();
  await expect(
    page.getByText("Activation-blocking structural findings"),
  ).toBeVisible();
  await expect(page.getByText(/blocked/i).first()).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Activate this snapshot" }),
  ).toBeDisabled();
  const receipt = await (
    await request.get(
      `${API_URL}/submissions/${candidate.batchId}/reviews/${new URL(page.url()).searchParams.get("review_id")}`,
      { headers: candidate.headers },
    )
  ).json();
  expect(receipt.validation_run_id).toBe(runId);
  expect(receipt.review_state).toBe("BLOCKED");
});

test("lost activation response is reconciled from provenance without an automatic second POST", async ({
  page,
  request,
}) => {
  const year = "2093-94";
  const candidate = await upload(request, year, initialCsv);
  await validate(request, candidate.batchId, candidate.headers);
  await signIn(page);
  await openSubmission(page, year, candidate.batchId);
  await page.getByRole("button", { name: "Create review receipt" }).click();
  await expect(
    page.getByRole("heading", { name: "Review replacement snapshot" }),
  ).toBeVisible();
  await page.getByLabel(/complete replacement declaration/).check();
  await page.getByLabel(/reviewed the APAAR, possible duplicate/).check();
  let posts = 0;
  await page.route(
    `**/submissions/${candidate.batchId}/activate`,
    async (route) => {
      posts += 1;
      await route.fetch();
      await route.fulfill({
        status: 502,
        headers: {
          "access-control-allow-origin": WEB_URL,
          "content-type": "application/json",
        },
        body: JSON.stringify({
          error: {
            code: "UPSTREAM_UNAVAILABLE",
            message: "Synthetic response lost after commit",
            request_id: "demo-request",
          },
        }),
      });
    },
  );
  await page.getByRole("button", { name: "Activate this snapshot" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Current snapshot activated",
  );
  expect(posts).toBe(1);
  const batch = await (
    await request.get(`${API_URL}/submissions/${candidate.batchId}`, {
      headers: candidate.headers,
    })
  ).json();
  expect(batch.snapshot_state).toBe("CURRENT");
});

test("officers can inspect activated receipts but do not receive activation controls", async ({
  page,
  request,
}) => {
  const year = "2094-95";
  const candidate = await upload(request, year, initialCsv);
  const runId = await validate(request, candidate.batchId, candidate.headers);
  const reviewId = await activate(
    request,
    candidate.batchId,
    runId,
    candidate.headers,
  );
  await signIn(page, "Demo AICTE officer");
  await page
    .getByRole("link", { name: "View Demo Cedar Institute", exact: true })
    .click();
  await page
    .getByRole("link", { name: "View submission history", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Academic year", exact: true })
    .fill(year);
  await page.getByRole("button", { name: "Apply filters" }).click();
  await page
    .getByRole("row")
    .filter({ hasText: candidate.batchId.slice(0, 8) })
    .getByRole("link", { name: "View validation" })
    .click();
  await expect(page).toHaveURL(new RegExp(`review_id=${reviewId}`));
  await expect(
    page.getByRole("heading", { name: "Review replacement snapshot" }),
  ).toBeVisible();
  await expect(page.getByText("Current snapshot activated")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Activate this snapshot" }),
  ).toHaveCount(0);
  const receipt = await (
    await request.get(
      `${API_URL}/submissions/${candidate.batchId}/reviews/${reviewId}`,
      { headers: candidate.headers },
    )
  ).json();
  const officerLogin = await request.post(`${API_URL}/auth/demo-login`, {
    data: { demo_alias: "demo_officer" },
  });
  const officerHeaders = {
    Authorization: `Bearer ${(await officerLogin.json()).access_token}`,
  };
  const deniedActivation = await request.post(
    `${API_URL}/submissions/${candidate.batchId}/activate`,
    {
      headers: officerHeaders,
      data: {
        review_id: reviewId,
        expected_scope_revision: receipt.expected_scope_revision,
        confirm_complete_replacement: true,
        acknowledge_review_warnings: true,
        acknowledge_omissions: false,
      },
    },
  );
  expect(deniedActivation.status()).toBe(403);
  const managerLogin = await request.post(`${API_URL}/auth/demo-login`, {
    data: { demo_alias: "demo_manager" },
  });
  const managerHeaders = {
    Authorization: `Bearer ${(await managerLogin.json()).access_token}`,
  };
  const deniedRead = await request.get(
    `${API_URL}/submissions/${candidate.batchId}/reviews/${reviewId}`,
    { headers: managerHeaders },
  );
  expect(deniedRead.status()).toBe(403);
});

test("a concurrent scope change makes the receipt stale and clears confirmation", async ({
  page,
  request,
}) => {
  const year = "2096-97";
  const candidate = await upload(request, year, initialCsv);
  const runId = await validate(request, candidate.batchId, candidate.headers);
  await signIn(page);
  await openSubmission(page, year, candidate.batchId);
  await page.getByRole("button", { name: "Create review receipt" }).click();
  await expect(
    page.getByRole("heading", { name: "Review replacement snapshot" }),
  ).toBeVisible();
  await page.getByLabel(/complete replacement declaration/).check();
  await page.getByLabel(/reviewed the APAAR, possible duplicate/).check();

  const competing = await upload(request, year, initialCsv);
  const competingRun = await validate(
    request,
    competing.batchId,
    competing.headers,
  );
  await activate(request, competing.batchId, competingRun, competing.headers);

  const activation = page.waitForResponse(
    (response) =>
      response.url() ===
        `${API_URL}/submissions/${candidate.batchId}/activate` &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Activate this snapshot" }).click();
  expect((await activation).status()).toBe(409);
  await expect(
    page.locator(".review-subsection").last().getByRole("alert"),
  ).toContainText("current snapshot changed since this review");
  await expect(
    page.getByLabel(/complete replacement declaration/),
  ).not.toBeChecked();
  await expect(
    page.getByLabel(/reviewed the APAAR, possible duplicate/),
  ).not.toBeChecked();
  const freshButton = page.getByRole("button", {
    name: "Create a fresh review from the selected run",
  });
  await expect(freshButton).toBeVisible();
  const fresh = page.waitForResponse(
    (response) =>
      response.url() ===
        `${API_URL}/submissions/${candidate.batchId}/reviews` &&
      response.request().method() === "POST",
  );
  await freshButton.click();
  expect((await fresh).status()).toBe(201);
  await expect(page).toHaveURL(/review_id=/);
  expect(new URL(page.url()).searchParams.get("run_id")).toBe(runId);
  await expect(
    page.getByRole("button", { name: "Activate this snapshot" }),
  ).toBeDisabled();
});

test("activation controls and comparison fit mobile width and remain accessible", async ({
  page,
  request,
}) => {
  const year = "2095-96";
  const candidate = await upload(request, year, initialCsv);
  await validate(request, candidate.batchId, candidate.headers);
  await signIn(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await openSubmission(page, year, candidate.batchId);
  await page.getByRole("button", { name: "Create review receipt" }).click();
  await expect(
    page.getByRole("heading", { name: "Review replacement snapshot" }),
  ).toBeVisible();
  await expect(page.locator("body")).toHaveJSProperty("scrollWidth", 390);
  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);
});
