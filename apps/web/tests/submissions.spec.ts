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
import { ApiError } from "../src/lib/api/client";
import {
  templateCSV,
  uploadError,
} from "../src/features/submissions/upload-state";
import { validAcademicYear } from "../src/features/submissions/data";
import type { components } from "../src/lib/api/generated";

const admission = readFileSync(
  resolve("../../samples/synthetic_admissions.csv"),
);
const initial = readFileSync(
  resolve("../../samples/synthetic_snapshot_initial.csv"),
);
type Policy = components["schemas"]["UploadPolicyResponse"];

function csv(year: string, code = "DEMO-COMP", source = admission): Buffer {
  return Buffer.from(
    source.toString().replaceAll("2026-27", year).replaceAll("DEMO-COMP", code),
  );
}

async function openUpload(page: Page, year = "2026-27") {
  await page
    .getByRole("link", { name: "Upload candidate", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "CSV requirements" }),
  ).toBeVisible();
  await expect(
    page.getByText("5,242,880 bytes", { exact: true }),
  ).toBeVisible();
  await fillUpload(page, year);
}

async function fillUpload(page: Page, year: string, buffer = csv(year)) {
  await page
    .getByRole("combobox", { name: "Programme", exact: true })
    .selectOption({ label: "DEMO-COMP — Demo Computing" });
  await page.getByRole("textbox", { name: /Academic year/ }).fill(year);
  await page
    .getByLabel("Synthetic student CSV")
    .setInputFiles({ name: "synthetic.csv", mimeType: "text/csv", buffer });
  await page
    .getByRole("checkbox", { name: /synthetic student records only/ })
    .check();
}

async function apiAccount(request: APIRequestContext, alias = "cedar_admin") {
  const login = await request.post(API_URL + "/auth/demo-login", {
    data: { demo_alias: alias },
  });
  expect(login.status()).toBe(200);
  const headers = {
    Authorization: `Bearer ${(await login.json()).access_token}`,
  };
  const me = await (await request.get(API_URL + "/me", { headers })).json();
  const programmes = await (
    await request.get(
      API_URL + `/institutions/${me.institution_id}/programmes`,
      { headers },
    )
  ).json();
  const programme = programmes.data.find(
    (item: { code: string }) => item.code === "DEMO-COMP",
  );
  return {
    headers,
    institutionId: me.institution_id as string,
    programmeId: programme.id as string,
  };
}

async function store(
  request: APIRequestContext,
  account: Awaited<ReturnType<typeof apiAccount>>,
  year: string,
  code = "DEMO-COMP",
  buffer = csv(year, code),
) {
  const response = await request.post(API_URL + "/submissions", {
    headers: account.headers,
    multipart: {
      institution_id: account.institutionId,
      programme_id: account.programmeId,
      academic_year: year,
      schema_version: "v1",
      file: { name: "synthetic.csv", mimeType: "text/csv", buffer },
    },
  });
  expect(response.status()).toBe(201);
  return (await response.json()).id as string;
}

async function capture(page: Page, filename: string) {
  // Axe/previous interactions may leave a focused skip link or a scrolled viewport.
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement)
      document.activeElement.blur();
    window.scrollTo(0, 0);
  });
  await page.screenshot({
    path: resolve(`../../.local/${filename}`),
    fullPage: true,
    caret: "initial",
  });
}

test("uncertain uploads are never described as confirmed rejection", () => {
  for (const error of [
    new Error("private CSV value"),
    new ApiError(0, "NETWORK_UNAVAILABLE"),
    new ApiError(408, "UPLOAD_TIMEOUT"),
    new ApiError(500, "DATABASE_ERROR"),
    new ApiError(503, "DATABASE_UNAVAILABLE"),
    new ApiError(201, "INVALID_RESPONSE"),
  ]) {
    expect(uploadError(error).uncertain).toBe(true);
    expect(uploadError(error).message).not.toContain("private CSV value");
  }
  expect(uploadError(new ApiError(422, "ROW_LIMIT_EXCEEDED"))).toMatchObject({
    uncertain: false,
  });
  expect(
    uploadError(new ApiError(422, "ROW_LIMIT_EXCEEDED")).message,
  ).toContain("Do not split");
  expect(templateCSV(["first", "second"])).toBe("first,second\r\n");
  expect(validAcademicYear("2026-27")).toBe(true);
  expect(validAcademicYear("2099-00")).toBe(true);
  for (const year of ["2026-28", "26-27", "2026/27", " 2026-27", "2026-270"])
    expect(validAcademicYear(year)).toBe(false);
});

