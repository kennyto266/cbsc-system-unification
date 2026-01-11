from playwright.sync_api import sync_playwright
import time
import os

def test_quick_actions_simple():
    with sync_playwright() as p:
        # 啟動瀏覽器（無頭模式）
        browser = p.chromium.launch(headless=False)  # 暫時使用非無頭模式以便調試
        page = browser.new_page()

        print("Navigating to http://localhost:3001...")
        page.goto('http://localhost:3001')
        page.wait_for_load_state('networkidle', timeout=30000)

        # 等待頁面完全加載
        page.wait_for_timeout(5000)

        # 保存當前頁面截圖
        screenshot_name = f'screenshot_{int(time.time())}.png'
        page.screenshot(path=screenshot_name, full_page=True)
        print(f"Screenshot saved: {screenshot_name}")

        # 獲取頁面標題
        title = page.title()
        print(f"Page title: {title}")

        # 獲取當前 URL
        url = page.url
        print(f"Current URL: {url}")

        # 檢查頁面內容是否包含 React 應用的標記
        content = page.content()
        if 'react' in content.lower() or 'next' in content.lower():
            print("[OK] React/Next.js app detected")
        else:
            print("[WARN] React/Next.js app not detected in content")

        # 嘗試多種選擇器來找到按鈕
        print("\nSearching for buttons...")

        # 檢查是否包含快速操作的文字
        button_texts = ["創建新策略", "查看市場數據", "運行回測", "導出報告"]

        for text in button_texts:
            # 嘗試多種選擇器
            selectors = [
                f'button:has-text("{text}")',
                f'a:has-text("{text}")',
                f'div:has-text("{text}")',
                f'*:has-text("{text}")',
                f'[data-testid*="{text}"]',
                f'[aria-label*="{text}"]',
            ]

            found = False
            for selector in selectors:
                elements = page.locator(selector)
                if elements.count() > 0:
                    print(f"  [FOUND] '{text}' with selector '{selector}' ({elements.count()} elements)")
                    found = True

                    # 如果找到，嘗試點擊第一個
                    if "創建新策略" in text and elements.count() > 0:
                        print(f"    -> Clicking '{text}'...")
                        elements.first.click()
                        page.wait_for_timeout(2000)
                        new_url = page.url
                        print(f"    -> Navigated to: {new_url}")
                        # 返回
                        page.goto('http://localhost:3001')
                        page.wait_for_load_state('networkidle')
                    break

            if not found:
                print(f"  [NOT FOUND] '{text}'")

        # 等待一段時間以便觀察
        print("\nPage will stay open for 5 seconds for inspection...")
        page.wait_for_timeout(5000)

        browser.close()
        print("\nTest completed.")

if __name__ == "__main__":
    test_quick_actions_simple()
