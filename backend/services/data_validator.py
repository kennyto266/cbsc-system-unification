"""
Data Validation Service
數據質量驗證服務
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from data_config import DataValidatorConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """驗證結果"""
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    data_quality_score: float  # 0.0 to 1.0


class DataValidator:
    """數據驗證器"""

    def __init__(self, config: Optional[DataValidatorConfig] = None):
        self.config = config or DataValidatorConfig()

    def validate_historical_data(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> ValidationResult:
        """
        驗證歷史數據質量

        Args:
            df: 歷史數據 DataFrame (必須包含 date, open, high, low, close 列)
            symbol: 股票代碼

        Returns:
            ValidationResult: 驗證結果
        """
        issues = []
        warnings = []

        # 基本檢查
        if df is None or len(df) == 0:
            return ValidationResult(
                is_valid=False,
                issues=[f"{symbol}: 數據為空"],
                warnings=[],
                data_quality_score=0.0
            )

        # 檢查必需列
        required_columns = ['date', 'open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return ValidationResult(
                is_valid=False,
                issues=[f"{symbol}: 缺少必需列: {missing_columns}"],
                warnings=[],
                data_quality_score=0.0
            )

        # 1. 檢查缺失值
        self._check_missing_values(df, symbol, issues, warnings)

        # 2. 檢查價格異常值
        self._check_price_anomalies(df, symbol, issues, warnings)

        # 3. 檢查價格邏輯 (high >= low, close 在區間內)
        self._check_price_logic(df, symbol, issues, warnings)

        # 4. 檢查時間序列連續性
        self._check_time_series_continuity(df, symbol, issues, warnings)

        # 5. 計算數據質量分數
        quality_score = self._calculate_quality_score(df, issues, warnings)

        is_valid = len(issues) == 0

        if is_valid:
            logger.info(f"{symbol}: 數據驗證通過，質量分數: {quality_score:.2f}")
        else:
            logger.error(f"{symbol}: 數據驗證失敗 - {issues}")

        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            data_quality_score=quality_score
        )

    def _check_missing_values(
        self,
        df: pd.DataFrame,
        symbol: str,
        issues: List[str],
        warnings: List[str]
    ) -> None:
        """檢查缺失值"""
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                missing_ratio = missing_count / len(df)
                if missing_ratio > self.config.max_missing_ratio:
                    issues.append(
                        f"{symbol}: 列 '{col}' 缺失值過多: "
                        f"{missing_count}/{len(df)} ({missing_ratio:.1%})"
                    )
                else:
                    warnings.append(
                        f"{symbol}: 列 '{col}' 有少量缺失值: "
                        f"{missing_count}/{len(df)}"
                    )

    def _check_price_anomalies(
        self,
        df: pd.DataFrame,
        symbol: str,
        issues: List[str],
        warnings: List[str]
    ) -> None:
        """檢查價格異常值"""
        price_columns = ['open', 'high', 'low', 'close']

        for col in price_columns:
            if col not in df.columns:
                continue

            # 檢查非正數
            invalid_prices = (df[col] <= 0).sum()
            if invalid_prices > 0:
                issues.append(
                    f"{symbol}: 列 '{col}' 包含 {invalid_prices} 個非正數值"
                )

            # 檢查極端變化
            if len(df) > 1:
                price_change = df[col].pct_change().abs()
                extreme_changes = (
                    price_change > self.config.max_price_change_ratio
                ).sum()

                if extreme_changes > 0:
                    warnings.append(
                        f"{symbol}: 列 '{col}' 有 {extreme_changes} 個極端變化 "
                        f"(>{self.config.max_price_change_ratio:.0%})"
                    )

    def _check_price_logic(
        self,
        df: pd.DataFrame,
        symbol: str,
        issues: List[str],
        warnings: List[str]
    ) -> None:
        """檢查價格邏輯"""
        if all(col in df.columns for col in ['high', 'low']):
            # high 必須 >= low
            invalid_hl = (df['high'] < df['low']).sum()
            if invalid_hl > 0:
                issues.append(
                    f"{symbol}: 有 {invalid_hl} 行 high < low"
                )

        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # close 應該在 high-low 區間內（允許少量誤差）
            close_above_high = (df['close'] > df['high'] * 1.01).sum()
            close_below_low = (df['close'] < df['low'] * 0.99).sum()

            if close_above_high > 0:
                warnings.append(
                    f"{symbol}: 有 {close_above_high} 行 close > high"
                )
            if close_below_low > 0:
                warnings.append(
                    f"{symbol}: 有 {close_below_low} 行 close < low"
                )

    def _check_time_series_continuity(
        self,
        df: pd.DataFrame,
        symbol: str,
        issues: List[str],
        warnings: List[str]
    ) -> None:
        """檢查時間序列連續性"""
        if 'date' not in df.columns:
            return

        try:
            df['date'] = pd.to_datetime(df['date'])
            df_sorted = df.sort_values('date')

            # 計算日期間隙
            if len(df_sorted) > 1:
                date_gaps = df_sorted['date'].diff()[1:]
                large_gaps = date_gaps[date_gaps > timedelta(days=self.config.max_gap_days)]

                if len(large_gaps) > 0:
                    if not self.config.allow_gaps:
                        issues.append(
                            f"{symbol}: 發現 {len(large_gaps)} 個大日期間隙 "
                            f"(>{self.config.max_gap_days} 天)"
                        )
                    else:
                        warnings.append(
                            f"{symbol}: 發現 {len(large_gaps)} 個日期間隙"
                        )

        except Exception as e:
            warnings.append(f"{symbol}: 日期解析失敗: {str(e)}")

    def _calculate_quality_score(
        self,
        df: pd.DataFrame,
        issues: List[str],
        warnings: List[str]
    ) -> float:
        """計算數據質量分數 (0.0 to 1.0)"""
        base_score = 1.0

        # 每個問題扣分
        issue_penalty = 0.3
        warning_penalty = 0.05

        score = base_score - (len(issues) * issue_penalty) - (len(warnings) * warning_penalty)

        return max(0.0, min(1.0, score))


class DataValidationError(Exception):
    """數據驗證錯誤"""

    def __init__(self, symbol: str, result: ValidationResult):
        self.symbol = symbol
        self.result = result
        message = f"{symbol} 數據驗證失敗: {'; '.join(result.issues)}"
        super().__init__(message)
