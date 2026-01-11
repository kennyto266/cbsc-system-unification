const { chromium } = require('playwright');
const fs = require('fs');

async function runDiagnostic() {
  console.log('🔍 运行 Dashboard 诊断...\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 访问页面
    console.log('1. 访问 Dashboard 页面...');
    await page.goto('http://localhost:3001/dashboard', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    // 等待页面加载
    await page.waitForTimeout(3000);

    // 获取页面标题
    const title = await page.title();
    console.log(`页面标题: ${title}\n`);

    // 获取页面HTML内容
    const htmlContent = await page.content();
    fs.writeFileSync('dashboard-page-source.html', htmlContent);
    console.log('📄 页面源代码已保存到: dashboard-page-source.html\n');

    // 查找所有按钮
    console.log('2. 查找所有按钮元素...');
    const buttons = await page.$$('button');
    console.log(`找到 ${buttons.length} 个按钮:`);

    for (let i = 0; i < buttons.length; i++) {
      const text = await buttons[i].textContent();
      const classList = await buttons[i].getAttribute('class');
      const id = await buttons[i].getAttribute('id');
      const dataTestId = await buttons[i].getAttribute('data-testid');

      console.log(`  按钮 ${i + 1}:`);
      console.log(`    文本: ${text}`);
      console.log(`    ID: ${id}`);
      console.log(`    data-testid: ${dataTestId}`);
      console.log(`    类名: ${classList}`);
      console.log('');
    }

    // 查找所有表格
    console.log('\n3. 查找所有表格元素...');
    const tables = await page.$$('table');
    console.log(`找到 ${tables.length} 个表格:`);

    for (let i = 0; i < tables.length; i++) {
      const headers = await tables[i].$$('thead th');
      const headerTexts = [];

      for (const header of headers) {
        const text = await header.textContent();
        headerTexts.push(text);
      }

      console.log(`  表格 ${i + 1}:`);
      console.log(`    表头: ${headerTexts.join(', ')}`);
      console.log('');
    }

    // 查找包含"策略"、"HIBOR"、"货币"、"汇率"等关键词的元素
    console.log('\n4. 查找关键内容元素...');
    const keywords = ['策略', 'strategy', 'HIBOR', '貨幣', '货币', '匯率', '汇率', 'market', '市场'];

    for (const keyword of keywords) {
      const elements = await page.$$(`text=/${keyword}/i`);
      if (elements.length > 0) {
        console.log(`找到 "${keyword}" 相关元素: ${elements.length} 个`);

        // 显示前3个元素的文本
        for (let i = 0; i < Math.min(3, elements.length); i++) {
          const text = await elements[i].textContent();
          const tag = await elements[i].evaluate(el => el.tagName);
          console.log(`  ${tag}: ${text?.substring(0, 100)}...`);
        }
      }
    }

    // 查找所有带有data-testid的元素
    console.log('\n5. 查找带有data-testid的元素...');
    const testElements = await page.$$('[data-testid]');
    console.log(`找到 ${testElements.length} 个带有data-testid的元素:`);

    for (let i = 0; i < Math.min(10, testElements.length); i++) {
      const testId = await testElements[i].getAttribute('data-testid');
      const text = await testElements[i].textContent();
      const tag = await testElements[i].evaluate(el => el.tagName);

      console.log(`  ${tag}[data-testid="${testId}"]: ${text?.substring(0, 50)}...`);
    }

    // 查找快速操作区域（可能是卡片、链接等）
    console.log('\n6. 查找可能的快速操作区域...');
    const possibleSelectors = [
      'a[href*="strategy"]',
      'a[href*="create"]',
      'a[href*="report"]',
      'a[href*="setting"]',
      '.quick-action',
      '.action-btn',
      '.dashboard-action',
      '[class*="card"]',
      '[class*="quick"]',
      '[class*="action"]'
    ];

    for (const selector of possibleSelectors) {
      try {
        const elements = await page.$$(selector);
        if (elements.length > 0) {
          console.log(`找到 "${selector}" 元素: ${elements.length} 个`);

          for (let i = 0; i < Math.min(2, elements.length); i++) {
            const text = await elements[i].textContent();
            const href = await elements[i].getAttribute('href');
            console.log(`    ${href ? `链接: ${href}` : `文本: ${text?.substring(0, 50)}`}`);
          }
        }
      } catch (e) {
        // 忽略选择器错误
      }
    }

    // 截图保存
    await page.screenshot({ path: 'dashboard-diagnostic-screenshot.png', fullPage: true });
    console.log('\n📸 已保存诊断截图: dashboard-diagnostic-screenshot.png');

    // 执行控制台命令检查框架
    console.log('\n7. 检查页面框架...');
    const frameworks = await page.evaluate(() => {
      const info = {
        react: !!(window.React || window.ReactDOM),
        angular: !!(window.angular || window.ng),
        vue: !!(window.Vue || window.Vue2 || window.Vue3),
        jquery: !!(window.jQuery || window.$),
        others: []
      };

      // 检查其他常见框架标识
      if (document.querySelector('[data-reactroot]')) info.others.push('React data-reactroot');
      if (document.querySelector('[ng-app]')) info.others.push('Angular ng-app');
      if (document.querySelector('#app[data-v-]')) info.others.push('Vue data-v-');

      return info;
    });

    console.log('前端框架信息:');
    console.log(`  React: ${frameworks.react}`);
    console.log(`  Angular: ${frameworks.angular}`);
    console.log(`  Vue: ${frameworks.vue}`);
    console.log(`  jQuery: ${frameworks.jquery}`);
    if (frameworks.others.length > 0) {
      console.log(`  其他: ${frameworks.others.join(', ')}`);
    }

  } catch (error) {
    console.error('\n❌ 诊断过程中发生错误:', error);
  } finally {
    await browser.close();
  }

  console.log('\n✅ 诊断完成！');
}

// 运行诊断
runDiagnostic().catch(console.error);