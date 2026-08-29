// Copyright 2026 ZyvorAI Labs Private Limited
// SPDX-License-Identifier: Apache-2.0

import { test, expect } from '../../playwright/fixtures/base';
import { waitForPageReady } from '../../playwright/utils/helpers';


test.describe('Coverage: Zeus OS · PacketWolf · Edge & Kubernetes Infrastructure | HyperSDK Platform | HyperSDK Platform · Zyvor', () => {
  test('Coverage: Zeus OS · PacketWolf · Edge & Kubernetes Infrastructure | HyperSDK Platform | HyperSDK Platform · Zyvor', async ({ page, consoleLogs }) => {



    await page.goto('/');
    await waitForPageReady(page);



    await waitForPageReady(page);




    await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveTitle(/.+/);




    const appErrors = consoleLogs.filter(
      (l) => l.startsWith('[error]') && !l.includes('Content Security Policy')
    );
    expect(appErrors).toHaveLength(0);
  });
});