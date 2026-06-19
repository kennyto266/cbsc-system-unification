#!/usr/bin/env python3
"""
Alpha 挖掘 Steps 2-5：相關性 → 特徵 → 神經網絡 → 回測
從 57 隻 HSI 成分股的千絲萬縷關係中找 alpha。

 用法:
    python scripts/alpha_engine.py                # 全流程
    python scripts/alpha_engine.py --correlation  # 只跑相關性
    python scripts/alpha_engine.py --train        # 只跑 NN 訓練
"""

import argparse
import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent

# ==============================================================================
# Step 2: 相關性分析
# ==============================================================================

def correlation_analysis(data: dict):
    """80x80 相關性矩陣 + 聚類 + 領先滯後"""
    print("\n" + "=" * 60)
    print("📊 Step 2: 相關性分析")
    print("=" * 60)

    returns = data["returns"].dropna(how="all").fillna(0)
    sectors = data["sectors"].set_index("symbol")
    n = returns.shape[1]
    print(f"  矩陣: {returns.shape[0]} 天 × {n} 隻")

    # 2a. Pearson 相關性
    corr = returns.corr()
    print(f"\n  📈 Pearson 相關性:")

    # 平均相關性（不含對角線）
    mask = ~np.eye(n, dtype=bool)
    avg_corr = corr.values[mask].mean()
    print(f"    平均相關係數: {avg_corr:.3f}")

    # 最高/最低相關性股票對
    corr_stacked = corr.where(mask).stack()
    top_pos = corr_stacked.nlargest(5)
    top_neg = corr_stacked.nsmallest(5)

    print(f"\n  🔗 最高正相關（同漲同跌）:")
    for (a, b), val in top_pos.items():
        print(f"    {a} ↔ {b}: {val:.3f}")

    print(f"\n  🔗 最低相關（分散化候選）:")
    for (a, b), val in top_neg.items():
        print(f"    {a} ↔ {b}: {val:.3f}")

    # 2b. 聚類分析（用 scipy）
    from scipy.cluster.hierarchy import linkage, fcluster
    from scipy.spatial.distance import squareform

    dist = 1 - corr.values
    np.fill_diagonal(dist, 0)
    dist = np.clip(dist, 0, 2)
    condensed = squareform(dist)
    Z = linkage(condensed, method="ward")
    labels = fcluster(Z, t=5, criterion="maxclust")

    clusters = {}
    for i, sym in enumerate(returns.columns):
        c = labels[i]
        clusters.setdefault(c, []).append(sym)

    print(f"\n  🏷️ 聚類結果（5 個板塊集群）:")
    for c, syms in sorted(clusters.items()):
        sector_names = [sectors.get(s, {}).get("sector", "?") for s in syms]
        from collections import Counter
        top_sector = Counter(sector_names).most_common(1)[0]
        print(f"    集群 {c} ({len(syms)} 隻, 主:{top_sector[0]}): {', '.join(syms[:6])}{'...' if len(syms)>6 else ''}")

    # 2c. 領先-滯後關係
    print(f"\n  ⏩ 領先-滯後分析（A 今日收益預測 B 明日收益）:")
    cross_corr = {}
    cols = returns.columns
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if i >= j:
                continue
            # A 今日 vs B 明日
            lagged = returns[b].shift(-1)
            valid = returns[a].notna() & lagged.notna()
            if valid.sum() > 100:
                c = returns[a][valid].corr(lagged[valid])
                if abs(c) > 0.15:  # 只看 >0.15 的
                    cross_corr[(a, b)] = round(c, 3)

    if cross_corr:
        sorted_xcorr = sorted(cross_corr.items(), key=lambda x: abs(x[1]), reverse=True)
        for (a, b), val in sorted_xcorr[:8]:
            direction = "領先" if val > 0 else "反向"
            print(f"    {a}({direction}) → {b}: {val:+.3f}")
    else:
        print(f"    無顯著領先-滯後關係（|r| > 0.15）")

    results = {
        "avg_correlation": round(avg_corr, 3),
        "top_positive": [(list(k), v) for k, v in top_pos.items()],
        "top_diverse": [(list(k), v) for k, v in top_neg.items()],
        "clusters": {str(k): v for k, v in clusters.items()},
        "cross_correlation": {f"{k[0]}->{k[1]}": v for k, v in list(cross_corr.items())[:20]},
    }
    return corr, results


