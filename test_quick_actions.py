from playwright.sync_api import sync_playwright
import time

def test_quick_actions():
    with sync_playwright() as p:
        # 啟動瀏覽器（非無頭模式以便觀察）
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("[INFO] 導航到 http://localhost:3001")
        page.goto('http://localhost:3001')
        page.wait_for_load_state('networkidle')

        # 截圖初始狀態
        page.screenshot(path='dashboard_initial.png', full_page=True)
        print("[INFO] 已截圖初始 Dashboard")

        # 測試創建新策略按鈕
        print("\n[INFO] 測試 '創建新策略' 按鈕...")
        createBtn = page.locator('button:has-text("創建新策略")')

        if createBtn.count() > 0:
            print("[OK] 找到創建新策略按鈕")
            # 檢查按鈕是否有 onClick 處理器
            hasOnClick = createBtn.get_attribute('onclick') is not None

            # 點擊按鈕
            print("[INFO] 點擊創建新策略按鈕...")
            createBtn.click()

            # 等待響應
            page.wait_for_timeout(2000)

            # 檢查是否導航到了策略頁面
            current_url = page.url
            if '/dashboard/strategies' in current_url:
                print(f"[OK] 成功導航到: {current_url}")
            else:
                print(f"[WARN] 未導航到策略頁面，當前URL: {current_url}")

            # 截圖點擊後的狀態
            page.screenshot(path='after_create_strategy.png', full_page=True)
            print("[INFO] 已截圖點擊後的狀態")

            # 返回 dashboard
            page.goto('http://localhost:3001/dashboard')
            page.wait_for_load_state('networkidle')
        else:
            print("❌ 未找到創建新策略按鈕")

        # 測試查看市場數據按鈕
        print("\n🔸 測試 '查看市場數據' 按鈕...")
        marketBtn = page.locator('button:has-text("查看市場數據")')

        if marketBtn.count() > 0:
            print("✅ 找到查看市場數據按鈕")

            # 監聽新標籤頁
            with page.expect_popup() as popup_info:
                marketBtn.click()

            # 檢查新標籤頁是否打開
            new_page = popup_info.value
            print("✅ 新標籤頁已打開")

            # 等待一下讓頁面加載
            new_page.wait_for_timeout(2000)

            # 檢查URL
            market_url = new_page.url
            print(f"📍 市場數據頁面URL: {market_url}")

            # 截圖市場數據頁面
            new_page.screenshot(path='market_data_page.png')
            print("📸 已截圖市場數據頁面")

            # 關閉新標籤頁
            new_page.close()
        else:
            print("❌ 未找到查看市場數據按鈕")

        # 測試運行回測按鈕
        print("\n🔸 測試 '運行回測' 按鈕...")
        backtestBtn = page.locator('button:has-text("運行回測")')

        if backtestBtn.count() > 0:
            print("✅ 找到運行回測按鈕")

            # 監聽控制台輸出
            console_messages = []
            page.on("console", lambda msg: console_messages.append(msg.text))

            # 點擊按鈕
            print("🖱️  點擊運行回測按鈕...")
            backtestBtn.click()

            # 等待API響應
            page.wait_for_timeout(3000)

            # 檢查控制台輸出
            if console_messages:
                print("📝 控制台輸出:")
                for msg in console_messages[-5:]:  # 顯示最後5條消息
                    print(f"   - {msg}")

            # 檢查是否有alert（如果有API錯誤）
            try:
                page.wait_for_selector('text=運行回測失敗', timeout=1000)
                print("⚠️  檢測到錯誤提示")
            except:
                print("✅ 回測按鈕點擊成功（無錯誤提示）")
        else:
            print("❌ 未找到運行回測按鈕")

        # 測試導出報告按鈕
        print("\n🔸 測試 '導出報告' 按鈕...")
        exportBtn = page.locator('button:has-text("導出報告")')

        if exportBtn.count() > 0:
            print("✅ 找到導出報告按鈕")

            # 處理下載
            with page.expect_download() as download_info:
                exportBtn.click()

            download = download_info.value
            print(f"✅ 開始下載文件: {download.suggested_filename}")

            # 保存下載的文件
            download.save_as(f"exported_report_{int(time.time())}.pdf")
            print(f"💾 文件已保存")
        else:
            print("❌ 未找到導出報告按鈕")

        # 最終截圖
        page.screenshot(path='dashboard_final.png', full_page=True)
        print("\n📸 已截圖最終 Dashboard 狀態")

        # 保持瀏覽器打開以便手動檢查
        print("\n⏸️  瀏覽器將保持打開，您可以手動檢查...")
        input("按 Enter 鍵關閉瀏覽器...")

        browser.close()

if __name__ == "__main__":
    test_quick_actions()