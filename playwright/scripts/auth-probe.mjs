// Copyright 2026 Zyvor AI Labs · https://zyvor.dev
// SPDX-License-Identifier: LicenseRef-Zyvor-Production-1.0

/**
 * Auth & session probe — log in (page form or API), capture a reusable
 * storageState (cookies + localStorage + sessionStorage — packetwolf stores the
 * JWT in sessionStorage), and assert the session behaves: protected access,
 * logout clears it, tampered/expired token is rejected, unauthenticated hits
 * redirect. Modelled on packetwolf auth.setup.ts + ragnarok session specs.
 *
 * Usage: node auth-probe.mjs <configJsonFile> <outDir>
 *   config: { base, login_url, api_login, protected, logout_url, username, password,
 *             token_path, save_session, session_out, insecure }
 * Progress → stderr, result JSON → stdout.
 */

import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { driveFormLogin } from './lib/form-login.mjs';

const cfgFile = process.argv[2];
const outDir = process.argv[3];
if (!cfgFile) { console.error('Usage: node auth-probe.mjs <configJsonFile> <outDir>'); process.exit(2); }
const cfg = JSON.parse(fs.readFileSync(cfgFile, 'utf-8'));
const base = (cfg.base || '').replace(/\/$/, '');
const emit = (m) => console.error(m);
const abs = (u) => (!u ? '' : /^https?:/.test(u) ? u : base + (u.startsWith('/') ? u : '/' + u));

