// CBSC Trading System - Playwright Global Setup
// E2E test global configuration

import { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Starting E2E tests...');
  console.log(`Base URL: ${config.projects?.[0]?.use?.baseURL || 'http://localhost:3000'}`);

  // Any global setup before all E2E tests
  // For example: database seeding, test data preparation, etc.
}

export default globalSetup;
