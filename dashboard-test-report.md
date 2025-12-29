# Dashboard 测试报告

测试时间: 2025-12-16T04:30:18.784Z

## 测试摘要

- ✅ 通过: 3
- ❌ 失败: 7
- ⚠️ 警告: 0

## 详细结果

### ✅ 页面加载

状态: PASS
详情: 状态码: 200

### ✅ 快速操作按钮 - 創建新策略

状态: PASS
详情: 可见: true, 可用: true, 模态框: false, 页面跳转: true

### ❌ 快速操作按钮 - 執行回測

状态: FAIL
详情: 错误: page.waitForSelector: Timeout 5000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("執行回測")') to be visible[22m


### ❌ 快速操作按钮 - 查看報告

状态: FAIL
详情: 错误: page.waitForSelector: Timeout 5000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("查看報告")') to be visible[22m


### ❌ 快速操作按钮 - 系統設置

状态: FAIL
详情: 错误: page.waitForSelector: Timeout 5000ms exceeded.
Call log:
[2m  - waiting for locator('button:has-text("系統設置")') to be visible[22m


### ❌ 政府数据表格 - HIBOR

状态: FAIL
详情: 表格未找到

### ❌ 政府数据表格 - 貨幣基礎

状态: FAIL
详情: 表格未找到

### ❌ 政府数据表格 - 匯率

状态: FAIL
详情: 表格未找到

### ❌ 市场数据真实性

状态: FAIL
详情: 未找到市场数据

### ✅ 策略管理显示

状态: PASS
详情: 策略数量: 8

## 建议

- 有 7 个测试失败，请检查相关功能
