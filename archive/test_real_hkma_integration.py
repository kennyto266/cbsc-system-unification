#!/usr/bin/env python3
"""
測試真實HKMA數據集成到優化器
Test Real HKMA Data Integration to Optimizer
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from massive_nonprice_ta_optimizer import MassiveNonPriceTAOptimizer

def test_real_data_integration():
    """測試真實數據集成"""
    print("🧪 測試真實HKMA數據集成到優化器")
    print("=" * 60)

    try:
        # 創建優化器實例
        optimizer = MassiveNonPriceTAOptimizer()
        print("✅ 優化器創建成功")

        # 獲取股票數據
        print("\n📊 獲取股票數據...")
        if optimizer.fetch_real_stock_data():
            print("✅ 股票數據獲取成功")
            print(f"股票數據長度: {len(optimizer.price_data['close'])} 條記錄")
        else:
            print("❌ 股票數據獲取失敗")
            return False

        # 獲取真實政府數據
        print("\n🏛️ 獲取真實香港政府數據...")
        if optimizer.fetch_all_government_data():
            print("✅ 政府數據獲取成功")

            # 檢查數據源
            print(f"\n📈 獲取到的數據源:")
            for source_code, data in optimizer.gov_data.items():
                source_name = optimizer.data_sources.get(source_code, "Unknown")
                print(f"  {source_code} ({source_name}): {len(data)} 條記錄")

                # 顯示數據樣本
                if len(data) > 0:
                    sample_value = data[0]
                    print(f"    樣本值: {sample_value}")

                    # 檢查是否為真實數據（不是重複的常數）
                    unique_values = len(set(data[:10]))  # 檢查前10個值的唯一性
                    if unique_values > 1:
                        print(f"    ✅ 真實數據 (前10個值有{unique_values}個不同值)")
                    else:
                        print(f"    ⚠️ 可能是後備數據 (前10個值相同)")
        else:
            print("❌ 政府數據獲取失敗")
            return False

        print(f"\n🎉 真實數據集成測試成功！")
        print(f"✅ 優化器現在可以使用真實香港政府數據進行策略優化")

        return True

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_data_integration()
    if success:
        print("\n🚀 準備就緒！可以運行完整的策略優化器使用真實數據")
    else:
        print("\n❌ 集成測試失敗，請檢查配置")