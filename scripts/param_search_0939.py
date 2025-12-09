import itertools
import numpy as np
from typing import List, Tuple, Dict, Any

import requests
import pandas as pd


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


def compute_indicators(df: pd.DataFrame, fast: int, slow: int, rsi_n: int) -> pd.DataFrame:
    out = df.copy()
    out["sma_fast"] = out["close"].rolling(fast).mean()
    out["sma_slow"] = out["close"].rolling(slow).mean()
    delta = out["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(rsi_n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_n).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi"] = 100 - (100 / (1 + rs))
    return out


def backtest(df: pd.DataFrame, signal_threshold: float, conf_threshold: float) -> Dict[str, Any]:
    data = df.dropna().copy()
    # 简化触发：sma_fast > sma_slow，且 rsi > rsi_mid(50)
    cond = (data["sma_fast"] > data["sma_slow"]) & (data["rsi"] > 50)
    position = cond.astype(int)
    ret = data["close"].pct_change().fillna(0)
    strategy_ret = ret * position.shift(1).fillna(0)

    cum_ret = (1 + strategy_ret).cumprod()
    max_cum = cum_ret.cummax()
    dd = cum_ret / max_cum - 1
    max_dd = float(dd.min()) if len(dd) else 0.0

    mean = strategy_ret.mean() * 252
    std = strategy_ret.std(ddof=0) * np.sqrt(252)
    sharpe = float(mean / std) if std and std > 0 else 0.0

    trades = int((position.diff() == 1).sum())
    win_rate = float((strategy_ret[strategy_ret > 0].count()) / max(1, strategy_ret[strategy_ret != 0].count()))

    return {
        "sharpe": sharpe,
        "max_dd": max_dd,
        "trades": trades,
        "win_rate": win_rate,
    }


def grid_search(
    df: pd.DataFrame,
    fast_list: List[int],
    slow_list: List[int],
    rsi_list: List[int],
    sig_thr_list: List[float],
    conf_thr_list: List[float],
    top_k: int = 10,
) -> List[Tuple[float, Dict[str, Any]]]:
    results: List[Tuple[float, Dict[str, Any]]] = []
    for f, s, r, st, ct in itertools.product(fast_list, slow_list, rsi_list, sig_thr_list, conf_thr_list):
        if f >= s:
            continue
        ind = compute_indicators(df, f, s, r)
        metrics = backtest(ind, st, ct)
        score = metrics["sharpe"]
        results.append((score, {"fast": f, "slow": s, "rsi": r, "signal_thr": st, "conf_thr": ct, **metrics}))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_k]


def main():
    symbol = "0939.HK"
    print(f"Fetching {symbol} ...")
    df = fetch_series(symbol)
    print(f"rows: {len(df)}, range: {df.index.min().date()} -> {df.index.max().date()}")

    top = grid_search(
        df,
        fast_list=[5, 7, 10, 12],
        slow_list=[14, 16, 20, 26],
        rsi_list=[10, 14],
        sig_thr_list=[0.1, 0.15, 0.2],
        conf_thr_list=[0.1, 0.15, 0.2],
        top_k=8,
    )

    print("Top configs (by Sharpe):")
    for score, cfg in top:
        print(cfg)


if __name__ == "__main__":
    main()