test("real upload, header-only template, duplicate versions and masked history", async ({
  page,
  request,
}) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await signIn(page);
  await openUpload(page, "2031-32");
  await expect(page.getByText(/all admission categories/)).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Download strict-v1 template" })
    .click();
  const stream = await (await downloadPromise).createReadStream();
  if (!stream) throw new Error("Missing template download");
  let template = "";
  for await (const chunk of stream) template += chunk.toString();
  expect(template.trim()).toBe(admission.toString().split(/\r?\n/)[0]);
  expect(template.trim().split(/\r?\n/)).toHaveLength(1);
  const firstResponse = page.waitForResponse(
    (response) =>
      response.url() === API_URL + "/submissions" &&
      response.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  const first = await (await firstResponse).json();
  await expect(
    page.getByRole("heading", { name: "Candidate stored" }),
  ).toBeVisible();
  await expect(
    page.getByRole("status").filter({ hasText: "Candidate stored" }),
  ).toContainText("unvalidated");
  await page.getByRole("button", { name: "Prepare another upload" }).click();
  await fillUpload(page, "2031-32");
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByText(/Repeated file detected/)).toBeVisible();
  await page
    .getByRole("link", { name: "View submission history", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Academic year", exact: true })
    .fill("2031-32");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(3);
  await expect(
    page.getByRole("table").getByText("Candidate", { exact: true }),
  ).toHaveCount(2);
  await expect(page.getByText("Repeated file · separate upload")).toHaveCount(
    2,
  );
  await expect(page.getByRole("main")).not.toContainText("900000000001");
  await expect(page.getByRole("main")).not.toContainText(
    "DEMO-MALFORMED-APAAR",
  );
  expect(errors.join(" ")).not.toContain("900000000001");
  const account = await apiAccount(request);
  const detail = await (
    await request.get(API_URL + `/submissions/${first.id}`, {
      headers: account.headers,
    })
  ).json();
  expect(detail.snapshot_state).toBe("CANDIDATE");
  expect(detail.is_current).toBe(false);
  expect(detail.validation_performed).toBe(false);
});

test("real history pagination, programme/year filters and provenance", async ({
  page,
  request,
}) => {
  const account = await apiAccount(request);
  const identifiers = [];
  for (let index = 0; index < 11; index++)
    identifiers.push(await store(request, account, "2032-33"));
  await signIn(page);
  await page.getByRole("link", { name: "Submissions", exact: true }).click();
  const historyRegion = page.getByRole("region", {
    name: /Submission history/,
  });
  await expect(historyRegion.getByRole("table")).toBeVisible();
  const yearField = page.getByRole("textbox", {
    name: "Academic year",
    exact: true,
  });
  await yearField.fill("2032-33");
  await expect(yearField).toHaveValue("2032-33");
  await page
    .getByRole("combobox", { name: "Programme", exact: true })
    .selectOption({ label: "DEMO-COMP — Demo Computing" });
  const filteredHistory = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/submissions" &&
      url.searchParams.get("academic_year") === "2032-33" &&
      url.searchParams.has("programme_id")
    );
  });
  await page.getByRole("button", { name: "Apply filters" }).click();
  await filteredHistory;
  await expect(yearField).toHaveValue("2032-33");
  await expect(historyRegion.getByRole("table").getByRole("row")).toHaveCount(
    11,
  );
  await expect(page.getByText("Page 1 of 2")).toBeVisible();
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(historyRegion.getByRole("table").getByRole("row")).toHaveCount(
    2,
  );
  await expect(page.getByText("Page 2 of 2")).toBeVisible();
  await page.getByRole("button", { name: /Show provenance/ }).click();
  await expect(
    page.getByRole("definition").filter({ hasText: identifiers[0] }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Programme", exact: true })
    .selectOption({ label: "DEMO-ELEC — Demo Electronics" });
  const noProgrammeHistory = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/submissions" &&
      url.searchParams.get("academic_year") === "2032-33" &&
      url.searchParams.has("programme_id")
    );
  });
  await page.getByRole("button", { name: "Apply filters" }).click();
  await noProgrammeHistory;
  await expect(
    page.getByRole("heading", { name: "No submissions found" }),
  ).toBeVisible();
  await expect(page.getByText("Page 1 of 1")).toBeVisible();
});

