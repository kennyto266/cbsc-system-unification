import time
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_with_selenium():
    print("使用 Selenium 測試快速操作按鈕...")
    
    # 使用 Chrome
    driver = webdriver.Chrome()
    
    try:
        # 訪問頁面
        driver.get("http://localhost:3001")
        print("✓ 頁面加載成功")
        
        # 等待頁面加載
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 測試1: 測試原生HTML按鈕
        print("\n測試1: 原生HTML按鈕")
        try:
            html_button = driver.find_element(By.XPATH, "//button[contains(text(), '原生 HTML 按鈕')]")
            print("✓ 找到原生HTML按鈕")
            html_button.click()
            print("✓ 原生HTML按鈕點擊成功")
            time.sleep(1)
            # 處理警告框
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("✓ 警告框已接受")
            except:
                pass
        except Exception as e:
            print(f"✗ 原生HTML按鈕測試失敗: {e}")
        
        # 測試2: 測試創建新策略
        print("\n測試2: 創建新策略")
        try:
            # 先查找包含"創建新策略"文字的元素
            create_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '創建新策略')]")
            if create_buttons:
                # 找到按鈕元素
                create_button = None
                for elem in create_buttons:
                    if elem.tag_name == 'button' or elem.tag_name == 'BUTTON':
                        create_button = elem
                        break
                    # 查找父級按鈕
                    parent = elem.find_element(By.XPATH, "./ancestor::button")
                    if parent:
                        create_button = parent
                        break
                
                if create_button:
                    print("✓ 找到創建新策略按鈕")
                    create_button.click()
                    print("✓ 創建新策略按鈕點擊成功")
                    time.sleep(2)
                    
                    # 檢查是否導航到正確的頁面
                    if 'strategies?action=create' in driver.current_url:
                        print("✓ 成功導航到創建策略頁面")
                    else:
                        print(f"! 當前URL: {driver.current_url}")
                    
                    # 返回儀表板
                    driver.get("http://localhost:3001")
                    time.sleep(1)
                else:
                    print("✗ 找不到創建新策略按鈕元素")
            else:
                print("✗ 找不到創建新策略文字")
        except Exception as e:
            print(f"✗ 創建新策略測試失敗: {e}")
        
        # 測試3: 測試查看市場數據
        print("\n測試3: 查看市場數據")
        try:
            market_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '查看市場數據')]")
            if market_buttons:
                market_button = None
                for elem in market_buttons:
                    if elem.tag_name == 'button' or elem.tag_name == 'BUTTON':
                        market_button = elem
                        break
                    parent = elem.find_element(By.XPATH, "./ancestor::button")
                    if parent:
                        market_button = parent
                        break
                
                if market_button:
                    print("✓ 找到查看市場數據按鈕")
                    # 存儲當前窗口句柄
                    original_window = driver.current_window_handle
                    market_button.click()
                    print("✓ 查看市場數據按鈕點擊成功")
                    time.sleep(2)
                    
                    # 檢查是否打開了新窗口
                    if len(driver.window_handles) > 1:
                        print("✓ 新窗口已打開")
                        # 關閉新窗口
                        for window in driver.window_handles:
                            if window != original_window:
                                driver.switch_to.window(window)
                                driver.close()
                        driver.switch_to.window(original_window)
                    else:
                        print("! 未檢測到新窗口打開")
                else:
                    print("✗ 找不到查看市場數據按鈕元素")
            else:
                print("✗ 找不到查看市場數據文字")
        except Exception as e:
            print(f"✗ 查看市場數據測試失敗: {e}")
        
        # 測試4: 測試運行回測
        print("\n測試4: 運行回測")
        try:
            backtest_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '運行回測')]")
            if backtest_buttons:
                backtest_button = None
                for elem in backtest_buttons:
                    if elem.tag_name == 'button' or elem.tag_name == 'BUTTON':
                        backtest_button = elem
                        break
                    parent = elem.find_element(By.XPATH, "./ancestor::button")
                    if parent:
                        backtest_button = parent
                        break
                
                if backtest_button:
                    print("✓ 找到運行回測按鈕")
                    backtest_button.click()
                    print("✓ 運行回測按鈕點擊成功")
                    time.sleep(3)
                    
                    # 處理可能的警告框
                    try:
                        alert = driver.switch_to.alert
                        print(f"✓ 收到回測響應: {alert.text}")
                        alert.accept()
                    except:
                        print("! 沒有收到警告框（可能正在處理中）")
                else:
                    print("✗ 找不到運行回測按鈕元素")
            else:
                print("✗ 找不到運行回測文字")
        except Exception as e:
            print(f"✗ 運行回測測試失敗: {e}")
        
        # 測試5: 測試導出報告
        print("\n測試5: 導出報告")
        try:
            export_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '導出報告')]")
            if export_buttons:
                export_button = None
                for elem in export_buttons:
                    if elem.tag_name == 'button' or elem.tag_name == 'BUTTON':
                        export_button = elem
                        break
                    parent = elem.find_element(By.XPATH, "./ancestor::button")
                    if parent:
                        export_button = parent
                        break
                
                if export_button:
                    print("✓ 找到導出報告按鈕")
                    export_button.click()
                    print("✓ 導出報告按鈕點擊成功")
                    time.sleep(3)
                    
                    # 處理可能的警告框
                    try:
                        alert = driver.switch_to.alert
                        print(f"✓ 收到導出響應: {alert.text}")
                        alert.accept()
                    except:
                        print("! 沒有收到警告框（下載可能已開始）")
                else:
                    print("✗ 找不到導出報告按鈕元素")
            else:
                print("✗ 找不到導出報告文字")
        except Exception as e:
            print(f"✗ 導出報告測試失敗: {e}")
        
        print("\n=== 測試總結 ===")
        print("所有按鈕測試完成。請檢查瀏覽器控制台以查看詳細日誌。")
        
        # 保持瀏覽器打開5秒供手動檢查
        print("\n瀏覽器將保持打開5秒供手動檢查...")
        time.sleep(5)
        
    except Exception as e:
        print(f"測試出錯: {e}")
    finally:
        driver.quit()
        print("\n測試完成")

if __name__ == "__main__":
    test_with_selenium()
