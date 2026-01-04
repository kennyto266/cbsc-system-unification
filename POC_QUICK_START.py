#!/usr/bin/env python3
"""
富途 OpenD POC 快速啟動腳本
運行此腳本快速驗證富途 API 連接和基本功能
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

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

class FutuPOC:
    def __init__(self, host='127.0.0.1', port=11111):
        # 支持從環境變量讀取端口配置
        import os
        env_host = os.getenv('FUTU_HOST')
        env_port = os.getenv('FUTU_PORT')

        self.host = env_host if env_host else host
        self.port = int(env_port) if env_port else port
        self.quote_ctx = None
        self.trade_ctx = None
        self.is_connected = False

    async def connect(self) -> bool:
        """建立連接"""
        logger.info("正在建立富途連接...")

        try:
            # 行情連接
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)

            # 交易連接（使用港股模擬盤）
            self.trade_ctx = ft.OpenHKTradeContext(host=self.host, port=self.port)

            # 測試連接
            ret, data = self.quote_ctx.get_global_state()
            if ret == ft.RET_OK:
                self.is_connected = True
                logger.info("✅ 富途連接建立成功")
                return True
            else:
                logger.error(f"❌ 富途連接失敗: {data}")
                return False

        except Exception as e:
            logger.error(f"❌ 連接異常: {e}")
            return False

    async def test_market_data(self, symbol="HK.00700"):
        """測試市場數據"""
        logger.info(f"正在測試市場數據: {symbol}")

        try:
            # 財實時報價
            ret, data = self.quote_ctx.get_market_snapshot([symbol])
            if ret == ft.RET_OK and data:
                snapshot = data[0]
                logger.info(f"✅ 實時報價獲取成功:")
                logger.info(f"   股票代碼: {snapshot['code']}")
                logger.info(f"   最新價: {snapshot['last_price']}")
                logger.info(f"   漲跌額: {snapshot['change_val']}")
                logger.info(f"   漲跌幅: {snapshot['change_rate']:.2%}")
                return True
            else:
                logger.error(f"❌ 市場數據獲取失敗: {data}")
                return False

        except Exception as e:
            logger.error(f"❌ 市場數據測試異常: {e}")
            return False

    async def test_account_info(self):
        """測試賬戶信息"""
        logger.info("正在測試賬戶信息...")

        try:
            # 獲取賬戶信息
            ret, data = self.trade_ctx.accinfo_query()
            if ret == ft.RET_OK and data:
                account = data[0]
                logger.info("✅ 賬戶信息獲取成功:")
                logger.info(f"   賬戶名: {account['acc_name']}")
                logger.info(f"   賬戶類型: {account['acc_type']}")
                logger.info(f"   幣種: {account['currency']}")
                return True
            else:
                logger.error(f"❌ 賬戶信息獲取失敗: {data}")
                return False

        except Exception as e:
            logger.error(f"❌ 賬戶信息測試異常: {e}")
            return False

    async def test_funds_query(self):
        """測試資金查詢"""
        logger.info("正在測試資金查詢...")

        try:
            # 獲取資金信息
            ret, data = self.trade_ctx.funds_query()
            if ret == ft.RET_OK and data:
                funds = data[0]
                logger.info("✅ 資金信息獲取成功:")
                logger.info(f"   總資產: {funds['total_assets']}")
                logger.info(f"   可用資金: {funds['cash']}")
                logger.info(f"   凍結資金: {funds['frozen_cash']}")
                return True
            else:
                logger.error(f"❌ 資金信息獲取失敗: {data}")
                return False

        except Exception as e:
            logger.error(f"❌ 資金查詢測試異常: {e}")
            return False

    async def test_position_query(self):
        """測試持倉查詢"""
        logger.info("正在測試持倉查詢...")

        try:
            # 獲取持倉信息
            ret, data = self.trade_ctx.position_list_query()
            if ret == ft.RET_OK:
                logger.info("✅ 持倉信息獲取成功:")
                if data:
                    for position in data[:5]:  # 只顯示前5個
                        logger.info(f"   {position['code']}: {position['qty']} 股")
                else:
                    logger.info("   當前無持倉")
                return True
            else:
                logger.error(f"❌ 持倉信息獲取失敗: {data}")
                return False

        except Exception as e:
            logger.error(f"❌ 持倉查詢測試異常: {e}")
            return False

    async def test_simulation_order(self, symbol="HK.00700"):
        """測試模擬交易"""
        logger.info(f"正在測試模擬交易: {symbol}")

        try:
            # 獲取當前價格
            ret, data = self.quote_ctx.get_market_snapshot([symbol])
            if ret != ft.RET_OK or not data:
                logger.error("❌ 無法獲取當前價格")
                return False

            current_price = data[0]['last_price']
            order_price = current_price * 0.99  # 使用略低於市價的價格

            # 下模擬訂單（買入 1 手）
            ret, order_data = self.trade_ctx.place_order(
                price=order_price,
                qty=100,  # 1 手
                code=symbol,
                trd_side=ft.TradeSide.BUY,
                order_type=ft.OrderType.NORMAL,
                trd_env=ft.TRD_ENV.SIM
            )

            if ret == ft.RET_OK:
                order_id = order_data['order_id']
                logger.info(f"✅ 模擬訂單提交成功:")
                logger.info(f"   訂單ID: {order_id}")
                logger.info(f"   股票代碼: {symbol}")
                logger.info(f"   買入價格: {order_price}")
                logger.info(f"   數量: 100 股")

                # 等待一下然後查詢訂單狀態
                await asyncio.sleep(2)

                ret, status_data = self.trade_ctx.order_list_query(order_id=order_id)
                if ret == ft.RET_OK and status_data:
                    status = status_data[0]
                    logger.info(f"   訂單狀態: {status['order_status']}")
                    logger.info(f"   成交數量: {status.get('dealt_qty', 0)}")

                return True
            else:
                logger.error(f"❌ 模擬訂單提交失敗: {order_data}")
                return False

        except Exception as e:
            logger.error(f"❌ 模擬交易測試異常: {e}")
            return False

    async def disconnect(self):
        """斷開連接"""
        logger.info("正在斷開富途連接...")

        try:
            if self.quote_ctx:
                self.quote_ctx.close()
            if self.trade_ctx:
                self.trade_ctx.close()

            self.is_connected = False
            logger.info("✅ 富途連接已斷開")

        except Exception as e:
            logger.error(f"❌ 斷開連接時發生錯誤: {e}")

    async def run_all_tests(self, test_symbol="HK.00700"):
        """運行所有測試"""
        logger.info("🚀 開始富途 OpenD POC 測試")
        logger.info(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        # 連接測試
        if not await self.connect():
            return False

        print("-" * 50)

        # 市場數據測試
        await self.test_market_data(test_symbol)
        print("-" * 50)

        # 賬戶信息測試
        await self.test_account_info()
        print("-" * 50)

        # 資金查詢測試
        await self.test_funds_query()
        print("-" * 50)

        # 持倉查詢測試
        await self.test_position_query()
        print("-" * 50)

        # 模擬交易測試
        await self.test_simulation_order(test_symbol)
        print("-" * 50)

        # 斷開連接
        await self.disconnect()

        logger.info("🎉 富途 OpenD POC 測試完成！")
        return True

def print_help():
    """打印幫助信息"""
    print("富途 OpenD POC 快速啟動腳本")
    print()
    print("使用方法:")
    print("  python POC_QUICK_START.py [股票代碼]")
    print()
    print("示例:")
    print("  python POC_QUICK_START.py HK.00700")
    print("  python POC_QUICK_START.py HK.00941")
    print()
    print("前提條件:")
    print("  1. 已安裝富途 OpenD: pip install futu-opensdk")
    print("  2. 富途 OpenD 正在運行 (默認地址: 127.0.0.1:11111)")
    print("  3. 已登錄富途賬戶")

async def main():
    """主函數"""
    # 檢查命令行參數
    test_symbol = sys.argv[1] if len(sys.argv) > 1 else "HK.00700"

    print_help()
    print(f"測試股票代碼: {test_symbol}")
    print()

    # 確認是否繼續
    while True:
        choice = input("是否繼續測試? (y/n): ").lower().strip()
        if choice in ['y', 'yes', '是']:
            break
        elif choice in ['n', 'no', '否']:
            print("測試已取消")
            return
        else:
            print("請輸入 y 或 n")

    # 創建 POC 實例
    poc = FutuPOC()

    # 運行測試
    try:
        success = await poc.run_all_tests(test_symbol)
        if success:
            print("\n✅ 所有測試通過！可以開始正式的 POC 開發。")
        else:
            print("\n❌ 測試失敗！請檢查環境配置。")
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
    finally:
        # 確保連接被正確關閉
        if poc.is_connected:
            await poc.disconnect()

if __name__ == "__main__":
    asyncio.run(main())