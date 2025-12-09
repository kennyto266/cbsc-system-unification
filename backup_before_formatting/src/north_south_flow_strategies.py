#!/usr / bin / env python3
# -*- coding: utf - 8 -*-
"""
🌊 南北水策略模組
將南北水技術指標整合到港股量化分析系統中

策略包括：
1. 南北水RSI策略
2. 南北水MACD策略
3. 南北水淨流入策略
4. 南北水綜合策略
5. 南北水與股票聯動策略
"""

import json
import os
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from data_handler import TechnicalIndicators

warnings.filterwarnings("ignore")


class NorthSouthFlowStrategies:
    def __init__(self):
        self.north_data_dir = "../../../北水json"

        # 市場定義
        self.markets = {
            0: "滬股通北向",  # SSE Northbound
            1: "滬股通南向",  # SSE Southbound
            2: "深股通北向",  # SZSE Northbound
            3: "深股通南向",  # SZSE Southbound
        }

        # 技術指標參數
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        print("🌊 南北水策略模組初始化完成")

    def load_north_south_data(self, start_date=None, end_date=None):
        """加載南北水數據"""
        print("📁 加載南北水數據...")

        # 檢查數據目錄是否存在
        if not os.path.exists(self.north_data_dir):
            print(f"❌ 北水數據目錄不存在: {self.north_data_dir}")
            return pd.DataFrame()

        # 獲取所有可用的JSON文件
        json_files = [f for f in os.listdir(self.north_data_dir) if f.endswith(".json")]
        if not json_files:
            print("❌ 未找到任何南北水數據文件")
            return pd.DataFrame()

        json_files.sort()  # 按日期排序

        # 如果沒有指定日期範圍，使用所有可用數據
        if start_date is None or end_date is None:
            try:
                # 從文件名獲取日期範圍
                first_date = datetime.strptime(json_files[0][:8], "%Y % m % d").date()
                last_date = datetime.strptime(json_files[-1][:8], "%Y % m % d").date()

                if start_date is None:
                    start_date = first_date
                if end_date is None:
                    end_date = last_date

                print(f"📅 使用可用數據範圍: {first_date} 到 {last_date}")
            except Exception as e:
                print(f"⚠️ 解析日期範圍時出錯: {str(e)}")
                return pd.DataFrame()

        # 獲取指定日期範圍內的JSON文件
        filtered_files = []
        for f in json_files:
            try:
                file_date = datetime.strptime(f[:8], "%Y % m % d").date()
                if start_date <= file_date <= end_date:
                    filtered_files.append(f)
            except Exception:
                continue

        if not filtered_files:
            print("❌ 未找到符合條件的南北水數據文件")
            return pd.DataFrame()

        filtered_files.sort()
        print(f"📄 找到 {len(filtered_files)} 個南北水數據文件")

        # 讀取所有JSON文件
        all_data = []
        for filename in filtered_files:
            try:
                file_path = os.path.join(self.north_data_dir, filename)
                with open(file_path, "r", encoding="utf - 8") as f:
                    data = json.load(f)

                    # 解析日期
                    date = datetime.strptime(filename[:8], "%Y % m % d").date()

                    # 處理每個市場的數據
                    for market_data in data:
                        market_id = market_data["id"]
                        market_name = self.markets.get(market_id, f"市場{market_id}")

                        if "content" in market_data and market_data["content"]:
                            for content in market_data["content"]:
                                if content.get("style") == 1:  # 總計數據
                                    table = content.get("table", {})
                                    tr_data = table.get("tr", [])

                                    if tr_data:
                                        try:
                                            record = {
                                                "date": date,
                                                "market": market_name,
                                            }

                                            # 處理不同市場的數據格式
                                            if "北向" in market_name:
                                                # 北向：只有總成交額
                                                record["total_turnover"] = float(
                                                    tr_data[0]["td"][0][0].replace(
                                                        ",", ""
                                                    )
                                                )
                                                if len(tr_data) > 1:
                                                    record["trade_count"] = int(
                                                        tr_data[1]["td"][0][0].replace(
                                                            ",", ""
                                                        )
                                                    )
                                            else:
                                                # 南向：有買入和賣出
                                                record["total_turnover"] = float(
                                                    tr_data[0]["td"][0][0].replace(
                                                        ",", ""
                                                    )
                                                )
                                                if len(tr_data) > 1:
                                                    record["buy_turnover"] = float(
                                                        tr_data[1]["td"][0][0].replace(
                                                            ",", ""
                                                        )
                                                    )
                                                if len(tr_data) > 2:
                                                    record["sell_turnover"] = float(
                                                        tr_data[2]["td"][0][0].replace(
                                                            ",", ""
                                                        )
                                                    )
                                                if len(tr_data) > 3:
                                                    record["trade_count"] = int(
                                                        tr_data[3]["td"][0][0].replace(
                                                            ",", ""
                                                        )
                                                    )
                                                record["net_flow"] = record.get(
                                                    "buy_turnover", 0
                                                ) - record.get("sell_turnover", 0)

                                            all_data.append(record)
                                        except (ValueError, IndexError, KeyError) as e:
                                            print(
                                                f"⚠️ 解析數據錯誤 {filename} - {market_name}: {str(e)}"
                                            )
                                            continue
            except Exception as e:
                print(f"⚠️ 處理文件 {filename} 時出錯: {str(e)}")
                continue

        if not all_data:
            print("❌ 無法從文件中讀取南北水數據")
            return pd.DataFrame()

        # 轉換為DataFrame
        df = pd.DataFrame(all_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["market", "date"]).reset_index(drop=True)

        print(f"✅ 加載南北水數據：{len(df)} 條記錄，{len(df.index.unique())} 個交易日")
        start_date = df.index.min()
        end_date = df.index.max()
        print(f"📅 數據範圍：{start_date} 到 {end_date}")

        return df

    def parse_daily_data(self, data, filename):
        """解析單日南北水數據"""
        try:
            date_str = filename[:8]
            date_obj = datetime.strptime(date_str, "%Y % m % d").date()

            records = []

            for market_data in data:
                market_id = market_data["id"]
                market_name = self.markets.get(market_id, f"市場{market_id}")

                if "content" in market_data and market_data["content"]:
                    total_turnover = 0
                    buy_turnover = 0
                    sell_turnover = 0
                    trade_count = 0

                    for content in market_data["content"]:
                        if content.get("style") == 1:
                            table = content.get("table", {})
                            tr_data = table.get("tr", [])

                            if tr_data:
                                try:
                                    if "北向" in market_name:
                                        total_turnover = float(
                                            tr_data[0]["td"][0][0].replace(",", "")
                                        )
                                        if len(tr_data) > 1:
                                            trade_count = int(
                                                tr_data[1]["td"][0][0].replace(",", "")
                                            )
                                    else:
                                        total_turnover = float(
                                            tr_data[0]["td"][0][0].replace(",", "")
                                        )
                                        if len(tr_data) > 1:
                                            buy_turnover = float(
                                                tr_data[1]["td"][0][0].replace(",", "")
                                            )
                                        if len(tr_data) > 2:
                                            sell_turnover = float(
                                                tr_data[2]["td"][0][0].replace(",", "")
                                            )
                                        if len(tr_data) > 3:
                                            trade_count = int(
                                                tr_data[3]["td"][0][0].replace(",", "")
                                            )
                                except (ValueError, IndexError, KeyError):
                                    continue

                    records.append(
                        {
                            "date": date_obj,
                            "market": market_name,
                            "market_id": market_id,
                            "total_turnover": total_turnover,
                            "buy_turnover": buy_turnover,
                            "sell_turnover": sell_turnover,
                            "net_flow": buy_turnover - sell_turnover,
                            "trade_count": trade_count,
                        }
                    )

            return records

        except Exception as e:
            return []

    def calculate_north_south_indicators(self, ns_data):
        """計算南北水技術指標"""
        print("🔢 計算南北水技術指標...")

        if ns_data.empty:
            print("❌ 南北水數據為空")
            return pd.DataFrame()

        try:
            # 確保數據按日期排序
            ns_data = ns_data.sort_index()

            # 計算滾動平均
            sma_periods = [5, 10, 20, 60]
            indicators = {}

            for market in ["sh", "sz"]:
                # 獲取市場數據
                market_data = ns_data[ns_data["market"] == market]
                if market_data.empty:
                    continue

                # 計算各個週期的移動平均
                for period in sma_periods:
                    col_name = f"{market}_sma_{period}"
                    indicators[col_name] = (
                        market_data["north_value"]
                        .rolling(window=period, min_periods=1)
                        .mean()
                    )

                # 計算RSI
                rsi_period = 14
                col_name = f"{market}_rsi"
                delta = market_data["north_value"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                rs = gain / loss.replace(0, np.nan)  # 避免除以零
                indicators[col_name] = 100 - (100 / (1 + rs))

                # 計算MACD
                exp1 = market_data["north_value"].ewm(span=12, adjust=False).mean()
                exp2 = market_data["north_value"].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9, adjust=False).mean()
                indicators[f"{market}_macd"] = macd
                indicators[f"{market}_macd_signal"] = signal
                indicators[f"{market}_macd_hist"] = macd - signal

            # 合併所有指標
            result = pd.DataFrame(indicators)
            result.fillna(method="ffill", inplace=True)
            result.fillna(method="bfill", inplace=True)

            print(f"✅ 技術指標計算完成，共 {len(result.columns)} 個指標")
            return result

        except Exception as e:
            print(f"❌ 計算技術指標時出錯: {str(e)}")
            return pd.DataFrame()

    def north_south_rsi_strategy(
        self, df, market_name="滬股通南向", rsi_oversold=30, rsi_overbought=70
    ):
        """南北水RSI策略"""
        market_df = df[df["market"] == market_name].copy()
        market_df = market_df.sort_values("date").reset_index(drop=True)

        if len(market_df) < 30:
            return pd.DataFrame()

        # 生成RSI信號
        market_df["signal"] = 0
        market_df.loc[market_df["ns_rsi"] < rsi_oversold, "signal"] = 1  # 超賣買入
        market_df.loc[market_df["ns_rsi"] > rsi_overbought, "signal"] = -1  # 超買賣出

        # 計算持倉
        market_df["position"] = (
            market_df["signal"].replace(0, np.nan).fillna(method="ffill").fillna(0)
        )

        # 計算收益（假設下一日開盤價買入）
        market_df["returns"] = market_df["ns_turnover_change"].shift(-1)
        market_df["strategy_returns"] = market_df["position"] * market_df["returns"]

        return market_df[
            ["date", "signal", "position", "returns", "strategy_returns", "ns_rsi"]
        ].copy()

    def north_south_macd_strategy(self, df, market_name="滬股通南向"):
        """南北水MACD策略"""
        market_df = df[df["market"] == market_name].copy()
        market_df = market_df.sort_values("date").reset_index(drop=True)

        if len(market_df) < 30:
            return pd.DataFrame()

        # 生成MACD信號
        market_df["signal"] = 0

        # 金叉買入：MACD線向上穿越信號線
        market_df.loc[
            (market_df["ns_macd"] > market_df["ns_macd_signal"])
            & (market_df["ns_macd"].shift(1) <= market_df["ns_macd_signal"].shift(1)),
            "signal",
        ] = 1

        # 死叉賣出：MACD線向下穿越信號線
        market_df.loc[
            (market_df["ns_macd"] < market_df["ns_macd_signal"])
            & (market_df["ns_macd"].shift(1) >= market_df["ns_macd_signal"].shift(1)),
            "signal",
        ] = -1

        # 計算持倉
        market_df["position"] = (
            market_df["signal"].replace(0, np.nan).fillna(method="ffill").fillna(0)
        )

        # 計算收益
        market_df["returns"] = market_df["ns_turnover_change"].shift(-1)
        market_df["strategy_returns"] = market_df["position"] * market_df["returns"]

        return market_df[
            [
                "date",
                "signal",
                "position",
                "returns",
                "strategy_returns",
                "ns_macd",
                "ns_macd_signal",
            ]
        ].copy()

    def north_south_net_flow_strategy(self, df, market_name="滬股通南向"):
        """南北水淨流入策略（僅適用於南向市場）"""
        if "南向" not in market_name:
            print(f"⚠️ {market_name} 不是南向市場，跳過淨流入策略")
            return pd.DataFrame()

        market_df = df[df["market"] == market_name].copy()
        market_df = market_df.sort_values("date").reset_index(drop=True)

        if len(market_df) < 30 or "ns_net_flow_rsi" not in market_df.columns:
            return pd.DataFrame()

        # 基於淨流入RSI生成信號
        market_df["signal"] = 0
        market_df.loc[market_df["ns_net_flow_rsi"] < 30, "signal"] = 1  # 淨流入超賣
        market_df.loc[market_df["ns_net_flow_rsi"] > 70, "signal"] = -1  # 淨流入超買

        # 結合淨流入MACD
        market_df["macd_signal"] = 0
        market_df.loc[
            (market_df["ns_net_flow_macd"] > market_df["ns_net_flow_macd_signal"])
            & (
                market_df["ns_net_flow_macd"].shift(1)
                <= market_df["ns_net_flow_macd_signal"].shift(1)
            ),
            "macd_signal",
        ] = 1
        market_df.loc[
            (market_df["ns_net_flow_macd"] < market_df["ns_net_flow_macd_signal"])
            & (
                market_df["ns_net_flow_macd"].shift(1)
                >= market_df["ns_net_flow_macd_signal"].shift(1)
            ),
            "macd_signal",
        ] = -1

        # 綜合信號：RSI和MACD都同向才發出信號
        market_df["combined_signal"] = 0
        market_df.loc[
            (market_df["signal"] == 1) & (market_df["macd_signal"] == 1),
            "combined_signal",
        ] = 1
        market_df.loc[
            (market_df["signal"] == -1) & (market_df["macd_signal"] == -1),
            "combined_signal",
        ] = -1

        # 計算持倉
        market_df["position"] = (
            market_df["combined_signal"]
            .replace(0, np.nan)
            .fillna(method="ffill")
            .fillna(0)
        )

        # 計算收益
        market_df["returns"] = market_df["ns_turnover_change"].shift(-1)
        market_df["strategy_returns"] = market_df["position"] * market_df["returns"]

        return market_df[
            [
                "date",
                "combined_signal",
                "position",
                "returns",
                "strategy_returns",
                "ns_net_flow_rsi",
            ]
        ].copy()

    def north_south_comprehensive_strategy(self, df):
        """南北水綜合策略：結合四個市場的信號"""
        print("🎯 計算南北水綜合策略...")

        # 為每個市場計算信號強度
        market_signals = {}

        for market in df["market"].unique():
            market_df = df[df["market"] == market].copy()
            market_df = market_df.sort_values("date").reset_index(drop=True)

            if len(market_df) < 30:
                continue

            # RSI信號強度 (0 - 1)
            rsi_signal = np.where(
                market_df["ns_rsi"] < 30, 1, np.where(market_df["ns_rsi"] > 70, -1, 0)
            )

            # MACD信號強度
            macd_signal = np.where(
                (market_df["ns_macd"] > market_df["ns_macd_signal"])
                & (
                    market_df["ns_macd"].shift(1)
                    <= market_df["ns_macd_signal"].shift(1)
                ),
                1,
                np.where(
                    (market_df["ns_macd"] < market_df["ns_macd_signal"])
                    & (
                        market_df["ns_macd"].shift(1)
                        >= market_df["ns_macd_signal"].shift(1)
                    ),
                    -1,
                    0,
                ),
            )

            # 趨勢信號（基於移動平均線）
            trend_signal = np.where(
                market_df["total_turnover"] > market_df["ns_ma20"],
                1,
                np.where(market_df["total_turnover"] < market_df["ns_ma20"], -1, 0),
            )

            # 市場權重（根據成交額大小）
            market_weight = (
                market_df["total_turnover"].rolling(5).mean().iloc[-1]
                if len(market_df) > 5
                else 1
            )

            market_signals[market] = {
                "date": market_df["date"],
                "rsi_signal": rsi_signal,
                "macd_signal": macd_signal,
                "trend_signal": trend_signal,
                "weight": market_weight,
                "turnover_change": market_df["ns_turnover_change"],
            }

        # 合併所有市場信號
        if not market_signals:
            return pd.DataFrame()

        # 使用最完整的市場數據作為基準日期
        base_market = max(
            market_signals.keys(), key=lambda x: len(market_signals[x]["date"])
        )
        base_dates = market_signals[base_market]["date"]

        comprehensive_df = pd.DataFrame({"date": base_dates})

        # 計算加權綜合信號
        total_weight = sum([data["weight"] for data in market_signals.values()])

        comprehensive_df["rsi_weighted_signal"] = 0
        comprehensive_df["macd_weighted_signal"] = 0
        comprehensive_df["trend_weighted_signal"] = 0
        comprehensive_df["combined_signal"] = 0

        for market, data in market_signals.items():
            if len(data["date"]) == len(comprehensive_df):
                weight_factor = data["weight"] / total_weight

                comprehensive_df["rsi_weighted_signal"] += (
                    data["rsi_signal"] * weight_factor
                )
                comprehensive_df["macd_weighted_signal"] += (
                    data["macd_signal"] * weight_factor
                )
                comprehensive_df["trend_weighted_signal"] += (
                    data["trend_signal"] * weight_factor
                )

        # 綜合信號：至少兩個指標同向才發出信號
        comprehensive_df["signal_strength"] = (
            comprehensive_df["rsi_weighted_signal"]
            + comprehensive_df["macd_weighted_signal"]
            + comprehensive_df["trend_weighted_signal"]
        ) / 3

        comprehensive_df["final_signal"] = 0
        comprehensive_df.loc[
            comprehensive_df["signal_strength"] > 0.3, "final_signal"
        ] = 1
        comprehensive_df.loc[
            comprehensive_df["signal_strength"] < -0.3, "final_signal"
        ] = -1

        # 計算持倉
        comprehensive_df["position"] = (
            comprehensive_df["final_signal"]
            .replace(0, np.nan)
            .fillna(method="ffill")
            .fillna(0)
        )

        # 使用主要市場的收益作為基準
        main_market_returns = market_signals[base_market]["turnover_change"]
        comprehensive_df["returns"] = main_market_returns.shift(-1)
        comprehensive_df["strategy_returns"] = (
            comprehensive_df["position"] * comprehensive_df["returns"]
        )

        return comprehensive_df[
            [
                "date",
                "final_signal",
                "position",
                "returns",
                "strategy_returns",
                "signal_strength",
            ]
        ].copy()

    def get_all_north_south_strategies(self, start_date=None, end_date=None):
        """獲取所有南北水策略結果"""
        print("🚀 計算所有南北水策略...")

        # 加載數據
        ns_data = self.load_north_south_data(start_date, end_date)

        # 計算技術指標
        ns_indicators = self.calculate_north_south_indicators(ns_data)

        strategies = {}

        # 1. 南北水RSI策略（針對主要市場）
        for market in ["滬股通南向", "深股通南向"]:
            if market in ns_indicators["market"].unique():
                strategy_name = f"南北水RSI策略_{market}"
                strategies[strategy_name] = self.north_south_rsi_strategy(
                    ns_indicators, market
                )

        # 2. 南北水MACD策略
        for market in ["滬股通南向", "深股通南向"]:
            if market in ns_indicators["market"].unique():
                strategy_name = f"南北水MACD策略_{market}"
                strategies[strategy_name] = self.north_south_macd_strategy(
                    ns_indicators, market
                )

        # 3. 南北水淨流入策略
        for market in ["滬股通南向", "深股通南向"]:
            if market in ns_indicators["market"].unique():
                strategy_name = f"南北水淨流入策略_{market}"
                net_flow_result = self.north_south_net_flow_strategy(
                    ns_indicators, market
                )
                if not net_flow_result.empty:
                    strategies[strategy_name] = net_flow_result

        # 4. 南北水綜合策略
        comprehensive_result = self.north_south_comprehensive_strategy(ns_indicators)
        if not comprehensive_result.empty:
            strategies["南北水綜合策略"] = comprehensive_result

        print(f"✅ 完成 {len(strategies)} 個南北水策略計算")

        return strategies

    def calculate_strategy_performance(self, strategy_df):
        """計算策略績效指標"""
        if strategy_df.empty or "strategy_returns" not in strategy_df.columns:
            return {}

        strategy_returns = strategy_df["strategy_returns"].dropna()

        if len(strategy_returns) == 0:
            return {}

        # 基本績效指標
        total_return = (1 + strategy_returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1
        volatility = strategy_returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        # 最大回撤
        cumulative_returns = (1 + strategy_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # 勝率
        win_rate = (strategy_returns > 0).mean()

        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "total_trades": len(strategy_returns),
        }

    def get_strategy_summary(self, strategies):
        """獲取策略績效摘要"""
        summary_data = []

        for strategy_name, strategy_df in strategies.items():
            performance = self.calculate_strategy_performance(strategy_df)

            if performance:
                summary_data.append(
                    {
                        "strategy_name": strategy_name,
                        "sharpe_ratio": performance["sharpe_ratio"],
                        "annual_return": performance["annual_return"],
                        "max_drawdown": performance["max_drawdown"],
                        "win_rate": performance["win_rate"],
                        "total_trades": performance["total_trades"],
                        "volatility": performance["volatility"],
                    }
                )

        summary_df = pd.DataFrame(summary_data)

        if not summary_df.empty:
            summary_df = summary_df.sort_values("sharpe_ratio", ascending=False)

        return summary_df

    def generate_equity_curve(self, signals, stock_data):
        """生成權益曲線"""
        if signals.empty or stock_data.empty:
            print("❌ 無法生成權益曲線：信號或股票數據為空")
            return pd.Series()

        # 確保日期索引格式一致
        signals.index = pd.to_datetime(signals.index)
        stock_data.index = pd.to_datetime(stock_data.index)

        # 計算每日收益率
        daily_returns = pd.Series(index=stock_data.index, dtype=float)

        # 初始化持倉狀態
        position = 0  # 0: 無倉位, 1: 多倉, -1: 空倉
        entry_price = 0

        for date in stock_data.index:
            if date in signals.index:
                signal = signals[date]

                # 平倉
                if position != 0 and signal == 0:
                    if position == 1:
                        returns = (
                            stock_data.loc[date, "close"] - entry_price
                        ) / entry_price
                    else:  # position == -1
                        returns = (
                            entry_price - stock_data.loc[date, "close"]
                        ) / entry_price
                    daily_returns[date] = returns
                    position = 0
                    entry_price = 0

                # 開倉
                elif position == 0 and signal != 0:
                    position = 1 if signal > 0 else -1
                    entry_price = stock_data.loc[date, "close"]
                    daily_returns[date] = 0

                # 持倉中
                elif position != 0:
                    if position == 1:
                        returns = (
                            stock_data.loc[date, "close"] - entry_price
                        ) / entry_price
                    else:  # position == -1
                        returns = (
                            entry_price - stock_data.loc[date, "close"]
                        ) / entry_price
                    daily_returns[date] = returns

                else:
                    daily_returns[date] = 0
            else:
                # 如果當日沒有信號但有持倉，計算收益率
                if position != 0:
                    if position == 1:
                        returns = (
                            stock_data.loc[date, "close"] - entry_price
                        ) / entry_price
                    else:  # position == -1
                        returns = (
                            entry_price - stock_data.loc[date, "close"]
                        ) / entry_price
                    daily_returns[date] = returns
                else:
                    daily_returns[date] = 0

        # 處理缺失值
        daily_returns = daily_returns.fillna(0)

        # 計算累積收益率
        equity_curve = (1 + daily_returns).cumprod()

        return equity_curve

    def generate_all_signals(self, stock_data):
        """生成所有南北水策略的信號"""
        print("🚀 生成所有南北水策略信號...")

        # 加載南北水數據
        ns_data = self.load_north_south_data()
        if ns_data.empty:
            print("❌ 無法生成信號：南北水數據為空")
            return {}

        # 計算技術指標
        indicators = self.calculate_north_south_indicators(ns_data)
        if indicators.empty:
            print("❌ 無法生成信號：技術指標計算失敗")
            return {}

        # 生成各個策略的信號
        signals = {}

        try:
            # RSI策略
            for market in ["sh", "sz"]:
                rsi_col = f"{market}_rsi"
                if rsi_col in indicators.columns:
                    strategy_name = f"{market.upper()}_RSI_Strategy"
                    signals[strategy_name] = self.generate_rsi_signals(
                        indicators[rsi_col]
                    )

            # MACD策略
            for market in ["sh", "sz"]:
                macd_col = f"{market}_macd"
                signal_col = f"{market}_macd_signal"
                if macd_col in indicators.columns and signal_col in indicators.columns:
                    strategy_name = f"{market.upper()}_MACD_Strategy"
                    signals[strategy_name] = self.generate_macd_signals(
                        indicators[macd_col], indicators[signal_col]
                    )

            # 移動平均策略
            for market in ["sh", "sz"]:
                sma_fast = f"{market}_sma_5"
                sma_slow = f"{market}_sma_20"
                if sma_fast in indicators.columns and sma_slow in indicators.columns:
                    strategy_name = f"{market.upper()}_MA_Strategy"
                    signals[strategy_name] = self.generate_ma_signals(
                        indicators[sma_fast], indicators[sma_slow]
                    )

            print(f"✅ 策略信號生成完成，共 {len(signals)} 個策略")
            return signals

        except Exception as e:
            print(f"❌ 生成策略信號時出錯: {str(e)}")
            return {}

    def generate_rsi_signals(self, rsi_series, oversold=30, overbought=70):
        """根據RSI生成交易信號"""
        signals = pd.Series(0, index=rsi_series.index)
        signals[rsi_series < oversold] = 1  # 買入信號
        signals[rsi_series > overbought] = -1  # 賣出信號
        return signals

    def generate_macd_signals(self, macd_series, signal_series):
        """根據MACD生成交易信號"""
        signals = pd.Series(0, index=macd_series.index)
        # 當MACD線上穿信號線時買入
        signals[
            (macd_series > signal_series)
            & (macd_series.shift(1) <= signal_series.shift(1))
        ] = 1
        # 當MACD線下穿信號線時賣出
        signals[
            (macd_series < signal_series)
            & (macd_series.shift(1) >= signal_series.shift(1))
        ] = -1
        return signals

    def generate_ma_signals(self, fast_ma, slow_ma):
        """根據移動平均線生成交易信號"""
        signals = pd.Series(0, index=fast_ma.index)
        # 當快線上穿慢線時買入
        signals[(fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))] = 1
        # 當快線下穿慢線時賣出
        signals[(fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))] = -1
        return signals


