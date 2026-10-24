import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Global settings
  testDir: './',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,

  // Reporters
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results.xml' }],
    ['json', { outputFile: 'test-results.json' }],
    ['line'], // Console reporter
  ],

  // Global setup and teardown
  globalSetup: './global-setup.ts',
  globalTeardown: './global-teardown.ts',

  // Projects
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Browser options
        launchOptions: {
          args: [
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--window-size=1920,1080'
          ]
        },
        // Context options
        contextOptions: {
          permissions: ['notifications', 'clipboard-read', 'clipboard-write'],
          viewport: { width: 1920, height: 1080 },
          ignoreHTTPSErrors: true,
          // User agent
        },
        // Custom timeouts
        actionTimeout: 30000,
        navigationTimeout: 60000,
      },
      // Test specific options
      testTimeout: 180000, // 3 minutes
      expect: {
        timeout: 10000
      },
      // Screenshot options
      screenshot: 'only-on-failure',
      video: 'retain-on-failure',
      trace: 'retain-on-failure',
    },

    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        launchOptions: {
          args: ['--window-size=1920,1080']
        },
        contextOptions: {
          permissions: ['notifications'],
          viewport: { width: 1920, height: 1080 },
          ignoreHTTPSErrors: true
        }
      }
    },

    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        contextOptions: {
          permissions: ['notifications'],
          viewport: { width: 1920, height: 1080 },
          ignoreHTTPSErrors: true
        }
      }
    },

    // Mobile browsers
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        contextOptions: {
          permissions: ['notifications'],
          ignoreHTTPSErrors: true,
          // Mobile specific options
          isMobile: true,
          hasTouch: true
        }
      }
    },

    {
      name: 'mobile-safari',
      use: {
        ...devices['iPhone 12'],
        contextOptions: {
          permissions: ['notifications'],
          ignoreHTTPSErrors: true,
          isMobile: true,
          hasTouch: true
        }
      }
    },

    // Tablet browsers
    {
      name: 'tablet-chrome',
      use: {
        ...devices['iPad Pro'],
        contextOptions: {
          permissions: ['notifications'],
          ignoreHTTPSErrors: true,
          isMobile: true,
          hasTouch: true
        }
      }
    }
  ],

  // Web server configuration
  webServer: {
    command: 'npm run dev',
    port: 3000,
    timeout: 120000,
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe'
  },

  // Output directory
  outputDir: 'test-results',

  // Global test options
  use: {
    // Global retries
    trace: 'on-first-retry',
    // Screenshots
    screenshot: {
      mode: 'only-on-failure',
      fullPage: true,
      animations: 'disabled'
    },
    // Video recording
    video: {
      mode: 'retain-on-failure',
      size: { width: 1920, height: 1080 }
    }
  },

  // Metadata
  metadata: {
    'test-process': 'playwright',
    'test-environment': process.env.NODE_ENV || 'test',
    'test-timestamp': new Date().toISOString()
  }
});