# ==============================================================================
# Step 3: 特徵工程
# ==============================================================================

def build_features(data: dict, corr: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """構建 NN 特徵矩陣 + target"""
    print("\n" + "=" * 60)
    print("🔧 Step 3: 特徵工程")
    print("=" * 60)

    returns = data["returns"]
    close = data["close"]
    volume = data["volume"]
    sb = data["southbound"]
    sectors = data["sectors"].set_index("symbol")
    symbols = data["symbols"]

    all_features = []

    for sym in symbols:
        if sym not in returns.columns:
            continue

        r = returns[sym]
        c = close[sym]
        v = volume[sym] if sym in volume.columns else pd.Series(0, index=c.index)

        f = pd.DataFrame(index=c.index)

        # === Price Features ===
        f[f"{sym}_ret_5d"] = c.pct_change(5)
        f[f"{sym}_ret_10d"] = c.pct_change(10)
        f[f"{sym}_ret_20d"] = c.pct_change(20)
        f[f"{sym}_vol_5d"] = r.rolling(5).std()
        f[f"{sym}_vol_20d"] = r.rolling(20).std()
        f[f"{sym}_vol_ratio"] = f[f"{sym}_vol_5d"] / (f[f"{sym}_vol_20d"] + 1e-8)

        # RSI
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        f[f"{sym}_rsi"] = 100 - (100 / (1 + rs))

        # Volume z-score
        f[f"{sym}_vol_z"] = (v - v.rolling(20).mean()) / (v.rolling(20).std() + 1e-8)

        # SMA ratio
        f[f"{sym}_sma_ratio"] = c / c.rolling(20).mean() - 1

        # === Cross-Sectional ===
        # 收益率排名（百分位）
        daily_rank = returns[sym].rank(pct=True, axis=0) if sym in returns.columns else pd.Series(0.5, index=c.index)
        f[f"{sym}_rank"] = daily_rank

        # === Non-Price ===
        sb_aligned = sb.reindex(c.index).ffill().fillna(0)
        f[f"{sym}_sb_net"] = sb_aligned
        f[f"{sym}_sb_5d"] = sb_aligned.rolling(5).mean()
        f[f"{sym}_sb_20d"] = sb_aligned.rolling(20).mean()

        # === Target: 未來5日收益率 ===
        f[f"{sym}_target"] = c.pct_change(5).shift(-5)

        all_features.append(f)

    # 合併所有股票的特徵
    features = pd.concat(all_features, axis=1)
    features = features.dropna(how="all")

    # 構建長格式（每行 = 一隻股票 × 一天）
    records = []
    for sym in symbols:
        if sym not in returns.columns:
            continue
        sym_cols = [c for c in features.columns if c.startswith(f"{sym}_") and not c.endswith("_target")]
        target_col = f"{sym}_target"

        for date in features.index:
            row_data = {}
            valid = True
            for col in sym_cols:
                val = features.loc[date, col]
                if pd.isna(val):
                    valid = False
                    break
                feat_name = col.replace(f"{sym}_", "")
                row_data[feat_name] = val

            if not valid:
                continue

            target = features.loc[date, target_col]
            if pd.isna(target):
                continue

            row_data["symbol"] = sym
            row_data["sector"] = sectors.get(sym, {}).get("sector", "")
            row_data["date"] = date
            row_data["target"] = target
            records.append(row_data)

    df = pd.DataFrame(records)
    print(f"  特徵矩陣: {len(df)} 行 × {len(df.columns)-3} 特徵")
    print(f"  日期範圍: {df.date.min()} to {df.date.max()}")
    print(f"  股票數: {df.symbol.nunique()}")

    # 分割特徵 + target
    feature_cols = [c for c in df.columns if c not in ("symbol", "sector", "date", "target")]
    X = df[feature_cols].values.astype(np.float32)
    y = df["target"].values.astype(np.float32)

    # 標準化
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"  X shape: {X_scaled.shape} | y shape: {y.shape}")
    print(f"  特徵: {feature_cols}")

    return X_scaled, y, df, feature_cols, scaler