function dotGet(obj, dotted) {
  return dotted.split('.').reduce((o, k) => (o == null ? o : o[k]), obj);
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: process.env.ZYVOR_NO_SANDBOX === 'true' ? ['--no-sandbox'] : [],
  });
  const insecure = cfg.insecure === true || process.env.ZYVOR_IGNORE_HTTPS_ERRORS === 'true';
  const context = await browser.newContext({ ignoreHTTPSErrors: insecure });
  const page = await context.newPage();
  const checks = [];
  const add = (name, ok, detail) => { checks.push({ name, ok, detail }); emit(`${ok ? '✓' : '✗'} ${name}${detail ? ' — ' + detail : ''}`); };

  const protectedUrl = abs(cfg.protected || '/');
  let token = '';

  // ── log in ──
  if (cfg.api_login) {
    // API login: POST credentials, extract token, inject into sessionStorage before app boots
    try {
      const resp = await page.request.post(abs(cfg.api_login), {
        data: { username: cfg.username, password: cfg.password, apiKey: cfg.password },
      });
      const j = await resp.json().catch(() => ({}));
      token = dotGet(j, cfg.token_path || 'token') || j.access_token || j.token || '';
      add('api login', !!token && resp.ok(), token ? 'token acquired' : `status ${resp.status()}`);
      if (token) {
        await context.addInitScript((t) => {
          try { sessionStorage.setItem('token', t); sessionStorage.setItem('access_token', t); } catch {}
          try { localStorage.setItem('token', t); } catch {}
        }, token);
      }
    } catch (e) { add('api login', false, String(e).slice(0, 120)); }
  } else if (cfg.login_url) {
    // drive the login form in-browser (Zoho two-step + Salesforce username fields)
    try {
      await page.goto(abs(cfg.login_url), { waitUntil: 'domcontentloaded', timeout: 30000 });
      const result = await driveFormLogin(page, cfg.username, cfg.password);
      add('form login', result.ok, result.detail);
    } catch (e) { add('form login', false, String(e).slice(0, 120)); }
  }

  // ── (1) protected access works with the session ──
  // Two flavours: header-bearer APIs (token in Authorization) and cookie/session apps.
  // Pass if EITHER an authenticated API request OR a browser navigation reaches the resource.
  try {
    let ok = false, detail = '';
    if (token) {
      // realistic check for a bearer-token API: send the Authorization header
      const resp = await page.request.get(protectedUrl, { headers: { Authorization: `Bearer ${token}` } });
      ok = resp.status() < 400;
      detail = `api ${resp.status()} (Bearer)`;
    }
    if (!ok) {
      const resp = await page.goto(protectedUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      const status = resp ? resp.status() : 0;
      const onLogin = /login|signin|sign-in/i.test(page.url()) || (await page.locator('input[type="password"]').count()) > 0;
      ok = status < 400 && !onLogin;
      detail = onLogin ? 'redirected to login' : `nav ${status}`;
    }
    add('authenticated access', ok, detail);
  } catch (e) { add('authenticated access', false, String(e).slice(0, 120)); }

  // ── save storageState (cookies + localStorage + sessionStorage) ──
  let sessionFile = '';
  if (cfg.save_session !== false && cfg.session_out) {
    try {
      // ensure we're on an app HTML origin (not a JSON API response) so sessionStorage is readable
      if (!/text\/html/i.test((await page.evaluate(() => document.contentType).catch(() => '')) || '')) {
        await page.goto(base + '/', { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
      }
      const state = await context.storageState();
      // storageState() misses sessionStorage — capture it manually and merge
      const ss = await page.evaluate(() => { try { return JSON.stringify(sessionStorage); } catch { return '{}'; } });
      state._sessionStorage = ss;
      if (token) state._token = token;
      fs.mkdirSync(path.dirname(cfg.session_out), { recursive: true });
      fs.writeFileSync(cfg.session_out, JSON.stringify(state));
      sessionFile = cfg.session_out;
      add('session saved', true, path.basename(cfg.session_out));
    } catch (e) { add('session saved', false, String(e).slice(0, 120)); }
  }

  // ── (2) unauthenticated access is gated (fresh context, no session) ──
  try {
    const anon = await browser.newContext({ ignoreHTTPSErrors: insecure });
    const ap = await anon.newPage();
    const resp = await ap.goto(protectedUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    const status = resp ? resp.status() : 0;
    const gated = status === 401 || status === 403 || /login|signin|sign-in/i.test(ap.url()) || (await ap.locator('input[type="password"]').count()) > 0;
    add('unauthenticated gated', gated, gated ? 'redirected/401' : `reachable (status ${status})`);
    await anon.close();
  } catch (e) { add('unauthenticated gated', false, String(e).slice(0, 120)); }

  // ── (3) negative auth: a tampered token is rejected ──
  if (token) {
    try {
      const bad = token.slice(0, -3) + 'xxx';
      const resp = await page.request.get(protectedUrl, { headers: { Authorization: `Bearer ${bad}` } });
      const rejected = resp.status() === 401 || resp.status() === 403;
      add('tampered token rejected', rejected, `status ${resp.status()}`);
    } catch (e) { add('tampered token rejected', false, String(e).slice(0, 120)); }
  }

  // ── (4) logout clears the session ──
  if (cfg.logout_url) {
    try {
      await page.goto(abs(cfg.logout_url), { waitUntil: 'domcontentloaded', timeout: 20000 }).catch(() => {});
      await page.request.post(abs(cfg.logout_url)).catch(() => {});
      const resp = await page.goto(protectedUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
      const status = resp ? resp.status() : 0;
      const gated = status >= 400 || /login|signin/i.test(page.url()) || (await page.locator('input[type="password"]').count()) > 0;
      add('logout clears session', gated, gated ? 'protected now gated' : 'still accessible');
    } catch (e) { add('logout clears session', false, String(e).slice(0, 120)); }
  }

  let shot = '';
  if (outDir) {
    fs.mkdirSync(outDir, { recursive: true });
    try { await page.screenshot({ path: path.join(outDir, 'auth.png') }); shot = 'auth.png'; } catch { /* ignore */ }
  }
  await browser.close();

  const passed = checks.filter((c) => c.ok).length;
  process.stdout.write(JSON.stringify({
    base, checks, passed, failed: checks.length - passed, total: checks.length,
    session_file: sessionFile, has_token: !!token, shot,
  }));
}

main().catch((e) => { console.error(e); process.exit(1); });
