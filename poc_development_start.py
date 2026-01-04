#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途POC開發啟動 - 使用端口1130
完整的市場數據獲取和模擬交易測試
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# 設置環境變數
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 添加富途SDK路徑
sys.path.append(r'C:\Users\Penguin8n\AppData\Roaming\Python\Python313\site-packages')

# 連接配置
API_PORT = 1130
HOST = '127.0.0.1'
WEBSOCKET_KEY = "cb8fe2a668e624da"
USER_ID = "2860386"

class FutuPOCDeveloper:
    def __init__(self):
        self.quote_ctx = None
        self.trade_ctx = None
        self.api_port = API_PORT
        self.user_id = USER_ID
        self.websocket_key = WEBSOCKET_KEY

    async def initialize_connection(self):
        """初始化連接"""
        print("=== Initialize Futu Connection ===")
        print(f"API Port: {self.api_port}")
        print(f"User ID: {self.user_id}")
        print(f"WebSocket Key: {self.websocket_key}")

        try:
            import futu as ft
            print(f"富途API版本: {ft.__version__}")

            # 創建連接
            print("創建行情連接...")
            self.quote_ctx = ft.OpenQuoteContext(host=HOST, port=self.api_port)
            print("創建交易連接...")
            self.trade_ctx = ft.OpenHKTradeContext(host=HOST, port=self.api_port)

            return True

        except Exception as e:
            print(f"初始化連接失敗: {e}")
            return False

    async def test_market_data(self):
        """測試市場數據獲取"""
        print("\n=== 市場數據測試 ===")

        try:
            import futu as ft

            # 測試多隻股票
            test_stocks = [
                'HK.00700',  # 騰訊控股
                'HK.0388',  # 香港交易所
                'HK.1398',  # 工商銀行
                'HK.0941',  # 中國移動
                'HK.2318'   # 中國平安
            ]

            market_data = []
            for stock_code in test_stocks:
                print(f"獲取 {stock_code} 數據...")

                # 獲取市場快照
                ret, data = self.quote_ctx.get_market_snapshot([stock_code])

                if ret == ft.RET_OK and data is not None and len(data) > 0:
                    stock_data = data.iloc[0]
                    stock_info = {
                        'code': stock_code,
                        'last_price': float(stock_data.get('last_price', 0)),
                        'volume': int(stock_data.get('volume', 0)),
                        'change_val': float(stock_data.get('change_val', 0)),
                        'change_rate': float(stock_data.get('change_rate', 0)),
                        'amplitude': float(stock_data.get('amplitude', 0)),
                        'timestamp': stock_data.get('last_time', '')
                    }
                    market_data.append(stock_info)

                    print(f"  {stock_code}: 價格={stock_info['last_price']}, "
                          f"成交量={stock_info['volume']}, "
                          f"漲跌={stock_info['change_val']}")
                else:
                    print(f"  {stock_code}: 數據獲取失敗")

                await asyncio.sleep(0.2)  # 避免頻繁請求

            print(f"\n成功獲取 {len(market_data)} 隻股票數據")
            return market_data

        except Exception as e:
            print(f"市場數據測試異常: {e}")
            return []

    async def test_demo_accounts(self):
        """測試模擬賬戶"""
        print("\n=== 模擬賬戶測試 ===")

        try:
            import futu as ft

            # 查詢模擬賬戶
            print("查詢模擬賬戶信息...")
            ret, data = self.trade_ctx.accinfo_query(trd_env=ft.TrdEnv.SIMULATE)

            if ret == ft.RET_OK:
                accounts = []
                if data is not None and len(data) > 0:
                    print(f"找到 {len(data)} 個模擬賬戶:")

                    for index, row in data.iterrows():
                        account_info = {
                            'acc_id': str(row.get('acc_id', '')),
                            'acc_type': str(row.get('acc_type', '')),
                            'currency': str(row.get('currency', '')),
                            'cash': float(row.get('cash', 0)),
                            'total_assets': float(row.get('total_assets', 0)),
                            'power': float(row.get('power', 0)),
                            'market_val': float(row.get('market_val', 0)),
                            'max_withdraw': float(row.get('max_withdraw', 0)),
                            'trade_pwd_required': bool(row.get('trade_pwd_required', False))
                        }
                        accounts.append(account_info)

                        print(f"  賬戶{index+1}:")
                        print(f"    ID: {account_info['acc_id']}")
                        print(f"    類型: {account_info['acc_type']}")
                        print(f"    總資產: {account_info['total_assets']:.2f}")
                        print(f"    可用資金: {account_info['power']:.2f}")

                    # 選擇第一個賬戶進行後續測試
                    if accounts:
                        selected_account = accounts[0]['acc_id']
                        print(f"\n選擇賬戶: {selected_account} 用於後續測試")
                        return accounts, selected_account

                return None, None
            else:
                print("模擬賬戶查詢失敗")
                return None, None

        except Exception as e:
            print(f"模擬賬戶測試異常: {e}")
            return None, None

    async def test_positions(self, acc_id):
        """測試持倉查詢"""
        print(f"\n=== 持倉查詢測試 (賬戶: {acc_id}) ===")

        try:
            import futu as ft

            # 查詢持倉列表
            ret, data = self.trade_ctx.position_list_query(
                trd_env=ft.TrdEnv.SIMULATE,
                acc_id=acc_id
            )

            if ret == ft.RET_OK:
                positions = []
                if data is not None and len(data) > 0:
                    print(f"找到 {len(data)} 個持倉:")

                    for index, row in data.iterrows():
                        position_info = {
                            'code': str(row.get('code', '')),
                            'qty': float(row.get('qty', 0)),
                            'cost_price': float(row.get('cost_price', 0)),
                            'market_val': float(row.get('market_val', 0)),
                            'unrealized_pl': float(row.get('unrealized_pl', 0)),
                            'unrealized_pl_ratio': float(row.get('unrealized_pl_ratio', 0))
                        }
                        positions.append(position_info)

                        print(f"  {position_info['code']}: "
                              f"{position_info['qty']}股, "
                              f"成本價{position_info['cost_price']}, "
                              f"盈虧{position_info['unrealized_pl']:.2f}")

                return positions
            else:
                print("當前無持倉")
                return []

        except Exception as e:
            print(f"持倉查詢異常: {e}")
            return []

    async def test_trade_simulation(self):
        """測試模擬交易"""
        print("\n=== 模擬交易測試 ===")

        try:
            import futu as ft

            # 測試股票 (騰訊控股)
            test_stock = 'HK.00700'
            print(f"測試股票: {test_stock}")

            # 獲取當前價格
            ret, data = self.quote_ctx.get_market_snapshot([test_stock])
            if ret != ft.RET_OK or not data:
                print("無法獲取股票價格")
                return False

            current_price = data.iloc[0]['last_price']
            print(f"當前價格: {current_price}")

            # 模擬下訂單 (下單1手，略低於市價)
            order_price = current_price * 0.99
            order_quantity = 100  # 1手

            print(f"模擬下單: 價格={order_price}, 數量={order_quantity}")

            # 下模擬訂單
            ret, order_data = self.trade_ctx.place_order(
                price=order_price,
                qty=order_quantity,
                code=test_stock,
                trd_side=ft.TradeSide.BUY,
                order_type=ft.OrderType.NORMAL,
                trd_env=ft.TrdEnv.SIMULATE
            )

            if ret == ft.RET_OK:
                order_id = order_data['order_id']
                print(f"模擬訂單提交成功!")
                print(f"訂單ID: {order_id}")

                # 等待一下查詢訂單狀態
                await asyncio.sleep(2)

                # 查詢訂單狀態
                ret, status_data = self.trade_ctx.order_list_query(
                    order_id=order_id,
                    trd_env=ft.TrdEnv.SIMULATE
                )

                if ret == ft.RET_OK and status_data:
                    status = status_data[0]
                    print(f"訂單狀態: {status.get('order_status', '')}")
                    print(f"成交數量: {status.get('dealt_qty', 0)}")
                    print(f"成交價格: {status.get('dealt_price', 0)}")

                return True
            else:
                print(f"模擬訂單提交失敗: {order_data}")
                return False

        except Exception as e:
            print(f"模擬交易測試異常: {e}")
            return False

    def cleanup(self):
        """清理資源"""
        print("\n=== 清理資源 ===")

        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                print("行情連接已關閉")

            if self.trade_ctx:
                self.trade_ctx.close()
                print("交易連接已關閉")

        except Exception as e:
            print(f"清理資源失敗: {e}")

    async def run_poc_development(self):
        """運行完整的POC開發測試"""
        print("Futu POC Development Tool")
        print(f"User ID: {self.user_id}")
        print(f"API Port: {self.api_port}")
        print(f"WebSocket Key: {self.websocket_key}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        results = {
            'connection': False,
            'market_data': [],
            'demo_accounts': None,
            'selected_account': None,
            'positions': [],
            'trade_simulation': False
        }

        try:
            # 1. 初始化連接
            results['connection'] = await self.initialize_connection()
            if not results['connection']:
                print("連接初始化失敗，POC測試終止")
                return results

            # 2. 市場數據測試
            results['market_data'] = await self.test_market_data()

            # 3. 模擬賬戶測試
            accounts, selected_account = await self.test_demo_accounts()
            results['demo_accounts'] = accounts
            results['selected_account'] = selected_account

            # 4. 持倉查詢測試
            if selected_account:
                results['positions'] = await self.test_positions(selected_account)

            # 5. 模擬交易測試
            if selected_account:
                results['trade_simulation'] = await self.test_trade_simulation()

        except Exception as e:
            print(f"POC開發測試異常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        return results

def save_poc_results(results):
    """保存POC測試結果"""
    print("\n" + "=" * 60)
    print("POC開發測試報告")
    print("-" * 30)

    # 顯示結果
    print(f"連接初始化: {'成功' if results['connection'] else '失敗'}")
    print(f"市場數據獲取: {len(results['market_data'])} 隻股票")
    print(f"模擬賬戶: {len(results['demo_accounts']) if results['demo_accounts'] else 0} 個")
    print(f"選中賬戶: {results['selected_account'] or 'N/A'}")
    print(f"持倉數量: {len(results['positions'])} 個")
    print(f"模擬交易: {'成功' if results['trade_simulation'] else '失敗'}")

    # 保存詳細結果
    report_data = {
        'user_id': USER_ID,
        'api_port': API_PORT,
        'websocket_key': WEBSOCKET_KEY,
        'test_time': datetime.now().isoformat(),
        'results': results
    }

    try:
        with open('futu_poc_results.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"\n詳細結果已保存到: futu_poc_results.json")
    except Exception as e:
        print(f"保存結果失敗: {e}")

    # 總結
    success_count = sum([
        results['connection'],
        len(results['market_data']) > 0,
        results['demo_accounts'] is not None,
        len(results['demo_accounts']) > 0 if results['demo_accounts'] else False,
        results['trade_simulation']
    ])

    total_tests = 5
    success_rate = success_count / total_tests

    if success_rate == 1.0:
        print(f"\n[SUCCESS] 所有POC功能測試通過！")
        print("[READY] 富途API完全就緒")
        print("[READY] 可以開始實時交易系統開發")
        print("\n[NEXT] 下一步開發計劃:")
        print("1. 實時行情監控系統")
        print("2. 自動交易策略執行")
        print("3. 風險管理系統")
        print("4. 回測引擎集成")
        print("5. Web界面開發")
    elif success_rate >= 0.8:
        print(f"\n[PARTIAL] 大部分POC功能可用 (成功率: {success_rate:.1%})")
        print("[GOOD] 基礎功能正常，可以開始開發")
    else:
        print(f"\n[WARNING] 部分功能需要檢查 (成功率: {success_rate:.1%})")
        print("[FIX] 請檢查相關配置")

async def main():
    """主函數"""
    poc = FutuPOCDeveloper()
    results = await poc.run_poc_development()
    save_poc_results(results)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nPOC開發測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\nPOC開發測試異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)