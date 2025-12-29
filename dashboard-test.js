const { chromium } = require('playwright');
const fs = require('fs');

async function runDashboardTest() {
  console.log('🚀 开始测试 Dashboard 功能...\n');

  const browser = await chromium.launch({
    headless: false, // 设置为 false 以便观察测试过程
    slowMo: 500 // 减慢操作速度以便观察
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // 创建测试报告
  const testResults = {
    timestamp: new Date().toISOString(),
    results: []
  };

  try {
    // 测试 1: 验证页面是否能正常加载
    console.log('📍 测试 1: 验证页面加载...');
    const response = await page.goto('http://localhost:3001/dashboard', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    if (response.status() === 200) {
      console.log('✅ 页面加载成功');
      testResults.results.push({
        test: '页面加载',
        status: 'PASS',
        details: `状态码: ${response.status()}`
      });
    } else {
      console.log(`❌ 页面加载失败，状态码: ${response.status()}`);
      testResults.results.push({
        test: '页面加载',
        status: 'FAIL',
        details: `状态码: ${response.status()}`
      });
    }

    // 等待页面完全加载
    await page.waitForTimeout(2000);

    // 测试 2: 测试4个快速操作按钮
    console.log('\n📍 测试 2: 测试快速操作按钮...');

    const quickActions = [
      { selector: 'button:has-text("創建新策略")', name: '創建新策略' },
      { selector: 'button:has-text("執行回測")', name: '執行回測' },
      { selector: 'button:has-text("查看報告")', name: '查看報告' },
      { selector: 'button:has-text("系統設置")', name: '系統設置' }
    ];

    for (const action of quickActions) {
      try {
        // 等待按钮可见
        await page.waitForSelector(action.selector, { timeout: 5000 });

        // 检查按钮是否可点击
        const isVisible = await page.isVisible(action.selector);
        const isEnabled = await page.isEnabled(action.selector);

        if (isVisible && isEnabled) {
          // 点击按钮
          console.log(`  点击按钮: ${action.name}`);
          await page.click(action.selector);

          // 等待响应
          await page.waitForTimeout(1000);

          // 检查是否有模态框或页面跳转
          const hasModal = await page.locator('.modal, .dialog, [role="dialog"]').count() > 0;
          const urlChanged = page.url() !== 'http://localhost:3001/dashboard';

          console.log(`    ✅ ${action.name} 按钮可以点击`);
          console.log(`    - 弹出模态框: ${hasModal ? '是' : '否'}`);
          console.log(`    - 页面跳转: ${urlChanged ? '是' : '否'}`);

          testResults.results.push({
            test: `快速操作按钮 - ${action.name}`,
            status: 'PASS',
            details: `可见: ${isVisible}, 可用: ${isEnabled}, 模态框: ${hasModal}, 页面跳转: ${urlChanged}`
          });

          // 如果有模态框或页面跳转，返回原页面
          if (hasModal) {
            await page.keyboard.press('Escape');
            await page.waitForTimeout(500);
          } else if (urlChanged) {
            await page.goto('http://localhost:3001/dashboard');
            await page.waitForTimeout(1000);
          }
        } else {
          console.log(`    ❌ ${action.name} 按钮不可用 (可见: ${isVisible}, 可用: ${isEnabled})`);
          testResults.results.push({
            test: `快速操作按钮 - ${action.name}`,
            status: 'FAIL',
            details: `按钮不可用 (可见: ${isVisible}, 可用: ${isEnabled})`
          });
        }
      } catch (error) {
        console.log(`    ❌ ${action.name} 按钮测试失败: ${error.message}`);
        testResults.results.push({
          test: `快速操作按钮 - ${action.name}`,
          status: 'FAIL',
          details: `错误: ${error.message}`
        });
      }
    }

    // 测试 3: 检查政府数据表格
    console.log('\n📍 测试 3: 检查政府数据表格...');

    const dataTables = [
      { selector: 'table:has-text("HIBOR")', name: 'HIBOR' },
      { selector: 'table:has-text("貨幣基礎")', name: '貨幣基礎' },
      { selector: 'table:has-text("匯率")', name: '匯率' }
    ];

    for (const table of dataTables) {
      try {
        const tableExists = await page.locator(table.selector).count() > 0;

        if (tableExists) {
          // 获取表格行数
          const rowCount = await page.locator(`${table.selector} tbody tr`).count();

          // 获取表格数据
          const tableData = await page.locator(`${table.selector} tbody tr`).first().textContent();

          console.log(`  ✅ ${table.name} 表格存在`);
          console.log(`    - 数据行数: ${rowCount}`);
          console.log(`    - 示例数据: ${tableData?.substring(0, 50)}...`);

          testResults.results.push({
            test: `政府数据表格 - ${table.name}`,
            status: 'PASS',
            details: `数据行数: ${rowCount}`
          });
        } else {
          console.log(`  ❌ ${table.name} 表格未找到`);
          testResults.results.push({
            test: `政府数据表格 - ${table.name}`,
            status: 'FAIL',
            details: '表格未找到'
          });
        }
      } catch (error) {
        console.log(`  ❌ ${table.name} 表格检查失败: ${error.message}`);
        testResults.results.push({
          test: `政府数据表格 - ${table.name}`,
          status: 'FAIL',
          details: `错误: ${error.message}`
        });
      }
    }

    // 测试 4: 验证市场数据是否使用真实数据
    console.log('\n📍 测试 4: 验证市场数据...');

    try {
      // 查找市场数据相关元素
      const marketDataElements = await page.locator('[data-testid*="market"], .market-data, [class*="market"]').all();

      if (marketDataElements.length > 0) {
        console.log(`  找到 ${marketDataElements.length} 个市场数据元素`);

        // 检查是否有 "demo" 或 "test" 字样
        let hasDemoData = false;
        for (const element of marketDataElements) {
          const text = await element.textContent();
          if (text && (text.toLowerCase().includes('demo') || text.toLowerCase().includes('test'))) {
            hasDemoData = true;
            break;
          }
        }

        if (!hasDemoData) {
          console.log('  ✅ 市场数据使用的是真实数据（未发现 demo/test 标记）');
          testResults.results.push({
            test: '市场数据真实性',
            status: 'PASS',
            details: '使用真实数据'
          });
        } else {
          console.log('  ⚠️ 市场数据可能包含演示数据');
          testResults.results.push({
            test: '市场数据真实性',
            status: 'WARNING',
            details: '可能包含演示数据'
          });
        }
      } else {
        console.log('  ❌ 未找到市场数据元素');
        testResults.results.push({
          test: '市场数据真实性',
          status: 'FAIL',
          details: '未找到市场数据'
        });
      }
    } catch (error) {
      console.log(`  ❌ 市场数据验证失败: ${error.message}`);
      testResults.results.push({
        test: '市场数据真实性',
        status: 'FAIL',
        details: `错误: ${error.message}`
      });
    }

    // 测试 5: 检查策略管理
    console.log('\n📍 测试 5: 检查策略管理...');

    try {
      // 查找策略数量显示
      const strategyCountSelectors = [
        '[data-testid*="strategy-count"]',
        '.strategy-count',
        'text=/策略\\s*\\d+/',
        'text=/\\d+\\s*个策略/'
      ];

      let strategyCount = null;
      for (const selector of strategyCountSelectors) {
        try {
          const element = await page.locator(selector).first();
          if (await element.count() > 0) {
            const text = await element.textContent();
            const match = text.match(/\d+/);
            if (match) {
              strategyCount = match[0];
              break;
            }
          }
        } catch (e) {
          // 继续尝试下一个选择器
        }
      }

      if (strategyCount) {
        console.log(`  ✅ 找到策略数量: ${strategyCount} 个策略`);
        testResults.results.push({
          test: '策略管理显示',
          status: 'PASS',
          details: `策略数量: ${strategyCount}`
        });
      } else {
        console.log('  ❌ 未找到策略数量显示');
        testResults.results.push({
          test: '策略管理显示',
          status: 'FAIL',
          details: '未找到策略数量'
        });
      }
    } catch (error) {
      console.log(`  ❌ 策略管理检查失败: ${error.message}`);
      testResults.results.push({
        test: '策略管理显示',
        status: 'FAIL',
        details: `错误: ${error.message}`
      });
    }

    // 截图保存
    await page.screenshot({ path: 'dashboard-test-screenshot.png', fullPage: true });
    console.log('\n📸 已保存页面截图: dashboard-test-screenshot.png');

  } catch (error) {
    console.error('\n❌ 测试过程中发生错误:', error);
    testResults.error = error.message;
  } finally {
    await browser.close();
  }

  // 生成测试报告
  const report = generateTestReport(testResults);
  fs.writeFileSync('dashboard-test-report.json', JSON.stringify(testResults, null, 2));
  fs.writeFileSync('dashboard-test-report.md', report);

  console.log('\n📊 测试完成！');
  console.log('📄 详细报告已保存至:');
  console.log('  - dashboard-test-report.json');
  console.log('  - dashboard-test-report.md');
}

function generateTestReport(results) {
  const passCount = results.results.filter(r => r.status === 'PASS').length;
  const failCount = results.results.filter(r => r.status === 'FAIL').length;
  const warnCount = results.results.filter(r => r.status === 'WARNING').length;

  let report = `# Dashboard 测试报告\n\n`;
  report += `测试时间: ${results.timestamp}\n\n`;
  report += `## 测试摘要\n\n`;
  report += `- ✅ 通过: ${passCount}\n`;
  report += `- ❌ 失败: ${failCount}\n`;
  report += `- ⚠️ 警告: ${warnCount}\n\n`;

  report += `## 详细结果\n\n`;

  results.results.forEach(result => {
    const icon = result.status === 'PASS' ? '✅' : result.status === 'FAIL' ? '❌' : '⚠️';
    report += `### ${icon} ${result.test}\n\n`;
    report += `状态: ${result.status}\n`;
    report += `详情: ${result.details}\n\n`;
  });

  if (results.error) {
    report += `## 错误信息\n\n`;
    report += `\`\`\`\n${results.error}\n\`\`\`\n\n`;
  }

  report += `## 建议\n\n`;

  if (failCount > 0) {
    report += `- 有 ${failCount} 个测试失败，请检查相关功能\n`;
  }

  if (warnCount > 0) {
    report += `- 有 ${warnCount} 个警告，建议进一步验证\n`;
  }

  if (failCount === 0 && warnCount === 0) {
    report += `- 所有测试通过，Dashboard 功能正常\n`;
  }

  return report;
}

// 运行测试
runDashboardTest().catch(console.error);