#!/usr/bin/env node
/** One-off Chrome E2E smoke for remote Mission Control deploy. */
import { chromium } from "@playwright/test";

const BASE = process.env.ARGUS_BASE_URL || "http://127.0.0.1:30080";
const USER = process.env.ARGUS_DASH_USER || "admin";
const PASS = process.env.ARGUS_DASH_PASS || "Admin@321";

const results = [];
const pass = (name, detail = "") => {
  results.push({ name, ok: true, detail });
  console.log("PASS", name, detail);
};
const fail = (name, detail = "") => {
  results.push({ name, ok: false, detail });
  console.log("FAIL", name, detail);
};

const browser = await chromium
  .launch({ headless: true, channel: "chrome" })
  .catch(() => chromium.launch({ headless: true }));
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});

try {
  const health = await page.request.get(`${BASE}/health`);
  health.ok() ? pass("GET /health", String(health.status())) : fail("GET /health", String(health.status()));

  await page.goto(`${BASE}/login`, { waitUntil: "networkidle", timeout: 30000 });
  const theme = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  theme === "dark" ? pass("Login dark theme default", theme) : fail("Login dark theme default", theme || "missing");
  await page.locator("text=Mission Control").first().waitFor({ state: "visible" });
  pass("Login page renders");

  await page.fill("#username", USER);
  await page.fill("#password", PASS);
  await page.click("#submit");
  await page.waitForURL("**/dashboard**", { timeout: 15000 });
  pass("Login redirect to dashboard");

  await page.waitForSelector(".side-rail", { timeout: 10000 });
  await page.waitForSelector("#hero", { timeout: 10000 });
  pass("Dashboard overview loads");

  const railAsk = page.locator('.rail-link[data-panel="ask"]');
  (await railAsk.count()) ? pass("Ask Zyra rail item present") : fail("Ask Zyra rail item present");
  const askLabel = await railAsk.locator(".rail-link-label").textContent();
  askLabel?.includes("Ask Zyra") ? pass("Ask Zyra label", askLabel.trim()) : fail("Ask Zyra label", askLabel || "");

  const layout = await page.locator(".stat-tile").first().evaluate((el) => {
    const label = el.querySelector(".stat-label");
    const value = el.querySelector(".stat-value");
    if (!label || !value) return null;
    const lr = label.getBoundingClientRect();
    const vr = value.getBoundingClientRect();
    return { stacked: vr.top >= lr.bottom - 2 };
  });
  layout?.stacked ? pass("Stat tiles stacked layout") : fail("Stat tiles stacked layout", JSON.stringify(layout));

  const toggle = page.locator("#theme-toggle");
  await toggle.click();
  await page.waitForTimeout(300);
  const light = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  light === "light" ? pass("Theme toggle to light", light) : fail("Theme toggle to light", light || "");
  await toggle.click();
  await page.waitForTimeout(300);
  const dark = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  dark === "dark" ? pass("Theme toggle back to dark", dark) : fail("Theme toggle back to dark", dark || "");

  await railAsk.click();
  await page.locator("#panel-ask.is-active").waitFor({ state: "visible", timeout: 5000 });
  pass("Ask Zyra panel opens");
  const askH1 = await page.locator("#panel-ask h1").textContent();
  askH1?.includes("Ask Zyra") ? pass("Ask Zyra panel title", askH1.trim()) : fail("Ask Zyra panel title", askH1 || "");

  await page.locator("#topbar-palette").click();
  await page.locator("#palette-input").waitFor({ state: "visible", timeout: 5000 });
  pass("Search palette opens");
  await page.keyboard.press("Escape");

  await page.locator('.rail-link[data-panel="pipeline"]').click();
  await page.locator("#panel-pipeline.is-active").waitFor({ state: "visible", timeout: 5000 });
  pass("Pipeline panel opens");

  const overview = await page.request.get(`${BASE}/api/dashboard/overview`);
  overview.ok()
    ? pass("GET /api/dashboard/overview", String(overview.status()))
    : fail("GET /api/dashboard/overview", String(overview.status()));

  const knowledge = await page.request.get(`${BASE}/api/dashboard/knowledge/status`);
  knowledge.ok()
    ? pass("GET /api/dashboard/knowledge/status", String(knowledge.status()))
    : fail("GET /api/dashboard/knowledge/status", String(knowledge.status()));

  await page.locator('.rail-link[data-panel="overview"]').click();
  await page.waitForTimeout(2000);
  const sync = await page.locator(".hero .sync").textContent();
  sync?.includes("synced") ? pass("Hero auto-sync", sync.trim().slice(0, 40)) : fail("Hero auto-sync", sync || "");

  errors.length ? fail("No console/page errors", errors.slice(0, 3).join(" | ")) : pass("No console/page errors");
} catch (e) {
  fail("Unhandled test error", e.message);
} finally {
  await browser.close();
}

const failed = results.filter((r) => !r.ok);
console.log("\n=== SUMMARY ===");
console.log(`${results.length - failed.length}/${results.length} passed`);
if (failed.length) {
  failed.forEach((f) => console.log("  ✗", f.name, f.detail));
  process.exit(1);
}