test("client checks invalid context and configured size without sending uploads", async ({
  page,
}) => {
  await signIn(page);
  await openUpload(page);
  let posts = 0;
  page.on("request", (request) => {
    if (
      request.url() === API_URL + "/submissions" &&
      request.method() === "POST"
    )
      posts++;
  });
  await page.getByRole("textbox", { name: /Academic year/ }).fill("2026-28");
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "consecutive",
  );
  await page.getByRole("textbox", { name: /Academic year/ }).fill("2026-27");
  await page.getByLabel("Synthetic student CSV").setInputFiles({
    name: "synthetic.csv",
    mimeType: "text/csv",
    buffer: Buffer.alloc(5 * 1024 * 1024 + 1, "x"),
  });
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "has not been sent",
  );
  expect(posts).toBe(0);
});

test("malformed and over-row-limit files are rejected; manual recovery works", async ({
  page,
}) => {
  await signIn(page);
  await openUpload(page, "2033-34");
  await fillUpload(
    page,
    "2033-34",
    Buffer.from("wrong,headers\nsynthetic,only\n"),
  );
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Upload not accepted" }),
  ).toBeVisible();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "strict-v1 template",
  );
  const header = admission.toString().split(/\r?\n/)[0] + "\n";
  await fillUpload(page, "2033-34", Buffer.from(header + '"unterminated\n'));
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "standard quoting",
  );
  await fillUpload(
    page,
    "2033-34",
    Buffer.concat([Buffer.from(header), Buffer.from([0xff])]),
  );
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "UTF-8",
  );
  const lines = csv("2033-34").toString().trim().split(/\r?\n/);
  await fillUpload(
    page,
    "2033-34",
    Buffer.from(lines[0] + "\n" + Array(1001).fill(lines[1]).join("\n")),
  );
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "data-record limit",
  );
  await fillUpload(page, "2033-34");
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Candidate stored" }),
  ).toBeVisible();
});

test("policy failure blocks upload; retry loads actual configuration", async ({
  page,
}) => {
  await page.route(API_URL + "/submissions/upload-policy", (route) =>
    fail(route, 503, "DATABASE_UNAVAILABLE"),
  );
  await signIn(page);
  await page
    .getByRole("link", { name: "Upload candidate", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Upload candidate", exact: true }),
  ).toBeDisabled();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "database is unavailable",
  );
  await page.unroute(API_URL + "/submissions/upload-policy");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(
    page.getByText("5,242,880 bytes", { exact: true }),
  ).toBeVisible();
});

test("returned policy controls displayed limits and client size guard", async ({
  page,
}) => {
  await page.route(API_URL + "/submissions/upload-policy", async (route) => {
    const response = await route.fetch();
    const body: Policy = await response.json();
    await route.fulfill({
      response,
      json: { ...body, max_file_bytes: 128, max_rows: 2 },
    });
  });
  await signIn(page);
  await page
    .getByRole("link", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByText("128 bytes", { exact: true })).toBeVisible();
  await expect(
    page.getByText("2 records, excluding the header", { exact: true }),
  ).toBeVisible();
  await fillUpload(page, "2034-35");
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "has not been sent",
  );
});

test("lost response after real persistence reports unknown and never retries", async ({
  page,
  request,
}) => {
  let posts = 0;
  await page.route(API_URL + "/submissions", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    posts++;
    const response = await route.fetch();
    expect(response.status()).toBe(201);
    await route.abort("connectionreset");
  });
  await signIn(page);
  await openUpload(page, "2035-36");
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Upload outcome unknown" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Upload candidate", exact: true }),
  ).toHaveCount(0);
  await page.context().setOffline(true);
  await page.context().setOffline(false);
  await page
    .getByRole("link", { name: "Check submission history", exact: true })
    .click();
  await page
    .getByRole("textbox", { name: "Academic year", exact: true })
    .fill("2035-36");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(2);
  expect(posts).toBe(1);
  const account = await apiAccount(request);
  const history = await (
    await request.get(API_URL + "/submissions?academic_year=2035-36", {
      headers: account.headers,
    })
  ).json();
  expect(history.pagination.total).toBe(1);
});

