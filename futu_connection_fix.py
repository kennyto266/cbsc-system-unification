#!/usr/bin/env python3
"""
富途 OpenD 連接修復工具 - 支持端口配置和連接測試
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
import asyncio

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 富途 OpenD SDK
try:
    import futu as ft
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False
    print("❌ 富途 SDK 未安裝，請運行: pip install futu-opensdk")
    sys.exit(1)

class FutuConnectionManager:
    def __init__(self, host='127.0.0.1', port=11111):
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None

    def connect_with_retry(self, max_retries=3, retry_delay=5) -> bool:
        """帶重試的連接方法"""
        for attempt in range(max_retries):
            try:
                logger.info(f"正在嘗試連接富途 (嘗試 {attempt + 1}/{max_retries})...")
                logger.info(f"連接地址: {self.host}:{self.port}")

                # 創建行情連接
                self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)

                # 測試連接
                ret, data = self.quote_ctx.get_global_state()
                if ret == ft.RET_OK:
                    logger.info("✅ 富途行情連接成功")

                    # 嘗試創建交易連接
                    try:
                        self.trade_ctx = ft.OpenHKTradeContext(host=self.host, port=self.port)
                        ret, data = self.trade_ctx.accinfo_query()
                        if ret == ft.RET_OK:
                            logger.info("✅ 富途交易連接成功")
                            return True
                        else:
                            logger.warning("⚠️ 富途交易連接失敗，但行情連接可用")
                            return True
                    except Exception as e:
                        logger.warning(f"⚠️ 交易連接異常: {e}")
                        logger.info("使用行情連接模式")
                        return True
                else:
                    logger.error(f"❌ 富途連接失敗: {data}")

            except Exception as e:
                logger.error(f"❌ 連接異常: {e}")

            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒後重試...")
                import time
                time.sleep(retry_delay)
            else:
                logger.error("❌ 所有重試都失敗了")

        return False

    def find_available_ports(self, test_ports=[11111, 11011, 11211, 11311, 11411]) -> list:
        """查找可用端口"""
        import socket

        available_ports = []

        for port in test_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    result = sock.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        logger.info(f"✅ 端口 {port} 可用")
                        available_ports.append(port)
                    else:
                        logger.info(f"❌ 端口 {port} 被占用")
            except Exception as e:
                logger.error(f"檢查端口 {port} 時發生錯誤: {e}")

        return available_ports

    def test_connection(self, port: int, timeout=10) -> bool:
        """測試指定端口的連接"""
        logger.info(f"測試富途連接 (端口: {port})...")

        try:
            test_ctx = ft.OpenQuoteContext(host=self.host, port=port)
            ret, data = test_ctx.get_global_state()

            if ret == ft.RET_OK:
                logger.info(f"✅ 端口 {port} 連接成功")
                test_ctx.close()
                return True
            else:
                logger.error(f"❌ 端口 {port} 連接失敗: {data}")
                test_ctx.close()
                return False

        except Exception as e:
            logger.error(f"❌ 測試端口 {port} 時發生異常: {e}")
            return False

def main():
    """主函數"""
    print("🔧 富途 OpenD 連接問題診斷和解決工具")
    print("=" * 60)

    # 步驟 1: 檢查可用端口
    print("\n[步驟 1/4] 檢查富途端口可用性...")

    manager = FutuConnectionManager()
    available_ports = manager.find_available_ports()

    if not available_ports:
        print("❌ 沒有可用的富途端口")
        print("\n解決方案:")
        print("1. 檢查是否有其他富途進程在運行")
        print("2. 終束占用端口的進程")
        print("3. 重啟電腦後再試")
        return False

    print(f"✅ 找到可用端口: {available_ports}")

    # 步驟 2: 測試富途客戶端狀態
    print(f"\n[步驟 2/4] 測試富途客戶端...")

    for port in available_ports[:3]:  # 只測試前3個端口
        if manager.test_connection(port, timeout=3):
            print(f"✅ 端口 {port} 的富途客戶端正在運行")
            working_port = port
            break
    else:
        print("❌ 沒有檢測到運行中的富途客戶端")
        print("\n解決方案:")
        print("1. 啟動富途客戶端 (FutuOpenD)")
        print("2. 確保客戶端登錄成功")
        print("3. 重新運行此工具進行檢查")
        return False

    # 步驟 3: 修復連接配置
    print(f"\n[步驟 3/4] 修復連接配置...")

    if working_port != 11111:
        print(f"⚠️ 富途使用的是非標準端口: {working_port}")
        print(f"💡 更新連接配置...")

        # 更新 POC 配置
        config_file = "POC_QUICK_START.py"
        if os.path.exists(config_file):
            print(f"更新 {config_file} 中的端口配置...")

            # 讀取原文件內容
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 替換端口配置
            old_line = "self.host = host\n        self.port = port"
            new_line = f"self.host = host\n        self.port = {working_port}"

            if old_line in content:
                content = content.replace(old_line, new_line)

                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"✅ 已更新 {config_file} 使用端口 {working_port}")
            else:
                print(f"⚠️ 未找到標準端口配置，請手動更新為 port={working_port}")

    # 步驟 4: 驗證修復
    print(f"\n[步驟 4/4] 驗證修復結果...")

    # 使用正確的端口重新測試連接
    fixed_manager = FutuConnectionManager(port=working_port)

    if fixed_manager.connect_with_retry():
        print(f"✅ 連接修復成功！")
        print(f"\n🎯 修復總結:")
        print(f"   富途端口: {working_port}")
        print(f"   連接地址: 127.0.0.1:{working_port}")
        print(f"   連接狀態: 正常")

        print(f"\n📝 下一步操作:")
        print(f"1. 確保富途客戶端保持運行")
        print(f"2. 運行: python POC_QUICK_START.py")
        print(f"3. 開始富途 POC 開發")

        # 測試基本功能
        try:
            print(f"\n🧪 測試基本功能...")
            ret, data = fixed_manager.quote_ctx.get_market_snapshot(["HK.00700"])
            if ret == ft.RET_OK and data:
                snapshot = data[0]
                print(f"✅ 行情數據獲取成功:")
                print(f"   騁豐控股 (00700): {snapshot['last_price']}")
                print(f"   漲跌: {snapshot['change_val']}")
        except Exception as e:
            print(f"⚠️ 行情測試失敗: {e}")

        return True
    else:
        print(f"❌ 連接修復失敗")
        return False

def print_manual_solutions():
    """打印手動解決方案"""
    print("\n" + "=" * 60)
    print("📋 手動解決方案")
    print("=" * 60)

    print("\n1. Windows 系統解決方案:")
    print("   # 打開命令提示符 (管理員模式)")
    print("   netstat -ano | findstr :11111")
    print("   # 查找占用進程的 PID")
    print("   taskkill /F /PID <PID>")
    print("   # 重啟富途客戶端")

    print("\n2. 富途客戶端設置:")
    print("   - 打開富途客戶端")
    print("   - 檢查設置中的端口配置")
    print("   - 確保端口為 11111")
    print("   - 重新登錄賬戶")

    print("\n3. 防火牆設置:")
    print("   - Windows 防火牆: 允許 FutuOpenD.exe 通過")
    print("   - 殺毒軟件: 將富途添加到白名單")
    print("   - 端口開放: 確保端口 11111 可用")

    print("\n4. 替代端口 (如果 11111 無法使用):")
    print("   - 富途客戶端設置中更改端口")
    print("   - 代碼中使用新端口連接")
    print("   - 確保防火牆允許新端口")

if __name__ == "__main__":
    try:
        success = main()

        if not success:
            print_manual_solutions()

            print("\n" + "=" * 60)
            print("📞 需要更多幫助?")
            print("=" * 60)
            print("1. 重啟電腦後再試")
            print("2. 檢查富途官方文檔")
            print("3. 聯繫富途技術支持")
            print("4. 使用不同的電腦進行測試")

    except KeyboardInterrupt:
        print("\n\n操作被用戶中斷")
    except Exception as e:
        print(f"\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    print("\n按任意鍵退出...")
    try:
        input()
    except:
        pass