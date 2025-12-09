# 夏普比率公式錯誤分析

## 🔍 正確的夏普比率公式

```
Sharpe = (策略回報期望 - 無風險利率) / 回報標準差
```

## 🚨 當前實施的錯誤

### 錯誤1: 使用超額回報的標準差
```python
# 當前錯誤實施
sharpe = (mean_excess * 252) / (std_excess * np.sqrt(252))
#         ↑ 超額回報均值      ↑ 超額回報標準差 ❌
```

### 錯誤2: 應該使用原始回報的標準差
```python
# 正確應該是
sharpe = (annualized_return - risk_free_rate) / (std_original * np.sqrt(252))
#         ↑ 年化回報                    ↑ 原始回報標準差 ✅
```

## 📊 兩種方法的差異

### 超額回報標準差 (錯誤方法):
- `std(excess_returns)` = 標準差(原始回報 - 日無風險利率)
- 這會**低估真實波動率**，因為減去常數會降低方差

### 原始回報標準差 (正確方法):
- `std(original_returns)` = 標準差(原始回報)
- 這是**真實的投資組合波動率**

## 🔧 數學證明

```
std(R - rf) ≠ std(R)

因為:
Var(R - rf) = Var(R)
std(R - rf) = sqrt(Var(R)) = std(R)

但是:
當rf是常數時，理論上應該相等

實際計算中的問題:
1. 超額回報去掉了每日無風險利率的變化
2. 年化時的處理不當
3. 分子和分母應該基於相同的基礎
```

## 💡 金融行業標準實踐

根據現代投資組合理論和業界標準:

```python
# 標準夏普比率計算 (業界標準)
def calculate_sharpe_standard(returns, risk_free_rate):
    # 計算年化回報率
    annual_return = (1 + np.mean(returns))**252 - 1

    # 計算年化無風險利率
    annual_rf = risk_free_rate

    # 計算年化波動率 (使用原始回報)
    annual_vol = np.std(returns, ddof=1) * np.sqrt(252)

    # 標準夏普比率公式
    sharpe = (annual_return - annual_rf) / annual_vol

    return sharpe
```

## 🎯 修正方案

需要立即修正 `ProfessionalSharpeCalculator` 中的所有方法：
1. 使用原始回報的標準差
2. 確保分子分母基於相同基礎
3. 遵循標準金融計算實踐

這將導致夏普比率進一步下降，但結果將更加準確和符合行業標準。