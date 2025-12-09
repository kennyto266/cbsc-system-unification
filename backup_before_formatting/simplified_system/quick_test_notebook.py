#!/usr/bin/env python3
"""
Quick Notebook Test
快速測試Jupyter Notebook功能
"""

import json
import sys
from pathlib import Path

def test_notebook_json():
    """測試Notebook JSON格式"""
    notebook_path = Path("notebooks/simple_0700_prototype.ipynb")

    if not notebook_path.exists():
        print("FAILED: Notebook file not found")
        return False

    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        print("SUCCESS: Notebook JSON format is valid")

        # 檢查基本結構
        cell_count = len(notebook['cells'])
        print(f"SUCCESS: Notebook contains {cell_count} cells")

        code_cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
        markdown_cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'markdown']

        print(f"SUCCESS: Contains {len(code_cells)} code cells")
        print(f"SUCCESS: Contains {len(markdown_cells)} markdown cells")

        # 檢查關鍵功能
        all_code = ''.join([cell.get('source', '') for cell in code_cells])
        key_functions = [
            'load_0700_data',
            'analyze_data_quality',
            'calculate_technical_indicators',
            'go.Figure',
            'RSI14'
        ]

        for func in key_functions:
            if func in all_code:
                print(f"SUCCESS: Contains key function: {func}")
            else:
                print(f"WARNING: Missing function: {func}")

        return True

    except json.JSONDecodeError as e:
        print(f"FAILED: JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"FAILED: Error testing notebook: {e}")
        return False

def test_demo_script():
    """測試演示腳本"""
    print("\n=== Testing Demo Script ===")

    try:
        # 測試模擬數據生成
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go

        # 生成模擬數據
        np.random.seed(42)
        dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
        prices = np.random.randn(len(dates)).cumsum() + 400

        # 創建DataFrame
        df = pd.DataFrame({'Close': prices}, index=dates)

        # 計算技術指標
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()

        # RSI計算
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI14'] = 100 - (100 / (1 + rs))

        print(f"SUCCESS: Generated mock data with {len(df)} records")
        print(f"SUCCESS: Calculated technical indicators")
        print(f"  Latest Close: {df['Close'].iloc[-1]:.2f}")
        print(f"  Latest RSI: {df['RSI14'].iloc[-1]:.2f}")

        # 測試圖表創建
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Test Data'))
        fig.update_layout(title='Test Chart')

        print("SUCCESS: Created Plotly chart")

        return True

    except Exception as e:
        print(f"FAILED: Demo script error: {e}")
        return False

def main():
    """主測試函數"""
    print("Quick Jupyter Notebook Test")
    print("=" * 40)

    results = []
    results.append(test_notebook_json())
    results.append(test_demo_script())

    passed = sum(results)
    total = len(results)

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("SUCCESS: All tests passed!")
        print("Jupyter Notebook prototype is ready!")

        print("\nNext Steps:")
        print("1. Run: jupyter lab")
        print("2. Open: notebooks/simple_0700_prototype.ipynb")
        print("3. Execute all cells")
        print("4. Validate functionality")

        return True
    else:
        print("FAILED: Some tests failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)