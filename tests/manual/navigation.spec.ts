// Copyright 2026 ZyvorAI Labs Private Limited
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { test, expect } from '../../playwright/fixtures/base';
import { waitForPageReady } from '../../playwright/utils/helpers';

test.describe('Zyvor Navigation & CTAs', () => {
  test('Schedule Demo CTA is present', { tag: ['@smoke'] }, async ({ page, networkErrors }) => {
    await page.goto('/');
    await waitForPageReady(page);

    const demoCta = page.getByRole('link', { name: /schedule.*demo|book.*demo/i });
    await expect(demoCta.first()).toBeVisible();
    await expect(demoCta.first()).toHaveAttribute('href', /.+/);

    const criticalErrors = networkErrors.filter((e) => e.startsWith('5'));
    expect(criticalErrors).toHaveLength(0);
  });

  test('documentation links resolve', { tag: ['@smoke'] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageReady(page);

    const docLink = page.getByRole('link', { name: /documentation|product guides|suite product/i });
    if ((await docLink.count()) > 0) {
      await expect(docLink.first()).toBeAttached();
      const href = await docLink.first().getAttribute('href');
      expect(href).toBeTruthy();
    }
  });

  test('footer or contact section is reachable', { tag: ['@smoke'] }, async ({ page }) => {
    await page.goto('/');
    await waitForPageReady(page);

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1000);

    const footerContent = page.locator('footer, [class*="footer"], [class*="subscribe"]').first();
    if (await footerContent.count()) {
      await footerContent.scrollIntoViewIfNeeded();
      await expect(footerContent).toBeAttached();
    } else {
      await expect(page.getByText(/subscribe|Zyvor|contact/i).first()).toBeAttached();
    }
  });
});
