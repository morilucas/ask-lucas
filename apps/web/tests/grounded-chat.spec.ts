import { expect, test } from "@playwright/test";

const SHOWCASE_QUESTION = "What AI and data systems has Lucas built?";
const SOURCE_SECTION = "Acme — AI & Data Engineer";

test("suggestion, grounded answer, follow-up, evidence, and new conversation", async ({ page }) => {
  await page.goto("/");

  const suggestion = page.getByRole("button", { name: SHOWCASE_QUESTION, exact: true });
  await expect(suggestion).toHaveCount(1);
  await suggestion.click();

  await expect(
    page.getByText(
      "In the synthetic public dataset, the example candidate builds data pipelines, operational dashboards, and analytical investigations for product teams.",
      { exact: false },
    ),
  ).toBeVisible();
  await expect(page.getByText("1 source ·", { exact: false })).toBeVisible();

  const firstCitation = page.getByRole("button", {
    name: `Open source 1 for claim 1: ${SOURCE_SECTION}`,
    exact: true,
  });
  await expect(firstCitation).toHaveCount(1);
  await firstCitation.click();

  const evidenceDialog = page.getByRole("dialog", { name: SOURCE_SECTION, exact: true });
  await expect(evidenceDialog).toBeVisible();
  await expect(
    evidenceDialog.getByText("Develops internal retrieval assistants", { exact: false }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(evidenceDialog).toBeHidden();
  await expect(firstCitation).toBeFocused();

  const secondCitation = page.getByRole("button", {
    name: `Open source 1 for claim 2: ${SOURCE_SECTION}`,
    exact: true,
  });
  await secondCitation.click();
  await page.getByRole("button", { name: "Close evidence", exact: true }).click();
  await expect(evidenceDialog).toBeHidden();
  await expect(secondCitation).toBeFocused();

  const input = page.getByLabel("Message Ask Lucas", { exact: true });
  await input.fill("Which tools did he use?");
  await input.press("Enter");
  await expect(
    page.getByText("The closest reviewed evidence is in", { exact: false }).first(),
  ).toBeVisible();

  await page.getByRole("button", { name: "New conversation", exact: true }).click();
  await input.fill("What is Lucas's favorite movie?");
  await input.press("Enter");

  await expect(
    page.getByText(
      "The synthetic public dataset does not contain a reviewed answer for that question.",
      { exact: false },
    ),
  ).toBeVisible();
});

test("the empty and evidence states do not create horizontal overflow", async ({ page }) => {
  await page.goto("/");

  const emptyWidths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(emptyWidths.scroll).toBeLessThanOrEqual(emptyWidths.client);

  await page.getByRole("button", { name: SHOWCASE_QUESTION, exact: true }).click();
  const citation = page.getByRole("button", {
    name: `Open source 1 for claim 1: ${SOURCE_SECTION}`,
    exact: true,
  });
  await expect(citation).toBeVisible();
  await citation.click();

  const evidenceWidths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(evidenceWidths.scroll).toBeLessThanOrEqual(evidenceWidths.client);
});

test("a public rate limit gives specific retry guidance and preserves the question", async ({
  page,
}) => {
  await page.route("**/v1/chat", async (route) => {
    await route.fulfill({
      status: 429,
      headers: { "Content-Type": "application/json", "Retry-After": "37" },
      body: JSON.stringify({
        code: "rate_limited",
        message: "You've asked several questions quickly. Please wait about 37 seconds and try again.",
        trace_id: "rate-limit-trace",
        retryable: true,
        retry_after_seconds: 37,
      }),
    });
  });
  await page.goto("/");

  const input = page.getByLabel("Message Ask Lucas", { exact: true });
  await input.fill(SHOWCASE_QUESTION);
  await input.press("Enter");

  await expect(page.getByText(SHOWCASE_QUESTION, { exact: true })).toBeVisible();
  await expect(page.getByText("Please wait about 37 seconds", { exact: false })).toBeVisible();
  await expect(page.getByText("Trace rate-limit-trace", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Try again in about 37s", exact: true }),
  ).toBeVisible();
});