def main():
    """示例：運行南北水策略"""
    try:

        # 初始化策略
        strategy = NorthSouthFlowStrategies()

        # 加載股票數據
        print("📈 加載股票數據...")
        stock_data = pd.read_csv(
            "data_output / csv / stock_data_2800_HK.csv", index_col=0, parse_dates=True
        )
        if stock_data.empty:
            print("❌ 無法加載股票數據")
            return

        # 生成所有策略的信號
        signals = strategy.generate_all_signals(stock_data)
        if not signals:
            print("❌ 無法生成策略信號")
            return

        # 生成權益曲線並保存
        equity_curves = {}
        strategy_summaries = []

        for strategy_name, signal_series in signals.items():
            print(f"📊 計算 {strategy_name} 的權益曲線...")
            equity_curve = strategy.generate_equity_curve(signal_series, stock_data)

            if not equity_curve.empty:
                equity_curves[strategy_name] = equity_curve

                # 計算策略績效
                total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
                max_drawdown = (
                    (equity_curve - equity_curve.expanding().max())
                    / equity_curve.expanding().max()
                ).min() * 100

                strategy_summaries.append(
                    {
                        "strategy_name": strategy_name,
                        "total_return": f"{total_return:.2f}%",
                        "max_drawdown": f"{max_drawdown:.2f}%",
                        "trading_days": len(equity_curve),
                    }
                )

        # 保存權益曲線
        if equity_curves:
            equity_df = pd.DataFrame(equity_curves)
            timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
            equity_file = f"data_output / csv / north_south_equity_{timestamp}.csv"
            equity_df.to_csv(equity_file)
            print(f"✅ 權益曲線已保存至: {equity_file}")

            # 保存策略摘要
            summary_df = pd.DataFrame(strategy_summaries)
            summary_file = f"data_output / csv / north_south_summary_{timestamp}.csv"
            summary_df.to_csv(summary_file, index=False)
            print(f"✅ 策略摘要已保存至: {summary_file}")

            # 打印策略績效
            print("\n📊 策略績效摘要:")
            print(summary_df.to_string(index=False))
        else:
            print("❌ 無法生成權益曲線")

            return True

    except Exception as e:
        print(f"❌ 運行策略時出錯: {str(e)}")
        return False


if __name__ == "__main__":
    main()
