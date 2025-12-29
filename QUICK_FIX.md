# 🔧 Jupyter Notebook 快速修復指南

## ❌ 問題：NameError: name 'plotly' is not defined

### 🔍 問題原因
Jupyter Notebook 單元格執行順序問題 - 後面的單元格試圖使用尚未導入的變數。

### ✅ 解決方案

#### 方法 1：重啟內核（推薦）
1. 在 VS Code 中：`Ctrl+Shift+P` → "Jupyter: Restart Kernel"
2. 在 Jupyter Lab：Kernel → Restart
3. 重新按順序執行所有單元格

#### 方法 2：按順序執行
確保按以下順序執行單元格：
1. **單元格 1**：環境設置與導入 ⭐
2. **單元格 2**：配置參數
3. **單元格 3-20**：其他分析單元格

#### 方法 3：手動導入
如果仍有問題，在任何單元格開頭加入：
```python
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
```

### 🔍 檢查修復是否成功

執行此測試代碼：
```python
import plotly.express as px
import plotly.graph_objects as go
print("✅ Plotly 導入成功")
```

### 🚀 已修復的內容

我已經更新了 Jupyter Notebook 來防止此問題：

1. **錯誤處理**：添加了 try-except 塊
2. **依賴檢查**：自動檢測庫是否可用
3. **安全導入**：防止導入錯誤導致崩潰
4. **狀態變數**：使用 `SKLEARN_AVAILABLE` 等標誌

### 📋 修復後的改進

```python
# 新的安全導入方式
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️ Plotly 未安裝")
```

### ⚠️ 其他可能問題

如果仍有問題，檢查：

1. **Python 路徑**：
   ```python
   import sys
   print(sys.executable)
   ```

2. **安裝庫**：
   ```bash
   pip install plotly pandas numpy matplotlib seaborn scikit-learn requests aiohttp
   ```

3. **VS Code 擴展**：
   - 確保安裝了 "Jupyter" 擴展
   - 確認 Python 解釋器正確

### 🎯 最佳實踐

1. **重啟後執行**：總是從第一個單元格開始
2. **檢查錯誤**：注意紅色錯誤訊息
3. **逐步執行**：不要跳過單元格
4. **保存進度**：定期保存筆記本

### 💡 快速測試

重啟內核後，執行這個測試：
```python
# 測試所有導入
print("測試庫導入...")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
print("✅ 所有庫導入成功！")
```

---

**現在請重啟 Jupyter 內核並從頭開始執行單元格！** 🚀