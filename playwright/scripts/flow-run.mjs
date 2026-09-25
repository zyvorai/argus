// Copyright 2026 Zyvor AI Labs · https://zyvor.dev
// SPDX-License-Identifier: LicenseRef-Zyvor-Production-1.0

/**
 * E2E flow runner — drive a multi-step user journey and record it as one video.
 * Modelled on zeus-os ui/scripts/e2e-create-vm-wizard.mjs.
 *
 * Usage: node flow-run.mjs <flowJsonFile> <outDir>
 *   flow JSON: { base, steps: [{action,target,value,assertion}], record: bool }
 *
 * Env: ZYVOR_IGNORE_HTTPS_ERRORS, ZYVOR_NO_SANDBOX,
 *      ZYVOR_TEST_USER / ZYVOR_TEST_PASSWORD (best-effort login).
 * Progress → stderr (live panel). Result JSON → stdout.
 */

import { chromium, devices, firefox, webkit } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { driveFormLogin, passwordFieldLocator } from './lib/form-login.mjs';

const ENGINES = { chromium, firefox, webkit };

const flowFile = process.argv[2];
const outDir = process.argv[3];
if (!flowFile || !outDir) {
  console.error('Usage: node flow-run.mjs <flowJsonFile> <outDir>');
  process.exit(2);
}
const flow = JSON.parse(fs.readFileSync(flowFile, 'utf-8'));
const base = (flow.base || '').replace(/\/$/, '');
const steps = flow.steps || [];
const record = flow.record !== false;

const FAIL_SNIPPETS = ['Something went wrong', 'ReferenceError', 'TypeError', 'is not defined', 'Application error', 'Cannot read propert'];
const emit = (m) => console.error(m);
function slug(t) { return (t || 'step').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'step'; }

// navigate with a few retries — survives server churn / cold starts (zeus-os pattern)
async function gotoRetry(page, url, { waitUntil = 'load', timeout = 30000, tries = 3 } = {}) {
  let lastErr;
  for (let attempt = 1; attempt <= tries; attempt++) {
    try {
      await page.goto(url, { waitUntil, timeout });
      return;
    } catch (err) {
      lastErr = err;
      emit(`flow: navigate ${url} failed (try ${attempt}/${tries}) — ${String(err.message || err).slice(0, 120)}`);
      if (attempt < tries) await page.waitForTimeout(1500 * attempt);
    }
  }
  throw lastErr;
}

// dismiss cookie banners / onboarding modals that overlay the first step (zeus-os e2e-lib)
const OVERLAY_LABELS = [
  'accept all', 'accept cookies', 'accept', 'i agree', 'agree', 'got it', 'ok', 'okay',
  'dismiss', 'no thanks', 'maybe later', 'skip', 'skip tour', 'close', 'continue', 'allow all',
];
async function dismissOverlays(page) {
  for (let round = 0; round < 3; round++) {
    let clicked = false;
    for (const label of OVERLAY_LABELS) {
      const btn = page.getByRole('button', { name: new RegExp('^\\s*' + escapeRe(label) + '\\s*$', 'i') }).first();
      try {
        if ((await btn.count()) && (await btn.isVisible())) {
          await btn.click({ timeout: 2000 });
          emit(`flow: dismissed overlay ("${label}")`);
          await page.waitForTimeout(250);
          clicked = true;
          break;
        }
      } catch { /* ignore */ }
    }
    // common close-icon patterns + Escape as a fallback
    if (!clicked) {
      const closeIcon = page.locator('[aria-label*="close" i], [class*="cookie" i] button, [class*="consent" i] button').first();
      try {
        if ((await closeIcon.count()) && (await closeIcon.isVisible())) {
          await closeIcon.click({ timeout: 1500 });
          clicked = true;
        }
      } catch { /* ignore */ }
    }
    if (!clicked) { await page.keyboard.press('Escape').catch(() => {}); break; }
  }
}

