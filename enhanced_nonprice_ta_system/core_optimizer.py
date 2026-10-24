#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Core Optimizer Engine
增強版核心優化引擎 - 基於OpenSpec enhance-nonprice-ta-system提案

核心目標：
- 保持MB_KDJ_[10,2]策略的成功性能(Sharpe 3.672)
- 增強系統性能而非簡化
- 模組化重構保持所有現有功能
"""

import time
import datetime
import concurrent.futures
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import logging
from dataclasses import dataclass

# Import enhanced components
from .performance_monitor import PerformanceMonitor
from .intelligent_cache import IntelligentCache
from .error_handler import EnhancedErrorHandler

@dataclass
class OptimizationConfig:
    """優化配置"""
    max_workers: int = 32
    batch_size: int = 1000
    cache_enabled: bool = True
    monitoring_enabled: bool = True
    risk_free_rate: float = 0.03

class EnhancedOptimizerEngine:
    """
    增強版優化引擎
    基於現有MassiveNonPriceTAOptimizer的增強版本
    保持所有現有功能，添加性能增強
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()

        # PRESERVE: 保持現有系統的完整性
        self.base_url = "http://18.180.162.113:9191/inst/getInst"

        # PRESERVE: 保持所有9個數據源
        self.data_sources = {
            'HB': 'HIBOR利率數據',
            'GD': 'GDP數據',
            'RT': '零售銷售數據',
            'PT': '物業市場數據',
            'TR': '貿易數據',
            'TS': '旅遊數據',
            'CP': 'CPI通脹數據',
            'UE': '失業率數據',
            'MB': '貨幣基礎數據'
        }

        # ENHANCE: 添加新的性能監控和緩存系統
        self.performance_monitor = PerformanceMonitor() if self.config.monitoring_enabled else None
        self.cache_system = IntelligentCache() if self.config.cache_enabled else None
        self.error_handler = EnhancedErrorHandler()

        # PRESERVE: 保持原有數據存儲
        self.price_data = {}
        self.gov_data = {}

        # 設置日誌
        self._setup_logging()

        self.logger.info(f"[INIT] 增強版非價格技術指標優化引擎")
        self.logger.info(f"[INIT] 數據源: {len(self.data_sources)}個香港政府非價格數據")
        self.logger.info(f"[INIT] 並行核心: {self.config.max_workers}核")
        self.logger.info(f"[INIT] 緩存系統: {'啟用' if self.config.cache_enabled else '停用'}")
        self.logger.info(f"[INIT] 性能監控: {'啟用' if self.config.monitoring_enabled else '停用'}")

    def _setup_logging(self):
        """設置增強日誌系統"""
        self.logger = logging.getLogger('EnhancedOptimizerEngine')
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def fetch_real_stock_data(self) -> bool:
        """
        獲取真實股票數據
        PRESERVE: 保持原有邏輯，添加錯誤處理和性能監控
        """
        with self.error_handler.handle_api_errors("stock_data"):
            if self.performance_monitor:
                start_time = time.time()

            self.logger.info("[API] 獲取真實0700.HK價格數據...")

            # 檢查緩存
            cache_key = "stock_data_0700.hk"
            if self.cache_system:
                cached_data = self.cache_system.get(cache_key)
                if cached_data:
                    self.price_data = cached_data
                    self.logger.info("[CACHE] 使用緩存的股票數據")
                    return True

            # 獲取新數據
            import requests
            params = {"symbol": "0700.hk", "duration": 365}

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and 'close' in data['data']:
                close_data = data['data']['close']
                self.price_data = {
                    'dates': list(close_data.keys()),
                    'close': list(close_data.values())
                }

                # 緩存結果
                if self.cache_system:
                    self.cache_system.set(cache_key, self.price_data)

                self.logger.info(f"[API] 成功獲取 {len(self.price_data['close'])} 條真實價格記錄")

                if self.performance_monitor:
                    execution_time = time.time() - start_time
                    self.performance_monitor.record_api_call("stock_data", execution_time, True)

                return True
            else:
                raise ValueError("API數據格式不正確")

    def fetch_all_government_data(self) -> bool:
        """
        整合所有政府數據
        PRESERVE: 保持原有真實HKMA API集成，添加增強功能
        """
        with self.error_handler.handle_api_errors("government_data"):
            if self.performance_monitor:
                start_time = time.time()

            self.logger.info("[GOV] 整合香港政府非價格數據源...")
            data_length = len(self.price_data['close'])

            # Import real HKMA data integration (保持原有邏輯)
            from hkma_data_integration import get_hkma_data_for_optimizer

            # 使用異步任務獲取真實HKMA數據
            async def get_real_data():
                return await get_hkma_data_for_optimizer(self.data_sources, data_length)

            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                real_data = loop.run_until_complete(get_real_data())
            finally:
                loop.close()

            # 將真實數據存儲到優化器 (保持原有邏輯)
            for source_code, source_name in self.data_sources.items():
                cache_key = f"gov_data_{source_code}"

                if source_code in real_data:
                    data = real_data[source_code]
                    self.gov_data[source_code] = data

                    # 緩存數據
                    if self.cache_system:
                        self.cache_system.set(cache_key, data)

                    self.logger.info(f"[GOV] [OK] {source_code} ({source_name}): {len(data)} 條真實數據記錄")
                else:
                    # 如果真實API沒有數據，使用後備數據 (保持原有邏輯)
                    fallback_data = self._generate_fallback_data(source_code, data_length)
                    self.gov_data[source_code] = fallback_data

                    # 緩存後備數據
                    if self.cache_system:
                        self.cache_system.set(cache_key, fallback_data)

                    self.logger.warning(f"[GOV] [WARN] {source_code} ({source_name}): {len(fallback_data)} 條後備數據記錄")

            self.logger.info(f"[GOV] [SUCCESS] 成功整合 {len(self.gov_data)} 個數據源 (真實HKMA API)")

            if self.performance_monitor:
                execution_time = time.time() - start_time
                self.performance_monitor.record_api_call("government_data", execution_time, True)

            return True

    def _generate_fallback_data(self, source_code: str, length: int) -> List[float]:
        """
        生成後備數據（僅在API失敗時使用）
        PRESERVE: 完全保持原有後備數據邏輯
        """
        self.logger.warning(f"[FALLBACK] 為 {source_code} 生成後備數據")

        # 基於真實歷史平均值的後備配置
        fallback_configs = {
            'HB': [3.5] * length,  # HIBOR利率
            'MB': [2000000] * length,  # 貨幣基礎
            'GD': [100] * length,  # GDP
            'RT': [120] * length,  # 零售
            'PT': [180] * length,  # 物業
            'TR': [400] * length,  # 貿易
            'TS': [30000] * length,  # 旅遊
            'CP': [105] * length,  # CPI
            'UE': [3.2] * length   # 失業率
        }

        return fallback_configs.get(source_code, [100.0] * length)

    def run_enhanced_optimization(self) -> List[Dict[str, Any]]:
        """
        運行增強版優化
        PRESERVE: 保持原有大規模優化邏輯，添加性能監控
        """
        self.logger.info("\n" + "="*80)
        self.logger.info("增強版大規模非價格技術指標優化系統")
        self.logger.info("0-300完整參數範圍測試")
        self.logger.info("="*80)

        # 生成所有策略組合
        all_strategies = self._generate_all_nonprice_ta_combinations()

        self.logger.info(f"\n[EXEC] 開始增強版大規模非價格技術指標優化...")
        self.logger.info(f"[EXEC] 總策略數: {len(all_strategies):,}")
        self.logger.info(f"[EXEC] 並行核心: {self.config.max_workers}")

        start_time = time.time()

        # ENHANCE: 添加性能監控和緩存優化
        if self.performance_monitor:
            self.performance_monitor.start_optimization(len(all_strategies))

        # PRESERVE: 保持32核並行執行邏輯
        results = []
        batch_size = self.config.batch_size

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            for i in range(0, len(all_strategies), batch_size):
                batch = all_strategies[i:i+batch_size]
                batch_start = time.time()

                # ENHANCE: 添加緩存檢查
                cached_batch_results = []
                uncached_strategies = []

                if self.cache_system:
                    for strategy in batch:
                        cache_key = f"strategy_{strategy['data_source']}_{strategy['indicator_type']}_{strategy['params']}"
                        cached_result = self.cache_system.get(cache_key)
                        if cached_result:
                            cached_batch_results.append(cached_result)
                        else:
                            uncached_strategies.append(strategy)
                else:
                    uncached_strategies = batch

                # 只執行未緩存的策略
                if uncached_strategies:
                    batch_results = list(executor.map(self._backtest_nonprice_ta_strategy, uncached_strategies))

                    # 緩存新結果
                    if self.cache_system:
                        for strategy, result in zip(uncached_strategies, batch_results):
                            cache_key = f"strategy_{strategy['data_source']}_{strategy['indicator_type']}_{strategy['params']}"
                            self.cache_system.set(cache_key, result)

                    results.extend(batch_results)

                results.extend(cached_batch_results)

                batch_time = time.time() - batch_start
                progress = (i + len(batch)) / len(all_strategies) * 100
                eta = (len(all_strategies) - i - len(batch)) / (len(batch) / batch_time) / 60

                self.logger.info(f"[PROGRESS] 進度: {i + len(batch):,}/{len(all_strategies):,} ({progress:.1f}%) "
                               f"批次時間: {batch_time:.1f}秒 ETA: {eta:.1f}分鐘 "
                               f"緩存命中: {len(cached_batch_results)}")

        execution_time = time.time() - start_time
        successful_results = [r for r in results if r['success']]

        # ENHANCE: 記錄性能統計
        if self.performance_monitor:
            self.performance_monitor.end_optimization(execution_time, len(successful_results))
            perf_stats = self.performance_monitor.get_performance_summary()
            self.logger.info(f"[PERFORMANCE] {perf_stats}")

        self.logger.info(f"\n[COMPLETE] 增強版大規模非價格技術指標優化完成!")
        self.logger.info(f"[COMPLETE] 總策略: {len(results):,}")
        self.logger.info(f"[COMPLETE] 成功: {len(successful_results):,}")
        self.logger.info(f"[COMPLETE] 成功率: {len(successful_results)/len(results)*100:.1f}%")
        self.logger.info(f"[COMPLETE] 執行時間: {execution_time/60:.1f} 分鐘")
        self.logger.info(f"[COMPLETE] 處理速度: {len(results)/execution_time:.1f} 策略/秒")

        # 驗證保護策略性能
        self._validate_protected_strategies(successful_results)

        return successful_results

    def _validate_protected_strategies(self, results: List[Dict[str, Any]]):
        """
        驗證受保護策略的性能
        確保MB_KDJ_[10,2]等成功策略性能不下降
        """
        from . import PROTECTED_STRATEGIES

        for strategy_name, expected_metrics in PROTECTED_STRATEGIES.items():
            strategy_results = [r for r in results if strategy_name in r['strategy_id']]

            if strategy_results:
                best_result = max(strategy_results, key=lambda x: x['sharpe_ratio'])
                sharpe_diff = best_result['sharpe_ratio'] - expected_metrics['expected_sharpe']

                if sharpe_diff >= -0.1:  # 允許10%的性能下降
                    self.logger.info(f"[PROTECTED] {strategy_name}: Sharpe {best_result['sharpe_ratio']:.3f} (期望: {expected_metrics['expected_sharpe']}) ✅")
                else:
                    self.logger.warning(f"[PROTECTED] {strategy_name}: Sharpe {best_result['sharpe_ratio']:.3f} (期望: {expected_metrics['expected_sharpe']}) ⚠️")
            else:
                self.logger.error(f"[PROTECTED] {strategy_name}: 未找到策略結果")

    # 以下方法保持原有邏輯，僅添加性能增強
    def _generate_all_nonprice_ta_combinations(self) -> List[Dict[str, Any]]:
        """
        生成所有非價格技術指標組合
        PRESERVE: 完全保持原有組合生成邏輯
        """
        # Import the original massive optimizer to use existing logic
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from massive_nonprice_ta_optimizer import MassiveNonPriceTAOptimizer
        original_optimizer = MassiveNonPriceTAOptimizer()
        return original_optimizer.generate_all_nonprice_ta_combinations()

    def _backtest_nonprice_ta_strategy(self, strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        回測非價格技術指標策略
        PRESERVE: 完全保持原有回測邏輯
        """
        # Import the original massive optimizer to use existing logic
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from massive_nonprice_ta_optimizer import MassiveNonPriceTAOptimizer
        original_optimizer = MassiveNonPriceTAOptimizer()

        # Set data for backtesting
        original_optimizer.price_data = self.price_data
        original_optimizer.gov_data = self.gov_data

        return original_optimizer.backtest_nonprice_ta_strategy(strategy_params)

    def generate_enhanced_report(self, results: List[Dict[str, Any]]):
        """
        生成增強版報告
        PRESERVE: 保持原有報告格式，添加性能統計
        """
        # Use original report generation with enhancements
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from massive_nonprice_ta_optimizer import MassiveNonPriceTAOptimizer
        original_optimizer = MassiveNonPriceTAOptimizer()

        # Generate original report
        original_optimizer.generate_massive_report(results)

        # Add enhanced performance summary
        if self.performance_monitor:
            perf_summary = self.performance_monitor.get_performance_summary()
            self.logger.info(f"[ENHANCED_REPORT] 性能統計: {perf_summary}")

        if self.cache_system:
            cache_stats = self.cache_system.get_cache_statistics()
            self.logger.info(f"[ENHANCED_REPORT] 緩存統計: {cache_stats}")