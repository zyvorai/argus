import { chromium } from "playwright";

export const BASE = process.env.ZQA_MC_URL || "http://127.0.0.1:30080";
export const USER = process.env.ZQA_MC_USER || "admin";
export const PASS = process.env.ZQA_MC_PASS || "Admin@321";

export async function openLoggedIn(videoDir, { skipLogin = true } = {}) {
  const browser = await chromium.launch({ channel: "chrome" });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: { dir: videoDir, size: { width: 1920, height: 1080 } },
  });
  const page = await context.newPage();
  if (skipLogin) {
    await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
    await page.fill('input[name="username"]', USER);
    await page.fill('input[name="password"]', PASS);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1500);
  }
  return { browser, context, page };
}

export async function closeAndSave(browser, context) {
  const page = context.pages()[0];
  await page.close();
  await context.close();
  await browser.close();
}