async function tryLogin(page) {
  const user = process.env.ZYVOR_TEST_USER, password = process.env.ZYVOR_TEST_PASSWORD;
  if (!user || !password) return;
  try {
    await gotoRetry(page, base + '/', { waitUntil: 'domcontentloaded', timeout: 30000, tries: 3 });
    await dismissOverlays(page);
    const pass = passwordFieldLocator(page);
    if ((await pass.count()) === 0 && (await page.locator('#login_id, #username').count()) === 0) return;
    const result = await driveFormLogin(page, user, password);
    if (result.ok) {
      emit(`flow: logged in as ${user}`);
      await dismissOverlays(page);
    } else {
      emit(`flow: login incomplete — ${result.detail}`);
    }
  } catch (err) { emit(`flow: login skipped (${err})`); }
}

async function resolveLocator(root, target) {
  if (!target) return root.locator('body').first();
  const byRole = root.getByRole('button', { name: new RegExp(escapeRe(target), 'i') }).first();
  const byLink = root.getByRole('link', { name: new RegExp(escapeRe(target), 'i') }).first();
  const byText = root.getByText(target, { exact: false }).first();
  if (await byRole.count()) return byRole;
  if (await byLink.count()) return byLink;
  if (await byText.count()) return byText;
  return root.locator(target).first();
}

async function resolveField(root, target) {
  const byLabel = root.getByLabel(new RegExp(escapeRe(target), 'i')).first();
  const byPh = root.getByPlaceholder(new RegExp(escapeRe(target), 'i')).first();
  if (await byLabel.count()) return byLabel;
  if (await byPh.count()) return byPh;
  return root.locator(`input[name*="${target}" i], textarea[name*="${target}" i], select[name*="${target}" i], ${target}`).first();
}

// iframe scope for subsequent steps; null = main page
let activeFrame = null;
let pendingDialog = null; // { action: 'accept'|'dismiss', text?: string }

function rootOf(page) {
  return activeFrame || page;
}

