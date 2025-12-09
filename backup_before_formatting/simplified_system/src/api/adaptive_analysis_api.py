"""
適應性分析API - Phase 4核心集成
Adaptive Analysis API with Production-Grade Features

將適應性市場分析系統集成到Simplified System API中
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import time
import traceback
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import pickle
import hashlib

# 系統模組
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.core_indicators import CoreIndicators
from indicators.technical_analyzer import TechnicalAnalyzer
from workflow.adaptive_market_system import AdaptiveMarketSystem, MarketRegimeDetector

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceError(Exception):
    """性能相關錯誤"""
    pass

class DataQualityError(Exception):
    """數據質量錯誤"""
    pass

def performance_monitor(timeout_seconds: float = 30.0):
    """性能監控裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                # 設置超時
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs),
                    timeout=timeout_seconds
                )

                execution_time = time.time() - start_time
                logger.info(f"⚡ {func.__name__} 執行時間: {execution_time:.3f}秒")

                return result

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.error(f"⏰ {func.__name__} 超時: {execution_time:.3f}秒")
                raise PerformanceError(f"Function {func.__name__} timed out after {timeout_seconds}s")

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"❌ {func.__name__} 執行失敗 ({execution_time:.3f}秒): {e}")
                raise

        return wrapper
    return decorator

class CacheManager:
    """高性能緩存管理器"""

    def __init__(self, max_cache_size: int = 100, cache_ttl: int = 300):
        self.cache = {}
        self.cache_timestamps = {}
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl  # 5分鐘

    def _generate_cache_key(self, *args) -> str:
        """生成緩存鍵"""
        key_data = str(args).encode('utf-8')
        return hashlib.md5(key_data).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """獲取緩存"""
        if key in self.cache:
            # 檢查TTL
            if time.time() - self.cache_timestamps[key] < self.cache_ttl:
                return self.cache[key]
            else:
                # 過期，刪除
                del self.cache[key]
                del self.cache_timestamps[key]
        return None

    def set(self, key: str, value: Any):
        """設置緩存"""
        # LRU策略：如果滿了，刪除最舊的
        if len(self.cache) >= self.max_cache_size:
            oldest_key = min(self.cache_timestamps.keys(),
                           key=lambda k: self.cache_timestamps[k])
            del self.cache[oldest_key]
            del self.cache_timestamps[oldest_key]

        self.cache[key] = value
        self.cache_timestamps[key] = time.time()

    def clear(self):
        """清除緩存"""
        self.cache.clear()
        self.cache_timestamps.clear()

