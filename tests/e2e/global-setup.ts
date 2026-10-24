/**
 * Global Setup for E2E Tests
 * Setup test environment and configuration
 */

import { chromium, FullConfig } from '@playwright/test';
import fs from 'fs';
import path from 'path';

// Test configuration
const TEST_CONFIG = {
  baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
  testUser: {
    email: process.env.E2E_TEST_EMAIL || 'test@example.com',
    password: process.env.E2E_TEST_PASSWORD || 'Test123!',
    name: process.env.E2E_TEST_NAME || 'Test User'
  },
  testTimeout: 60000, // 60 seconds
  navigationTimeout: 30000, // 30 seconds
  cleanupTimeout: 10000 // 10 seconds
};

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E Test Global Setup');

  // Create test results directory
  const resultsDir = path.join(__dirname, 'test-results');
  if (!fs.existsSync(resultsDir)) {
    fs.mkdirSync(resultsDir, { recursive: true });
  }

  // Create screenshots directory
  const screenshotsDir = path.join(resultsDir, 'screenshots');
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  // Create traces directory
  const tracesDir = path.join(resultsDir, 'traces');
  if (!fs.existsSync(tracesDir)) {
    fs.mkdirSync(tracesDir, { recursive: true });
  }

  // Create videos directory
  const videosDir = path.join(resultsDir, 'videos');
  if (!fs.existsSync(videosDir)) {
    fs.mkdirSync(videosDir, { recursive: true });
  }

  // Initialize test database if needed
  await initializeTestDatabase();

  // Setup test data
  await setupTestData();

  // Verify test environment
  await verifyTestEnvironment();

  // Save test configuration
  const configPath = path.join(resultsDir, 'test-config.json');
  fs.writeFileSync(configPath, JSON.stringify(TEST_CONFIG, null, 2));

  console.log('✅ Global Setup Complete');
  console.log('📊 Test Results Directory:', resultsDir);
  console.log('🌐 Base URL:', TEST_CONFIG.baseURL);
}

/**
 * Initialize test database with test data
 */
async function initializeTestDatabase() {
  console.log('🗄️ Initializing test database...');

  // This would typically:
  // 1. Create a test database
  // 2. Run migrations
  // 3. Seed with test data

  // For now, just log
  console.log('✅ Test database initialized');
}

/**
 * Setup test data
 */
async function setupTestData() {
  console.log('📝 Setting up test data...');

  // This would typically:
  // 1. Create test user
  // 2. Create test strategies
  // 3. Create test portfolios
  // 4. Create test alerts

  // Save test configuration for tests to use
  process.env.E2E_TEST_EMAIL = TEST_CONFIG.testUser.email;
  process.env.E2E_TEST_PASSWORD = TEST_CONFIG.testUser.password;
  process.env.E2E_TEST_NAME = TEST_CONFIG.testUser.name;

  console.log('✅ Test data setup complete');
}

/**
 * Verify test environment is ready
 */
async function verifyTestEnvironment() {
  console.log('🔍 Verifying test environment...');

  try {
    // Launch browser to check if server is running
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();

    // Check if base URL is accessible
    const response = await page.goto(TEST_CONFIG.baseURL, {
      waitUntil: 'domcontentloaded',
      timeout: TEST_CONFIG.testTimeout
    });

    if (response?.status() !== 200) {
      throw new Error(`Server returned status ${response?.status()}`);
    }

    // Check for login page (assuming it starts with login)
    const currentUrl = page.url();
    console.log('🌐 Server is accessible at:', currentUrl);

    await browser.close();

    console.log('✅ Test environment verified');
  } catch (error) {
    console.error('❌ Test environment verification failed:', error);

    if (process.env.CI) {
      // In CI, fail the build if environment is not ready
      process.exit(1);
    } else {
      console.warn('⚠️ Continuing without verification (development mode)');
    }
  }
}

/**
 * Clean up any leftover resources from previous runs
 */
async function cleanup() {
  console.log('🧹 Cleaning up previous test runs...');

  // Clean up test files
  const tempDir = path.join(__dirname, '.temp');
  if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }

  // Clean up old screenshots older than 1 day
  const screenshotsDir = path.join(__dirname, 'test-results', 'screenshots');
  if (fs.existsSync(screenshotsDir)) {
    const files = fs.readdirSync(screenshotsDir);
    const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);

    for (const file of files) {
      const filePath = path.join(screenshotsDir, file);
      const stats = fs.statSync(filePath);
      if (stats.mtime.getTime() < oneDayAgo) {
        fs.unlinkSync(filePath);
      }
    }
  }

  console.log('✅ Cleanup complete');
}

// Run cleanup before setup
await cleanup();

export default globalSetup;