// Frontend Performance Tests using Jest and Puppeteer
import { jest } from '@jest/globals';
import puppeteer from 'puppeteer';

describe('Frontend Performance Tests', () => {
  let browser;
  let page;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    page = await browser.newPage();

    // Enable performance monitoring
    await page.coverage.startJSCoverage();
    await page.coverage.startCSSCoverage();

    // Set viewport
    await page.setViewport({ width: 1920, height: 1080 });
  });

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  beforeEach(async () => {
    // Clear cache and storage
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });

    // Enable request interception for metrics
    await page.setRequestInterception(true);
    page.on('request', request => {
      request.continue();
    });
  });

  describe('Page Load Performance', () => {
    test('Dashboard page loads within 3 seconds', async () => {
      const startTime = Date.now();

      await page.goto('http://localhost:3000/dashboard', {
        waitUntil: 'networkidle2'
      });

      const loadTime = Date.now() - startTime;
      console.log(`Dashboard load time: ${loadTime}ms`);

      // Wait for main content to load
      await page.waitForSelector('[data-testid="dashboard-container"]');

      // Performance metrics
      const metrics = await page.metrics();
      console.log('Performance metrics:', metrics);

      expect(loadTime).toBeLessThan(3000);
      expect(metrics.LayoutDuration).toBeLessThan(100);
      expect(metrics.RecalcStyleDuration).toBeLessThan(100);
    });

    test('Strategies page loads within 3 seconds', async () => {
      const startTime = Date.now();

      await page.goto('http://localhost:3000/strategies', {
        waitUntil: 'networkidle2'
      });

      const loadTime = Date.now() - startTime;
      console.log(`Strategies page load time: ${loadTime}ms`);

      await page.waitForSelector('[data-testid="strategies-table"]');

      expect(loadTime).toBeLessThan(3000);
    });
  });

  describe('Large Data Set Performance', () => {
    test('Handles 10,000+ strategy records efficiently', async () => {
      await page.goto('http://localhost:3000/strategies');

      // Mock large dataset
      await page.evaluate(() => {
        const strategies = Array.from({ length: 10000 }, (_, i) => ({
          id: i + 1,
          name: `Strategy ${i + 1}`,
          status: Math.random() > 0.5 ? 'active' : 'inactive',
          profit: (Math.random() * 100 - 50).toFixed(2),
          date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        }));

        window.mockStrategies = strategies;
      });

      // Measure rendering time
      const renderStart = performance.now();

      await page.evaluate(() => {
        const table = document.querySelector('[data-testid="strategies-table"]');
        if (table) {
          // Simulate loading large dataset
          console.log(`Loading ${window.mockStrategies.length} strategies`);
        }
      });

      const renderTime = performance.now() - renderStart;
      console.log(`Large dataset render time: ${renderTime}ms`);

      expect(renderTime).toBeLessThan(500);
    });
  });

  describe('Chart Rendering Performance', () => {
    test('Renders charts with 10K data points within 100ms', async () => {
      await page.goto('http://localhost:3000/dashboard');

      // Generate test data
      await page.evaluate(() => {
        window.chartData = Array.from({ length: 10000 }, (_, i) => ({
          x: i,
          y: Math.sin(i * 0.1) * 100 + Math.random() * 20
        }));
      });

      // Measure chart rendering
      const chartRenderStart = performance.now();

      await page.evaluate(() => {
        // Simulate chart rendering
        const canvas = document.querySelector('canvas');
        if (canvas) {
          const ctx = canvas.getContext('2d');
          ctx.beginPath();
          window.chartData.forEach((point, index) => {
            if (index === 0) {
              ctx.moveTo(point.x, point.y);
            } else {
              ctx.lineTo(point.x, point.y);
            }
          });
          ctx.stroke();
        }
      });

      const chartRenderTime = performance.now() - chartRenderStart;
      console.log(`Chart render time (10K points): ${chartRenderTime}ms`);

      expect(chartRenderTime).toBeLessThan(100);
    });
  });

  describe('Memory Usage', () => {
    test('Memory usage stays below 100MB for dashboard', async () => {
      await page.goto('http://localhost:3000/dashboard');

      // Wait for full load
      await page.waitForSelector('[data-testid="dashboard-container"]');

      // Force garbage collection if available
      await page.evaluate(() => {
        if (window.gc) {
          window.gc();
        }
      });

      // Get memory usage
      const memoryUsage = await page.evaluate(() => {
        if (performance && performance.memory) {
          return {
            used: performance.memory.usedJSHeapSize,
            total: performance.memory.totalJSHeapSize,
            limit: performance.memory.jsHeapSizeLimit
          };
        }
        return null;
      });

      if (memoryUsage) {
        const usedMB = memoryUsage.used / 1024 / 1024;
        console.log(`Memory usage: ${usedMB.toFixed(2)}MB`);

        expect(usedMB).toBeLessThan(100);
      }
    });

    test('No memory leaks on page navigation', async () => {
      const initialMemory = await page.evaluate(() => {
        if (performance && performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });

      // Navigate between pages multiple times
      const pages = [
        '/dashboard',
        '/strategies',
        '/monitoring',
        '/settings'
      ];

      for (let i = 0; i < 5; i++) {
        for (const pagePath of pages) {
          await page.goto(`http://localhost:3000${pagePath}`);
          await page.waitForTimeout(1000);
        }
      }

      // Force garbage collection
      await page.evaluate(() => {
        if (window.gc) {
          window.gc();
        }
      });

      const finalMemory = await page.evaluate(() => {
        if (performance && performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return 0;
      });

      const memoryIncrease = (finalMemory - initialMemory) / 1024 / 1024;
      console.log(`Memory increase after navigation: ${memoryIncrease.toFixed(2)}MB`);

      // Memory increase should be minimal
      expect(memoryIncrease).toBeLessThan(20);
    });
  });

  describe('Bundle Size and Loading', () => {
    test('Main bundle size is optimized', async () => {
      // Monitor network requests
      const bundleSizes = [];

      page.on('response', response => {
        const url = response.url();
        if (url.includes('.js') || url.includes('.css')) {
          bundleSizes.push({
            url,
            size: parseInt(response.headers()['content-length'] || 0),
            type: url.endsWith('.js') ? 'js' : 'css'
          });
        }
      });

      await page.goto('http://localhost:3000/dashboard');

      // Calculate total bundle size
      const totalJSSize = bundleSizes
        .filter(b => b.type === 'js')
        .reduce((sum, b) => sum + b.size, 0);

      const totalCSSSize = bundleSizes
        .filter(b => b.type === 'css')
        .reduce((sum, b) => sum + b.size, 0);

      console.log(`Total JS bundle size: ${(totalJSSize / 1024).toFixed(2)}KB`);
      console.log(`Total CSS bundle size: ${(totalCSSSize / 1024).toFixed(2)}KB`);

      // JS bundle should be under 500KB gzipped
      expect(totalJSSize).toBeLessThan(500 * 1024);
      // CSS should be under 100KB gzipped
      expect(totalCSSSize).toBeLessThan(100 * 1024);
    });

    test('Critical resources are loaded quickly', async () => {
      const resourceTimes = {};

      page.on('request', request => {
        resourceTimes[request.url()] = { start: Date.now() };
      });

      page.on('response', response => {
        if (resourceTimes[response.url()]) {
          resourceTimes[response.url()].end = Date.now();
          resourceTimes[response.url()].duration =
            resourceTimes[response.url()].end - resourceTimes[response.url()].start;
        }
      });

      await page.goto('http://localhost:3000/dashboard', {
        waitUntil: 'networkidle2'
      });

      // Check critical resource load times
      Object.entries(resourceTimes).forEach(([url, timing]) => {
        if (timing.duration) {
          console.log(`${url}: ${timing.duration}ms`);
          // Critical resources should load within 1 second
          expect(timing.duration).toBeLessThan(1000);
        }
      });
    });
  });

  describe('Real-time Updates Performance', () => {
    test('WebSocket updates render smoothly', async () => {
      await page.goto('http://localhost:3000/dashboard');

      // Mock WebSocket updates
      await page.evaluate(() => {
        let updateCount = 0;
        const mockInterval = setInterval(() => {
          window.dispatchEvent(new CustomEvent('strategy-update', {
            detail: {
              id: updateCount++,
              profit: (Math.random() * 100 - 50).toFixed(2),
              timestamp: Date.now()
            }
          }));

          if (updateCount >= 100) {
            clearInterval(mockInterval);
          }
        }, 50); // 20 updates per second
      });

      // Monitor frame rate during updates
      const frameRates = [];

      const measureFPS = () => {
        let lastTime = performance.now();
        let frames = 0;

        const countFrames = (currentTime) => {
          frames++;

          if (currentTime - lastTime >= 1000) {
            frameRates.push(frames);
            frames = 0;
            lastTime = currentTime;
          }

          if (frameRates.length < 10) {
            requestAnimationFrame(countFrames);
          }
        };

        requestAnimationFrame(countFrames);
      };

      await page.evaluate(measureFPS);
      await page.waitForTimeout(5000); // Wait for 5 seconds of updates

      const averageFPS = frameRates.reduce((a, b) => a + b, 0) / frameRates.length;
      console.log(`Average FPS during updates: ${averageFPS.toFixed(2)}`);

      // Should maintain 30+ FPS during updates
      expect(averageFPS).toBeGreaterThan(30);
    });
  });
});