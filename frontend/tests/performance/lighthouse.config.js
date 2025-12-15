// Lighthouse Performance Testing Configuration
module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3000/dashboard',
        'http://localhost:3000/strategies',
        'http://localhost:3000/strategies/create',
        'http://localhost:3000/monitoring'
      ],
      startServerCommand: 'npm run dev',
      startServerReadyPattern: 'Local:',
      startServerReadyTimeout: 30000,
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--no-sandbox --headless',
        preset: 'desktop',
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0
        }
      }
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.8 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['off'],
        'categories:pwa': ['off']
      }
    },
    upload: {
      target: 'filesystem',
      outputDir: './lighthouse-results'
    }
  }
};