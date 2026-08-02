import { expect, test } from "@playwright/test";

const SHOWCASE_QUESTION = "What AI and data systems has Lucas built?";
const SOURCE_SECTION = "Acme — AI & Data Engineer";

test("dark is the default and the light preference persists", async ({ page }) => {
  await page.goto("/");

  const root = page.locator("html");
  await expect(root).toHaveAttribute("data-theme", "dark");

  const useLightTheme = page.getByRole("button", { name: "Use light theme", exact: true });
  await expect(useLightTheme).toBeVisible();
  await useLightTheme.click();

  await expect(root).toHaveAttribute("data-theme", "light");
  await expect(
    page.getByRole("button", { name: "Use dark theme", exact: true }),
  ).toBeVisible();

  await page.reload();
  await expect(root).toHaveAttribute("data-theme", "light");
  await expect(
    page.getByRole("button", { name: "Use dark theme", exact: true }),
  ).toBeVisible();
});

test("suggestion, grounded answer, follow-up, evidence, and new conversation", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "What would you like to know?", exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel("Message Ask Lucas", { exact: true })).toBeVisible();

  const suggestion = page.getByRole("button", { name: SHOWCASE_QUESTION, exact: true });
  await expect(suggestion).toHaveCount(1);
  await suggestion.click();
  await expect(page.getByTestId("chat-transcript")).toBeVisible();
  await expect(page.getByText("You", { exact: true })).toBeVisible();

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
  await page.getByRole("button", { name: "Close inspector", exact: true }).click();
  await expect(evidenceDialog).toBeHidden();
  await expect(secondCitation).toBeFocused();

  const systemLens = page.getByRole("button", { name: "System lens", exact: true });
  await systemLens.click();
  const systemDialog = page.getByRole("dialog", {
    name: "How this answer was made",
    exact: true,
  });
  await expect(systemDialog).toBeVisible();
  await expect(systemDialog.getByText("sqlite-fts5", { exact: true })).toBeVisible();
  await expect(systemDialog.getByText("experience:acme-ai-data-engineer", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close inspector", exact: true }).click();
  await expect(systemLens).toBeFocused();

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
  await expect(
    page.getByRole("button", { name: SHOWCASE_QUESTION, exact: true }),
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
  await expect(
    page.getByRole("article").getByText("Please wait about 37 seconds", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("Trace rate-limit-trace", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Try again in about 37s", exact: true }),
  ).toBeVisible();
});

test("composer validation and interrupted requests preserve editable questions", async ({ page }) => {
  await page.goto("/");
  const input = page.getByLabel("Message Ask Lucas", { exact: true });

  await input.press("Enter");
  await expect(page.locator("#composer-validation")).toHaveText("Enter a question before sending.");
  await expect(input).toBeFocused();

  await input.fill("x".repeat(501));
  await input.press("Enter");
  await expect(
    page.locator("#composer-validation"),
  ).toHaveText("Keep the question to 500 characters or fewer.");
  await expect(input).toBeFocused();

  await page.route("**/v1/chat", async (route) => route.abort("failed"));
  await input.fill("Which systems did Lucas build?");
  await input.press("Enter");
  await expect(
    page
      .getByRole("article")
      .getByText("The connection was interrupted before a complete answer arrived.", {
        exact: true,
      }),
  ).toBeVisible();
  await expect(page.getByText("Which systems did Lucas build?", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Try again", exact: true })).toBeVisible();
});

test("a pending request exposes the honest slow-response state", async ({ page }) => {
  await page.clock.install();
  let releaseResponse: (() => void) | undefined;
  const responseGate = new Promise<void>((resolve) => {
    releaseResponse = resolve;
  });
  await page.route("**/v1/chat", async (route) => {
    await responseGate;
    await route.continue();
  });
  await page.goto("/");

  await page.getByRole("button", { name: SHOWCASE_QUESTION, exact: true }).click();
  await expect(
    page.getByRole("article").getByText("Reviewing approved sources", { exact: false }),
  ).toBeVisible();
  await page.clock.fastForward(8_100);
  await expect(
    page
      .getByRole("article")
      .getByText("The answer is taking longer than usual, but it is still working.", {
        exact: true,
      }),
  ).toBeVisible();

  releaseResponse?.();
  await expect(page.getByText("1 source ·", { exact: false })).toBeVisible();
});

test("evidence inspector navigates all cited sources", async ({ page }) => {
  await page.route("**/v1/chat", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        kind: "grounded",
        blocks: [
          { text: "One supported claim.", source_ids: ["profile:first"] },
          { text: "Another supported claim.", source_ids: ["projects:second"] },
        ],
        sources: [
          {
            source_id: "profile:first",
            title: "Profile",
            section: "First section",
            excerpt: "First approved excerpt.",
            content_path: "content/profile.md",
          },
          {
            source_id: "projects:second",
            title: "Projects",
            section: "Second section",
            excerpt: "Second approved excerpt.",
            content_path: "content/projects.md",
          },
        ],
        trace: {
          trace_id: "two-source-trace",
          retrieval_strategy: "sqlite-fts5",
          score_kind: "bm25",
          score_order: "lower_is_better",
          retrieved: [
            { source_id: "profile:first", rank: 1, raw_score: -2 },
            { source_id: "projects:second", rank: 2, raw_score: -1 },
          ],
          provider_mode: "mock",
          model: null,
          retrieval_ms: 1,
          generation_ms: 1,
          total_ms: 2,
        },
      }),
    });
  });
  await page.goto("/");
  await page.getByRole("button", { name: SHOWCASE_QUESTION, exact: true }).click();
  await page.getByRole("button", { name: "Open source 1 for claim 1: First section" }).click();

  const dialog = page.getByRole("dialog", { name: "First section", exact: true });
  await expect(dialog.getByText("First approved excerpt.", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Second section", exact: true })).toBeVisible();
  await expect(page.getByText("Second approved excerpt.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Previous", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "First section", exact: true })).toBeVisible();
});
