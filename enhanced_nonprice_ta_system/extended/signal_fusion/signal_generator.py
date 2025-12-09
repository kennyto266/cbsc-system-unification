"""
Signal Generator - Phase 4.1 Implementation
单指标信号生成器 - Phase 4.1实施

This module implements comprehensive signal generation for individual indicators,
including signal strength scoring, confidence assessment, and historical tracking.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from pathlib import Path
import warnings

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型枚举"""
    BUY = 1
    SELL = -1
    HOLD = 0
    STRONG_BUY = 2
    STRONG_SELL = -2
    WEAK_BUY = 0.5
    WEAK_SELL = -0.5

class SignalFormat(Enum):
    """信号格式枚举"""
    BINARY = "binary"          # 简单买卖信号
    MULTI_LEVEL = "multi_level"  # 多级信号
    CONTINUOUS = "continuous"   # 连续分数
    PROBABILITY = "probability"  # 概率分布

@dataclass
class Signal:
    """单个信号数据结构"""
    timestamp: datetime
    indicator_name: str
    signal_type: SignalType
    signal_value: float
    strength: float  # 信号强度 1-10
    confidence: float  # 置信度 0-1
    raw_indicator_value: float
    parameters: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'indicator_name': self.indicator_name,
            'signal_type': self.signal_type.value,
            'signal_value': self.signal_value,
            'strength': self.strength,
            'confidence': self.confidence,
            'raw_indicator_value': self.raw_indicator_value,
            'parameters': self.parameters,
            'metadata': self.metadata
        }

@dataclass
class SignalStatistics:
    """信号统计信息"""
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    avg_strength: float = 0.0
    avg_confidence: float = 0.0
    signal_frequency: float = 0.0  # 每日信号数量
    last_update: datetime = field(default_factory=datetime.now)

