import path from "node:path";

import { expect, test } from "@playwright/test";

const RUN_REAL_BACKEND_E2E = process.env.RUN_REAL_BACKEND_E2E === "1";

test.describe("real backend upload flow", () => {
  test.skip(!RUN_REAL_BACKEND_E2E, "Set RUN_REAL_BACKEND_E2E=1 and run frontend+backend servers to execute this test.");

  test("accepts single PDF upload and shows queued/running status", async ({ page, request, baseURL }) => {
    const healthUrl = `${process.env.E2E_BACKEND_URL ?? "http://127.0.0.1:8000"}/api/health`;
    const health = await request.get(healthUrl);
    expect(health.ok()).toBeTruthy();

    await page.goto(baseURL ?? "http://127.0.0.1:3000");

    const filePath = path.resolve(process.cwd(), "..", "CTSE - Assignment 2.pdf");

    await page.setInputFiles("#resume", filePath);
    await page.fill("#candidateName", "Playwright Candidate");
    await page.fill("#jobDescription", "Need Python and AWS");
    await page.fill("#requiredSkills", "Python, AWS");

    await page.getByRole("button", { name: "Start Agentic Evaluation" }).click();

    await expect(page.getByText("Pipeline Status")).toBeVisible();
    await expect(page.getByText("Job ID:")).toBeVisible();
    await expect(page.locator(".status-badge")).toContainText(/queued|running|completed|failed/i);
  });
});
