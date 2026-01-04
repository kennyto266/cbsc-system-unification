#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途API連接測試 - 使用新的端口配置
API端口: 1130, WebSocket端口: 11111
"""

import os
import sys
import json
from datetime import datetime

# 設置環境變數
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加富途SDK路徑
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# 新的連接配置
API_PORT = 1130
WEBSOCKET_PORT = 11111
WEBSOCKET_KEY = "cb8fe2a668e624da"
HOST = '127.0.0.1'

class FutuUpdatedConnectionTester:
    def __init__(self):
        self.quote_ctx = None
        self.trade_ctx = None
        self.api_port = API_PORT
        self.websocket_port = WEBSOCKET_PORT
        self.websocket_key = WEBSOCKET_KEY

    def test_port_connectivity(self):
        """測試端口連通性"""
        print("=== 端口連通性測試 ===")
        print(f"API端口: {self.api_port}")
        print(f"WebSocket端口: {self.websocket_port}")
        print(f"WebSocket密钥: {self.websocket_key}")
        print("-" * 50)

        import socket
        ports_to_test = [
            (self.api_port, "API"),
            (self.websocket_port, "WebSocket")
        ]

        all_ok = True
        for port, port_type in ports_to_test:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((HOST, port))
                sock.close()

                if result == 0:
                    print(f"✅ {port_type}端口 {port} 可連接")
                else:
                    print(f"❌ {port_type}端口 {port} 連接失敗 (錯誤: {result})")
                    all_ok = False

            except Exception as e:
                print(f"❌ 檢查{port_type}端口 {port} 失敗: {e}")
                all_ok = False

        return all_ok

    def test_api_connection(self):
        """測試API連接"""
        print("\n=== API連接測試 ===")

        try:
            import futu as ft
            print(f"富途API版本: {ft.__version__}")

            # 使用新的API端口創建連接
            print(f"正在連接到 API端口 {self.api_port}...")
            self.quote_ctx = ft.OpenQuoteContext(host=HOST, port=self.api_port)

            # 測試連接狀態
            print("測試連接狀態...")
            ret, data = self.quote_ctx.get_global_state()

            if ret == ft.RET_OK:
                print("✅ API連接成功！")
                print(f"全局狀態: {data}")
                return True
            else:
                print(f"❌ API連接失敗: {data}")
                return False

        except Exception as e:
            print(f"❌ API連接異常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_user_info(self):
        """測試用戶信息"""
        print("\n=== 用戶信息測試 ===")

        try:
            import futu as ft

            # 獲取用戶信息
            ret, data = self.quote_ctx.get_user_info()

            if ret == ft.RET_OK:
                print("✅ 用戶信息獲取成功")
                if data is not None and len(data) > 0:
                    user_info = data.iloc[0]
                    print(f"  用戶ID: {user_info.get('user_id', 'N/A')}")
                    print(f"  登錄狀態: {user_info.get('login_status', 'N/A')}")
                    print(f"  賬戶名稱: {user_info.get('name', 'N/A')}")
                    return True
                else:
                    print("⚠️ 用戶信息為空")
                    return True
            else:
                print(f"❌ 用戶信息獲取失敗: {data}")
                return False

        except Exception as e:
            print(f"❌ 用戶信息測試異常: {e}")
            return False

    def test_demo_accounts(self):
        """測試模擬賬戶"""
        print("\n=== 模擬賬戶測試 ===")

        try:
            import futu as ft

            # 創建交易上下文
            print("創建交易上下文...")
            self.trade_ctx = ft.OpenHKTradeContext(host=HOST, port=self.api_port)

            # 查詢模擬賬戶
            print("查詢模擬賬戶...")
            ret, data = self.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            if ret == ft.RET_OK:
                print("✅ 模擬賬戶查詢成功")

                if data is not None and len(data) > 0:
                    print(f"找到 {len(data)} 個模擬賬戶:")
                    for index, row in data.iterrows():
                        acc_id = str(row.get('acc_id', ''))
                        acc_type = str(row.get('acc_type', ''))
                        cash = float(row.get('cash', 0))
                        total_assets = float(row.get('total_assets', 0))

                        print(f"  賬戶 {index + 1}:")
                        print(f"    賬戶ID: {acc_id}")
                        print(f"    賬戶類型: {acc_type}")
                        print(f"    總資產: {total_assets}")

                    return True
                else:
                    print("⚠️ 沒有找到模擬賬戶")
                    return False
            else:
                print(f"❌ 模擬賬戶查詢失敗: {data}")
                return False

        except Exception as e:
            print(f"❌ 模擬賬戶測試異常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_market_data(self):
        """測試市場數據"""
        print("\n=== 市場數據測試 ===")

        try:
            import futu as ft

            # 測試港股
            test_stocks = ['HK.00700', 'HK.0388', 'HK.1398']

            for stock_code in test_stocks:
                print(f"測試股票: {stock_code}")

                # 獲取市場快照
                ret, data = self.quote_ctx.get_market_snapshot([stock_code])

                if ret == ft.RET_OK and data is not None and len(data) > 0:
                    stock_data = data.iloc[0]
                    last_price = float(stock_data.get('last_price', 0))
                    volume = int(stock_data.get('volume', 0))
                    change_val = float(stock_data.get('change_val', 0))

                    print(f"  ✅ 最新價: {last_price}")
                    print(f"  成交量: {volume}")
                    print(f"  漲跌額: {change_val}")
                else:
                    print(f"  ❌ 無法獲取數據: {data}")

            return True

        except Exception as e:
            print(f"❌ 市場數據測試異常: {e}")
            return False

    def cleanup(self):
        """清理資源"""
        print("\n=== 清理資源 ===")

        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                print("✅ 行情上下文已關閉")

            if self.trade_ctx:
                self.trade_ctx.close()
                print("✅ 交易上下文已關閉")

        except Exception as e:
            print(f"❌ 清理資源失敗: {e}")

    def run_full_test(self):
        """運行完整測試"""
        print("富途API連接測試 (新端口配置)")
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        results = {
            'port_connectivity': False,
            'api_connection': False,
            'user_info': False,
            'demo_accounts': False,
            'market_data': False
        }

        try:
            # 1. 端口連通性測試
            results['port_connectivity'] = self.test_port_connectivity()
            if not results['port_connectivity']:
                print("❌ 端口連通性失敗，測試終止")
                return results

            # 2. API連接測試
            results['api_connection'] = self.test_api_connection()
            if not results['api_connection']:
                print("❌ API連接失敗，測試終止")
                return results

            # 3. 用戶信息測試
            results['user_info'] = self.test_user_info()

            # 4. 模擬賬戶測試
            results['demo_accounts'] = self.test_demo_accounts()

            # 5. 市場數據測試
            results['market_data'] = self.test_market_data()

        except Exception as e:
            print(f"❌ 測試過程發生異常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        return results

def generate_report(results):
    """生成測試報告"""
    print("\n" + "=" * 60)
    print("測試結果報告")
    print("-" * 30)

    status_map = {
        True: "✅ PASS",
        False: "❌ FAIL"
    }

    print(f"端口連通性: {status_map.get(results['port_connectivity'])}")
    print(f"API連接: {status_map.get(results['api_connection'])}")
    print(f"用戶信息: {status_map.get(results['user_info'])}")
    print(f"模擬賬戶: {status_map.get(results['demo_accounts'])}")
    print(f"市場數據: {status_map.get(results['market_data'])}")

    # 保存結果
    report_data = {
        'api_port': API_PORT,
        'websocket_port': WEBSOCKET_PORT,
        'websocket_key': WEBSOCKET_KEY,
        'test_time': datetime.now().isoformat(),
        'results': results
    }

    try:
        with open('futu_connection_results.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"\n詳細結果已保存到: futu_connection_results.json")
    except Exception as e:
        print(f"保存結果失敗: {e}")

    # 總結
    success_count = sum(1 for v in results.values() if v is True)
    total_count = len(results)

    if success_count == total_count:
        print(f"\n🎉 所有測試通過！富途API完全就緒")
        print("✅ 可以開始POC開發和實時交易系統集成")
        print("\n🚀 下一步操作:")
        print("1. 開發實時行情獲取功能")
        print("2. 實現交易訂單執行")
        print("3. 集成風險管理系統")
        print("4. 構建量化策略回測")
    elif success_count >= total_count * 0.7:
        print(f"\n✅ 大部分功能可用")
        print("📊 基本功能正常，可以開始開發")
    else:
        print(f"\n⚠️ 部分功能需要檢查")
        print("🔧 請檢查富途客戶端登錄狀態和端口配置")

def main():
    """主函數"""
    tester = FutuUpdatedConnectionTester()
    results = tester.run_full_test()
    generate_report(results)

    # 判斷整體成功
    success = all(results.values())
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)