async function runStep(page, step, n, seenResponses = []) {
  const { action, target, value, assertion } = step;
  const root = rootOf(page);
  switch (action) {
    case 'goto': {
      const url = /^https?:/.test(target) ? target : base + (target?.startsWith('/') ? target : '/' + (target || ''));
      await gotoRetry(page, url, { waitUntil: 'load', timeout: 30000, tries: 3 });
      await page.waitForLoadState('domcontentloaded').catch(() => {});
      await dismissOverlays(page);
      activeFrame = null;
      break;
    }
    case 'hover': {
      const loc = await resolveLocator(root, target);
      await loc.hover({ timeout: 10000 });
      break;
    }
    case 'click': {
      if (pendingDialog) {
        const cfg = pendingDialog;
        pendingDialog = null;
        page.once('dialog', async (dlg) => {
          if (cfg.text && !String(dlg.message() || '').includes(cfg.text)) {
            await dlg.dismiss();
            throw new Error(`dialog message did not match "${cfg.text}": ${dlg.message()}`);
          }
          if (cfg.action === 'dismiss') await dlg.dismiss();
          else await dlg.accept(cfg.promptValue || undefined);
        });
      }
      const loc = await resolveLocator(root, target);
      await loc.click({ timeout: 10000 });
      await page.waitForTimeout(400);
      break;
    }
    case 'fill': {
      const val = value ?? '';
      const field = await resolveField(root, target);
      await field.fill(val, { timeout: 8000 });
      break;
    }
    case 'select': {
      const field = await resolveField(root, target);
      await field.selectOption({ label: value }).catch(async () => {
        await field.selectOption(value);
      });
      break;
    }
    case 'upload': {
      const field = await resolveField(root, target);
      await field.setInputFiles(value || target);
      break;
    }
    case 'download': {
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 30000 }),
        (await resolveLocator(root, target)).click({ timeout: 10000 }),
      ]);
      const dest = value || path.join(outDir, download.suggestedFilename());
      await download.saveAs(dest);
      emit(`flow: downloaded ${dest}`);
      break;
    }
    case 'dialog': {
      pendingDialog = { action: (value || 'accept').toLowerCase(), text: assertion || '' };
      break;
    }
    case 'iframe': {
      if (!target) {
        activeFrame = null;
        emit('flow: iframe scope cleared');
      } else {
        activeFrame = page.frameLocator(target);
        emit(`flow: iframe scope ${target}`);
      }
      break;
    }
    case 'drag': {
      const src = await resolveLocator(root, target);
      const dst = await resolveLocator(root, value);
      await src.dragTo(dst);
      break;
    }
    case 'press':
      await page.keyboard.press(value || 'Enter');
      break;
    case 'clock': {
      const v = String(value || '').trim();
      if (v === 'install' || v.startsWith('install')) {
        await page.clock.install();
      } else if (v.startsWith('set:') || v.startsWith('set ')) {
        const t = v.replace(/^set[:\s]+/i, '').trim();
        await page.clock.setFixedTime(new Date(t));
      } else if (v.startsWith('fastForward:') || v.startsWith('fast-forward:') || v.startsWith('fastforward')) {
        const ms = Number(String(v).replace(/^[^\d]+/, '')) || 1000;
        await page.clock.fastForward(ms);
      } else {
        throw new Error(`unknown clock value: ${v} (use install | set:ISO | fastForward:ms)`);
      }
      break;
    }
    case 'wait':
      if (target) await page.waitForSelector(target, { timeout: 15000 });
      else await page.waitForTimeout(Number(value) || 1500);
      break;
    case 'wait_until': {
      const text = target || assertion;
      const timeout = Number(value) || 30000;
      const looksLikeSel = text && (/^[.#\[]/.test(text) || text.includes('='));
      const loc = looksLikeSel
        ? root.locator(text).first()
        : root.getByText(text, { exact: false }).filter({ visible: true }).first();
      // Prefer a visible match — marketing sites often hide dropdown clones of the same text
      try {
        await loc.waitFor({ state: 'visible', timeout });
      } catch {
        await root.getByText(text, { exact: false }).first().waitFor({ state: 'visible', timeout: Math.min(timeout, 5000) });
      }
      break;
    }
    case 'assert': {
      const text = assertion || target;
      if (/^https?:|^\//.test(text || '')) {
        await page.waitForURL(new RegExp(escapeRe(text)), { timeout: 10000 });
      } else if (text) {
        const loc = root.getByText(text, { exact: false }).first();
        await loc.waitFor({ state: 'visible', timeout: 10000 });
      } else {
        await root.getByRole('heading').first().waitFor({ state: 'visible', timeout: 10000 });
      }
      break;
    }
    case 'assert_url': {
      const text = assertion || target;
      await page.waitForURL(new RegExp(escapeRe(text)), { timeout: 10000 });
      break;
    }
    case 'assert_api': {
      const substr = target;
      const wantStatus = value ? Number(value) : null;
      const match = (r) => r.url.includes(substr) && (wantStatus == null || r.status === wantStatus);
      const already = seenResponses.find(match);
      if (already) break;
      const resp = await page.waitForResponse(
        (r) => r.url().includes(substr) && (wantStatus == null || r.status() === wantStatus),
        { timeout: 30000 },
      );
      if (wantStatus != null && resp.status() !== wantStatus) {
        throw new Error(`assert_api ${substr}: expected ${wantStatus}, got ${resp.status()}`);
      }
      break;
    }
    case 'assert_aria': {
      const sel = target || 'body';
      const loc = root.locator(sel).first();
      const got = await loc.ariaSnapshot();
      const want = (assertion || value || '').trim();
      if (want && !got.includes(want.replace(/^- /, '').split('\n')[0].trim()) && got.trim() !== want) {
        // soft structural match: every non-empty want line must appear in got
        const lines = want.split('\n').map((l) => l.trim()).filter(Boolean);
        const missing = lines.filter((l) => !got.includes(l.replace(/^- /, '')));
        if (missing.length) {
          throw new Error(`assert_aria mismatch; missing: ${missing.slice(0, 3).join(' | ')}\n--- got ---\n${got.slice(0, 500)}`);
        }
      }
      break;
    }
    case 'assert_not': {
      const text = assertion || target;
      const loc = root.getByText(text, { exact: false }).first();
      const deadline = Date.now() + 8000;
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const cnt = await loc.count().catch(() => 0);
        const vis = cnt ? await loc.isVisible().catch(() => false) : false;
        if (!vis) break;
        if (Date.now() > deadline) throw new Error(`expected "${text}" to be absent, but it is visible`);
        await page.waitForTimeout(250);
      }
      break;
    }
    case 'assert_count': {
      const want = Number(value);
      const got = await root.locator(target).count();
      if (got !== want) throw new Error(`expected ${want} of "${target}", found ${got}`);
      break;
    }
    case 'assert_value': {
      const field = await resolveField(root, target);
      const got = await field.inputValue({ timeout: 8000 });
      if (String(got) !== String(value ?? '')) throw new Error(`expected ${target} = "${value}", got "${got}"`);
      break;
    }
    default:
      throw new Error(`unknown action: ${action}`);
  }
  // runtime-error gate (zeus-os failure-snippet pattern)
  const body = (await page.textContent('body').catch(() => '')) || '';
  const snip = FAIL_SNIPPETS.find((s) => body.includes(s));
  if (snip) throw new Error(`runtime error on page: "${snip}"`);
}

