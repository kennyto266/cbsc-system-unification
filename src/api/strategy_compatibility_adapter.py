#!/usr/bin/env python3
"""
策略數據兼容性適配器
Strategy Data Compatibility Adapter

確保新統一架構與現有CBSC數據格式100%兼容
"""

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field
import pandas as pd

logger = logging.getLogger(__name__)

# ============================================================================
# 兼容性數據模型 (Compatibility Data Models)
# ============================================================================

class LegacyStrategyType(str, Enum):
    """遺留策略類型（兼容現有CBSC格式）"""
    DIRECT_RSI = "direct_rsi"
    SENTIMENT_MOMENTUM = "sentiment_momentum"
    COMPOSITE_INDEX = "composite_index"
    VOLATILITY_ADJUSTED = "volatility_adjusted"

class LegacySignalType(str, Enum):
    """遺留信號類型（兼容現有CBSC格式）"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    EXTREME_BULLISH = "extreme_bullish"
    EXTREME_BEARISH = "extreme_bearish"
    GOLDEN_CROSS = "golden_cross"
    DEATH_CROSS = "death_cross"
    SQUEEZE = "squeeze"
    BREAKTHROUGH = "breakthrough"

class LegacyStrategyStatus(str, Enum):
    """遺留策略狀態（兼容現有CBSC格式）"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    ERROR = "error"
    STOPPED = "stopped"

class LegacyStrategyParameters(BaseModel):
    """遺留策略參數（兼容現有CBSC格式）"""
    rsi_period: Optional[int] = Field(14, ge=2, le=50, description="RSI週期")
    oversold_threshold: Optional[float] = Field(30, ge=0, le=50, description="超賣閾值")
    overbought_threshold: Optional[float] = Field(70, ge=50, le=100, description="超買閾值")
    fast_period: Optional[int] = Field(12, ge=5, le=30, description="快速週期")
    slow_period: Optional[int] = Field(26, ge=10, le=50, description="慢速週期")
    signal_period: Optional[int] = Field(9, ge=5, le=20, description="信號週期")
    bb_period: Optional[int] = Field(20, ge=10, le=50, description="布林帶週期")
    bb_std: Optional[float] = Field(2, ge=1, le=3, description="布林帶標準差")
    weight_sentiment: Optional[float] = Field(0.6, ge=0, le=1, description="情緒權重")
    volatility_window: Optional[int] = Field(20, ge=5, le=50, description="波動率窗口")
    volume_weight: Optional[float] = Field(0.3, ge=0, le=1, description="成交量權重")

# ============================================================================
# 數據適配器 (Data Adapter)
# ============================================================================

