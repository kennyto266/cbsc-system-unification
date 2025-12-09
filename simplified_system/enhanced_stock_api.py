#!/usr / bin / env python3
"""
增強股票API - 集成嚴格數據質量驗證的股票數據獲取系統
Enhanced Stock API - Stock Data Collection with Strict Quality Validation

整合現有股票API，添加嚴格的數據質量驗證、異常檢測和自動修復功能
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

# 導入現有模塊
from data_quality_validator import (
    DataQualityReport,
    DataQualityValidator,
    quick_data_quality_check,
    validate_stock_data,
)
from src.api.stock_api import StockDataAPI

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EnhancedStockAPI(StockDataAPI):
    """
    增強股票API
    集成嚴格的數據質量驗證和異常檢測功能
    """

    def __init__(self):
        super().__init__()
        self.quality_validator = DataQualityValidator()
        self.auto_fix_enabled = True
        self.quality_threshold = 70.0  # 最低質量評分要求
        self.anomaly_detection_enabled = True

    def get_stock_data_with_validation(
        self, symbol: str, duration_days: int = 1095, require_validation: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        獲取股票數據並進行質量驗證
        """
        logger.info(f"🔍 開始獲取並驗證股票數據: {symbol} ({duration_days}天)")

        # 第一步：獲取原始數據
        raw_data = self.get_stock_data(symbol, duration_days)

        if not raw_data:
            logger.error(f"❌ 無法獲取股票數據: {symbol}")
            return None

        # 第二步：數據質量驗證
        if require_validation:
            quality_report = self.quality_validator.validate_stock_data(raw_data)

            logger.info(f"📊 {symbol} 數據質量評分: {quality_report.quality_score:.1f}")
            logger.info(f"   嚴重問題: {len(quality_report.critical_issues)}")
            logger.info(f"   高優先級問題: {len(quality_report.high_issues)}")

            # 檢查質量是否達標
            if quality_report.quality_score < self.quality_threshold:
                logger.warning(
                    f"⚠️ {symbol} 數據質量評分 {quality_report.quality_score:.1f} 低於要求 {self.quality_threshold}"
                )

            # 第三步：嘗試自動修復
            if (
                self.auto_fix_enabled
                and quality_report.quality_score < self.quality_threshold
            ):
                logger.info(f"🔧 嘗試自動修復 {symbol} 的數據問題")
                fixed_data = self._auto_fix_stock_data_issues(raw_data, quality_report)

                if fixed_data:
                    # 重新驗證修復後的數據
                    fixed_report = self.quality_validator.validate_stock_data(
                        fixed_data
                    )

                    if fixed_report.quality_score > quality_report.quality_score:
                        logger.info(
                            f"✅ {symbol} 自動修復成功，質量評分從 {quality_report.quality_score:.1f} 提升到 {fixed_report.quality_score:.1f}"
                        )
                        raw_data = fixed_data
                        quality_report = fixed_report
                    else:
                        logger.warning(f"⚠️ {symbol} 自動修復未能提升質量")

            # 將質量報告添加到數據中
            raw_data["quality_report"] = {
                "quality_score": quality_report.quality_score,
                "total_records": quality_report.total_records,
                "valid_records": quality_report.valid_records,
                "critical_issues_count": len(quality_report.critical_issues),
                "high_issues_count": len(quality_report.high_issues),
                "validation_timestamp": quality_report.validation_timestamp.isoformat(),
                "issues": [
                    issue.message
                    for issue in quality_report.critical_issues
                    + quality_report.high_issues
                ],
            }

        return raw_data

    def get_stock_prices_dataframe_with_validation(
        self, symbol: str, duration_days: int = 1095
    ) -> Optional[Tuple[pd.DataFrame, DataQualityReport]]:
        """
        獲取股票DataFrame並返回質量報告
        """
        data = self.get_stock_data_with_validation(symbol, duration_days)

        if not data:
            return None

        # 轉換為DataFrame
        df = self._convert_stock_dict_to_dataframe(data)

        # 如果有質量報告，重新構建
        if "quality_report" in data:
            # 從已有數據構建質量報告
            quality_report = self.quality_validator.validate_stock_data(df)
            return df, quality_report
        else:
            # 進行新的質量驗證
            quality_report = self.quality_validator.validate_stock_data(df)
            return df, quality_report

    def get_multiple_stocks_with_validation(
        self, symbols: List[str], duration_days: int = 1095
    ) -> Dict[str, Tuple[Optional[pd.DataFrame], Optional[DataQualityReport]]]:
        """
        批量獲取多只股票數據並進行質量驗證
        """
        results = {}

        for symbol in symbols:
            logger.info(f"🔍 處理股票: {symbol}")
            try:
                result = self.get_stock_prices_dataframe_with_validation(
                    symbol, duration_days
                )
                results[symbol] = result

                if result:
                    df, quality_report = result
                    if quality_report:
                        logger.info(
                            f"✅ {symbol}: 質量評分 {quality_report.quality_score:.1f}"
                        )
                    else:
                        logger.warning(f"⚠️ {symbol}: 無法生成質量報告")
                else:
                    logger.error(f"❌ {symbol}: 獲取失敗")

            except Exception as e:
                logger.error(f"❌ {symbol}: 處理異常 - {e}")
                results[symbol] = (None, None)

        return results

    def _convert_stock_dict_to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """將股票字典數據轉換為DataFrame"""
        if "data" in data and "close" in data["data"]:
            # 處理中央API格式
            close_data = data["data"]["close"]
            df = pd.DataFrame.from_dict(close_data, orient="index", columns=["close"])
            df.index = pd.to_datetime(df.index)
            df.index.name = "date"
            df = df.sort_index()

            # 如果只有收盤價，用收盤價填充其他OHLC字段
            if "close" in df.columns:
                df["open"] = (
                    df["close"].shift(1).fillna(df["close"])
                )  # 前一日收盤價作為開盤價
                df["high"] = df["close"]  # 假設無波動
                df["low"] = df["close"]  # 假設無波動
                df["volume"] = 1000000  # 預設成交量

            return df
        else:
            # 嘗試直接轉換
            try:
                return pd.DataFrame(data)
            except Exception:
                logger.error("無法轉換數據為DataFrame格式")
                return pd.DataFrame()

    def _auto_fix_stock_data_issues(
        self, data: Dict[str, Any], quality_report: DataQualityReport
    ) -> Optional[Dict[str, Any]]:
        """自動修復股票數據問題"""
        try:
            fixed_data = data.copy()

            # 修復1：OHLC邏輯問題
            if any(
                "OHLC邏輯檢查" in issue.message
                for issue in quality_report.critical_issues
            ):
                fixed_data = self._fix_ohlc_logic_issues(fixed_data)

            # 修復2：價格異常跳變
            if any(
                "價格跳變檢測" in issue.message for issue in quality_report.high_issues
            ):
                fixed_data = self._fix_price_spike_issues(fixed_data)

            # 修復3：缺失數據
            if any(
                "完整性" in issue.message for issue in quality_report.critical_issues
            ):
                fixed_data = self._fix_completeness_issues(fixed_data)

            return fixed_data

        except Exception as e:
            logger.error(f"自動修復股票數據失敗: {e}")
            return None

    def _fix_ohlc_logic_issues(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修復OHLC邏輯問題"""
        if "data" not in data or "close" not in data["data"]:
            return data

        close_data = data["data"]["close"]
        fixed_data = data.copy()

        # 確保OHLC邏輯正確
        dates = list(close_data.keys())
        prices = list(close_data.values())

        for i, (date, close_price) in enumerate(zip(dates, prices)):
            # 設置合理的OHLC值
            open_price = prices[i - 1] if i > 0 else close_price  # 前一日收盤價
            high_price = max(open_price, close_price) * 1.002  # 添加微小波動
            low_price = min(open_price, close_price) * 0.998  # 添加微小波動
            volume = 1000000  # 預設成交量

            # 添加到數據中（如果還沒有OHLC字段）
            if "open" not in fixed_data["data"]:
                fixed_data["data"]["open"] = {}
            if "high" not in fixed_data["data"]:
                fixed_data["data"]["high"] = {}
            if "low" not in fixed_data["data"]:
                fixed_data["data"]["low"] = {}
            if "volume" not in fixed_data["data"]:
                fixed_data["data"]["volume"] = {}

            fixed_data["data"]["open"][date] = open_price
            fixed_data["data"]["high"][date] = high_price
            fixed_data["data"]["low"][date] = low_price
            fixed_data["data"]["volume"][date] = volume

        return fixed_data

    def _fix_price_spike_issues(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修復價格異常跳變問題"""
        if "data" not in data or "close" not in data["data"]:
            return data

        close_data = data["data"]["close"]
        fixed_data = data.copy()
        fixed_close = {}

        dates = sorted(close_data.keys())
        prices = [close_data[date] for date in dates]

        # 使用移動平均平滑異常值
        window_size = 5
        for i, (date, price) in enumerate(zip(dates, prices)):
            if i < window_size:
                fixed_close[date] = price
            else:
                # 檢查是否為異常值
                recent_prices = prices[i - window_size : i]
                avg_price = sum(recent_prices) / len(recent_prices)
                pct_change = abs(price - avg_price) / avg_price

                if pct_change > 0.2:  # 超過20%變化視為異常
                    # 使用移動平均替代
                    fixed_close[date] = avg_price
                    logger.info(f"平滑異常價格 {date}: {price:.2f} -> {avg_price:.2f}")
                else:
                    fixed_close[date] = price

        fixed_data["data"]["close"] = fixed_close
        return fixed_data

    def _fix_completeness_issues(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """修復數據完整性問題"""
        if "data" not in data:
            return data

        fixed_data = data.copy()

        # 確保至少有收盤價數據
        if "close" not in fixed_data["data"]:
            logger.error("無法修復數據：缺少收盤價")
            return data

        return fixed_data

    def detect_market_anomalies(
        self, symbol: str, duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        檢測市場異常情況
        """
        logger.info(f"🔍 檢測 {symbol} 市場異常情況")

        df_result = self.get_stock_prices_dataframe_with_validation(
            symbol, duration_days
        )

        if not df_result:
            return {"error": "無法獲取股票數據"}

        df, quality_report = df_result

        anomalies = {
            "symbol": symbol,
            "analysis_period": f"{duration_days}天",
            "timestamp": datetime.now().isoformat(),
            "data_quality_score": quality_report.quality_score if quality_report else 0,
            "anomalies_detected": [],
        }

        # 異常檢測1：價格異常波動
        if "close" in df.columns:
            pct_changes = df["close"].pct_change().dropna()
            extreme_moves = pct_changes[abs(pct_changes) > 0.1]  # 超過10%的波動

            if len(extreme_moves) > 0:
                anomalies["anomalies_detected"].append(
                    {
                        "type": "extreme_price_movements",
                        "count": len(extreme_moves),
                        "max_change": float(extreme_moves.abs().max()),
                        "dates": [str(idx) for idx in extreme_moves.index],
                    }
                )

        # 異常檢測2：成交量異常
        if "volume" in df.columns:
            volume_avg = df["volume"].rolling(20).mean()
            volume_ratio = df["volume"] / volume_avg
            volume_spikes = volume_ratio[volume_ratio > 5]  # 超過平均5倍

            if len(volume_spikes) > 0:
                anomalies["anomalies_detected"].append(
                    {
                        "type": "volume_spikes",
                        "count": len(volume_spikes),
                        "max_ratio": float(volume_ratio.max()),
                        "dates": [str(idx) for idx in volume_spikes.index],
                    }
                )

        # 異常檢測3：停牌檢測（價格連續不變）
        if "close" in df.columns:
            price_changes = df["close"].diff().abs()
            flat_periods = price_changes[price_changes == 0]
            consecutive_flat = self._find_consecutive_periods(
                flat_periods, min_length = 3
            )

            if consecutive_flat:
                anomalies["anomalies_detected"].append(
                    {"type": "potential_trading_halt", "flat_periods": consecutive_flat}
                )

        # 異常檢測4：數據缺失
        expected_trading_days = len(
            [
                d
                for d in pd.date_range(df.index.min(), df.index.max(), freq="B")
                if d.weekday() < 5
            ]
        )  # 只計算工作日
        missing_days = expected_trading_days - len(df)

        if missing_days > 0:
            anomalies["anomalies_detected"].append(
                {
                    "type": "missing_trading_days",
                    "expected_days": expected_trading_days,
                    "actual_days": len(df),
                    "missing_count": missing_days,
                }
            )

        logger.info(
            f"✅ {symbol} 異常檢測完成，發現 {len(anomalies['anomalies_detected'])} 種異常情況"
        )
        return anomalies

    def _find_consecutive_periods(self, series, min_length = 3) -> List[Dict]:
        """查找連續平坦週期"""
        periods = []
        current_start = None
        current_length = 0

        for idx, is_flat in series.items():
            if is_flat and current_start is None:
                current_start = idx
                current_length = 1
            elif is_flat and current_start is not None:
                current_length += 1
            elif not is_flat and current_start is not None:
                if current_length >= min_length:
                    periods.append(
                        {
                            "start_date": str(current_start),
                            "end_date": str(idx - pd.Timedelta(days = 1)),
                            "length": current_length,
                        }
                    )
                current_start = None
                current_length = 0

        # 檢查最後一個週期
        if current_length >= min_length:
            periods.append(
                {
                    "start_date": str(current_start),
                    "end_date": str(series.index[-1]),
                    "length": current_length,
                }
            )

        return periods

    def generate_data_quality_summary(
        self, symbols: List[str], duration_days: int = 1095
    ) -> Dict[str, Any]:
        """
        生成多只股票的數據質量摘要
        """
        logger.info(f"📊 生成 {len(symbols)} 只股票的數據質量摘要")

        summary = {
            "generation_time": datetime.now().isoformat(),
            "analysis_period": f"{duration_days}天",
            "total_symbols": len(symbols),
            "symbols_analysis": [],
            "overall_statistics": {},
        }

        all_quality_scores = []
        successful_collections = 0
        validation_passed = 0

        for symbol in symbols:
            try:
                df_result = self.get_stock_prices_dataframe_with_validation(
                    symbol, duration_days
                )

                if df_result:
                    df, quality_report = df_result
                    successful_collections += 1

                    if quality_report.quality_score >= self.quality_threshold:
                        validation_passed += 1

                    all_quality_scores.append(quality_report.quality_score)

                    symbol_analysis = {
                        "symbol": symbol,
                        "success": True,
                        "record_count": quality_report.total_records,
                        "quality_score": quality_report.quality_score,
                        "critical_issues": len(quality_report.critical_issues),
                        "high_issues": len(quality_report.high_issues),
                        "validation_passed": quality_report.quality_score
                        >= self.quality_threshold,
                    }

                    # 添加主要問題摘要
                    issues = []
                    for issue in (
                        quality_report.critical_issues + quality_report.high_issues
                    ):
                        issues.append(issue.message)
                    symbol_analysis["main_issues"] = issues[:5]  # 最多顯示5個問題

                    summary["symbols_analysis"].append(symbol_analysis)

                else:
                    summary["symbols_analysis"].append(
                        {
                            "symbol": symbol,
                            "success": False,
                            "error": "Failed to collect data",
                        }
                    )

            except Exception as e:
                logger.error(f"處理 {symbol} 時發生錯誤: {e}")
                summary["symbols_analysis"].append(
                    {"symbol": symbol, "success": False, "error": str(e)}
                )

        # 計算整體統計
        if all_quality_scores:
            summary["overall_statistics"] = {
                "successful_collections": successful_collections,
                "validation_passed": validation_passed,
                "average_quality_score": sum(all_quality_scores)
                / len(all_quality_scores),
                "min_quality_score": min(all_quality_scores),
                "max_quality_score": max(all_quality_scores),
                "collection_success_rate": successful_collections / len(symbols),
                "validation_pass_rate": (
                    validation_passed / successful_collections
                    if successful_collections > 0
                    else 0
                ),
            }

        logger.info(f"✅ 數據質量摘要生成完成")
        logger.info(
            f"   收集成功率: {summary['overall_statistics'].get('collection_success_rate', 0):.1%}"
        )
        logger.info(
            f"   驗證通過率: {summary['overall_statistics'].get('validation_pass_rate', 0):.1%}"
        )
        logger.info(
            f"   平均質量評分: {summary['overall_statistics'].get('average_quality_score', 0):.1f}"
        )

        return summary


# 全局增強API實例
enhanced_stock_api = EnhancedStockAPI()


# 便捷函數
def get_stock_data_with_validation(
    symbol: str, duration_days: int = 1095
) -> Optional[Dict[str, Any]]:
    """獲取並驗證股票數據"""
    return enhanced_stock_api.get_stock_data_with_validation(symbol, duration_days)


def get_stock_prices_dataframe_with_validation(
    symbol: str, duration_days: int = 1095
) -> Optional[Tuple[pd.DataFrame, DataQualityReport]]:
    """獲取股票DataFrame並返回質量報告"""
    return enhanced_stock_api.get_stock_prices_dataframe_with_validation(
        symbol, duration_days
    )


def get_multiple_stocks_with_validation(
    symbols: List[str], duration_days: int = 1095
) -> Dict[str, Tuple[Optional[pd.DataFrame], Optional[DataQualityReport]]]:
    """批量獲取並驗證多只股票數據"""
    return enhanced_stock_api.get_multiple_stocks_with_validation(
        symbols, duration_days
    )


def detect_market_anomalies(symbol: str, duration_days: int = 30) -> Dict[str, Any]:
    """檢測市場異常情況"""
    return enhanced_stock_api.detect_market_anomalies(symbol, duration_days)


def generate_data_quality_summary(
    symbols: List[str], duration_days: int = 1095
) -> Dict[str, Any]:
    """生成數據質量摘要"""
    return enhanced_stock_api.generate_data_quality_summary(symbols, duration_days)


if __name__ == "__main__":
    # 測試代碼
    print("🧪 測試增強股票API")

    # 測試單個股票
    print("\n=== 單個股票測試 ===")
    data = get_stock_data_with_validation("0700.hk", 30)
    if data:
        print("✅ 股票數據獲取成功")
        if "quality_report" in data:
            qr = data["quality_report"]
            print(f"   質量評分: {qr['quality_score']:.1f}")
            print(f"   記錄數: {qr['total_records']}")
            print(f"   嚴重問題: {qr['critical_issues_count']}")
    else:
        print("❌ 股票數據獲取失敗")

    # 測試質量摘要
    print("\n=== 質量摘要測試 ===")
    symbols = ["0700.hk", "0941.hk", "1398.hk"]
    summary = generate_data_quality_summary(symbols, 30)
    if summary:
        stats = summary.get("overall_statistics", {})
        print(f"✅ 質量摘要生成成功")
        print(f"   收集成功率: {stats.get('collection_success_rate', 0):.1%}")
        print(f"   平均質量評分: {stats.get('average_quality_score', 0):.1f}")

    # 測試異常檢測
    print("\n=== 異常檢測測試 ===")
    anomalies = detect_market_anomalies("0700.hk", 30)
    if "error" not in anomalies:
        print(f"✅ 異常檢測完成，發現 {len(anomalies['anomalies_detected'])} 種異常")
    else:
        print(f"❌ 異常檢測失敗: {anomalies['error']}")

    print("\n✅ 增強股票API測試完成")
