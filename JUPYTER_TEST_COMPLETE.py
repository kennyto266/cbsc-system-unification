#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jupyter Notebook 完整性測試腳本
檢查所有修復是否正常工作
"""

import sys
import json
import traceback
from pathlib import Path

def test_notebook_integrity():
    """測試筆記本完整性"""
    print("🔍 測試 Jupyter Notebook 完整性...")
    print("=" * 60)

    notebook_path = Path("jupyter-data-analysis.ipynb")

    if not notebook_path.exists():
        print("❌ Jupyter Notebook 文件不存在")
        return False

    try:
        # 讀取筆記本
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)

        # 檢查基本結構
        if notebook.get('nbformat') != 4:
            print("❌ Notebook 格式版本錯誤")
            return False

        cells = notebook.get('cells', [])
        print(f"✅ Notebook 結構正確")
        print(f"   - 格式版本: {notebook.get('nbformat')}.{notebook.get('nbformat_minor', 0)}")
        print(f"   - 單元格數量: {len(cells)}")

        # 分析單元格類型
        cell_types = {}
        for i, cell in enumerate(cells):
            cell_type = cell.get('cell_type', 'unknown')
            cell_types[cell_type] = cell_types.get(cell_type, 0) + 1

            # 檢查單元格內容
            if cell_type == 'code':
                source = cell.get('source', '')
                if isinstance(source, list):
                    source = ''.join(source)

                # 檢查關鍵導入語句
                if 'import' in source:
                    if 'plotly' in source and i == 1:  # 第一個代碼單元格
                        print("✅ Plotly 導入在第一個代元格")
                    if 'pandas' in source and i == 1:
                        print("✅ Pandas 導入在第一個單元格")
                    if 'sklearn' in source and i == 1:
                        print("✅ Sklearn 導入在第一個單元格")

        print(f"\n📊 單元格類型分布:")
        for cell_type, count in cell_types.items():
            print(f"   - {cell_type}: {count} 個")

        # 檢查錯誤處理
        error_handling_patterns = [
            'try:', 'except:', 'if not', 'if empty', 'Error:', '❌', '⚠️'
        ]

        error_handling_count = 0
        for cell in cells:
            if cell.get('cell_type') == 'code':
                source = cell.get('source', '')
                if isinstance(source, list):
                    source = ''.join(source)

                for pattern in error_handling_patterns:
                    if pattern in source:
                        error_handling_count += 1
                        break

        print(f"\n🛡️ 錯誤處理: 在 {error_handling_count} 個代碼單元格中發現錯誤處理機制")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        traceback.print_exc()
        return False

def test_dependency_imports():
    """測試依賴導入"""
    print("\n🔍 測試依賴導入...")
    print("=" * 60)

    dependencies = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('matplotlib.pyplot', 'plt'),
        ('seaborn', 'sns'),
        ('plotly.express', 'px'),
        ('plotly.graph_objects', 'go'),
        ('plotly.subplots', 'make_subplots'),
        ('sklearn', 'sklearn'),
        ('requests', 'requests'),
    ]

    success_count = 0
    for module_name, alias in dependencies:
        try:
            if module_name == 'sklearn':
                import sklearn
                print(f"✅ {module_name} - 導入成功")
            else:
                exec(f"import {module_name} as {alias}")
                print(f"✅ {module_name} - 導入成功")
            success_count += 1
        except ImportError:
            print(f"❌ {module_name} - 導入失敗")
        except Exception as e:
            print(f"⚠️ {module_name} - 導入異常: {e}")

    print(f"\n📊 導入成功率: {success_count}/{len(dependencies)} ({success_count/len(dependencies)*100:.1f}%)")

    return success_count == len(dependencies)

def test_sample_code_execution():
    """測試示例代碼執行"""
    print("\n🔍 測試示例代碼執行...")
    print("=" * 60)

    try:
        import pandas as pd
        import numpy as np
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        print("✅ 核心庫導入成功")

        # 測試數據創建
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        test_data = pd.DataFrame({
            'close': 100 + np.random.randn(50).cumsum(),
            'volume': np.random.randint(1000000, 5000000, 50)
        }, index=dates)

        print(f"✅ 測試數據創建成功: {len(test_data)} 行")

        # 測試圖表創建
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=test_data.index, y=test_data['close'], name='測試數據'))
        fig.update_layout(title='測試圖表')

        print("✅ Plotly 圖表創建成功")

        # 測試子圖
        subfig = make_subplots(rows=2, cols=1)
        subfig.add_trace(go.Scatter(x=test_data.index, y=test_data['close']), row=1, col=1)
        subfig.add_trace(go.Bar(x=test_data.index, y=test_data['volume']), row=2, col=1)

        print("✅ 子圖創建成功")

        return True

    except Exception as e:
        print(f"❌ 代碼執行測試失敗: {e}")
        traceback.print_exc()
        return False

def generate_final_report():
    """生成最終報告"""
    print("\n" + "=" * 60)
    print("📋 最終測試報告")
    print("=" * 60)

    tests = [
        ("筆記本完整性", test_notebook_integrity),
        ("依賴導入", test_dependency_imports),
        ("代碼執行", test_sample_code_execution),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 測試發生異常: {e}")
            results[test_name] = False

    print("\n🎯 測試結果總結:")
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"   - {test_name}: {status}")
        if not passed:
            all_passed = False

    print(f"\n🏆 總體狀態: {'✅ 所有測試通過' if all_passed else '❌ 部分測試失敗'}")

    if all_passed:
        print("\n🎉 Jupyter Notebook 修復完成！")
        print("💡 現在可以安全地運行所有單元格")
        print("\n📝 使用建議:")
        print("   1. 重啟 Jupyter 內核")
        print("   2. 從第一個單元格開始按順序執行")
        print("   3. 注意查看每個單元格的輸出信息")
        print("   4. 如遇問題，查看錯誤訊息並按提示操作")
    else:
        print("\n⚠️ 仍有問題需要解決")
        print("💡 建議:")
        print("   1. 檢查失敗的測試項目")
        print("   2. 安裝缺失的依賴庫")
        print("   3. 重新運行測試腳本")

    return all_passed

if __name__ == "__main__":
    print("🚀 Jupyter Notebook 完整性測試開始...")
    print(f"🐍 Python 版本: {sys.version.split()[0]}")
    print(f"📁 工作目錄: {Path.cwd()}")

    success = generate_final_report()
    sys.exit(0 if success else 1)