test("in-flight processing disables duplicate submission", async ({ page }) => {
  let release = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let posts = 0;
  await page.route(API_URL + "/submissions", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    posts++;
    const response = await route.fetch();
    await gate;
    await route.fulfill({ response });
  });
  try {
    await signIn(page);
    await openUpload(page, "2036-37");
    await page
      .getByRole("button", { name: "Upload candidate", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Uploading and processing…" }),
    ).toBeDisabled();
    await expect(page.getByLabel("Synthetic student CSV")).toBeDisabled();
    await expect.poll(() => posts).toBe(1);
    await page
      .getByRole("link", { name: "Submission history", exact: true })
      .click();
    await page
      .getByRole("link", { name: "Upload candidate", exact: true })
      .click();
    await expect(
      page.getByRole("button", {
        name: /^(Upload candidate|Uploading and processing…)$/,
      }),
    ).toBeDisabled();
    await expect(
      page
        .getByRole("status")
        .filter({ hasText: /still awaiting a response|Keep this page open/ }),
    ).toBeVisible();
    release();
    // Next.js may preserve the original page's state across navigation. Either
    // restored success or a fresh enabled form is valid after the pending request ends.
    await expect(
      page.getByRole("button", {
        name: /^(Prepare another upload|Upload candidate)$/,
      }),
    ).toBeEnabled();
    expect(posts).toBe(1);
  } finally {
    release();
  }
});

test("expiry during an upload clears private UI and explains uncertainty", async ({
  page,
}) => {
  await page.clock.install();
  let release = () => {};
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(API_URL + "/submissions", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const response = await route.fetch();
    await gate;
    try {
      await route.fulfill({ response });
    } catch {
      /* session cancellation */
    }
  });
  try {
    await signIn(page);
    await openUpload(page, "2037-38");
    await page
      .getByRole("button", { name: "Upload candidate", exact: true })
      .click();
    await expect(
      page.getByRole("button", { name: "Uploading and processing…" }),
    ).toBeVisible();
    await page.clock.fastForward(901000);
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("main").getByRole("alert")).toContainText(
      "session expired",
    );
    await expect(
      page.getByText(/upload may still have completed/),
    ).toBeVisible();
    release();
  } finally {
    release();
  }
});