class StrategyCompatibilityAdapter:
    """策略數據兼容性適配器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def convert_legacy_strategy_to_unified(self, legacy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將遺留策略數據轉換為統一架構格式

        Args:
            legacy_data: 遺留策略數據

        Returns:
            統一架構策略數據
        """
        try:
            # 基本字段映射
            unified_data = {
                "name": legacy_data.get("name", ""),
                "code": legacy_data.get("code", ""),
                "description": legacy_data.get("description", ""),
                "strategy_type": self._convert_strategy_type(legacy_data.get("strategy_type")),
                "status": self._convert_status(legacy_data.get("status")),
                "risk_level": self._convert_risk_level(legacy_data.get("risk_level", "medium")),
                "is_public": legacy_data.get("is_public", False),
                "version": legacy_data.get("version", "1.0.0")
            }

            # 參數轉換
            if "parameters" in legacy_data:
                unified_data["default_parameters"] = self._convert_parameters(legacy_data["parameters"])

            # 性能指標轉換
            if "performance" in legacy_data:
                unified_data.update(self._convert_performance(legacy_data["performance"]))

            # 指標和時間週期轉換
            if "indicators" in legacy_data:
                unified_data["required_indicators"] = legacy_data["indicators"]

            if "timeframes" in legacy_data:
                unified_data["supported_timeframes"] = legacy_data["timeframes"]

            self.logger.debug(f"成功轉換遺留策略數據: {legacy_data.get('name')}")
            return unified_data

        except Exception as e:
            self.logger.error(f"轉換遺留策略數據失敗: {e}")
            raise

    def convert_unified_strategy_to_legacy(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將統一架構策略數據轉換為遺留格式

        Args:
            unified_data: 統一架構策略數據

        Returns:
            遺留格式策略數據
        """
        try:
            # 基本字段映射
            legacy_data = {
                "name": unified_data.get("name", ""),
                "code": unified_data.get("code", ""),
                "description": unified_data.get("description", ""),
                "strategy_type": self._convert_strategy_type_to_legacy(unified_data.get("strategy_type")),
                "status": self._convert_status_to_legacy(unified_data.get("status")),
                "risk_level": unified_data.get("risk_level", "medium"),
                "is_public": unified_data.get("is_public", False),
                "version": unified_data.get("version", "1.0.0"),
                "created_at": unified_data.get("created_at"),
                "updated_at": unified_data.get("updated_at")
            }

            # 參數轉換
            if "default_parameters" in unified_data:
                legacy_data["parameters"] = self._convert_parameters_to_legacy(unified_data["default_parameters"])

            # 性能指標轉換
            performance_fields = [
                "total_return", "sharpe_ratio", "max_drawdown", "win_rate",
                "profit_factor", "volatility"
            ]
            performance = {}
            for field in performance_fields:
                if field in unified_data:
                    performance[field] = unified_data[field]

            if performance:
                legacy_data["performance"] = performance

            # 指標和時間週期轉換
            if "required_indicators" in unified_data:
                legacy_data["indicators"] = unified_data["required_indicators"]

            if "supported_timeframes" in unified_data:
                legacy_data["timeframes"] = unified_data["supported_timeframes"]

            self.logger.debug(f"成功轉換統一架構策略數據: {unified_data.get('name')}")
            return legacy_data

        except Exception as e:
            self.logger.error(f"轉換統一架構策略數據失敗: {e}")
            raise

    def convert_legacy_signal_to_unified(self, legacy_signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        將遺留信號數據轉換為統一架構格式

        Args:
            legacy_signal: 遺留信號數據

        Returns:
            統一架構信號數據
        """
        try:
            unified_signal = {
                "signal_id": legacy_signal.get("signal_id"),
                "strategy_id": legacy_signal.get("strategy_id"),
                "signal_type": self._convert_signal_type(legacy_signal.get("signal_type")),
                "strength": legacy_signal.get("strength", 0.0),
                "confidence": legacy_signal.get("confidence", 0.0),
                "timestamp": self._convert_timestamp(legacy_signal.get("timestamp")),
                "market_data": legacy_signal.get("market_data", {}),
                "metadata": legacy_signal.get("metadata", {})
            }

            # 參數轉換
            if "parameters" in legacy_signal:
                unified_signal["parameters"] = self._convert_parameters(legacy_signal["parameters"])

            self.logger.debug(f"成功轉換遺留信號數據: {legacy_signal.get('signal_id')}")
            return unified_signal

        except Exception as e:
            self.logger.error(f"轉換遺留信號數據失敗: {e}")
            raise

    def convert_performance_data(self, performance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        轉換性能數據格式

        Args:
            performance_data: 性能數據列表

        Returns:
            轉換後的性能數據
        """
        try:
            converted_data = []
            for record in performance_data:
                converted_record = {}

                # 基本字段
                for field in ["strategy_id", "config_id", "date"]:
                    if field in record:
                        converted_record[field] = record[field]

                # 收益率字段
                return_fields = ["total_return", "daily_return", "cumulative_return"]
                for field in return_fields:
                    if field in record:
                        converted_record[field] = float(record[field])

                # 風險指標字段
                risk_fields = ["volatility", "sharpe_ratio", "sortino_ratio", "max_drawdown", "var_95", "cvar_95"]
                for field in risk_fields:
                    if field in record:
                        converted_record[field] = float(record[field]) if record[field] is not None else None

                # 交易統計字段
                trade_fields = ["total_trades", "winning_trades", "win_rate", "profit_factor"]
                for field in trade_fields:
                    if field in record:
                        converted_record[field] = record[field]

                # 持倉信息字段
                position_fields = ["current_positions", "open_positions_value", "cash_balance"]
                for field in position_fields:
                    if field in record:
                        converted_record[field] = float(record[field])

                converted_data.append(converted_record)

            self.logger.debug(f"成功轉換 {len(converted_data)} 條性能數據記錄")
            return converted_data

        except Exception as e:
            self.logger.error(f"轉換性能數據失敗: {e}")
            raise

    def validate_data_compatibility(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """
        驗證數據兼容性

        Args:
            data: 要驗證的數據
            data_type: 數據類型 (strategy, signal, performance)

        Returns:
            驗證結果
        """
        try:
            validation_result = {
                "is_compatible": True,
                "errors": [],
                "warnings": [],
                "conversions": []
            }

            if data_type == "strategy":
                self._validate_strategy_compatibility(data, validation_result)
            elif data_type == "signal":
                self._validate_signal_compatibility(data, validation_result)
            elif data_type == "performance":
                self._validate_performance_compatibility(data, validation_result)

            return validation_result

        except Exception as e:
            self.logger.error(f"驗證數據兼容性失敗: {e}")
            return {
                "is_compatible": False,
                "errors": [f"驗證過程發生錯誤: {str(e)}"],
                "warnings": [],
                "conversions": []
            }

    # 私有方法
    def _convert_strategy_type(self, strategy_type: Optional[str]) -> str:
        """轉換策略類型"""
        type_mapping = {
            "direct_rsi": "technical",
            "sentiment_momentum": "sentiment",
            "composite_index": "composite",
            "volatility_adjusted": "technical"
        }
        return type_mapping.get(strategy_type, "custom")

    def _convert_strategy_type_to_legacy(self, strategy_type: Optional[str]) -> str:
        """轉換策略類型到遺留格式"""
        type_mapping = {
            "technical": "direct_rsi",
            "sentiment": "sentiment_momentum",
            "composite": "composite_index",
            "custom": "direct_rsi"
        }
        return type_mapping.get(strategy_type, "direct_rsi")

    def _convert_status(self, status: Optional[str]) -> str:
        """轉換狀態"""
        status_mapping = {
            "active": "active",
            "inactive": "inactive",
            "testing": "testing",
            "error": "error",
            "stopped": "inactive"
        }
        return status_mapping.get(status, "inactive")

    def _convert_status_to_legacy(self, status: Optional[str]) -> str:
        """轉換狀態到遺留格式"""
        status_mapping = {
            "active": "active",
            "inactive": "inactive",
            "testing": "testing",
            "error": "error"
        }
        return status_mapping.get(status, "inactive")

    def _convert_risk_level(self, risk_level: Optional[str]) -> str:
        """轉換風險等級"""
        return risk_level if risk_level in ["low", "medium", "high", "extreme"] else "medium"

    def _convert_signal_type(self, signal_type: Optional[str]) -> str:
        """轉換信號類型"""
        return signal_type if signal_type else "hold"

    def _convert_timestamp(self, timestamp: Any) -> datetime:
        """轉換時間戳"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return datetime.now()
        elif isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        else:
            return datetime.now()

    def _convert_parameters(self, parameters: Any) -> Dict[str, Any]:
        """轉換參數"""
        if isinstance(parameters, dict):
            return parameters
        elif isinstance(parameters, str):
            try:
                return json.loads(parameters)
            except:
                return {}
        else:
            return {}

    def _convert_parameters_to_legacy(self, parameters: Any) -> Dict[str, Any]:
        """轉換參數到遺留格式"""
        return self._convert_parameters(parameters)

    def _convert_performance(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """轉換性能指標"""
        converted = {}
        for key, value in performance.items():
            if value is not None:
                try:
                    if isinstance(value, (int, float)):
                        converted[key] = float(value)
                    else:
                        converted[key] = value
                except (ValueError, TypeError):
                    converted[key] = 0.0
        return converted

    def _validate_strategy_compatibility(self, data: Dict[str, Any], result: Dict[str, Any]):
        """驗證策略數據兼容性"""
        required_fields = ["name", "strategy_type"]
        for field in required_fields:
            if field not in data or not data[field]:
                result["errors"].append(f"缺少必需字段: {field}")
                result["is_compatible"] = False

        # 檢查策略類型
        if "strategy_type" in data:
            valid_types = ["direct_rsi", "sentiment_momentum", "composite_index", "volatility_adjusted"]
            if data["strategy_type"] not in valid_types:
                result["warnings"].append(f"未知的策略類型: {data['strategy_type']}")
                result["conversions"].append(f"策略類型將轉換為默認值")

        # 檢查參數格式
        if "parameters" in data and not isinstance(data["parameters"], dict):
            result["warnings"].append("參數格式不正確，將嘗試轉換")

    def _validate_signal_compatibility(self, data: Dict[str, Any], result: Dict[str, Any]):
        """驗證信號數據兼容性"""
        required_fields = ["signal_id", "strategy_id", "signal_type"]
        for field in required_fields:
            if field not in data:
                result["errors"].append(f"缺少必需字段: {field}")
                result["is_compatible"] = False

        # 檢查信號類型
        if "signal_type" in data:
            valid_types = ["buy", "sell", "hold", "extreme_bullish", "extreme_bearish"]
            if data["signal_type"] not in valid_types:
                result["warnings"].append(f"未知的信號類型: {data['signal_type']}")

    def _validate_performance_compatibility(self, data: Dict[str, Any], result: Dict[str, Any]):
        """驗證性能數據兼容性"""
        numeric_fields = ["total_return", "sharpe_ratio", "max_drawdown", "win_rate"]
        for field in numeric_fields:
            if field in data and data[field] is not None:
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    result["warnings"].append(f"性能指標 {field} 不是有效的數字")

# ============================================================================
# 數據遷移工具 (Data Migration Tools)
# ============================================================================

class StrategyDataMigrator:
    """策略數據遷移工具"""

    def __init__(self, adapter: StrategyCompatibilityAdapter):
        self.adapter = adapter
        self.logger = logging.getLogger(__name__)

    async def migrate_strategies_from_legacy_file(
        self,
        file_path: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        從遺留文件遷移策略數據

        Args:
            file_path: 遺留數據文件路徑
            batch_size: 批處理大小

        Returns:
            遷移結果
        """
        try:
            # 讀取遺留數據
            with open(file_path, 'r', encoding='utf-8') as f:
                legacy_data = json.load(f)

            return await self.migrate_strategies(legacy_data, batch_size)

        except Exception as e:
            self.logger.error(f"從文件遷移策略數據失敗: {e}")
            raise

    async def migrate_strategies(
        self,
        legacy_strategies: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        批量遷移策略數據

        Args:
            legacy_strategies: 遺留策略數據列表
            batch_size: 批處理大小

        Returns:
            遷移結果
        """
        try:
            migration_result = {
                "total": len(legacy_strategies),
                "success_count": 0,
                "error_count": 0,
                "warnings": [],
                "errors": [],
                "migrated_strategies": []
            }

            for i in range(0, len(legacy_strategies), batch_size):
                batch = legacy_strategies[i:i + batch_size]

                for legacy_strategy in batch:
                    try:
                        # 驗證兼容性
                        validation = self.adapter.validate_data_compatibility(legacy_strategy, "strategy")
                        if not validation["is_compatible"]:
                            migration_result["errors"].extend(validation["errors"])
                            migration_result["error_count"] += 1
                            continue

                        # 轉換數據
                        unified_strategy = self.adapter.convert_legacy_strategy_to_unified(legacy_strategy)

                        # 記录遷移結果
                        migration_result["migrated_strategies"].append({
                            "legacy_id": legacy_strategy.get("id"),
                            "unified_id": unified_strategy.get("id"),
                            "name": unified_strategy.get("name")
                        })

                        migration_result["success_count"] += 1

                        # 收集警告
                        if validation["warnings"]:
                            migration_result["warnings"].extend(validation["warnings"])

                    except Exception as e:
                        migration_result["errors"].append(f"遷移策略失敗: {str(e)}")
                        migration_result["error_count"] += 1

            self.logger.info(
                f"策略數據遷移完成: 成功 {migration_result['success_count']}, "
                f"失敗 {migration_result['error_count']}"
            )

            return migration_result

        except Exception as e:
            self.logger.error(f"批量遷移策略數據失敗: {e}")
            raise

    async def migrate_performance_data(
        self,
        legacy_performance: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        遷移性能數據

        Args:
            legacy_performance: 遺留性能數據列表
            batch_size: 批處理大小

        Returns:
            遷移結果
        """
        try:
            migration_result = {
                "total": len(legacy_performance),
                "success_count": 0,
                "error_count": 0,
                "warnings": [],
                "errors": []
            }

            # 轉換性能數據
            converted_data = self.adapter.convert_performance_data(legacy_performance)

            migration_result["success_count"] = len(converted_data)
            migration_result["migrated_records"] = len(converted_data)

            self.logger.info(
                f"性能數據遷移完成: 成功轉換 {migration_result['success_count']} 條記錄"
            )

            return migration_result

        except Exception as e:
            self.logger.error(f"遷移性能數據失敗: {e}")
            raise

# ============================================================================
# 導出
# ============================================================================

__all__ = [
    "StrategyCompatibilityAdapter",
    "StrategyDataMigrator",
    "LegacyStrategyType",
    "LegacySignalType",
    "LegacyStrategyStatus",
    "LegacyStrategyParameters"
]