// Memory Leak Detection Tool
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class MemoryLeakDetector {
  constructor() {
    this.memorySnapshots = [];
    this.leaks = [];
  }

  async run(options = {}) {
    const {
      url = 'http://localhost:3000/dashboard',
      iterations = 10,
      waitTime = 5000,
      outputPath = './memory-leak-report.json'
    } = options;

    console.log('🔍 Starting Memory Leak Detection...\n');

    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--enable-precise-memory-info']
    });

    try {
      const page = await browser.newPage();

      // Enable memory monitoring
      await page.coverage.startJSCoverage();

      // Collect baseline memory
      console.log('📊 Collecting baseline memory...');
      const baseline = await this.captureMemorySnapshot(page, 'baseline');
      this.memorySnapshots.push(baseline);

      // Run iterations
      for (let i = 0; i < iterations; i++) {
        console.log(`🔄 Iteration ${i + 1}/${iterations}`);

        // Navigate to page
        await page.goto(url, { waitUntil: 'networkidle2' });

        // Simulate user interactions
        await this.simulateUserActivity(page);

        // Wait for garbage collection
        await page.evaluate(() => {
          if (window.gc) {
            window.gc();
          }
        });

        // Wait for async operations
        await page.waitForTimeout(waitTime);

        // Capture memory snapshot
        const snapshot = await this.captureMemorySnapshot(page, `iteration-${i + 1}`);
        this.memorySnapshots.push(snapshot);

        // Check for leaks
        await this.checkForLeaks(snapshot, i);
      }

      // Generate report
      const report = this.generateReport();

      // Save report
      if (outputPath) {
        fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
        console.log(`\n📄 Report saved to: ${outputPath}`);
      }

      // Print summary
      this.printSummary(report);

      return report;

    } finally {
      await browser.close();
    }
  }

  async captureMemorySnapshot(page, label) {
    const metrics = await page.metrics();

    const memoryInfo = await page.evaluate(() => {
      if (performance && performance.memory) {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      }
      return null;
    });

    // Get detailed heap snapshot
    const client = await page.target().createCDPSession();
    const heapSnapshot = await client.send('HeapProfiler.takeHeapSnapshot', {
      reportProgress: false
    });

    const snapshot = {
      label,
      timestamp: new Date().toISOString(),
      metrics,
      memoryInfo,
      heapSnapshot
    };

    if (memoryInfo) {
      console.log(`  💾 Memory - Used: ${(memoryInfo.usedJSHeapSize / 1024 / 1024).toFixed(2)}MB, Total: ${(memoryInfo.totalJSHeapSize / 1024 / 1024).toFixed(2)}MB`);
    }

    return snapshot;
  }

  async simulateUserActivity(page) {
    // Simulate typical user interactions
    const actions = [
      // Scroll around
      () => page.evaluate(() => window.scrollTo(0, document.body.scrollHeight)),
      () => page.waitForTimeout(500),
      () => page.evaluate(() => window.scrollTo(0, 0)),

      // Click on navigation items
      () => page.click('[data-testid="nav-dashboard"]').catch(() => {}),
      () => page.waitForTimeout(500),
      () => page.click('[data-testid="nav-strategies"]').catch(() => {}),

      // Interact with tables (if present)
      () => page.evaluate(() => {
        const rows = document.querySelectorAll('table tbody tr');
        if (rows.length > 0) {
          rows[0].click();
        }
      }),

      // Simulate form interactions
      () => page.type('input[type="text"]', 'test input', { delay: 50 }).catch(() => {}),
      () => page.type('input[type="number"]', '123', { delay: 50 }).catch(() => {}),

      // Trigger chart updates
      () => page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('data-update', {
          detail: { timestamp: Date.now() }
        }));
      })
    ];

    // Execute random actions
    for (let i = 0; i < actions.length; i++) {
      if (Math.random() > 0.5) {
        await actions[i]();
      }
    }
  }

  async checkForLeaks(snapshot, iteration) {
    if (iteration === 0) return; // Skip first iteration

    const current = snapshot.memoryInfo;
    const previous = this.memorySnapshots[this.memorySnapshots.length - 2].memoryInfo;

    if (!current || !previous) return;

    const memoryGrowth = current.usedJSHeapSize - previous.usedJSHeapSize;
    const growthMB = memoryGrowth / 1024 / 1024;

    if (growthMB > 5) { // Threshold for potential leak
      this.leaks.push({
        iteration: iteration + 1,
        memoryGrowth: growthMB,
        currentUsage: current.usedJSHeapSize / 1024 / 1024,
        snapshot: snapshot
      });

      console.log(`  ⚠️ Memory growth detected: +${growthMB.toFixed(2)}MB`);
    }
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalSnapshots: this.memorySnapshots.length,
        leaksDetected: this.leaks.length,
        memoryTrend: this.calculateMemoryTrend()
      },
      snapshots: this.memorySnapshots,
      leaks: this.leaks,
      recommendations: this.generateRecommendations()
    };

    return report;
  }

  calculateMemoryTrend() {
    const memoryValues = this.memorySnapshots
      .filter(s => s.memoryInfo)
      .map(s => s.memoryInfo.usedJSHeapSize / 1024 / 1024);

    if (memoryValues.length < 2) return 'insufficient_data';

    const firstHalf = memoryValues.slice(0, Math.floor(memoryValues.length / 2));
    const secondHalf = memoryValues.slice(Math.floor(memoryValues.length / 2));

    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

    const growth = ((secondAvg - firstAvg) / firstAvg) * 100;

    if (growth > 20) return 'increasing';
    if (growth < -10) return 'decreasing';
    return 'stable';
  }

  generateRecommendations() {
    const recommendations = [];

    if (this.leaks.length > 0) {
      recommendations.push({
        severity: 'high',
        message: `${this.leaks.length} potential memory leaks detected. Check for:`,
        details: [
          'Event listeners not being removed',
          'Timers/intervals not being cleared',
          'DOM references not being nullified',
          'Large objects retained in closures'
        ]
      });
    }

    const trend = this.calculateMemoryTrend();
    if (trend === 'increasing') {
      recommendations.push({
        severity: 'medium',
        message: 'Memory usage is trending upward. Consider:',
        details: [
          'Implementing object pooling',
          'Using WeakMap/WeakSet for temporary references',
          'Regular cleanup in useEffect cleanup functions',
          'Virtual scrolling for large lists'
        ]
      });
    }

    recommendations.push({
      severity: 'info',
      message: 'Best practices to prevent memory leaks:',
      details: [
        'Always remove event listeners in cleanup',
        'Clear timeouts/intervals when unmounting',
        'Avoid memory-intensive operations in render',
        'Use React.memo for expensive components',
        'Implement proper state cleanup'
      ]
    });

    return recommendations;
  }

  printSummary(report) {
    console.log('\n📊 Memory Leak Detection Report');
    console.log('===============================\n');

    // Summary
    console.log(`📈 Total snapshots: ${report.summary.totalSnapshots}`);
    console.log(`🚨 Leaks detected: ${report.summary.leaksDetected}`);
    console.log(`📊 Memory trend: ${report.summary.memoryTrend}\n`);

    // Leaks
    if (report.leaks.length > 0) {
      console.log('⚠️ Detected Leaks:');
      console.log('-------------------');
      report.leaks.forEach(leak => {
        console.log(`Iteration ${leak.iteration}: +${leak.memoryGrowth.toFixed(2)}MB (${leak.currentUsage.toFixed(2)}MB total)`);
      });
      console.log();
    }

    // Recommendations
    console.log('💡 Recommendations:');
    console.log('-------------------');
    report.recommendations.forEach(rec => {
      const icon = rec.severity === 'high' ? '🚨' : rec.severity === 'medium' ? '⚠️' : '💡';
      console.log(`${icon} ${rec.message}`);
      if (rec.details) {
        rec.details.forEach(detail => {
          console.log(`   • ${detail}`);
        });
      }
      console.log();
    });
  }
}

// Run detection if called directly
if (require.main === module) {
  const detector = new MemoryLeakDetector();
  detector.run().catch(console.error);
}

module.exports = MemoryLeakDetector;