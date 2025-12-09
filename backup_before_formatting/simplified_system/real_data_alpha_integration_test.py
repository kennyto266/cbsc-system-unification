#!/usr/bin/env python3
"""
真實數據Alpha集成測試系統
Real Data Alpha Integration Test System

驗證真實香港政府數據與獨立Alpha源系統的集成效果
Validate integration of real Hong Kong government data with independent Alpha system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import numpy as np
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import time
import requests
from pathlib import Path

# Import simplified system modules
from src.api.government_data import GovernmentDataAPI, get_hibor_data, get_latest_hibor
from src.api.stock_api import get_hk_stock_data, get_multiple_stocks
from unified_data_architecture_standard import UnifiedDataArchitectureStandard, DataSourceType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealDataAlphaIntegration:
    """真實數據Alpha集成測試系統"""

    def __init__(self):
        self.government_api = GovernmentDataAPI()
        self.data_standardizer = UnifiedDataArchitectureStandard()
        self.test_results = {}
        self.performance_metrics = {}

    def test_government_data_integration(self) -> Dict[str, Any]:
        """測試政府數據集成"""
        logger.info("=== 測試政府數據集成 ===")

        results = {
            'test_name': 'government_data_integration',
            'start_time': datetime.now().isoformat(),
            'data_sources': {},
            'data_quality': {},
            'errors': []
        }

        try:
            # 測試HIBOR數據
            logger.info("測試HIBOR利率數據...")
            hibor_data = self.government_api.get_hibor_data(30)

            if hibor_data:
                results['data_sources']['hibor'] = {
                    'status': 'success',
                    'records': hibor_data['count'],
                    'source': hibor_data['source'],
                    'latest_rate': hibor_data['data'][0]['overnight'] if hibor_data['data'] else None
                }

                # 數據質量檢查
                if hibor_data['data']:
                    latest = hibor_data['data'][0]
                    quality_score = self._assess_hibor_data_quality(latest)
                    results['data_quality']['hibor'] = quality_score
            else:
                results['data_sources']['hibor'] = {
                    'status': 'failed',
                    'error': 'No HIBOR data retrieved'
                }
                results['errors'].append('HIBOR data retrieval failed')

            # 測試匯率數據
            logger.info("測試匯率數據...")
            exchange_data = self.government_api.get_exchange_rates(30)

            if exchange_data:
                results['data_sources']['exchange_rates'] = {
                    'status': 'success',
                    'records': exchange_data['count'],
                    'source': exchange_data['source']
                }
            else:
                results['data_sources']['exchange_rates'] = {
                    'status': 'failed',
                    'error': 'No exchange rate data retrieved'
                }
                results['errors'].append('Exchange rate data retrieval failed')

            # 測試貨幣基礎數據
            logger.info("測試貨幣基礎數據...")
            monetary_data = self.government_api.get_monetary_base(12)

            if monetary_data:
                results['data_sources']['monetary_base'] = {
                    'status': 'success',
                    'records': monetary_data['count'],
                    'source': monetary_data['source']
                }
            else:
                results['data_sources']['monetary_base'] = {
                    'status': 'failed',
                    'error': 'No monetary base data retrieved'
                }
                results['errors'].append('Monetary base data retrieval failed')

            # 成功統計
            success_count = sum(1 for source in results['data_sources'].values()
                              if source['status'] == 'success')
            total_sources = len(results['data_sources'])

            results['integration_score'] = success_count / total_sources if total_sources > 0 else 0
            results['success_rate'] = f"{success_count}/{total_sources}"

            logger.info(f"政府數據集成測試完成: {results['success_rate']} 成功")

        except Exception as e:
            logger.error(f"政府數據集成測試失敗: {e}")
            results['errors'].append(str(e))

        results['end_time'] = datetime.now().isoformat()
        results['duration_seconds'] = (
            datetime.fromisoformat(results['end_time']) -
            datetime.fromisoformat(results['start_time'])
        ).total_seconds()

        return results

    def test_data_standardization(self) -> Dict[str, Any]:
        """測試數據標準化"""
        logger.info("=== 測試數據標準化 ===")

        results = {
            'test_name': 'data_standardization',
            'start_time': datetime.now().isoformat(),
            'standardization_results': {},
            'errors': []
        }

        try:
            # 獲取真實政府數據
            hibor_data = self.government_api.get_hibor_data(10)

            if hibor_data and hibor_data['data']:
                # 標準化HIBOR數據
                standardized_hibor = self.data_standardizer.standardize_data(
                    hibor_data['data'],
                    DataSourceType.GOVERNMENT_DATA
                )

                if standardized_hibor is not None:
                    results['standardization_results']['hibor'] = {
                        'status': 'success',
                        'original_records': len(hibor_data['data']),
                        'standardized_records': len(standardized_hibor),
                        'columns': list(standardized_hibor.columns),
                        'data_types': standardized_hibor.dtypes.to_dict()
                    }
                    logger.info(f"HIBOR數據標準化成功: {len(standardized_hibor)} 條記錄")
                else:
                    results['standardization_results']['hibor'] = {
                        'status': 'failed',
                        'error': 'Standardization returned None'
                    }
                    results['errors'].append('HIBOR standardization failed')
            else:
                results['errors'].append('No HIBOR data available for standardization')

            # 獲取股票數據並標準化
            try:
                stock_data = get_hk_stock_data('0700.HK', 30)

                if stock_data is not None and len(stock_data) > 0:
                    # 標準化股票數據
                    standardized_stock = self.data_standardizer.standardize_data(
                        stock_data.to_dict('records'),
                        DataSourceType.STOCK_API
                    )

                    if standardized_stock is not None:
                        results['standardization_results']['stock'] = {
                            'status': 'success',
                            'original_records': len(stock_data),
                            'standardized_records': len(standardized_stock),
                            'columns': list(standardized_stock.columns)
                        }
                        logger.info(f"股票數據標準化成功: {len(standardized_stock)} 條記錄")
                    else:
                        results['standardization_results']['stock'] = {
                            'status': 'failed',
                            'error': 'Stock standardization returned None'
                        }
                        results['errors'].append('Stock data standardization failed')
                else:
                    results['errors'].append('No stock data available for standardization')

            except Exception as e:
                logger.error(f"股票數據獲取失敗: {e}")
                results['errors'].append(f'Stock data retrieval failed: {str(e)}')

            # 計算標準化成功率
            success_count = sum(1 for result in results['standardization_results'].values()
                              if result['status'] == 'success')
            total_count = len(results['standardization_results'])

            results['standardization_success_rate'] = success_count / total_count if total_count > 0 else 0

        except Exception as e:
            logger.error(f"數據標準化測試失敗: {e}")
            results['errors'].append(str(e))

        results['end_time'] = datetime.now().isoformat()
        return results

    def test_alpha_signal_generation(self) -> Dict[str, Any]:
        """測試Alpha信號生成（使用真實數據）"""
        logger.info("=== 測試Alpha信號生成 ===")

        results = {
            'test_name': 'alpha_signal_generation',
            'start_time': datetime.now().isoformat(),
            'signal_results': {},
            'performance_metrics': {},
            'errors': []
        }

        try:
            # 獲取真實市場數據
            logger.info("獲取股票市場數據...")
            stock_data = get_hk_stock_data('0700.HK', 60)

            if stock_data is None or len(stock_data) == 0:
                results['errors'].append('Failed to retrieve stock data')
                return results

            # 獲取政府經濟數據
            logger.info("獲取政府經濟數據...")
            hibor_data = self.government_api.get_hibor_data(60)
            monetary_data = self.government_api.get_monetary_base(6)

            # 生成基於真實數據的Alpha信號
            alpha_signals = self._generate_real_data_alpha_signals(
                stock_data, hibor_data, monetary_data
            )

            if alpha_signals:
                results['signal_results'] = {
                    'status': 'success',
                    'total_signals': len(alpha_signals),
                    'signal_types': list(alpha_signals.keys()) if isinstance(alpha_signals, dict) else ['composite'],
                    'latest_signal': alpha_signals[-1] if isinstance(alpha_signals, list) else 'N/A'
                }

                # 計算信號質量指標
                signal_quality = self._evaluate_signal_quality(alpha_signals, stock_data)
                results['performance_metrics'] = signal_quality

                logger.info(f"Alpha信號生成成功: {results['signal_results']['total_signals']} 個信號")
            else:
                results['signal_results'] = {
                    'status': 'failed',
                    'error': 'No alpha signals generated'
                }
                results['errors'].append('Alpha signal generation failed')

        except Exception as e:
            logger.error(f"Alpha信號生成測試失敗: {e}")
            results['errors'].append(str(e))

        results['end_time'] = datetime.now().isoformat()
        return results

    def _generate_real_data_alpha_signals(self, stock_data: pd.DataFrame,
                                        hibor_data: Optional[Dict],
                                        monetary_data: Optional[Dict]) -> List[Dict]:
        """使用真實數據生成Alpha信號"""
        signals = []

        try:
            if len(stock_data) < 20:
                return []

            # 技術分析信號 (基於真實股價數據)
            close_prices = stock_data['close']

            # RSI信號
            rsi = self._calculate_rsi(close_prices, 14)
            if rsi is not None:
                signals.append({
                    'type': 'RSI',
                    'value': rsi,
                    'signal': 'OVERSOLD' if rsi < 30 else 'OVERBOUGHT' if rsi > 70 else 'NEUTRAL',
                    'weight': 0.3,
                    'data_source': 'stock_price'
                })

            # 動量信號
            momentum_20 = (close_prices.iloc[-1] / close_prices.iloc[-20] - 1) * 100
            signals.append({
                'type': 'MOMENTUM',
                'value': momentum_20,
                'signal': 'BULLISH' if momentum_20 > 5 else 'BEARISH' if momentum_20 < -5 else 'NEUTRAL',
                'weight': 0.2,
                'data_source': 'stock_price'
            })

            # 政府數據信號 (基於真實HIBOR數據)
            if hibor_data and hibor_data.get('data'):
                latest_hibor = hibor_data['data'][0]
                hibor_overnight = latest_hibor.get('overnight', 0)

                # HIBOR變化信號
                if len(hibor_data['data']) > 1:
                    prev_hibor = hibor_data['data'][1].get('overnight', hibor_overnight)
                    hibor_change = hibor_overnight - prev_hibor

                    signals.append({
                        'type': 'HIBOR_CHANGE',
                        'value': hibor_change,
                        'signal': 'RATE_CUTTING' if hibor_change < -0.1 else 'RATE_HIKING' if hibor_change > 0.1 else 'STABLE',
                        'weight': 0.25,
                        'data_source': 'hibor'
                    })

                # 絕對利率水平信號
                signals.append({
                    'type': 'HIBOR_LEVEL',
                    'value': hibor_overnight,
                    'signal': 'LOOSE' if hibor_overnight < 3.0 else 'TIGHT' if hibor_overnight > 5.0 else 'NEUTRAL',
                    'weight': 0.15,
                    'data_source': 'hibor'
                })

            # 貨幣基礎信號
            if monetary_data and monetary_data.get('data'):
                latest_monetary = monetary_data['data'][0]
                monetary_base = latest_monetary.get('monetary_base_billion_hkd', 0)

                if monetary_base > 0:
                    signals.append({
                        'type': 'MONETARY_BASE',
                        'value': monetary_base,
                        'signal': 'EXPANSIONARY' if monetary_base > 2000 else 'CONTRACTIONARY' if monetary_base < 1500 else 'NEUTRAL',
                        'weight': 0.1,
                        'data_source': 'monetary_base'
                    })

        except Exception as e:
            logger.error(f"Alpha信號生成錯誤: {e}")

        return signals

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """計算RSI指標"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.iloc[-1] if not rsi.empty else None
        except Exception as e:
            logger.error(f"RSI計算錯誤: {e}")
            return None

    def _assess_hibor_data_quality(self, hibor_record: Dict) -> Dict[str, Any]:
        """評估HIBOR數據質量"""
        quality_score = 100
        issues = []

        # 檢查數據完整性
        required_fields = ['overnight', '1_week', '1_month', '3_months']
        missing_fields = [field for field in required_fields if hibor_record.get(field) is None]

        if missing_fields:
            quality_score -= len(missing_fields) * 10
            issues.append(f"Missing fields: {missing_fields}")

        # 檢查數值合理性
        if hibor_record.get('overnight', 0) < 0 or hibor_record.get('overnight', 0) > 20:
            quality_score -= 20
            issues.append("Overnight rate out of reasonable range")

        # 檢查期限結構合理性
        overnight = hibor_record.get('overnight', 0)
        three_month = hibor_record.get('3_months', 0)

        if three_month and overnight and (three_month < overnight * 0.8 or three_month > overnight * 3):
            quality_score -= 15
            issues.append("Term structure anomaly detected")

        return {
            'score': max(0, quality_score),
            'issues': issues,
            'data_completeness': len(required_fields) - len(missing_fields),
            'total_fields': len(required_fields)
        }

    def _evaluate_signal_quality(self, signals: List[Dict], stock_data: pd.DataFrame) -> Dict[str, Any]:
        """評估信號質量"""
        quality_metrics = {
            'signal_diversity': 0,
            'data_source_diversity': 0,
            'weight_distribution': 0,
            'total_weight': 0
        }

        try:
            if not signals:
                return quality_metrics

            # 信號類型多樣性
            signal_types = set(signal['type'] for signal in signals)
            quality_metrics['signal_diversity'] = len(signal_types)

            # 數據源多樣性
            data_sources = set(signal['data_source'] for signal in signals)
            quality_metrics['data_source_diversity'] = len(data_sources)

            # 權重分布
            weights = [signal['weight'] for signal in signals]
            quality_metrics['total_weight'] = sum(weights)
            quality_metrics['weight_distribution'] = max(weights) - min(weights) if weights else 0

            # 信號時效性（基於最新數據）
            latest_timestamp = stock_data.index[-1] if not stock_data.empty else datetime.now()
            quality_metrics['signal_freshness'] = (
                datetime.now() - latest_timestamp).total_seconds() / 3600  # hours

        except Exception as e:
            logger.error(f"信號質量評估錯誤: {e}")

        return quality_metrics

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """運行綜合測試"""
        logger.info("開始運行真實數據Alpha集成綜合測試...")

        comprehensive_results = {
            'test_session': {
                'session_id': f"real_data_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'start_time': datetime.now().isoformat(),
                'environment': 'simplified_system'
            },
            'test_results': {},
            'overall_score': 0,
            'recommendations': []
        }

        try:
            # 1. 政府數據集成測試
            gov_data_result = self.test_government_data_integration()
            comprehensive_results['test_results']['government_data'] = gov_data_result

            # 2. 數據標準化測試
            std_result = self.test_data_standardization()
            comprehensive_results['test_results']['data_standardization'] = std_result

            # 3. Alpha信號生成測試
            alpha_result = self.test_alpha_signal_generation()
            comprehensive_results['test_results']['alpha_signals'] = alpha_result

            # 計算綜合評分
            scores = []
            if 'integration_score' in gov_data_result:
                scores.append(gov_data_result['integration_score'] * 0.4)  # 40% weight

            if 'standardization_success_rate' in std_result:
                scores.append(std_result['standardization_success_rate'] * 0.3)  # 30% weight

            if alpha_result['signal_results'].get('status') == 'success':
                scores.append(0.3)  # 30% weight for successful alpha generation

            comprehensive_results['overall_score'] = sum(scores) if scores else 0

            # 生成建議
            recommendations = self._generate_recommendations(comprehensive_results)
            comprehensive_results['recommendations'] = recommendations

            # 保存測試結果
            self._save_test_results(comprehensive_results)

        except Exception as e:
            logger.error(f"綜合測試執行錯誤: {e}")
            comprehensive_results['error'] = str(e)

        comprehensive_results['test_session']['end_time'] = datetime.now().isoformat()

        return comprehensive_results

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """基於測試結果生成建議"""
        recommendations = []

        try:
            # 政府數據建議
            gov_result = results.get('test_results', {}).get('government_data', {})
            if gov_result.get('integration_score', 0) < 1.0:
                failed_sources = [name for name, data in gov_result.get('data_sources', {}).items()
                                if data.get('status') == 'failed']
                recommendations.append(f"修復失敗的數據源: {', '.join(failed_sources)}")

            # 數據標準化建議
            std_result = results.get('test_results', {}).get('data_standardization', {})
            if std_result.get('standardization_success_rate', 0) < 1.0:
                recommendations.append("改進數據標準化流程，處理更多數據格式")

            # Alpha信號建議
            alpha_result = results.get('test_results', {}).get('alpha_signals', {})
            if alpha_result.get('signal_results', {}).get('status') != 'success':
                recommendations.append("增強Alpha信號生成算法，提高可靠性")

            # 整體建議
            overall_score = results.get('overall_score', 0)
            if overall_score > 0.8:
                recommendations.append("[SUCCESS] 系統集成優秀，可以投入生產使用")
            elif overall_score > 0.6:
                recommendations.append("[WARNING] 系統基本可用，建議改進薄弱環節")
            else:
                recommendations.append("[ERROR] 系統需要重大改進才能滿足生產要求")

        except Exception as e:
            logger.error(f"建議生成錯誤: {e}")
            recommendations.append("無法生成建議，請檢查測試結果格式")

        return recommendations

    def _save_test_results(self, results: Dict):
        """保存測試結果"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"real_data_integration_test_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"測試結果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存測試結果失敗: {e}")

def main():
    """主函數"""
    print("啟動真實數據Alpha集成測試系統...")
    print("=" * 60)

    # 創建測試系統
    integration_tester = RealDataAlphaIntegration()

    # 運行綜合測試
    results = integration_tester.run_comprehensive_test()

    # 顯示測試結果摘要
    print("\n" + "=" * 60)
    print("測試結果摘要")
    print("=" * 60)

    session_info = results['test_session']
    print(f"測試會話ID: {session_info['session_id']}")
    print(f"開始時間: {session_info['start_time']}")
    print(f"結束時間: {session_info['end_time']}")
    print(f"綜合評分: {results['overall_score']:.2%}")

    # 顯示各項測試結果
    test_results = results.get('test_results', {})

    print("\n政府數據集成:")
    gov_result = test_results.get('government_data', {})
    if 'integration_score' in gov_result:
        print(f"  集成評分: {gov_result['integration_score']:.2%}")
        print(f"  成功率: {gov_result.get('success_rate', 'N/A')}")
        for source, info in gov_result.get('data_sources', {}).items():
            status_icon = "[OK]" if info['status'] == 'success' else "[FAIL]"
            print(f"  {status_icon} {source}: {info['status']}")

    print("\n數據標準化:")
    std_result = test_results.get('data_standardization', {})
    if 'standardization_success_rate' in std_result:
        print(f"  標準化成功率: {std_result['standardization_success_rate']:.2%}")
        for source, info in std_result.get('standardization_results', {}).items():
            status_icon = "[OK]" if info['status'] == 'success' else "[FAIL]"
            print(f"  {status_icon} {source}: {info['status']}")

    print("\nAlpha信號生成:")
    alpha_result = test_results.get('alpha_signals', {})
    signal_info = alpha_result.get('signal_results', {})
    if signal_info.get('status') == 'success':
        print(f"  [OK] 信號生成: 成功")
        print(f"  總信號數: {signal_info.get('total_signals', 0)}")
        print(f"  信號類型: {', '.join(signal_info.get('signal_types', []))}")
    else:
        print(f"  [FAIL] 信號生成: 失敗")
        if alpha_result.get('errors'):
            print(f"  錯誤: {', '.join(alpha_result['errors'])}")

    # 顯示建議
    print("\n優化建議:")
    recommendations = results.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    print("\n" + "=" * 60)
    print("測試完成！")

    return results

if __name__ == "__main__":
    test_results = main()