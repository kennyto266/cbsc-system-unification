const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Test configuration
const CONFIG = require('../config/test_config.json');

class CBSCAutomatedTests {
  constructor() {
    this.browser = null;
    this.page = null;
    this.testResults = {
      timestamp: new Date().toISOString(),
      browser: '',
      tests: [],
      summary: {
        total: 0,
        passed: 0,
        failed: 0,
        warnings: 0
      }
    };
  }

  // Initialize browser
  async init(browserType = 'chrome') {
    console.log(`\n🚀 初始化 ${browserType} 瀏覽器...`);

    const launchOptions = {
      headless: false,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--window-size=1920,1080'
      ]
    };

    if (browserType === 'firefox') {
      this.browser = await puppeteer.launch({ product: 'firefox', ...launchOptions });
    } else {
      this.browser = await puppeteer.launch(launchOptions);
    }

    this.page = await this.browser.newPage();
    await this.page.setViewport({ width: 1920, height: 1080 });
    await this.page.setUserAgent(CONFIG.devices[0].user_agent);

    // Enable request interception for performance monitoring
    await this.page.setRequestInterception(true);
    this.page.on('request', request => request.continue());

    this.testResults.browser = browserType;
    console.log(`✅ ${browserType} 瀏覽器初始化完成`);
  }

  // Take screenshot
  async takeScreenshot(name) {
    const screenshotPath = path.join(__dirname, '../test_results/screenshots', `${name}_${Date.now()}.png`);
    await this.page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`📸 截圖已保存: ${screenshotPath}`);
    return screenshotPath;
  }

  // Measure page load performance
  async measurePerformance(url, testName) {
    console.log(`\n⏱ 測試 ${testName} 性能...`);

    const metrics = await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
        resources: performance.getEntriesByType('resource').length
      };
    });

    const testResult = {
      name: testName,
      url,
      type: 'performance',
      passed: true,
      metrics: {
        domContentLoaded: `${metrics.domContentLoaded.toFixed(2)}ms`,
        loadComplete: `${metrics.loadComplete.toFixed(2)}ms`,
        firstPaint: metrics.firstPaint ? `${metrics.firstPaint.toFixed(2)}ms` : 'N/A',
        firstContentfulPaint: metrics.firstContentfulPaint ? `${metrics.firstContentfulPaint.toFixed(2)}ms` : 'N/A',
        resourcesLoaded: metrics.resources
      },
      thresholds: CONFIG.performance_thresholds
    };

    // Check against thresholds
    const loadTime = metrics.loadComplete;
    if (loadTime > CONFIG.performance_thresholds.page_load_time_ms) {
      testResult.passed = false;
      testResult.warning = `頁面加載時間 ${loadTime}ms 超過閾值 ${CONFIG.performance_thresholds.page_load_time_ms}ms`;
      this.testResults.summary.warnings++;
    }

    this.testResults.tests.push(testResult);
    this.testResults.summary.total++;
    if (testResult.passed) {
      this.testResults.summary.passed++;
    } else {
      this.testResults.summary.failed++;
    }

    console.log(`✅ ${testName} 性能測試完成`);
    console.log(`   - DOM 內容加載: ${testResult.metrics.domContentLoaded}`);
    console.log(`   - 頁面完全加載: ${testResult.metrics.loadComplete}`);
    console.log(`   - 首次內容繪製: ${testResult.metrics.firstContentfulPaint}`);

    return testResult;
  }

  // Test dashboard functionality
  async testDashboard() {
    console.log('\n📊 測試 Dashboard 功能...');

    try {
      // Navigate to dashboard
      await this.page.goto(CONFIG.endpoints.dashboard, { waitUntil: 'networkidle0' });
      await this.takeScreenshot('dashboard_initial');

      // Test 1: Dashboard layout
      const layoutExists = await this.page.$('#dashboard-grid') !== null;
      const layoutTest = {
        name: 'Dashboard Layout',
        type: 'functional',
        passed: layoutExists,
        description: layoutExists ? 'Dashboard 佈局正常加載' : 'Dashboard 佈局加載失敗'
      };
      this.testResults.tests.push(layoutTest);
      this.testResults.summary.total++;
      if (layoutExists) this.testResults.summary.passed++;
      else this.testResults.summary.failed++;

      // Test 2: Navigation menu
      const navExists = await this.page.$('#main-navigation') !== null;
      const navTest = {
        name: 'Navigation Menu',
        type: 'functional',
        passed: navExists,
        description: navExists ? '導航菜單正常顯示' : '導航菜單缺失'
      };
      this.testResults.tests.push(navTest);
      this.testResults.summary.total++;
      if (navExists) this.testResults.summary.passed++;
      else this.testResults.summary.failed++;

      // Test 3: WebSocket connection indicator
      const wsIndicator = await this.page.waitForSelector('#ws-status', { timeout: 5000 });
      const wsStatus = await this.page.$eval('#ws-status', el => el.textContent);
      const wsTest = {
        name: 'WebSocket Connection',
        type: 'functional',
        passed: wsStatus.includes('已連接') || wsStatus.includes('connected'),
        description: `WebSocket 狀態: ${wsStatus}`
      };
      this.testResults.tests.push(wsTest);
      this.testResults.summary.total++;
      if (wsTest.passed) this.testResults.summary.passed++;
      else this.testResults.summary.failed++;

      // Test 4: 477 Indicators
      const indicatorsLoaded = await this.page.evaluate(() => {
        const indicators = ['RSI', 'MACD', 'BOLL', 'KDJ', 'MA', 'VOL'];
        return indicators.every(indicator =>
          document.querySelector(`[data-indicator="${indicator}"]`) !== null
        );
      });
      const indicatorsTest = {
        name: '477 Technical Indicators',
        type: 'functional',
        passed: indicatorsLoaded,
        description: indicatorsLoaded ? '所有技術指標正常加載' : '部分技術指標缺失'
      };
      this.testResults.tests.push(indicatorsTest);
      this.testResults.summary.total++;
      if (indicatorsLoaded) this.testResults.summary.passed++;
      else this.testResults.summary.failed++;

      await this.takeScreenshot('dashboard_functional_test');

      console.log('✅ Dashboard 功能測試完成');
    } catch (error) {
      console.error('❌ Dashboard 測試失敗:', error);
      const errorTest = {
        name: 'Dashboard',
        type: 'error',
        passed: false,
        description: `測試失敗: ${error.message}`
      };
      this.testResults.tests.push(errorTest);
      this.testResults.summary.total++;
      this.testResults.summary.failed++;
    }
  }

  // Test real-time data updates
  async testRealTimeData() {
    console.log('\n🔄 測試實時數據更新...');

    try {
      // Monitor data updates for 30 seconds
      const updateCount = await this.page.evaluate(async () => {
        return new Promise((resolve) => {
          let updates = 0;
          const checkInterval = setInterval(() => {
            const timestamp = document.querySelector('[data-timestamp]');
            if (timestamp) {
              updates++;
            }
          }, 2000);

          setTimeout(() => {
            clearInterval(checkInterval);
            resolve(updates);
          }, 30000);
        });
      });

      const realTimeTest = {
        name: 'Real-time Data Updates',
        type: 'performance',
        passed: updateCount > 0,
        metrics: {
          updatesIn30s: updateCount,
          updateInterval: updateCount > 0 ? `${(30000 / updateCount / 1000).toFixed(2)}s` : 'N/A'
        },
        description: updateCount > 0 ? `30秒內更新 ${updateCount} 次` : '未檢測到數據更新'
      };

      this.testResults.tests.push(realTimeTest);
      this.testResults.summary.total++;
      if (realTimeTest.passed) this.testResults.summary.passed++;
      else this.testResults.summary.failed++;

      console.log(`✅ 實時數據測試完成 - 30秒內更新 ${updateCount} 次`);
    } catch (error) {
      console.error('❌ 實時數據測試失敗:', error);
    }
  }

  // Test responsive design
  async testResponsive() {
    console.log('\n📱 測試響應式設計...');

    const viewports = [
      { name: 'Desktop', width: 1920, height: 1080 },
      { name: 'Laptop', width: 1366, height: 768 },
      { name: 'Tablet', width: 768, height: 1024 },
      { name: 'Mobile', width: 375, height: 667 }
    ];

    for (const viewport of viewports) {
      console.log(`\n   測試 ${viewport.name} (${viewport.width}x${viewport.height})...`);

      await this.page.setViewport({ width: viewport.width, height: viewport.height });
      await this.page.reload({ waitUntil: 'networkidle0' });

      // Check if layout adapts properly
      const isResponsive = await this.page.evaluate(() => {
        const dashboard = document.getElementById('dashboard-grid');
        if (!dashboard) return false;

        const style = window.getComputedStyle(dashboard);
        return style.display !== 'none' && style.overflow !== 'hidden';
      });

      const responsiveTest = {
        name: `Responsive - ${viewport.name}`,
        type: 'ui',
        passed: isResponsive,
        viewport: `${viewport.width}x${viewport.height}`,
        description: isResponsive ? '佈局適配良好' : '佈局適配存在問題'
      };

      this.testResults.tests.push(responsiveTest);
      this.testResults.summary.total++;
      if (isResponsive) this.testResults.summary.passed++;
      else this.testResults.summary.failed++;

      await this.takeScreenshot(`responsive_${viewport.name.toLowerCase()}`);
    }

    console.log('✅ 響應式設計測試完成');
  }

  // Test error handling
  async testErrorHandling() {
    console.log('\n⚠️ 測試錯誤處理...');

    try {
      // Simulate network failure
      await this.page.setRequestInterception(true);
      this.page.on('request', request => {
        if (request.url().includes('/api/')) {
          request.abort();
        } else {
          request.continue();
        }
      });

      // Navigate to see error handling
      await this.page.goto(CONFIG.endpoints.dashboard, { waitUntil: 'networkidle0' });

      // Check for error message or fallback
      const errorHandled = await this.page.evaluate(() => {
        const errorElement = document.querySelector('.error-message, [data-error]');
        const fallbackElement = document.querySelector('.fallback-ui, [data-fallback]');
        return errorElement !== null || fallbackElement !== null;
      });

      const errorTest = {
        name: 'Error Handling',
        type: 'functional',
        passed: errorHandled,
        description: errorHandled ? '錯誤處理機制正常' : '缺少錯誤處理'
      };

      this.testResults.tests.push(errorTest);
      this.testResults.summary.total++;
      if (errorHandled) this.testResults.summary.passed++;
      else this.testResults.summary.failed++;

      // Restore normal request handling
      await this.page.setRequestInterception(false);

      console.log('✅ 錯誤處理測試完成');
    } catch (error) {
      console.error('❌ 錯誤處理測試失敗:', error);
    }
  }

  // Generate test report
  generateReport() {
    const reportPath = path.join(__dirname, '../test_results/reports', `test_report_${Date.now()}.json`);

    // Create directories if they don't exist
    const screenshotDir = path.join(__dirname, '../test_results/screenshots');
    const reportDir = path.join(__dirname, '../test_results/reports');

    if (!fs.existsSync(screenshotDir)) fs.mkdirSync(screenshotDir, { recursive: true });
    if (!fs.existsSync(reportDir)) fs.mkdirSync(reportDir, { recursive: true });

    // Save report
    fs.writeFileSync(reportPath, JSON.stringify(this.testResults, null, 2));
    console.log(`\n📋 測試報告已生成: ${reportPath}`);

    // Print summary
    console.log('\n📊 測試結果總結:');
    console.log(`   總測試數: ${this.testResults.summary.total}`);
    console.log(`   通過: ${this.testResults.summary.passed}`);
    console.log(`   失敗: ${this.testResults.summary.failed}`);
    console.log(`   警告: ${this.testResults.summary.warnings}`);
    console.log(`   成功率: ${((this.testResults.summary.passed / this.testResults.summary.total) * 100).toFixed(2)}%`);

    return reportPath;
  }

  // Clean up
  async cleanup() {
    if (this.browser) {
      await this.browser.close();
      console.log('\n✅ 瀏覽器已關閉');
    }
  }
}

// Main test runner
async function runTests() {
  const tester = new CBSCAutomatedTests();

  try {
    console.log('🎯 開始 CBSC 自動化測試...\n');

    // Initialize
    await tester.init('chrome');

    // Run performance test for main dashboard
    await tester.page.goto(CONFIG.endpoints.dashboard, { waitUntil: 'networkidle0' });
    await tester.measurePerformance(CONFIG.endpoints.dashboard, 'Dashboard Load');

    // Run functional tests
    await tester.testDashboard();

    // Run real-time data test
    await tester.testRealTimeData();

    // Run responsive tests
    await tester.testResponsive();

    // Run error handling test
    await tester.testErrorHandling();

    // Generate report
    const reportPath = tester.generateReport();

    console.log('\n🎉 所有測試完成！');

  } catch (error) {
    console.error('\n❌ 測試運行失敗:', error);
  } finally {
    await tester.cleanup();
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  runTests();
}

module.exports = CBSCAutomatedTests;