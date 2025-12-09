import requests
import pandas as pd
import numpy as np
from datetime import datetime


def fetch_series(symbol: str = "0939.HK", duration: int = 1385) -> pd.DataFrame:
    url = "http://18.180.162.113:9191/inst/getInst"
    r = requests.get(url, params={"symbol": symbol, "duration": duration}, timeout=20, headers={"accept": "application/json"})
    r.raise_for_status()
    j = r.json()
    if isinstance(j, dict) and "data" in j and isinstance(j["data"], dict):
        j = j["data"]
    # 期望字段为 dict: {ts_iso: value}
    def to_series(d):
        if not isinstance(d, dict):
            return pd.Series(dtype=float)
        s = pd.Series(d)
        # 将索引转为 datetime
        s.index = pd.to_datetime(s.index)
        s = s.sort_index()
        return s.astype(float)

    cols = {}
    for key in ["open", "high", "low", "close", "volume", "Open", "High", "Low", "Close", "Volume"]:
        if key in j and isinstance(j[key], dict):
            base_key = key.lower()
            cols[base_key] = to_series(j[key])

    if not cols:
        raise ValueError("API 返回不含时间序列字段")

    df = pd.concat(cols.values(), axis=1)
    df.columns = list(cols.keys())
    df = df.dropna(how="all")
    if "volume" in df.columns:
        df["volume"] = df["volume"].fillna(0).round()
    return df


def compute_indicators(df: pd.DataFrame, fast: int = 10, slow: int = 20, rsi_n: int = 14) -> pd.DataFrame:
    out = df.copy()
    out["sma_fast"] = out["close"].rolling(fast).mean()
    out["sma_slow"] = out["close"].rolling(slow).mean()

    # RSI
    delta = out["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(rsi_n).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_n).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi"] = 100 - (100 / (1 + rs))
    return out


def backtest_sma_rsi(df: pd.DataFrame) -> dict:
    data = df.dropna().copy()
    # 进场：sma_fast > sma_slow 且 rsi > 50；出场：相反
    cond = (data["sma_fast"] > data["sma_slow"]) & (data["rsi"] > 50)
    position = cond.astype(int)
    ret = data["close"].pct_change().fillna(0)
    strategy_ret = ret * position.shift(1).fillna(0)

    cum_ret = (1 + strategy_ret).cumprod()
    max_cum = cum_ret.cummax()
    dd = cum_ret / max_cum - 1
    max_dd = dd.min()

    # 年化夏普（假设日频，252）
    mean = strategy_ret.mean() * 252
    std = strategy_ret.std(ddof=0) * np.sqrt(252)
    sharpe = mean / std if std and std > 0 else 0.0

    return {
        "last_date": data.index[-1].isoformat(),
        "last_price": float(data["close"].iloc[-1]),
        "in_position": bool(position.iloc[-1] == 1),
        "last_signal": "long" if position.iloc[-1] == 1 else "flat",
        "fast": int(df["sma_fast"].iloc[-1]) if not np.isnan(df["sma_fast"].iloc[-1]) else None,
        "slow": int(df["sma_slow"].iloc[-1]) if not np.isnan(df["sma_slow"].iloc[-1]) else None,
        "rsi": float(df["rsi"].iloc[-1]) if not np.isnan(df["rsi"].iloc[-1]) else None,
        "sharpe": float(sharpe),
        "max_drawdown": float(max_dd),
        "total_points": int(len(data)),
    }


def main():
    symbol = "0939.HK"
    print(f"Fetching {symbol} ...")
    df = fetch_series(symbol)
    print(f"rows: {len(df)}, from {df.index[0].date()} to {df.index[-1].date()}")

    df = compute_indicators(df)
    res = backtest_sma_rsi(df)
    print("Strategy summary:")
    for k, v in res.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()