test("history errors stay separate from empty data and recover on retry", async ({
  page,
}) => {
  await page.route(API_URL + "/submissions?*", (route) =>
    fail(route, 503, "DATABASE_UNAVAILABLE"),
  );
  await signIn(page);
  await page.getByRole("link", { name: "Submissions", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "database is unavailable",
  );
  await expect(
    page.getByRole("heading", { name: "No submissions found" }),
  ).toHaveCount(0);
  await page.unroute(API_URL + "/submissions?*");
  const retry = page.getByRole("button", { name: "Refresh history" });
  await expect(retry).toBeEnabled();
  await retry.focus();
  await expect(retry).toBeFocused();
  await retry.press("Enter");
  await expect
    .poll(
      async () =>
        (await page
          .getByRole("heading", { name: "No submissions found" })
          .count()) +
        (await page
          .getByRole("region", { name: /Submission history/ })
          .getByRole("table")
          .count()),
    )
    .toBeGreaterThan(0);
});

test("officer can browse scoped history but cannot upload; manager is denied", async ({
  page,
  request,
}) => {
  const account = await apiAccount(request);
  await signIn(page, "Demo AICTE officer");
  await page
    .getByRole("link", { name: "View Demo Cedar Institute", exact: true })
    .click();
  await page
    .getByRole("link", { name: "View submission history", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Upload history" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Upload candidate CSV" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Upload candidate", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await signIn(page, "Demo AICTE manager");
  await expect(
    page.getByRole("link", { name: "Submissions", exact: true }),
  ).toHaveCount(0);
  await page.goto(`/submissions?institution_id=${account.institutionId}`);
  // Hard navigation clears memory auth; after sign-in, use client navigation to verify the role guard.
  await expect(page).toHaveURL(/\/login$/);
  const login = await request.post(API_URL + "/auth/demo-login", {
    data: { demo_alias: "demo_manager" },
  });
  const headers = {
    Authorization: `Bearer ${(await login.json()).access_token}`,
  };
  expect(
    (await request.get(API_URL + "/submissions", { headers })).status(),
  ).toBe(403);
  expect(
    (await request.post(API_URL + "/submissions", { headers })).status(),
  ).toBe(403);
});

test("account switching clears selected files and scoped submission history", async ({
  page,
}) => {
  await signIn(page);
  await openUpload(page, "2038-39");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await signIn(page, "Demo Willow Institute");
  await page.getByRole("link", { name: "Submissions", exact: true }).click();
  await page
    .getByRole("textbox", { name: "Academic year", exact: true })
    .fill("2038-39");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(
    page.getByRole("heading", { name: "No submissions found" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Upload candidate", exact: true })
    .click();
  await expect(page.getByLabel("Synthetic student CSV")).toHaveValue("");
  await expect(
    page.getByRole("checkbox", { name: /synthetic student records only/ }),
  ).not.toBeChecked();
  await expect(page.getByRole("main")).toContainText("Demo Willow Institute");
  await expect(page.getByRole("main")).not.toContainText(
    "Demo Cedar Institute",
  );
});

test("desktop and mobile upload/history are accessible and do not overflow", async ({
  page,
}) => {
  await signIn(page);
  await openUpload(page, "2039-40");
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await capture(page, "5b-upload-desktop.png");
  await page.setViewportSize({ width: 390, height: 844 });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await capture(page, "5b-upload-mobile.png");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .getByRole("button", { name: "Upload candidate", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Candidate stored" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "View submission history", exact: true })
    .click();
  await expect(page.getByRole("table")).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await capture(page, "5b-history-mobile.png");
  expect(
    await page.evaluate(() => ({
      width: document.documentElement.scrollWidth,
      viewport: window.innerWidth,
      outside: Array.from(document.querySelectorAll("main *"))
        .filter(
          (item) =>
            !item.closest(".table-scroll") &&
            item.getBoundingClientRect().right > window.innerWidth,
        )
        .map((item) => ({
          tag: item.tagName,
          class: item.className,
          right: item.getBoundingClientRect().right,
        })),
    })),
  ).toEqual({ width: 390, viewport: 390, outside: [] });
});

test("history shows actual current and previous snapshots without activating in the UI", async ({
  page,
  request,
}) => {
  const account = await apiAccount(request);
  const year = "2040-41";
  const first = await store(
    request,
    account,
    year,
    "DEMO-COMP",
    csv(year, "DEMO-COMP", initial),
  );
  const second = await store(
    request,
    account,
    year,
    "DEMO-COMP",
    csv(year, "DEMO-COMP", initial),
  );
  for (const batch of [first, second]) {
    const validation = await request.post(
      API_URL + `/submissions/${batch}/validate`,
      { headers: account.headers },
    );
    expect(validation.status()).toBe(201);
    const run = await validation.json();
    const review = await request.post(
      API_URL + `/submissions/${batch}/reviews`,
      { headers: account.headers, data: { validation_run_id: run.id } },
    );
    expect(review.status()).toBe(201);
    const receipt = await review.json();
    const activation = await request.post(
      API_URL + `/submissions/${batch}/activate`,
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
  }
  await store(request, account, year);
  await signIn(page);
  await page.getByRole("link", { name: "Submissions", exact: true }).click();
  const historyRegion = page.getByRole("region", {
    name: /Submission history/,
  });
  await expect(historyRegion.getByRole("table")).toBeVisible();
  const yearField = page.getByRole("textbox", {
    name: "Academic year",
    exact: true,
  });
  await yearField.fill(year);
  await expect(yearField).toHaveValue(year);
  const filteredHistory = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/submissions" &&
      url.searchParams.get("academic_year") === year
    );
  });
  await page.getByRole("button", { name: "Apply filters" }).click();
  await filteredHistory;
  await expect(yearField).toHaveValue(year);
  for (const label of ["Current", "Previous", "Candidate"])
    await expect(
      historyRegion.getByRole("table").getByText(label, { exact: true }),
    ).toHaveCount(1);
  await expect(
    page.getByRole("button", { name: /activate|validate|review/i }),
  ).toHaveCount(0);
});
