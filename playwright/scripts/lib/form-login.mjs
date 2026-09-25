// Copyright 2026 Zyvor AI Labs · https://zyvor.dev
// SPDX-License-Identifier: LicenseRef-Zyvor-Production-1.0
/**
 * Shared CRM/SaaS form-login heuristics for auth-probe + flow-run.
 * Handles Zoho Accounts two-step (#login_id → Next → #password) and
 * Salesforce My Domain / login.salesforce.com (#username / #password / #Login).
 */

/** Prefer CRM-specific fields, then generic email/user/text. */
export function userFieldLocator(page) {
  return page.locator(
    [
      '#username',
      '#login_id',
      'input[name="username"]',
      'input[id*="login" i]',
      'input[name*="login" i]',
      'input[type="email"]',
      'input[name*="user" i]',
      'input[name*="email" i]',
      'input[type="text"]',
    ].join(', ')
  ).first();
}

export function passwordFieldLocator(page) {
  return page.locator('#password, input[name="pw"], input[name="password"], input[type="password"]').first();
}

export function submitLocator(page) {
  return page.locator(
    [
      '#Login',
      '#nextbtn',
      'button#nextbtn',
      'input#Login',
      'button[type="submit"]',
      'input[type="submit"]',
      'button:has-text("sign in")',
      'button:has-text("log in")',
      'button:has-text("next")',
      'button:has-text("continue")',
    ].join(', ')
  ).first();
}

/**
 * Drive a visible login form. Supports Zoho email-first (password hidden until Next).
 * @returns {{ ok: boolean, detail: string }}
 */
export async function driveFormLogin(page, username, password, { timeout = 8000 } = {}) {
  const userLoc = userFieldLocator(page);
  await userLoc.waitFor({ state: 'visible', timeout });
  await userLoc.fill(username, { timeout });

  let pass = passwordFieldLocator(page);
  const passVisible = await pass.isVisible().catch(() => false);
  if (!passVisible) {
    // Zoho Accounts: email step → Next → password step
    const next = page.locator('#nextbtn, button#nextbtn, button:has-text("Next"), button:has-text("Continue")').first();
    if ((await next.count()) && (await next.isVisible().catch(() => false))) {
      await next.click({ timeout });
      await pass.waitFor({ state: 'visible', timeout: 15000 });
    }
  }

  pass = passwordFieldLocator(page);
  await pass.waitFor({ state: 'visible', timeout });
  await pass.fill(password, { timeout });

  const before = page.url();
  await Promise.all([
    page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {}),
    submitLocator(page).click({ timeout }),
  ]);
  // Leave login host or drop the password field
  await page.waitForTimeout(800);
  try {
    await page.waitForFunction(
      (prev) => {
        const u = location.href;
        if (u !== prev && !/signin|login\.do|\/login\/?/i.test(u)) return true;
        return !document.querySelector('input[type="password"]');
      },
      before,
      { timeout: 25000 }
    );
  } catch {
    /* fall through — caller judges success */
  }

  const stillPassword = (await page.locator('input[type="password"]').count()) > 0
    && /signin|login|salesforce\.com\/\?|accounts\.zoho/i.test(page.url());
  return {
    ok: !stillPassword,
    detail: stillPassword ? 'still on login page' : `now at ${page.url()}`,
  };
}
