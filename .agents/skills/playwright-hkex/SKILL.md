---
name: playwright-hkex
description: 使用 Playwright 自動化操作 HKEX 網站，抓取日報表、南北水數據、驗證 Dashboard 頁面。適用於數據採集、網頁測試、截圖驗證、自動化工作流。
---

# Playwright HKEX 自動化技能

使用 Playwright（Python sync API）執行瀏覽器自動化操作。

## 何時使用

- 抓取 HKEX 日報表 / 南北水 / Stock Connect 數據
- 驗證 Dashboard 頁面是否正常顯示
- 自動化點擊、截圖、表單提交
- 網頁內容提取（JavaScript 動態渲染的頁面）

## 核心模式

### 1. 啟動瀏覽器 + 抓取頁面內容

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.hkex.com.hk/...", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)  # 等 JS 渲染
    
    # 提取文字
    text = page.inner_text("body")
    
    # 提取特定元素
    elements = page.query_selector_all(".some-class")
    
    browser.close()
```

### 2. 點擊 + 導航 + 截圖

```python
page.click("text=滬港通")           # 點擊文字
page.click(".ant-menu-item >> nth=0")  # 點擊 CSS
page.screenshot(path="screenshot.png")
```

### 3. 監聽網絡請求（找 hidden API）

```python
api_urls = []
def on_response(response):
    if "json" in response.headers.get("content-type", ""):
        api_urls.append(response.url)
page.on("response", on_response)
page.goto(url, wait_until="networkidle")
# api_urls 裡有所有 API endpoint
```

### 4. HKEX 特定用法

#### 日報表（主板）
- URL pattern: `https://www.hkex.com.hk/chi/stat/smstat/dayquot/d{YYMMDD}c.htm`
- Big5 編碼
- 直接用 `requests` 抓（不需要 Playwright，靜態 HTML）

#### 南北水（Stock Connect）
- 今日數據: `https://www.hkex.com.hk/chi/csm/script/data_SBSH_Turnover_chi.js`
- 歷史數據: `https://www.hkex.com.hk/chi/csm/DailyStat/data_tab_daily_{YYYYMMDD}c.js`
- 靜態 JS 文件，直接用 `requests` 抓

#### 需要 Playwright 的場景
- HKEX Mutual Market 主頁（JavaScript 動態渲染）
- Dashboard 頁面驗證（localhost:3001）
- 任何需要點擊/滾動/等待的場景

### 5. Dashboard 驗證模板

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1489, "height": 900})
    
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    
    page.goto("http://localhost:3001/dashboard", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    html_len = len(page.inner_html("#root"))
    crashed = "应用程序出现错误" in page.inner_text("body")
    
    print(f"HTML: {html_len}, Crashed: {crashed}, Errors: {len(errors)}")
    
    # 測試 sidebar 點擊
    items = page.query_selector_all(".ant-menu-item")
    for item in items:
        item.click()
        page.wait_for_timeout(1000)
        body = page.inner_text("body")
        if "应用程序出现错误" in body:
            print(f"CRASH on: {item.inner_text()}")
    
    browser.close()
```

## 安裝

```bash
pip install playwright beautifulsoup4 requests pandas openpyxl
npx playwright install chromium
```

## 相關腳本

| 腳本 | 用途 | 數據源 |
|---|---|---|
| `scripts/hkex_full_crawler.py` | HKEX 日報表完整數據 | d{YYMMDD}c.htm |
| `scripts/hkex_daily_crawler.py` | HKEX 成交統計（簡版） | d{YYMMDD}c.htm |
| `scripts/stock_connect_crawler.py` | 南北水資金流向 | csm/script/*.js |
| `scripts/multiprocess_backtest.py` | 多 CPU 回測 | 本地 API |
| `scripts/export_dashboard_data.py` | 導出 JSON 供 Dashboard | CSV → JSON |

## 注意事項

- HKEX 頁面用 **Big5 編碼**，requests 要設 `r.encoding = "big5"`
- **只有交易日有數據**，週末/假期返回 404
- 請求間隔至少 0.3 秒，避免被封
- Playwright headless 模式適合自動化，headed 適合 debug
