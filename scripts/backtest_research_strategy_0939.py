import requests
import pandas as pd
import numpy as np


def fetch_series(symbol: str = "0939.HK", duration: int = 1385) -> pd.DataFrame:
    url = "http://18.180.162.113:9191/inst/getInst"
    r = requests.get(url, params={"symbol": symbol, "duration": duration}, timeout=20, headers={"accept": "application/json"})
    r.raise_for_status()
    j = r.json()
    if isinstance(j, dict) and "data" in j and isinstance(j["data"], dict):
        j = j["data"]

    def to_series(d):
        if not isinstance(d, dict):
            return pd.Series(dtype=float)
        s = pd.Series(d)
        s.index = pd.to_datetime(s.index)
        s = s.sort_index()
        return s.astype(float)

    cols = {}
    for key in ["open", "high", "low", "close", "volume", "Open", "High", "Low", "Close", "Volume"]:
        if key in j and isinstance(j[key], dict):
            cols[key.lower()] = to_series(j[key])

    if not cols:
        raise ValueError("API 返回不含时间序列字段")

    df = pd.concat(cols.values(), axis=1)
    df.columns = list(cols.keys())
    df = df.dropna(how="all")
    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0).round()
    return df


def compute_indicators(df: pd.DataFrame, fast: int = 5, slow: int = 14, rsi_n: int = 14) -> pd.DataFrame:
    out = df.copy()
    out["sma_fast"] = out["close"].rolling(fast).mean()
    out["sma_slow"] = out["close"].rolling(slow).mean()
    delta = out["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(rsi_n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_n).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi"] = 100 - (100 / (1 + rs))
    return out


def derive_decision_row(row_prev: pd.Series, hist: pd.DataFrame, idx: int) -> int:
    # technical direction
    tech_dir = 0
    if not np.isnan(row_prev.get("sma_fast")) and not np.isnan(row_prev.get("sma_slow")) and not np.isnan(row_prev.get("rsi")):
        if row_prev["sma_fast"] > row_prev["sma_slow"] and row_prev["rsi"] > 50:
            tech_dir = 1
        elif row_prev["sma_fast"] < row_prev["sma_slow"] and row_prev["rsi"] < 50:
            tech_dir = -1

    # sentiment proxy: mom5 vs mom20
    if idx >= 20:
        p = hist["close"].iloc[idx-20:idx+1]
        mom5 = p.iloc[-1] / p.iloc[-6] - 1 if len(p) >= 6 else 0.0
        mom20 = p.iloc[-1] / p.iloc[0] - 1 if len(p) >= 1 else 0.0
        sent_dir = 1 if mom5 > mom20 * 1.05 else -1 if mom5 < mom20 * 0.95 else 0
    else:
        sent_dir = 0

    # news proxy: volatility last 20 bars (neutral weighting)
    news_dir = 0  # 不主导方向

    # fundamental proxy: long momentum 60 bars
    if idx >= 60:
        p60 = hist["close"].iloc[idx-60:idx+1]
        long_mom = p60.iloc[-1] / p60.iloc[0] - 1
        fund_dir = 1 if long_mom > 0 else -1 if long_mom < 0 else 0
    else:
        fund_dir = 0

    # vote
    votes = tech_dir + sent_dir + fund_dir + news_dir
    if votes > 0:
        return 1
    if votes < 0:
        return -1
    return 0


def backtest_research(df: pd.DataFrame) -> dict:
    ind = compute_indicators(df)
    ind = ind.dropna().copy()
    # build position by bar using previous bar signals (avoid lookahead)
    dirs = []
    closes = ind["close"].values
    for i in range(len(ind)):
        if i == 0:
            dirs.append(0)
        else:
            dirs.append(derive_decision_row(ind.iloc[i-1], ind, i-1))
    pos = pd.Series(dirs, index=ind.index)

    ret = ind["close"].pct_change().fillna(0)
    strat_ret = ret * pos.shift(1).fillna(0)

    cum = (1 + strat_ret).cumprod()
    max_cum = cum.cummax()
    dd = cum / max_cum - 1
    max_dd = float(dd.min()) if len(dd) else 0.0
    mean = strat_ret.mean() * 252
    std = strat_ret.std(ddof=0) * np.sqrt(252)
    sharpe = float(mean / std) if std and std > 0 else 0.0
    trades = int((pos.diff().abs() == 2).sum() + (pos.diff() == 1).sum() + (pos.diff() == -1).sum())
    win_rate = float((strat_ret[strat_ret > 0].count()) / max(1, strat_ret[strat_ret != 0].count()))

    return {
        "sharpe": sharpe,
        "max_dd": max_dd,
        "trades": trades,
        "win_rate": win_rate,
        "points": int(len(ind)),
    }


def main():
    symbol = "0939.HK"
    df = fetch_series(symbol)
    res = backtest_research(df)
    print("Research-Decision Strategy (single-symbol)")
    for k, v in res.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()