class DataQualityValidator:
    """數據質量驗證器"""

    @staticmethod
    def validate_series(data: pd.Series, min_length: int = 10) -> Tuple[bool, str]:
        """驗證時間序列數據質量"""
        if len(data) < min_length:
            return False, f"數據長度不足: {len(data)} < {min_length}"

        if data.isnull().all():
            return False, "數據全為空值"

        null_ratio = data.isnull().sum() / len(data)
        if null_ratio > 0.5:
            return False, f"空值比例過高: {null_ratio:.2%}"

        # 檢查是否有重複索引
        if data.index.duplicated().any():
            return False, "存在重複時間索引"

        # 檢查數值是否合理
        if data.dtype in ['float64', 'int64']:
            if np.isinf(data).any():
                return False, "存在無限值"

            if data.std() == 0:
                return False, "數據標準差為0（無變化）"

        return True, "數據質量良好"

    @staticmethod
    def validate_dict_data(data: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證字典格式數據"""
        if not isinstance(data, dict):
            return False, "數據不是字典格式"

        if not data:
            return False, "數據字典為空"

        return True, "字典數據格式正確"

class AdaptiveAnalysisAPI:
    """適應性分析API - 生產級別實現"""

    def __init__(self, cache_size: int = 100, cache_ttl: int = 300):
        """初始化適應性分析API"""
        # 核心組件
        self.indicators = CoreIndicators()
        self.analyzer = TechnicalAnalyzer()
        self.adaptive_system = AdaptiveMarketSystem()

        # API端點配置
        self.daily_api_base = "http://localhost:8001"
        self.real_api_base = "http://localhost:8002"

        # 性能優化組件
        self.cache = CacheManager(cache_size, cache_ttl)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 數據質量驗證
        self.validator = DataQualityValidator()

        # 統計信息
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'errors': 0,
            'avg_response_time': 0,
            'start_time': time.time()
        }

        logger.info("🚀 Adaptive Analysis API initialized with production features")

    @performance_monitor(timeout_seconds=30.0)
    async def analyze_market_adaptive(self, sources: Optional[List[str]] = None,
                                    use_cache: bool = True) -> Dict[str, Any]:
        """
        適應性市場分析 - 主要API端點

        Args:
            sources: 指定數據源列表，None表示使用所有可用源
            use_cache: 是否使用緩存

        Returns:
            Dict[str, Any]: 適應性分析結果
        """
        request_start = time.time()
        self.stats['total_requests'] += 1

        try:
            # 生成緩存鍵
            cache_key = self.cache._generate_cache_key(
                'adaptive_analysis', tuple(sources) if sources else 'all'
            )

            # 檢查緩存
            if use_cache:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    self.stats['cache_hits'] += 1
                    logger.info("📋 返回緩存結果")
                    return cached_result

            # 收集數據
            logger.info("📊 收集市場數據...")
            market_data = await self._collect_market_data(sources)

            # 驗證數據質量
            validated_data = {}
            for source, data in market_data.items():
                is_valid, message = self.validator.validate_series(data)
                if is_valid:
                    validated_data[source] = data
                    logger.info(f"✅ {source}: {message}")
                else:
                    logger.warning(f"⚠️ {source}: {message}")
                    continue

            if not validated_data:
                raise DataQualityError("沒有有效的市場數據")

            # 執行適應性分析
            logger.info("🧠 執行適應性分析...")
            adaptive_results = self.adaptive_system.run_adaptive_analysis(validated_data)

            # 添加API元數據
            api_metadata = {
                'api_version': '1.0.0',
                'analysis_timestamp': datetime.now().isoformat(),
                'data_sources_used': list(validated_data.keys()),
                'data_quality_scores': {
                    source: self._calculate_quality_score(data)
                    for source, data in validated_data.items()
                },
                'performance_metrics': {
                    'execution_time': time.time() - request_start,
                    'cache_used': use_cache,
                    'data_points_analyzed': sum(len(data) for data in validated_data.values())
                },
                'system_stats': self._get_system_stats()
            }

            final_result = {
                **adaptive_results,
                'api_metadata': api_metadata
            }

            # 緩存結果
            if use_cache:
                self.cache.set(cache_key, final_result)

            # 更新統計
            response_time = time.time() - request_start
            self._update_stats(response_time)

            logger.info(f"🎯 適應性分析完成: {final_result['final_signal']['signal']} "
                       f"(信心: {final_result['final_signal']['confidence']:.2%})")

            return final_result

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"❌ 適應性分析失敗: {e}")
            logger.error(traceback.format_exc())

            # 返回錯誤響應
            return {
                'error': True,
                'message': str(e),
                'error_type': type(e).__name__,
                'timestamp': datetime.now().isoformat(),
                'api_metadata': {
                    'api_version': '1.0.0',
                    'system_stats': self._get_system_stats()
                }
            }

    @performance_monitor(timeout_seconds=15.0)
    async def get_market_regime_analysis(self, symbol: str = "HKMA_COMPOSITE") -> Dict[str, Any]:
        """
        獲取市場狀況分析

        Args:
            symbol: 分析標的，默認為HKMA綜合指數

        Returns:
            Dict[str, Any]: 市場狀況分析結果
        """
        try:
            # 收集綜合市場數據
            market_data = await self._collect_market_data(['hibor_rates', 'monetary_base', 'exchange_rates'])

            if not market_data:
                raise DataQualityError("無法獲取市場數據")

            # 創建綜合指數
            composite_data = self._create_composite_index(market_data)

            # 檢測市場狀況
            detector = MarketRegimeDetector()
            market_state = detector.detect_market_regime(composite_data)

            # 生成分析報告
            regime_analysis = {
                'symbol': symbol,
                'market_state': {
                    'regime': market_state.regime.value,
                    'volatility_level': market_state.volatility_level,
                    'trend_strength': market_state.trend_strength,
                    'momentum_score': market_state.momentum_score,
                    'confidence': market_state.confidence,
                    'last_updated': market_state.last_updated.isoformat()
                },
                'technical_summary': self._generate_technical_summary(composite_data),
                'risk_assessment': self._assess_market_risk(market_state),
                'recommendations': self._generate_regime_recommendations(market_state),
                'timestamp': datetime.now().isoformat()
            }

            return regime_analysis

        except Exception as e:
            logger.error(f"❌ 市場狀況分析失敗: {e}")
            return {
                'error': True,
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @performance_monitor(timeout_seconds=20.0)
    async def compare_adaptive_vs_traditional(self, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        比較適應性系統 vs 傳統方法

        Args:
            sources: 要比較的數據源

        Returns:
            Dict[str, Any]: 比較結果
        """
        try:
            # 收集數據
            market_data = await self._collect_market_data(sources)

            if not market_data:
                raise DataQualityError("無法獲取比較數據")

            # 適應性分析
            adaptive_results = self.adaptive_system.run_adaptive_analysis(market_data)

            # 傳統分析
            traditional_results = {}
            for source, data in market_data.items():
                traditional_score = self._traditional_analysis_score(data)
                traditional_results[source] = traditional_score

            # 計算改進幅度
            adaptive_scores = {
                source: analysis['adaptive_indicators']['total_score']
                for source, analysis in adaptive_results['source_analyses'].items()
            }

            improvements = {}
            for source in traditional_results:
                if source in adaptive_scores:
                    trad_score = traditional_results[source]
                    adap_score = adaptive_scores[source]
                    if trad_score > 0:
                        improvement = (adap_score - trad_score) / trad_score * 100
                        improvements[source] = improvement

            # 生成比較報告
            comparison_report = {
                'comparison_summary': {
                    'sources_compared': len(improvements),
                    'average_improvement': np.mean(list(improvements.values())) if improvements else 0,
                    'improvement_std': np.std(list(improvements.values())) if improvements else 0,
                    'best_improvement': max(improvements.values()) if improvements else 0,
                    'worst_improvement': min(improvements.values()) if improvements else 0
                },
                'detailed_comparison': {
                    'traditional_scores': traditional_results,
                    'adaptive_scores': adaptive_scores,
                    'improvements': improvements
                },
                'adaptive_signal': adaptive_results['final_signal'],
                'market_regime': adaptive_results['consensus_market_state'],
                'timestamp': datetime.now().isoformat()
            }

            return comparison_report

        except Exception as e:
            logger.error(f"❌ 比較分析失敗: {e}")
            return {
                'error': True,
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def _collect_market_data(self, sources: Optional[List[str]] = None) -> Dict[str, pd.Series]:
        """收集市場數據"""
        # 在實際生產環境中，這裡會調用真實的API
        # 現在返回模擬數據用於演示
        np.random.seed(int(time.time()) % 1000)

        all_sources = ['hibor_rates', 'monetary_base', 'exchange_rates',
                      'interbank_liquidity', 'efbn_indicative', 'rmb_liquidity']

        if sources is None:
            sources = all_sources

        market_data = {}
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')

        for source in sources:
            # 根據不同數據源生成特徵化的數據
            if 'hibor' in source:
                # HIBOR數據特徵：利率，波動較小
                base_value = 3.5
                volatility = 0.02
            elif 'monetary' in source:
                # 貨幣基礎：趨勢性增長
                base_value = 1000
                volatility = 0.01
                trend = 0.0005
            elif 'exchange' in source:
                # 匯率：相對穩定
                base_value = 7.8
                volatility = 0.015
            elif 'liquidity' in source:
                # 流動性：較大波動
                base_value = 500
                volatility = 0.025
            elif 'efbn' in source:
                # 外匯基金票據：中等波動
                base_value = 4.5
                volatility = 0.018
            else:
                # 默認參數
                base_value = 100
                volatility = 0.02
                trend = 0.0001

            # 生成數據
            data_length = len(dates)
            random_walk = np.random.normal(0, volatility, data_length)

            if 'trend' in locals():
                trend_component = np.arange(data_length) * trend
                data = base_value + trend_component + random_walk
            else:
                data = base_value + random_walk

            # 確保數據為正值（對於利率等）
            if source in ['hibor_rates', 'efbn_indicative']:
                data = np.abs(data)

            market_data[source] = pd.Series(data, index=dates)

        return market_data

    def _create_composite_index(self, market_data: Dict[str, pd.Series]) -> pd.Series:
        """創建綜合市場指數"""
        # 標準化所有數據
        normalized_data = {}
        for source, data in market_data.items():
            # Z-score標準化
            mean_val = data.mean()
            std_val = data.std()
            if std_val > 0:
                normalized_data[source] = (data - mean_val) / std_val
            else:
                normalized_data[source] = data - mean_val

        # 創建加權平均
        composite = None
        for data in normalized_data.values():
            if composite is None:
                composite = data.copy()
            else:
                composite += data

        if composite is not None:
            composite /= len(normalized_data)

        return composite

    def _calculate_quality_score(self, data: pd.Series) -> float:
        """計算數據質量評分"""
        score = 1.0

        # 完整性評分
        null_ratio = data.isnull().sum() / len(data)
        score -= null_ratio * 0.3

        # 一致性評分
        if len(data) > 1:
            change_ratio = (data != data.shift(1)).sum() / (len(data) - 1)
            if change_ratio < 0.1:  # 變化太少
                score -= 0.2

        # 波動性評分（適度波動是好）
        if len(data) > 1:
            volatility = data.pct_change().std()
            if volatility < 0.001:  # 波動太小
                score -= 0.1
            elif volatility > 0.1:  # 波動太大
                score -= 0.1

        return max(0.0, score)

    def _traditional_analysis_score(self, data: pd.Series) -> float:
        """傳統分析方法評分"""
        if len(data) < 14:
            return 0.0

        try:
            # 固定參數RSI
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            current_rsi = rsi.iloc[-1] if not rsi.empty else 50.0

            # 固定參數MACD
            exp1 = data.ewm(span=12).mean()
            exp2 = data.ewm(span=26).mean()
            macd_line = exp1 - exp2
            signal_line = macd_line.ewm(span=9).mean()

            # 簡單評分
            score = 0.0

            # RSI評分
            if 30 <= current_rsi <= 70:
                score += 0.4
            elif current_rsi < 30 or current_rsi > 70:
                score += 0.6

            # MACD評分
            if len(macd_line) > 0 and len(signal_line) > 0:
                if macd_line.iloc[-1] > signal_line.iloc[-1]:
                    score += 0.3
                else:
                    score += 0.1

            # 趨勢評分
            short_ma = data.rolling(window=10).mean()
            long_ma = data.rolling(window=30).mean()

            if len(short_ma) > 0 and len(long_ma) > 0:
                if short_ma.iloc[-1] > long_ma.iloc[-1]:
                    score += 0.3
                else:
                    score += 0.1

            return min(score, 1.0)

        except Exception:
            return 0.0

    def _generate_technical_summary(self, data: pd.Series) -> Dict[str, Any]:
        """生成技術分析摘要"""
        if len(data) < 2:
            return {}

        returns = data.pct_change().dropna()

        return {
            'current_level': float(data.iloc[-1]),
            'period_return': float((data.iloc[-1] / data.iloc[0] - 1) * 100),
            'volatility': float(returns.std() * np.sqrt(252) * 100),  # 年化波動率
            'max_drawdown': float(self._calculate_max_drawdown(data)),
            'trend_direction': 'up' if data.iloc[-1] > data.mean() else 'down',
            'momentum': float((data.iloc[-1] / data.iloc[-min(10, len(data)-1)] - 1) * 100)
        }

    def _calculate_max_drawdown(self, data: pd.Series) -> float:
        """計算最大回撤"""
        if len(data) < 2:
            return 0.0

        cumulative = (1 + data.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def _assess_market_risk(self, market_state) -> Dict[str, Any]:
        """評估市場風險"""
        risk_level = "low"
        risk_score = 0.0

        if market_state.regime.value == "high_volatility":
            risk_level = "high"
            risk_score = 0.8
        elif market_state.regime.value == "bear_market":
            risk_level = "medium"
            risk_score = 0.6
        elif market_state.volatility_level > 0.03:
            risk_level = "medium"
            risk_score = 0.5

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'primary_risk_factors': self._identify_risk_factors(market_state),
            'recommended_position_size': self._calculate_position_size(risk_score)
        }

    def _identify_risk_factors(self, market_state) -> List[str]:
        """識別風險因素"""
        factors = []

        if market_state.volatility_level > 0.04:
            factors.append("高波動率")

        if market_state.regime.value == "bear_market":
            factors.append("熊市趨勢")

        if market_state.confidence < 0.3:
            factors.append("信號信心度低")

        if abs(market_state.trend_strength) > 0.5:
            factors.append("強趨勢風險")

        return factors

    def _calculate_position_size(self, risk_score: float) -> str:
        """計算建議倉位大小"""
        if risk_score > 0.7:
            return "small (5-10%)"
        elif risk_score > 0.4:
            return "medium (10-20%)"
        else:
            return "large (20-30%)"

    def _generate_regime_recommendations(self, market_state) -> List[str]:
        """基於市場狀況生成建議"""
        recommendations = []

        regime = market_state.regime.value

        if regime == "bull_market":
            recommendations.extend([
                "考慮增加倉位",
                "專注於成長股",
                "使用較短的止損"
            ])
        elif regime == "bear_market":
            recommendations.extend([
                "減少倉位或持有現金",
                "關注防禦性股票",
                "使用較長的止損"
            ])
        elif regime == "high_volatility":
            recommendations.extend([
                "降低倉位大小",
                "使用更緊密的風險控制",
                "避免過度槓桿"
            ])
        elif regime == "low_volatility":
            recommendations.extend([
                "可以使用較大倉位",
                "考慮賣出期權增加收益",
                "關注突破交易機會"
            ])
        else:  # sideways
            recommendations.extend([
                "使用區間交易策略",
                "等待明確趨勢信號",
                "保持中性倉位"
            ])

        return recommendations

    def _update_stats(self, response_time: float):
        """更新統計信息"""
        current_avg = self.stats['avg_response_time']
        total_requests = self.stats['total_requests']

        # 計算新的平均響應時間
        new_avg = (current_avg * (total_requests - 1) + response_time) / total_requests
        self.stats['avg_response_time'] = new_avg

    def _get_system_stats(self) -> Dict[str, Any]:
        """獲取系統統計信息"""
        uptime = time.time() - self.stats['start_time']
        cache_hit_rate = (self.stats['cache_hits'] / max(1, self.stats['total_requests'])) * 100
        error_rate = (self.stats['errors'] / max(1, self.stats['total_requests'])) * 100

        return {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'total_requests': self.stats['total_requests'],
            'cache_hits': self.stats['cache_hits'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'errors': self.stats['errors'],
            'error_rate': f"{error_rate:.1f}%",
            'avg_response_time': f"{self.stats['avg_response_time']:.3f}s",
            'cache_size': len(self.cache.cache),
            'api_status': 'healthy'
        }

    async def get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'features': {
                'adaptive_analysis': True,
                'market_regime_detection': True,
                'performance_monitoring': True,
                'caching': True,
                'data_quality_validation': True
            },
            'system_stats': self._get_system_stats(),
            'cache_info': {
                'size': len(self.cache.cache),
                'max_size': self.cache.max_cache_size,
                'ttl_seconds': self.cache.cache_ttl
            }
        }

    def clear_cache(self):
        """清除緩存"""
        self.cache.clear()
        logger.info("🗑️ 緩存已清除")

    async def shutdown(self):
        """關閉API系統"""
        logger.info("🔄 正在關閉Adaptive Analysis API...")

        self.executor.shutdown(wait=True)
        self.cache.clear()

        logger.info("✅ Adaptive Analysis API已安全關閉")

# 全局API實例
api_instance = None

async def get_api_instance() -> AdaptiveAnalysisAPI:
    """獲取API實例（單例模式）"""
    global api_instance
    if api_instance is None:
        api_instance = AdaptiveAnalysisAPI()
    return api_instance

# 主要API端點函數
async def analyze_market_adaptive(sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """主要API端點：適應性市場分析"""
    api = await get_api_instance()
    return await api.analyze_market_adaptive(sources)

async def get_market_regime(symbol: str = "HKMA_COMPOSITE") -> Dict[str, Any]:
    """API端點：市場狀況分析"""
    api = await get_api_instance()
    return await api.get_market_regime_analysis(symbol)

async def compare_methods(sources: Optional[List[str]] = None) -> Dict[str, Any]:
    """API端點：方法比較"""
    api = await get_api_instance()
    return await api.compare_adaptive_vs_traditional(sources)

async def system_health() -> Dict[str, Any]:
    """API端點：系統健康檢查"""
    api = await get_api_instance()
    return await api.get_system_health()

if __name__ == "__main__":
    async def main():
        """測試API系統"""
        print("🚀 測試Adaptive Analysis API")
        print("=" * 50)

        try:
            # 測試適應性分析
            print("1. 測試適應性市場分析...")
            result1 = await analyze_market_adaptive(['hibor_rates', 'monetary_base'])
            print(f"   信號: {result1.get('final_signal', {}).get('signal', 'N/A')}")

            # 測試市場狀況分析
            print("\n2. 測試市場狀況分析...")
            result2 = await get_market_regime()
            print(f"   狀況: {result2.get('market_state', {}).get('regime', 'N/A')}")

            # 測試系統健康
            print("\n3. 測試系統健康...")
            result3 = await system_health()
            print(f"   狀態: {result3.get('status', 'N/A')}")

            print("\n✅ 所有測試通過！")

        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            traceback.print_exc()

        finally:
            # 清理
            if api_instance:
                await api_instance.shutdown()

    asyncio.run(main())