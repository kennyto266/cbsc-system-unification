const { chromium } = require('playwright');
const fs = require('fs');

async function runFunctionalTest() {
  console.log('🚀 运行 Dashboard 功能测试...\n');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  const testResults = {
    timestamp: new Date().toISOString(),
    results: []
  };

  try {
    // 访问页面
    console.log('1. 访问 Dashboard 页面...');
    await page.goto('http://localhost:3001/dashboard', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // 等待页面完全加载
    await page.waitForTimeout(3000);

    // 检查页面标题
    const title = await page.title();
    console.log(`页面标题: ${title}`);
    testResults.results.push({
      test: '页面标题',
      status: 'PASS',
      details: `标题: ${title}`
    });

    // 查找所有快速操作相关的元素
    console.log('\n2. 查找快速操作按钮...');
    const possibleQuickActions = await page.$$('[class*="quick"], [class*="action"], button, a[href]');

    console.log(`找到 ${possibleQuickActions.length} 个可能的操作元素:`);
    for (let i = 0; i < Math.min(10, possibleQuickActions.length); i++) {
      const element = possibleQuickActions[i];
      const text = await element.textContent();
      const tag = await element.evaluate(el => el.tagName);
      const href = await element.getAttribute('href');
      const className = await element.getAttribute('class');

      if (text && (text.includes('策略') || text.includes('回測') || text.includes('報告') || text.includes('設置'))) {
        console.log(`  - ${tag} [${className?.substring(0, 50)}]: ${text?.substring(0, 50)}${href ? ` (${href})` : ''}`);
      }
    }

    // 测试策略管理链接
    console.log('\n3. 测试策略管理...');
    const strategyLink = await page.locator('a:has-text("策略管理"), a[href*="strategy"]').first();
    if (await strategyLink.count() > 0) {
      console.log('✅ 找到策略管理链接');
      await strategyLink.click();
      await page.waitForTimeout(2000);

      // 返回 dashboard
      await page.goto('http://localhost:3001/dashboard');
      await page.waitForTimeout(2000);
    } else {
      console.log('❌ 未找到策略管理链接');
    }

    // 查找数据表格
    console.log('\n4. 查找数据表格...');
    const tables = await page.$$('table');
    console.log(`找到 ${tables.length} 个表格`);

    for (let i = 0; i < tables.length; i++) {
      const table = tables[i];
      const headers = await table.$$('thead th');
      const rows = await table.$$('tbody tr');

      console.log(`\n表格 ${i + 1}:`);
      console.log(`  表头数量: ${headers.length}`);
      console.log(`  数据行数: ${rows.length}`);

      // 获取表头文本
      const headerTexts = [];
      for (const header of headers) {
        const text = await header.textContent();
        if (text) headerTexts.push(text.trim());
      }
      console.log(`  表头内容: ${headerTexts.join(', ')}`);
    }

    // 查找 HIBOR、货币基础、汇率相关的组件
    console.log('\n5. 查找政府数据组件...');
    const dataComponents = await page.$$('[class*="card"], [class*="data"], [class*="rates"]');
    console.log(`找到 ${dataComponents.length} 个数据组件`);

    for (let i = 0; i < Math.min(5, dataComponents.length); i++) {
      const component = dataComponents[i];
      const text = await component.textContent();
      if (text && (text.includes('HIBOR') || text.includes('貨幣') || text.includes('匯率') || text.includes('利率'))) {
        console.log(`\n组件 ${i + 1}:`);
        console.log(`  内容预览: ${text.substring(0, 100)}...`);
      }
    }

    // 查找策略数量显示
    console.log('\n6. 查找策略相关信息...');
    const strategyTexts = await page.locator('text=/\\d+\\s*个?策略/').all();
    if (strategyTexts.length > 0) {
      for (const element of strategyTexts) {
        const text = await element.textContent();
        console.log(`策略信息: ${text}`);
      }
    }

    // 检查侧边栏或导航菜单
    console.log('\n7. 检查导航菜单...');
    const navElements = await page.$$('nav, [class*="nav"], [class*="menu"], [class*="sidebar"]');
    console.log(`找到 ${navElements.length} 个导航元素`);

    if (navElements.length > 0) {
      for (let i = 0; i < navElements.length; i++) {
        const nav = navElements[i];
        const links = await nav.$$('a');
        if (links.length > 0) {
          console.log(`\n导航 ${i + 1} 包含 ${links.length} 个链接:`);
          for (let j = 0; j < Math.min(5, links.length); j++) {
            const linkText = await links[j].textContent();
            const linkHref = await links[j].getAttribute('href');
            if (linkText) {
              console.log(`  - ${linkText.trim()} (${linkHref || '无链接'})`);
            }
          }
        }
      }
    }

    // 截图
    await page.screenshot({ path: 'dashboard-functional-test-screenshot.png', fullPage: true });
    console.log('\n📸 已保存功能测试截图: dashboard-functional-test-screenshot.png');

  } catch (error) {
    console.error('\n❌ 测试过程中发生错误:', error);
    testResults.error = error.message;
  } finally {
    await browser.close();
  }

  // 保存测试结果
  fs.writeFileSync('dashboard-functional-test-results.json', JSON.stringify(testResults, null, 2));

  console.log('\n✅ 功能测试完成！');
  console.log('📄 测试结果已保存到: dashboard-functional-test-results.json');
}

// 运行测试
runFunctionalTest().catch(console.error);