function describe(step) {
  const { action, target, value, assertion } = step;
  if (action === 'goto') return `go to ${target || '/'}`;
  if (action === 'hover') return `hover "${target}"`;
  if (action === 'click') return `click "${target}"`;
  if (action === 'fill') return `fill ${target} = "${value}"`;
  if (action === 'select') return `select ${target} = "${value}"`;
  if (action === 'upload') return `upload ${target} = "${value}"`;
  if (action === 'download') return `download "${target}"`;
  if (action === 'dialog') return `dialog ${value}${assertion ? ` "${assertion}"` : ''}`;
  if (action === 'iframe') return target ? `iframe ${target}` : 'iframe off';
  if (action === 'drag') return `drag "${target}" to "${value}"`;
  if (action === 'press') return `press ${value}`;
  if (action === 'clock') return `clock ${value}`;
  if (action === 'wait') return `wait ${target || (value || '') + 'ms'}`;
  if (action === 'wait_until') return `wait until "${target}"`;
  if (action === 'assert') return `assert "${assertion || target}"`;
  if (action === 'assert_url') return `assert url "${assertion || target}"`;
  if (action === 'assert_api') return `assert api ${target}${value ? ` = ${value}` : ''}`;
  if (action === 'assert_aria') return `assert aria ${target}`;
  if (action === 'assert_not') return `assert NOT "${assertion || target}"`;
  if (action === 'assert_count') return `assert count "${target}" = ${value}`;
  if (action === 'assert_value') return `assert ${target} value = "${value}"`;
  return action;
}
function escapeRe(s) { return String(s || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

async function main() {
  const engineName = ENGINES[process.env.ZYVOR_BROWSER] ? process.env.ZYVOR_BROWSER : 'chromium';
  const engine = ENGINES[engineName];
  if (engineName !== 'chromium') emit(`flow: browser ${engineName}`);
  const browser = await engine.launch({
    headless: true,
    args: engineName === 'chromium' && process.env.ZYVOR_NO_SANDBOX === 'true' ? ['--no-sandbox'] : [],
  });
  const ctxOpts = { ignoreHTTPSErrors: process.env.ZYVOR_IGNORE_HTTPS_ERRORS === 'true', viewport: { width: 1440, height: 900 } };
  const deviceName = process.env.ZYVOR_DEVICE;
  if (deviceName && devices[deviceName]) { Object.assign(ctxOpts, devices[deviceName]); emit(`flow: device ${deviceName}`); }
  fs.mkdirSync(outDir, { recursive: true });
  if (record) ctxOpts.recordVideo = { dir: outDir, size: { width: 1440, height: 900 } };

  // reuse a saved session (auth_test) — cookies + localStorage, plus sessionStorage + token re-injected
  let savedSessionStorage = null, savedToken = '';
  if (flow.session && fs.existsSync(flow.session)) {
    try {
      const state = JSON.parse(fs.readFileSync(flow.session, 'utf-8'));
      ctxOpts.storageState = { cookies: state.cookies || [], origins: state.origins || [] };
      savedSessionStorage = state._sessionStorage || null;
      savedToken = state._token || '';
      emit('flow: reusing saved session');
    } catch (e) { emit(`flow: session load failed — ${e}`); }
  }
  const context = await browser.newContext(ctxOpts);
  if (savedSessionStorage || savedToken) {
    await context.addInitScript(({ json, token }) => {
      try { const d = JSON.parse(json || '{}'); for (const k in d) sessionStorage.setItem(k, d[k]); } catch {}
      if (token) {
        const keys = ['token', 'access_token', 'auth_token', 'authToken', 'jwt', 'id_token', 'zeus_os_token', 'zyvor_token', 'apiToken'];
        for (const k of keys) { try { localStorage.setItem(k, token); } catch {} try { sessionStorage.setItem(k, token); } catch {} }
      }
    }, { json: savedSessionStorage, token: savedToken });
  }
  // Playwright trace — time-travel debugger (DOM/network/console per step)
  const wantTrace = flow.trace !== false;
  if (wantTrace) {
    await context.tracing.start({ screenshots: true, snapshots: true, sources: true }).catch(() => {});
  }
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', (e) => pageErrors.push(String(e.message || e)));
  const seenResponses = [];
  page.on('response', (r) => {
    seenResponses.push({ url: r.url(), status: r.status() });
  });

  // network throttle (chromium only — CDP)
  const throttle = process.env.ZYVOR_THROTTLE;
  if ((throttle === '3g' || throttle === 'offline') && engineName === 'chromium') {
    try {
      const cdp = await context.newCDPSession(page);
      await cdp.send('Network.enable');
      await cdp.send('Network.emulateNetworkConditions', throttle === 'offline'
        ? { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 }
        : { offline: false, latency: 400, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8 });
      emit(`flow: throttle ${throttle}`);
    } catch (e) { emit(`flow: throttle failed — ${e}`); }
  }

  // if a session is supplied, skip the best-effort form login
  if (!flow.session) await tryLogin(page);

  const results = [];
  let passed = 0, failed = 0;
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const desc = describe(step);
    emit(`▶ step ${i + 1}/${steps.length}: ${desc}`);
    const before = pageErrors.length;
    let status = 'passed', error = '';
    try {
      await runStep(page, step, i + 1, seenResponses);
      if (pageErrors.length > before) throw new Error(`console: ${pageErrors[before]}`);
      emit(`✓ step ${i + 1}: ${desc}`);
      passed++;
    } catch (err) {
      status = 'failed';
      error = String(err.message || err).slice(0, 300);
      failed++;
      emit(`✗ step ${i + 1}: ${desc} — ${error}`);
    }
    let shot = '';
    try {
      const f = `step-${String(i + 1).padStart(2, '0')}-${slug(desc)}.png`;
      await page.screenshot({ path: path.join(outDir, f) });
      shot = f;
    } catch { /* ignore */ }
    results.push({ n: i + 1, action: step.action, desc, status, error, shot });
    if (status === 'failed' && flow.stop_on_fail) break;
  }

  // stop trace before closing the context
  let traceFile = '';
  if (wantTrace) {
    try {
      traceFile = 'trace.zip';
      await context.tracing.stop({ path: path.join(outDir, traceFile) });
    } catch { traceFile = ''; }
  }

  // finalize video: close context THEN saveAs (Playwright writes on close)
  let videoFile = '';
  const video = record ? page.video() : null;
  await context.close();
  if (video) {
    try {
      videoFile = 'journey.webm';
      await video.saveAs(path.join(outDir, videoFile));
      // remove Playwright's raw hash-named original, keep only journey.webm
      for (const f of fs.readdirSync(outDir)) {
        if (f.endsWith('.webm') && f !== videoFile) fs.rmSync(path.join(outDir, f), { force: true });
      }
    } catch { videoFile = ''; }
  }
  await browser.close();

  process.stdout.write(JSON.stringify({
    base, passed, failed, total: steps.length, steps: results, video: videoFile, trace: traceFile,
    browser: engineName, device: deviceName || 'desktop', throttle: throttle || 'none',
  }));
}

main().catch((err) => { console.error(err); process.exit(1); });