# ==============================================================================
# Step 4: 神經網絡（PyTorch MLP）
# ==============================================================================

def train_nn(X: np.ndarray, y: np.ndarray, df: pd.DataFrame):
    """PyTorch MLP 訓練"""
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    print("\n" + "=" * 60)
    print("🧠 Step 4: 神經網絡訓練（PyTorch MLP）")
    print("=" * 60)

    # Walk-forward 分割：用日期切分
    dates = pd.to_datetime(df["date"])
    train_mask = dates < "2025-01-01"
    val_mask = (dates >= "2025-01-01") & (dates < "2026-01-01")
    test_mask = dates >= "2026-01-01"

    X_train, y_train = X[train_mask.values], y[train_mask.values]
    X_val, y_val = X[val_mask.values], y[val_mask.values]
    X_test, y_test = X[test_mask.values], y[test_mask.values]

    print(f"  訓練集: {len(X_train)} 樣本 (至 2024)")
    print(f"  驗證集: {len(X_val)} 樣本 (2025)")
    print(f"  測試集: {len(X_test)} 樣本 (2026)")

    if len(X_train) < 100:
        print("  ⚠ 訓練數據太少，跳過")
        return None

    # Model
    input_dim = X_train.shape[1]
    model = nn.Sequential(
        nn.Linear(input_dim, 128),
        nn.BatchNorm1d(128),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(128, 64),
        nn.BatchNorm1d(64),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    )

    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    criterion = nn.MSELoss()

    # DataLoader
    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    train_dl = DataLoader(train_ds, batch_size=256, shuffle=True)

    val_X = torch.FloatTensor(X_val)
    val_y = torch.FloatTensor(y_val)

    # 訓練
    best_val_loss = float("inf")
    patience, no_improve = 30, 0
    epochs = 200

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for xb, yb in train_dl:
            pred = model(xb).squeeze()
            loss = criterion(pred, yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Validation
        model.eval()
        with torch.no_grad():
            val_pred = model(val_X).squeeze()
            val_loss = criterion(val_pred, val_y).item()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = model.state_dict()
            no_improve = 0
        else:
            no_improve += 1

        if (epoch + 1) % 20 == 0:
            print(f"  Epoch {epoch+1}: train_loss={total_loss/len(train_dl):.6f}, val_loss={val_loss:.6f} {'★' if no_improve==0 else ''}")

        if no_improve >= patience:
            print(f"  Early stopping at epoch {epoch+1}")
            break

    # 載入最佳模型
    model.load_state_dict(best_state)

    # 測試集評估
    test_X = torch.FloatTensor(X_test)
    model.eval()
    with torch.no_grad():
        test_pred = model(test_X).squeeze().numpy()
        train_pred = model(torch.FloatTensor(X_train)).squeeze().numpy()

    # 評估：預測分數與實際收益率的相關性
    from scipy.stats import spearmanr
    train_rho, _ = spearmanr(train_pred, y_train)
    test_rho, _ = spearmanr(test_pred, y_test)

    print(f"\n  📊 NN 績效:")
    print(f"    訓練集 Spearman ρ: {train_rho:.3f}")
    print(f"    測試集 Spearman ρ: {test_rho:.3f}")

    # 分組分析：NN 預測 top 20% vs bottom 20%
    test_df = df[test_mask.values].copy()
    test_df["pred"] = test_pred
    test_df["pred_rank"] = test_df.groupby("date")["pred"].rank(pct=True)

    top = test_df[test_df["pred_rank"] > 0.8]
    bottom = test_df[test_df["pred_rank"] < 0.2]

    top_mean = top.groupby("date")["target"].mean().mean()
    bot_mean = bottom.groupby("date")["target"].mean().mean()
    print(f"    Top 20% 平均5日回報: {top_mean*100:.2f}%")
    print(f"    Bottom 20% 平均5日回報: {bot_mean*100:.2f}%")
    print(f"    Alpha (top - bottom): {(top_mean - bot_mean)*100:.2f}% per 5 days")

    # 保存模型
    torch.save({"model_state": best_state, "input_dim": input_dim, "scaler_mean": None}, ROOT / "data" / "alpha_nn_model.pt")

    # 保存預測結果
    test_df.to_csv(ROOT / "data" / "alpha_nn_predictions.csv", index=False)

    return model, test_df


# ==============================================================================
# Step 5: NN 信號回測
# ==============================================================================

def backtest_nn(model, test_df: pd.DataFrame, data: dict):
    """用 NN 預測做回測"""
    print("\n" + "=" * 60)
    print("💰 Step 5: NN 信號回測")
    print("=" * 60)

    import torch

    close_all = data["close"]
    symbols = test_df["symbol"].unique()
    rf = 0.02  # 無風險利率
    fees = 0.0023

    results = []

    for sym in symbols:
        if sym not in close_all.columns:
            continue

        sym_data = test_df[test_df["symbol"] == sym].sort_values("date")
        if len(sym_data) < 20:
            continue

        close = close_all[sym].reindex(sym_data["date"])
        if len(close) < 20:
            continue

        # NN 信號：pred > 中位數 → 買入
        median_pred = sym_data["pred"].median()
        entries = sym_data["pred"] > median_pred
        exits = sym_data["pred"] < 0

        # 對齊到 close index
        entries = entries.reindex(close.index).ffill().fillna(False)
        exits = exits.reindex(close.index).ffill().fillna(False)

        try:
            import vectorbt as vbt
            pf = vbt.Portfolio.from_signals(
                close, entries, exits,
                freq="D", fees=fees, sl_stop=0.08, tp_stop=0.25,
            )
            daily_rf = rf / 252
            sharpe = pf.sharpe_ratio(rf_req=daily_rf) if hasattr(pf, 'sharpe_ratio') else 0
            if not np.isfinite(sharpe):
                sharpe = 0

            results.append({
                "symbol": sym,
                "sharpe": round(float(sharpe), 3),
                "total_return": round(float(pf.total_return()), 3),
                "max_dd": round(float(pf.max_drawdown()), 3),
                "win_rate": round(float(pf.trades.win_rate()), 3) if pf.trades.count() > 0 else 0,
                "num_trades": int(pf.trades.count()),
            })
        except Exception as e:
            pass

    if not results:
        print("  ⚠ 無回測結果")
        return

    results_df = pd.DataFrame(results).sort_values("sharpe", ascending=False)
    print(f"\n  🏆 NN 信號回測 Top 10:")
    print(results_df.head(10).to_string(index=False))

    sr_above_1 = (results_df["sharpe"] > 1.0).sum()
    sr_above_05 = (results_df["sharpe"] > 0.5).sum()
    print(f"\n  📈 統計:")
    print(f"    SR > 1.0: {sr_above_1}/{len(results_df)} ({sr_above_1/len(results_df)*100:.0f}%)")
    print(f"    SR > 0.5: {sr_above_05}/{len(results_df)} ({sr_above_05/len(results_df)*100:.0f}%)")
    print(f"    正收益: {(results_df['total_return']>0).sum()}")

    results_df.to_csv(ROOT / "data" / "alpha_nn_backtest.csv", index=False)
    return results_df


# ==============================================================================
# 主控
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Alpha 挖掘引擎")
    parser.add_argument("--correlation", action="store_true")
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--data", type=str, default="data/alpha_data.pkl")
    args = parser.parse_args()

    print("🚀 Alpha 挖掘引擎")
    data_path = ROOT / args.data
    if not data_path.exists():
        print(f"❌ {data_path} 不存在。先運行 alpha_data.py")
        return

    data = pd.read_pickle(data_path)
    print(f"   載入: {data['returns'].shape[0]} 天 × {data['returns'].shape[1]} 隻")

    # Step 2
    corr, corr_results = correlation_analysis(data)
    with open(ROOT / "data" / "alpha_correlation.json", "w", encoding="utf-8") as f:
        json.dump(corr_results, f, ensure_ascii=False, indent=2, default=str)

    if args.correlation:
        return

    # Step 3 + 4 + 5
    X, y, feature_df, feature_cols, scaler = build_features(data, corr)
    nn_result = train_nn(X, y, feature_df)

    if nn_result is not None:
        model, test_df = nn_result
        backtest_nn(model, test_df, data)

    print("\n✅ Alpha 挖掘完成！")


if __name__ == "__main__":
    main()
