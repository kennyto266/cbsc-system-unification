// CBSC Trading System - Playwright Global Teardown
// E2E test global cleanup

import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('E2E tests completed.');

  // Any global cleanup after all E2E tests
  // For example: database cleanup, test data removal, etc.
}

export default globalTeardown;