class SignalGenerator:
    """
    信号生成器 - Phase 4.1核心实现

    功能：
    1. 标准化信号格式生成
    2. 信号强度评分 (1-10)
    3. 信号置信度评估
    4. 信号历史记录
    5. 信号统计分析
    """

    def __init__(self,
                 signal_format: SignalFormat = SignalFormat.MULTI_LEVEL,
                 confidence_threshold: float = 0.6,
                 strength_method: str = 'z_score',
                 enable_historical_tracking: bool = True,
                 cache_dir: Optional[str] = None):
        """
        初始化信号生成器

        Args:
            signal_format: 信号格式
            confidence_threshold: 置信度阈值
            strength_method: 强度计算方法 ('z_score', 'percentile', 'absolute')
            enable_historical_tracking: 启用历史跟踪
            cache_dir: 缓存目录
        """
        self.signal_format = signal_format
        self.confidence_threshold = confidence_threshold
        self.strength_method = strength_method
        self.enable_historical_tracking = enable_historical_tracking

        # 历史信号存储
        self.signal_history: Dict[str, List[Signal]] = {}
        self.signal_statistics: Dict[str, SignalStatistics] = {}

        # 缓存设置
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./cache/signal_fusion")
        if enable_historical_tracking:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_historical_data()

        # 信号强度计算配置
        self.strength_config = {
            'z_score': {
                'weak_threshold': 1.0,
                'medium_threshold': 1.5,
                'strong_threshold': 2.0
            },
            'percentile': {
                'weak_threshold': 0.6,
                'medium_threshold': 0.8,
                'strong_threshold': 0.9
            },
            'absolute': {
                'weak_threshold': 0.3,
                'medium_threshold': 0.6,
                'strong_threshold': 0.8
            }
        }

        logger.info(f"SignalGenerator initialized with format: {signal_format.value}")

    def generate_signal(self,
                       indicator_name: str,
                       indicator_values: pd.Series,
                       parameters: Dict[str, Any],
                       current_value: Optional[float] = None,
                       market_context: Optional[Dict] = None) -> Signal:
        """
        生成单个指标信号

        Args:
            indicator_name: 指标名称
            indicator_values: 指标值序列
            parameters: 指标参数
            current_value: 当前指标值（可选，默认使用最后一个值）
            market_context: 市场上下文信息

        Returns:
            Signal: 生成的信号
        """
        try:
            # 获取当前值
            if current_value is None:
                current_value = indicator_values.iloc[-1]

            # 计算信号值和类型
            signal_type, signal_value = self._calculate_signal_type_and_value(
                indicator_values, current_value, parameters
            )

            # 计算信号强度
            strength = self._calculate_signal_strength(
                indicator_values, current_value, signal_type
            )

            # 计算置信度
            confidence = self._calculate_signal_confidence(
                indicator_values, current_value, parameters, market_context
            )

            # 创建信号
            signal = Signal(
                timestamp=datetime.now(),
                indicator_name=indicator_name,
                signal_type=signal_type,
                signal_value=signal_value,
                strength=strength,
                confidence=confidence,
                raw_indicator_value=current_value,
                parameters=parameters,
                metadata={
                    'signal_format': self.signal_format.value,
                    'strength_method': self.strength_method,
                    'market_context': market_context or {}
                }
            )

            # 更新历史记录
            if self.enable_historical_tracking:
                self._update_historical_record(signal)

            logger.debug(f"Generated signal for {indicator_name}: {signal_type.name} "
                        f"(strength: {strength:.2f}, confidence: {confidence:.2f})")

            return signal

        except Exception as e:
            logger.error(f"Error generating signal for {indicator_name}: {str(e)}")
            # 返回中性信号
            return Signal(
                timestamp=datetime.now(),
                indicator_name=indicator_name,
                signal_type=SignalType.HOLD,
                signal_value=0.0,
                strength=1.0,
                confidence=0.0,
                raw_indicator_value=current_value or 0.0,
                parameters=parameters,
                metadata={'error': str(e)}
            )

    def _calculate_signal_type_and_value(self,
                                       indicator_values: pd.Series,
                                       current_value: float,
                                       parameters: Dict[str, Any]) -> Tuple[SignalType, float]:
        """
        计算信号类型和数值

        Args:
            indicator_values: 指标值序列
            current_value: 当前值
            parameters: 指标参数

        Returns:
            Tuple[SignalType, float]: 信号类型和数值
        """
        indicator_name = parameters.get('name', 'UNKNOWN')

        # 根据不同指标类型计算信号
        if indicator_name in ['RSI', 'STOCHASTIC', 'WILLIAMS_R', 'CCI', 'MFI']:
            return self._calculate_oscillator_signal(current_value, parameters)
        elif indicator_name in ['MACD', 'MACD_HIST']:
            return self._calculate_momentum_signal(current_value, indicator_values, parameters)
        elif indicator_name in ['SMA', 'EMA', 'DEMA', 'TEMA']:
            return self._calculate_trend_signal(current_value, indicator_values, parameters)
        elif 'BOLLINGER' in indicator_name or 'KELTNER' in indicator_name:
            return self._calculate_volatility_signal(current_value, parameters)
        else:
            # 默认使用Z-score方法
            return self._calculate_zscore_signal(current_value, indicator_values)

    def _calculate_oscillator_signal(self,
                                   current_value: float,
                                   parameters: Dict[str, Any]) -> Tuple[SignalType, float]:
        """
        计算摆荡器类指标信号
        """
        # 获取超买超卖阈值
        oversold = parameters.get('oversold', 30)
        overbought = parameters.get('overbought', 70)

        if current_value <= oversold:
            # 超卖，买入信号
            strength = min(10, (oversold - current_value) / oversold * 10)
            if strength > 7:
                return SignalType.STRONG_BUY, 2.0
            else:
                return SignalType.BUY, 1.0
        elif current_value >= overbought:
            # 超买，卖出信号
            strength = min(10, (current_value - overbought) / (100 - overbought) * 10)
            if strength > 7:
                return SignalType.STRONG_SELL, -2.0
            else:
                return SignalType.SELL, -1.0
        else:
            # 中性区域
            deviation = (current_value - 50) / 50
            if abs(deviation) < 0.1:
                return SignalType.HOLD, 0.0
            elif deviation > 0:
                return SignalType.WEAK_SELL, -0.5
            else:
                return SignalType.WEAK_BUY, 0.5

    def _calculate_momentum_signal(self,
                                 current_value: float,
                                 indicator_values: pd.Series,
                                 parameters: Dict[str, Any]) -> Tuple[SignalType, float]:
        """
        计算动量类指标信号
        """
        if len(indicator_values) < 2:
            return SignalType.HOLD, 0.0

        # 计算变化率
        prev_value = indicator_values.iloc[-2]
        change = current_value - prev_value
        change_pct = change / abs(prev_value) if prev_value != 0 else 0

        # 根据变化强度确定信号
        if abs(change_pct) < 0.01:
            return SignalType.HOLD, 0.0
        elif change_pct > 0.05:
            return SignalType.STRONG_BUY, 2.0
        elif change_pct > 0.02:
            return SignalType.BUY, 1.0
        elif change_pct > 0.01:
            return SignalType.WEAK_BUY, 0.5
        elif change_pct < -0.05:
            return SignalType.STRONG_SELL, -2.0
        elif change_pct < -0.02:
            return SignalType.SELL, -1.0
        else:
            return SignalType.WEAK_SELL, -0.5

    def _calculate_trend_signal(self,
                              current_value: float,
                              indicator_values: pd.Series,
                              parameters: Dict[str, Any]) -> Tuple[SignalType, float]:
        """
        计算趋势类指标信号
        """
        if len(indicator_values) < 5:
            return SignalType.HOLD, 0.0

        # 计算趋势方向
        recent_values = indicator_values.tail(5)
        trend_slope = np.polyfit(range(len(recent_values)), recent_values, 1)[0]

        # 计算当前值相对于移动平均的位置
        mean_value = recent_values.mean()
        deviation = (current_value - mean_value) / mean_value if mean_value != 0 else 0

        # 综合趋势和偏离度
        if abs(trend_slope) < 0.01 and abs(deviation) < 0.02:
            return SignalType.HOLD, 0.0
        elif trend_slope > 0.02 and deviation > 0.03:
            return SignalType.STRONG_BUY, 2.0
        elif trend_slope > 0.01 or deviation > 0.01:
            return SignalType.BUY, 1.0
        elif trend_slope < -0.02 and deviation < -0.03:
            return SignalType.STRONG_SELL, -2.0
        elif trend_slope < -0.01 or deviation < -0.01:
            return SignalType.SELL, -1.0
        else:
            return SignalType.HOLD, 0.0

    def _calculate_volatility_signal(self,
                                   current_value: float,
                                   parameters: Dict[str, Any]) -> Tuple[SignalType, float]:
        """
        计算波动率类指标信号
        """
        # 对于布林带等波动率指标，通常根据位置生成信号
        # 这里需要具体的指标逻辑，暂时返回中性信号
        return SignalType.HOLD, 0.0

    def _calculate_zscore_signal(self,
                               current_value: float,
                               indicator_values: pd.Series) -> Tuple[SignalType, float]:
        """
        基于Z-score计算信号
        """
        if len(indicator_values) < 20:
            return SignalType.HOLD, 0.0

        mean_val = indicator_values.mean()
        std_val = indicator_values.std()

        if std_val == 0:
            return SignalType.HOLD, 0.0

        z_score = (current_value - mean_val) / std_val

        # 根据Z-score确定信号
        if abs(z_score) < 1.0:
            return SignalType.HOLD, 0.0
        elif z_score > 2.0:
            return SignalType.STRONG_BUY, z_score
        elif z_score > 1.0:
            return SignalType.BUY, z_score
        elif z_score < -2.0:
            return SignalType.STRONG_SELL, z_score
        else:
            return SignalType.SELL, z_score

    def _calculate_signal_strength(self,
                                 indicator_values: pd.Series,
                                 current_value: float,
                                 signal_type: SignalType) -> float:
        """
        计算信号强度 (1-10)
        """
        if signal_type == SignalType.HOLD:
            return 1.0

        if self.strength_method == 'z_score':
            return self._calculate_zscore_strength(indicator_values, current_value)
        elif self.strength_method == 'percentile':
            return self._calculate_percentile_strength(indicator_values, current_value)
        elif self.strength_method == 'absolute':
            return self._calculate_absolute_strength(current_value, signal_type)
        else:
            return 5.0  # 默认中等强度

    def _calculate_zscore_strength(self,
                                 indicator_values: pd.Series,
                                 current_value: float) -> float:
        """基于Z-score计算信号强度"""
        if len(indicator_values) < 20:
            return 5.0

        mean_val = indicator_values.mean()
        std_val = indicator_values.std()

        if std_val == 0:
            return 1.0

        z_score = abs(current_value - mean_val) / std_val

        config = self.strength_config['z_score']

        if z_score >= config['strong_threshold']:
            return min(10.0, 8.0 + (z_score - config['strong_threshold']))
        elif z_score >= config['medium_threshold']:
            return 6.0 + (z_score - config['medium_threshold']) * 2
        elif z_score >= config['weak_threshold']:
            return 4.0 + (z_score - config['weak_threshold']) * 2
        else:
            return 2.0 + z_score * 2

    def _calculate_percentile_strength(self,
                                     indicator_values: pd.Series,
                                     current_value: float) -> float:
        """基于百分位数计算信号强度"""
        if len(indicator_values) < 10:
            return 5.0

        percentile = (indicator_values < current_value).mean()
        distance_from_center = abs(percentile - 0.5) * 2

        config = self.strength_config['percentile']

        if distance_from_center >= config['strong_threshold']:
            return 9.0
        elif distance_from_center >= config['medium_threshold']:
            return 7.0
        elif distance_from_center >= config['weak_threshold']:
            return 5.0
        else:
            return 3.0

    def _calculate_absolute_strength(self,
                                   current_value: float,
                                   signal_type: SignalType) -> float:
        """基于绝对值计算信号强度"""
        abs_value = abs(current_value)

        config = self.strength_config['absolute']

        if abs_value >= config['strong_threshold']:
            return 9.0
        elif abs_value >= config['medium_threshold']:
            return 7.0
        elif abs_value >= config['weak_threshold']:
            return 5.0
        else:
            return 3.0

    def _calculate_signal_confidence(self,
                                   indicator_values: pd.Series,
                                   current_value: float,
                                   parameters: Dict[str, Any],
                                   market_context: Optional[Dict] = None) -> float:
        """
        计算信号置信度 (0-1)

        考虑因素：
        1. 数据质量
        2. 指标稳定性
        3. 市场条件
        4. 参数优化程度
        """
        confidence_factors = []

        # 1. 数据长度置信度
        data_length_factor = min(1.0, len(indicator_values) / 100)
        confidence_factors.append(data_length_factor)

        # 2. 数据稳定性置信度
        if len(indicator_values) >= 20:
            recent_volatility = indicator_values.tail(20).std()
            overall_volatility = indicator_values.std()
            stability_factor = 1.0 - min(0.5, abs(recent_volatility - overall_volatility) / overall_volatility)
            confidence_factors.append(stability_factor)

        # 3. 信号一致性置信度
        if len(indicator_values) >= 10:
            recent_trend = np.polyfit(range(10), indicator_values.tail(10), 1)[0]
            consistency_factor = 1.0 - min(0.3, abs(recent_trend) / abs(current_value) if current_value != 0 else 0)
            confidence_factors.append(consistency_factor)

        # 4. 市场条件置信度
        if market_context:
            market_volatility = market_context.get('volatility', 0.2)
            market_confidence = max(0.3, 1.0 - market_volatility)
            confidence_factors.append(market_confidence)

        # 5. 参数优化置信度
        param_quality = parameters.get('optimization_score', 0.5)
        confidence_factors.append(param_quality)

        # 计算综合置信度
        if confidence_factors:
            overall_confidence = np.mean(confidence_factors)
        else:
            overall_confidence = 0.5

        return max(0.0, min(1.0, overall_confidence))

    def _update_historical_record(self, signal: Signal):
        """更新历史记录"""
        if signal.indicator_name not in self.signal_history:
            self.signal_history[signal.indicator_name] = []

        # 添加新信号
        self.signal_history[signal.indicator_name].append(signal)

        # 限制历史记录长度（保留最近1000个信号）
        if len(self.signal_history[signal.indicator_name]) > 1000:
            self.signal_history[signal.indicator_name] = self.signal_history[signal.indicator_name][-1000:]

        # 更新统计信息
        self._update_statistics(signal.indicator_name)

        # 定期保存到文件
        if len(self.signal_history[signal.indicator_name]) % 10 == 0:
            self._save_historical_data(signal.indicator_name)

    def _update_statistics(self, indicator_name: str):
        """更新信号统计信息"""
        signals = self.signal_history[indicator_name]

        if not signals:
            return

        # 计算统计数据
        total_signals = len(signals)
        buy_signals = sum(1 for s in signals if s.signal_type.value > 0)
        sell_signals = sum(1 for s in signals if s.signal_type.value < 0)
        hold_signals = total_signals - buy_signals - sell_signals

        avg_strength = np.mean([s.strength for s in signals])
        avg_confidence = np.mean([s.confidence for s in signals])

        # 计算信号频率（每日信号数）
        if len(signals) >= 2:
            time_span = (signals[-1].timestamp - signals[0].timestamp).days
            signal_frequency = total_signals / max(1, time_span)
        else:
            signal_frequency = 0

        self.signal_statistics[indicator_name] = SignalStatistics(
            total_signals=total_signals,
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            hold_signals=hold_signals,
            avg_strength=avg_strength,
            avg_confidence=avg_confidence,
            signal_frequency=signal_frequency,
            last_update=datetime.now()
        )

    def get_signal_statistics(self, indicator_name: str) -> Optional[SignalStatistics]:
        """获取指标信号统计信息"""
        return self.signal_statistics.get(indicator_name)

    def get_recent_signals(self,
                          indicator_name: str,
                          hours: int = 24) -> List[Signal]:
        """获取最近的信号"""
        if indicator_name not in self.signal_history:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [s for s in self.signal_history[indicator_name]
                if s.timestamp >= cutoff_time]

    def get_all_recent_signals(self, hours: int = 24) -> Dict[str, List[Signal]]:
        """获取所有指标的最近信号"""
        result = {}
        for indicator_name in self.signal_history:
            recent_signals = self.get_recent_signals(indicator_name, hours)
            if recent_signals:
                result[indicator_name] = recent_signals
        return result

    def _load_historical_data(self):
        """加载历史数据"""
        try:
            # 扫描缓存目录中的历史文件
            for file_path in self.cache_dir.glob("*.json"):
                indicator_name = file_path.stem
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 恢复信号历史
                    self.signal_history[indicator_name] = []
                    for signal_data in data.get('signals', []):
                        signal = Signal(
                            timestamp=datetime.fromisoformat(signal_data['timestamp']),
                            indicator_name=signal_data['indicator_name'],
                            signal_type=SignalType(signal_data['signal_type']),
                            signal_value=signal_data['signal_value'],
                            strength=signal_data['strength'],
                            confidence=signal_data['confidence'],
                            raw_indicator_value=signal_data['raw_indicator_value'],
                            parameters=signal_data['parameters'],
                            metadata=signal_data.get('metadata', {})
                        )
                        self.signal_history[indicator_name].append(signal)

                    # 恢复统计信息
                    stats_data = data.get('statistics', {})
                    if stats_data:
                        self.signal_statistics[indicator_name] = SignalStatistics(
                            total_signals=stats_data['total_signals'],
                            buy_signals=stats_data['buy_signals'],
                            sell_signals=stats_data['sell_signals'],
                            hold_signals=stats_data['hold_signals'],
                            avg_strength=stats_data['avg_strength'],
                            avg_confidence=stats_data['avg_confidence'],
                            signal_frequency=stats_data['signal_frequency'],
                            last_update=datetime.fromisoformat(stats_data['last_update'])
                        )

                    logger.debug(f"Loaded {len(self.signal_history[indicator_name])} historical signals for {indicator_name}")

                except Exception as e:
                    logger.warning(f"Failed to load historical data for {indicator_name}: {str(e)}")

        except Exception as e:
            logger.warning(f"Failed to scan historical data directory: {str(e)}")

    def _save_historical_data(self, indicator_name: str):
        """保存历史数据"""
        try:
            file_path = self.cache_dir / f"{indicator_name}.json"

            # 准备保存数据
            signals_data = [signal.to_dict() for signal in self.signal_history[indicator_name]]

            stats = self.signal_statistics.get(indicator_name)
            stats_data = stats.__dict__ if stats else {}

            data = {
                'signals': signals_data,
                'statistics': stats_data,
                'last_saved': datetime.now().isoformat()
            }

            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(signals_data)} signals for {indicator_name}")

        except Exception as e:
            logger.error(f"Failed to save historical data for {indicator_name}: {str(e)}")

    def export_signals(self,
                      indicator_name: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        导出信号数据

        Args:
            indicator_name: 指标名称（None表示所有指标）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 信号数据
        """
        all_signals = []

        indicators = [indicator_name] if indicator_name else self.signal_history.keys()

        for ind_name in indicators:
            if ind_name not in self.signal_history:
                continue

            for signal in self.signal_history[ind_name]:
                # 时间过滤
                if start_date and signal.timestamp < start_date:
                    continue
                if end_date and signal.timestamp > end_date:
                    continue

                # 转换为字典
                signal_dict = signal.to_dict()
                all_signals.append(signal_dict)

        if not all_signals:
            return pd.DataFrame()

        df = pd.DataFrame(all_signals)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df.sort_values('timestamp')

    def clear_history(self, indicator_name: Optional[str] = None):
        """清除历史数据"""
        if indicator_name:
            if indicator_name in self.signal_history:
                del self.signal_history[indicator_name]
            if indicator_name in self.signal_statistics:
                del self.signal_statistics[indicator_name]

            # 删除缓存文件
            file_path = self.cache_dir / f"{indicator_name}.json"
            if file_path.exists():
                file_path.unlink()
        else:
            # 清除所有历史数据
            self.signal_history.clear()
            self.signal_statistics.clear()

            # 删除所有缓存文件
            for file_path in self.cache_dir.glob("*.json"):
                file_path.unlink()

        logger.info(f"Cleared historical data for indicator: {indicator_name or 'all'}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {
            'total_indicators': len(self.signal_history),
            'total_signals': sum(len(signals) for signals in self.signal_history.values()),
            'signal_statistics': {},
            'configuration': {
                'signal_format': self.signal_format.value,
                'confidence_threshold': self.confidence_threshold,
                'strength_method': self.strength_method,
                'historical_tracking_enabled': self.enable_historical_tracking
            }
        }

        for indicator_name, stats in self.signal_statistics.items():
            summary['signal_statistics'][indicator_name] = {
                'total_signals': stats.total_signals,
                'buy_ratio': stats.buy_signals / stats.total_signals if stats.total_signals > 0 else 0,
                'sell_ratio': stats.sell_signals / stats.total_signals if stats.total_signals > 0 else 0,
                'avg_strength': stats.avg_strength,
                'avg_confidence': stats.avg_confidence,
                'signal_frequency': stats.signal_frequency
            }

        return summary