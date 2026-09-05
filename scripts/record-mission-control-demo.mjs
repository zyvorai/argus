#!/usr/bin/env node
/**
 * Record a Mission Control UX demo: login → dashboard → fill Flow URL/steps → Run → result.
 *
 * Usage:
 *   node scripts/record-mission-control-demo.mjs [baseUrl] [out.webm]
 * Env: DASH_USER / DASH_PASS (defaults admin / Admin@321)
 */
import { chromium } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const base = (process.argv[2] || process.env.ZQA_MC_URL || "http://127.0.0.1:30080").replace(/\/$/, "");
const outWebm =
  process.argv[3] ||
  path.join(root, "docs/assets/guestkit-mission-control-demo.webm");
const user = process.env.DASH_USER || "admin";
const pass = process.env.DASH_PASS || "Admin@321";

const stepsText = [
  "goto /",
  'wait until "GuestKit" 25000ms',
  'assert "GuestKit"',
  "wait 1200ms",
  "press PageDown",
  "wait 1000ms",
  'assert "Offline VM intelligence"',
  "wait 1500ms",
].join("\n");

const targetUrl = "https://github.com/hypersdk/guestkit";
const outDir = path.join(root, "reports/artifacts/flows/mc-demo");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  args: process.env.ZYVOR_NO_SANDBOX === "1" ? ["--no-sandbox"] : [],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: outDir, size: { width: 1440, height: 900 } },
});
const page = await context.newPage();
const pause = (ms) => page.waitForTimeout(ms);

async function typeSlow(locator, text, delay = 28) {
  await locator.click();
  await locator.fill("");
  await locator.pressSequentially(text, { delay });
}

try {
  // ── 1. Login ──────────────────────────────────────────────
  await page.goto(`${base}/login`, { waitUntil: "networkidle", timeout: 60000 });
  await pause(2200);
  await typeSlow(page.locator("#username"), user, 60);
  await pause(500);
  await typeSlow(page.locator("#password"), pass, 50);
  await pause(900);
  await page.locator("#submit").click();
  await page.waitForURL(/dashboard|\/$/, { timeout: 30000 }).catch(() => {});
  await pause(800);
  await page.goto(`${base}/dashboard`, { waitUntil: "networkidle", timeout: 60000 });

  // ── 2. Show Mission Control (hero / pods) ─────────────────
  await pause(3500);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  await pause(2000);
  // peek at cluster cards
  await page.evaluate(() => window.scrollBy({ top: 280, behavior: "smooth" }));
  await pause(2200);

  // ── 3. Scroll to Flow test, enter GuestKit URL + steps ────
  const flowTitle = page.locator(".act-title", { hasText: "Flow test" }).first();
  await flowTitle.scrollIntoViewIfNeeded();
  await pause(1600);

  await typeSlow(page.locator("#fw-url"), targetUrl, 35);
  await pause(1000);

  const desc = page.locator("#fw-desc");
  await desc.click();
  await desc.fill("");
  await desc.pressSequentially(stepsText, { delay: 12 });
  await pause(1500);

  const rec = page.locator("#fw-record");
  if (!(await rec.isChecked())) await rec.check();
  await pause(800);

  // highlight the Run button briefly
  const runBtn = page.locator('button[data-kind="flow"]');
  await runBtn.scrollIntoViewIfNeeded();
  await pause(900);
  await runBtn.click();

  // ── 4. Watch live job panel ───────────────────────────────
  await pause(1200);
  const liveCard = page.locator("#job-live");
  await liveCard.waitFor({ state: "visible", timeout: 20000 }).catch(() => {});
  await liveCard.scrollIntoViewIfNeeded().catch(() => {});

  const deadline = Date.now() + 200000;
  let last = null;
  while (Date.now() < deadline) {
    last = await page.evaluate(async () => {
      try {
        const r = await fetch("/api/dashboard/jobs/status", { credentials: "same-origin" });
        return await r.json();
      } catch {
        return { running: false };
      }
    });
    if (last && last.running === false && last.kind) break;
    await pause(1500);
  }
  await pause(2500);

  // ── 5. Show result card if present ────────────────────────
  const result = page.locator("#job-result");
  if (await result.isVisible().catch(() => false)) {
    await result.scrollIntoViewIfNeeded();
    await pause(3500);
  } else {
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: "smooth" }));
    await pause(2500);
  }
  await pause(2000);
} finally {
  const video = page.video();
  await page.close();
  await context.close();
  await browser.close();
  if (video) {
    const raw = await video.path();
    fs.mkdirSync(path.dirname(outWebm), { recursive: true });
    fs.copyFileSync(raw, outWebm);
    console.log(`Wrote ${outWebm}`);
  }
}
