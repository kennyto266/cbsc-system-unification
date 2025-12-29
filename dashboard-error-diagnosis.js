const { chromium } = require('playwright');
const fs = require('fs');

async function diagnoseError() {
  console.log('🔍 诊断 Dashboard 错误...\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 监听控制台输出
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
    console.log(`[${msg.type()}] ${msg.text()}`);
  });

  // 监听页面错误
  const pageErrors = [];
  page.on('pageerror', error => {
    pageErrors.push({
      message: error.message,
      stack: error.stack,
      name: error.name
    });
    console.log(`\n❌ 页面错误: ${error.message}\n`);
  });

  // 监听请求和响应
  const requests = [];
  page.on('request', request => {
    requests.push({
      url: request.url(),
      method: request.method(),
      headers: request.headers()
    });
  });

  const responses = [];
  page.on('response', response => {
    responses.push({
      url: response.url(),
      status: response.status(),
      headers: response.headers()
    });
  });

  try {
    // 访问页面
    console.log('1. 访问 Dashboard 页面...');
    await page.goto('http://localhost:3001/dashboard', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // 等待页面加载完成
    await page.waitForTimeout(5000);

    // 检查是否有错误提示
    const errorElement = await page.locator('text=/num\\.toFixed is not a function/').first();
    if (await errorElement.count() > 0) {
      console.log('\n发现错误信息: num.toFixed is not a function');

      // 查找相关代码位置
      const pageContent = await page.content();

      // 查找可能的错误源
      console.log('\n2. 分析错误来源...');

      // 检查页面是否有数据加载
      const dataElements = await page.evaluate(() => {
        const results = {
          scripts: [],
          dataElements: []
        };

        // 查找所有脚本
        document.querySelectorAll('script').forEach(script => {
          if (script.src) {
            results.scripts.push(script.src);
          }
        });

        // 查找可能的数据容器
        document.querySelectorAll('[class*="data"], [class*="table"], [class*="card"]').forEach(el => {
          results.dataElements.push({
            tag: el.tagName,
            class: el.className,
            text: el.textContent?.substring(0, 100)
          });
        });

        return results;
      });

      console.log(`\n找到 ${dataElements.scripts.length} 个脚本:`);
      dataElements.scripts.slice(0, 5).forEach(script => {
        console.log(`  - ${script}`);
      });

      console.log(`\n找到 ${dataElements.dataElements.length} 个数据元素:`);
      dataElements.dataElements.forEach(el => {
        console.log(`  - ${el.tag}: ${el.class}`);
      });
    }

    // 尝试点击重试按钮
    const retryButton = await page.locator('button:has-text("重試")').first();
    if (await retryButton.count() > 0) {
      console.log('\n3. 点击重试按钮...');
      await retryButton.click();
      await page.waitForTimeout(3000);

      // 检查页面是否恢复正常
      const hasError = await page.locator('text=/系统错误|num\\.toFixed/').count() > 0;
      if (!hasError) {
        console.log('✅ 页面已恢复正常！');

        // 重新测试功能
        await testFeatures(page);
      } else {
        console.log('❌ 重试后仍有错误');
      }
    }

    // 保存诊断信息
    const diagnosis = {
      timestamp: new Date().toISOString(),
      url: page.url(),
      consoleMessages,
      pageErrors,
      requests: requests.slice(0, 10),
      responses: responses.slice(0, 10)
    };

    fs.writeFileSync('dashboard-diagnosis.json', JSON.stringify(diagnosis, null, 2));
    console.log('\n📄 诊断信息已保存到: dashboard-diagnosis.json');

  } catch (error) {
    console.error('\n❌ 诊断失败:', error);
  } finally {
    await browser.close();
  }
}

async function testFeatures(page) {
  console.log('\n🧪 测试页面功能...');

  // 测试快速操作按钮
  const actions = ['創建新策略', '執行回測', '查看報告', '系統設置'];

  for (const action of actions) {
    const button = await page.locator(`button:has-text("${action}")`).first();
    if (await button.count() > 0) {
      console.log(`✅ 找到按钮: ${action}`);
      const isVisible = await button.isVisible();
      const isEnabled = await button.isEnabled();
      console.log(`   - 可见: ${isVisible}, 可用: ${isEnabled}`);
    } else {
      console.log(`❌ 未找到按钮: ${action}`);
    }
  }

  // 检查表格
  const tables = await page.$$('table');
  console.log(`\n找到 ${tables.length} 个表格`);

  // 检查策略相关内容
  const strategyTexts = await page.locator('text=/策略/').all();
  console.log(`\n找到 ${strategyTexts.length} 个包含"策略"的元素`);
}

// 运行诊断
diagnoseError().catch(console.error);