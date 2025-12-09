#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試0700.HK數據獲取功能
"""

import sys
import os
import logging

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'simplified_system', 'src'))

from simplified_system.src.api.stock_api import get_hk_stock_data, get_stock_prices_dataframe
from simplified_system.src.api.government_data import get_hibor_data

def test_data_acquisition():
    """測試數據獲取"""
    print("=" * 60)
    print("0700.HK數據獲取測試")
    print("=" * 60)

    try:
        # 測試股價數據獲取
        print("\n1. 測試股價數據獲取...")
        stock_dict = get_hk_stock_data("0700.hk", 365)

        if stock_dict:
            print("SUCCESS: 股價字典獲取成功")
            print(f"   鍵: {list(stock_dict.keys())}")
        else:
            print("FAILED: 股價字典獲取失敗")
            return

        # 測試DataFrame轉換
        print("\n2. 測試DataFrame轉換...")
        stock_df = get_stock_prices_dataframe("0700.hk", 365)

        if stock_df is not None:
            print("SUCCESS: 股價DataFrame獲取成功")
            print(f"   形狀: {stock_df.shape}")
            print(f"   日期範圍: {stock_df.index[0]} 至 {stock_df.index[-1]}")
            print(f"   價格範圍: {stock_df['price'].min():.2f} - {stock_df['price'].max():.2f}")
        else:
            print("FAILED: 股價DataFrame轉換失敗")
            return

        # 測試HIBOR數據獲取
        print("\n3. 測試HIBOR數據獲取...")
        hibor_data = get_hibor_data(365)

        if hibor_data is not None:
            print("SUCCESS: HIBOR數據獲取成功")
            print(f"   形狀: {hibor_data.shape}")
            print(f"   欄位: {list(hibor_data.columns)}")
        else:
            print("FAILED: HIBOR數據獲取失敗")
            return

        print("\nSUCCESS: 所有數據測試通過！")
        return {
            'stock_df': stock_df,
            'stock_dict': stock_dict,
            'hibor_data': hibor_data
        }

    except Exception as e:
        print(f"FAILED: 測試失敗 - {e}")
        return None

if __name__ == "__main__":
    test_data_acquisition()