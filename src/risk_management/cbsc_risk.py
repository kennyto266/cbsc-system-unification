"""
CBSC (Callable Bull/Bear Contract) Risk Management
牛熊證風險管理模組

This module provides specialized risk management calculations for CBSC products,
including call risk assessment, leverage controls, and time decay modeling.

Author: CBSC Backtesting System Team
Date: 2025-12-04
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal

from ..models.cbsc_models import (
    CBSCContract, WarrantSentiment, CBSCPortfolioPosition,
    CBSCType, SentimentLevel, SignalType
)
from ..models.base import RiskMetrics, RiskLevel
from .risk_calculator import RiskCalculator

logger = logging.getLogger(__name__)

class CBSCRiskManager:
    """CBSC風險管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 風險參數
        self.max_leverage_ratio = config.get('max_leverage_ratio', 0.1)  # 最大槓桿10%
        self.call_price_buffer = config.get('call_price_buffer', 0.05)  # 收回價緩衝5%
        self.max_single_position = config.get('max_single_position', 0.05)  # 單一倉位最大5%
        self.min_distance_to_call = config.get('min_distance_to_call', 0.02)  # 距離收回價最小2%
        self.time_decay_threshold = config.get('time_decay_threshold', 0.1)  # 時間衰減閾值10%

        # 波動率參數
        self.volatility_window = config.get('volatility_window', 20)  # 波動率計算窗口
        self.extreme_volatility_threshold = config.get('extreme_volatility_threshold', 0.03)  # 極端波動率閾值

    def calculate_call_risk(self, contract: CBSCContract, current_price: float) -> Dict[str, Any]:
        """計算收回風險"""
        if current_price <= 0:
            return {
                'distance_to_call': float('inf'),
                'call_probability': 1.0,
                'risk_level': RiskLevel.CRITICAL,
                'recommendation': 'AVOID'
            }

        distance_to_call = contract.calculate_distance_to_call(current_price)

        # 收回風險評估
        if distance_to_call <= 0:
            call_probability = 1.0  # 已經被收回
            risk_level = RiskLevel.CRITICAL
            recommendation = 'LIQUIDATE'
        elif distance_to_call <= self.call_price_buffer:
            # 接近收回價，使用指數風險模型
            call_probability = np.exp(-distance_to_call / self.call_price_buffer)
            risk_level = RiskLevel.HIGH
            recommendation = 'REDUCE'
        elif distance_to_call <= self.min_distance_to_call:
            # 低緩衝區，線性風險模型
            call_probability = 1 - (distance_to_call - self.min_distance_to_call) / (self.call_price_buffer - self.min_distance_to_call)
            risk_level = RiskLevel.MEDIUM
            recommendation = 'MONITOR'
        else:
            # 安全距離，低風險
            call_probability = max(0, 1 - distance_to_call)
            risk_level = RiskLevel.LOW
            recommendation = 'HOLD'

        return {
            'distance_to_call': distance_to_call,
            'call_probability': float(call_probability),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'call_price': contract.call_price,
            'current_price': current_price,
            'buffer_used': distance_to_call <= self.call_price_buffer
        }

    def calculate_time_decay_risk(self, contract: CBSCContract, current_date: date) -> Dict[str, Any]:
        """計算時間衰減風險"""
        time_decay_factor = contract.calculate_time_decay_factor(current_date)
        days_to_maturity = (contract.maturity_date - current_date).days

        if days_to_maturity < 0:
            # 已經到期
            risk_level = RiskLevel.CRITICAL
            decay_rate = 1.0
            recommendation = 'LIQUIDATE'
        elif days_to_maturity <= 30:
            # 30天內到期
            risk_level = RiskLevel.HIGH
            decay_rate = 1 - time_decay_factor
            recommendation = 'REDUCE'
        elif days_to_maturity <= 90:
            # 90天內到期
            risk_level = RiskLevel.MEDIUM
            decay_rate = (1 - time_decay_factor) * 0.5  # 減半衰減影響
            recommendation = 'MONITOR'
        else:
            # 充足時間
            risk_level = RiskLevel.LOW
            decay_rate = max(0, 1 - time_decay_factor) * 0.1  # 低衰減影響
            recommendation = 'HOLD'

        return {
            'time_decay_factor': time_decay_factor,
            'days_to_maturity': days_to_maturity,
            'decay_rate': decay_rate,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'maturity_date': contract.maturity_date,
            'current_date': current_date
        }

    def calculate_leverage_risk(self, position: CBSCPortfolioPosition) -> Dict[str, Any]:
        """計算槓桿風險"""
        if not position.current_price:
            return {
                'current_leverage': 0.0,
                'leverage_utilization': 0.0,
                'risk_level': RiskLevel.LOW,
                'recommendation': 'MONITOR'
            }

        current_value = position.quantity * position.current_price
        entry_value = position.quantity * position.entry_price

        if entry_value <= 0:
            return {
                'current_leverage': 0.0,
                'leverage_utilization': 0.0,
                'risk_level': RiskLevel.CRITICAL,
                'recommendation': 'LIQUIDATE'
            }

        # 計算當前槓桿倍數（基於合約規格）
        current_leverage = position.contract.leverage_ratio

        # 計算槓桿利用率（基於損益）
        if position.unrealized_pnl:
            leverage_utilization = abs(position.unrealized_pnl) / entry_value
        else:
            leverage_utilization = 0.0

        # 風險評估
        if current_leverage > 10 or leverage_utilization > 0.5:
            risk_level = RiskLevel.CRITICAL
            recommendation = 'LIQUIDATE'
        elif current_leverage > 7 or leverage_utilization > 0.3:
            risk_level = RiskLevel.HIGH
            recommendation = 'REDUCE'
        elif current_leverage > 5 or leverage_utilization > 0.2:
            risk_level = RiskLevel.MEDIUM
            recommendation = 'MONITOR'
        else:
            risk_level = RiskLevel.LOW
            recommendation = 'HOLD'

        return {
            'current_leverage': current_leverage,
            'leverage_utilization': float(leverage_utilization),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'contract_leverage': position.contract.leverage_ratio,
            'entry_value': float(entry_value),
            'current_value': float(current_value)
        }

    def calculate_sentiment_risk(self, sentiment_data: List[WarrantSentiment]) -> Dict[str, Any]:
        """計算情緒風險"""
        if not sentiment_data:
            return {
                'sentiment_risk_score': 0.5,
                'volatility_risk': 0.0,
                'consistency_risk': 0.0,
                'overall_risk_level': RiskLevel.MEDIUM,
                'recommendation': 'MONITOR'
            }

        # 按日期排序
        sorted_data = sorted(sentiment_data, key=lambda x: x.date)
        recent_data = sorted_data[-10:]  # 最近10條記錄

        # 計算情緒波動率
        sentiment_strengths = [record.sentiment_strength for record in recent_data]
        sentiment_volatility = np.std(sentiment_strengths) if len(sentiment_strengths) > 1 else 0.0

        # 計算情緒一致性
        extreme_count = sum(1 for record in recent_data if record.get_extreme_signal())
        consistency_score = 1 - (extreme_count / len(recent_data))

        # 計算情緒風險評分
        volatility_risk = min(1.0, sentiment_volatility * 10)  # 波動率風險
        consistency_risk = 1 - consistency_score  # 一致性風險

        # 綜合風險評分
        sentiment_risk_score = (volatility_risk + consistency_risk) / 2

        # 風險等級評估
        if sentiment_risk_score > 0.7:
            overall_risk_level = RiskLevel.CRITICAL
            recommendation = 'REDUCE'
        elif sentiment_risk_score > 0.5:
            overall_risk_level = RiskLevel.HIGH
            recommendation = 'MONITOR'
        elif sentiment_risk_score > 0.3:
            overall_risk_level = RiskLevel.MEDIUM
            recommendation = 'CAUTION'
        else:
            overall_risk_level = RiskLevel.LOW
            recommendation = 'PROCEED'

        return {
            'sentiment_risk_score': sentiment_risk_score,
            'volatility_risk': volatility_risk,
            'consistency_risk': consistency_risk,
            'overall_risk_level': overall_risk_level,
            'recommendation': recommendation,
            'data_points': len(recent_data),
            'extreme_signal_ratio': extreme_count / len(recent_data)
        }

    def calculate_comprehensive_risk(self, position: CBSCPortfolioPosition,
                                   current_date: date,
                                   sentiment_data: Optional[List[WarrantSentiment]] = None) -> Dict[str, Any]:
        """計算綜合風險評估"""
        if not position.current_price:
            return {
                'overall_risk_score': 1.0,
                'risk_level': RiskLevel.CRITICAL,
                'recommendation': 'LIQUIDATE',
                'risk_components': {}
            }

        # 單項風險計算
        call_risk = self.calculate_call_risk(position.contract, position.current_price)
        time_risk = self.calculate_time_decay_risk(position.contract, current_date)
        leverage_risk = self.calculate_leverage_risk(position)

        risk_components = {
            'call_risk': call_risk,
            'time_risk': time_risk,
            'leverage_risk': leverage_risk
        }

        # 如果有情緒數據，加入情緒風險
        if sentiment_data:
            sentiment_risk = self.calculate_sentiment_risk(sentiment_data)
            risk_components['sentiment_risk'] = sentiment_risk

        # 綜合風險評分
        risk_scores = []
        risk_weights = []

        # 收回風險權重最高
        call_risk_score = self._risk_level_to_score(call_risk['risk_level'])
        risk_scores.append(call_risk_score)
        risk_weights.append(0.4)

        # 時間衰減風險
        time_risk_score = self._risk_level_to_score(time_risk['risk_level'])
        risk_scores.append(time_risk_score)
        risk_weights.append(0.3)

        # 槓桿風險
        leverage_risk_score = self._risk_level_to_score(leverage_risk['risk_level'])
        risk_scores.append(leverage_risk_score)
        risk_weights.append(0.3)

        # 情緒風險（如果有數據）
        if sentiment_data:
            sentiment_risk_score = self._risk_level_to_score(sentiment_risk['overall_risk_level'])
            risk_scores.append(sentiment_risk_score)
            risk_weights.append(0.2)  # 增加權重總和到1.2，然後重新標準化

        # 計算加權平均風險評分
        total_weight = sum(risk_weights)
        overall_risk_score = sum(score * weight for score, weight in zip(risk_scores, risk_weights)) / total_weight

        # 確定最終風險等級
        if overall_risk_score >= 0.8:
            overall_risk_level = RiskLevel.CRITICAL
            recommendation = 'LIQUIDATE'
        elif overall_risk_score >= 0.6:
            overall_risk_level = RiskLevel.HIGH
            recommendation = 'REDUCE'
        elif overall_risk_score >= 0.4:
            overall_risk_level = RiskLevel.MEDIUM
            recommendation = 'MONITOR'
        else:
            overall_risk_level = RiskLevel.LOW
            recommendation = 'HOLD'

        return {
            'overall_risk_score': overall_risk_score,
            'risk_level': overall_risk_level,
            'recommendation': recommendation,
            'risk_components': risk_components,
            'position_summary': {
                'ticker': position.contract.ticker,
                'current_price': position.current_price,
                'quantity': position.quantity,
                'unrealized_pnl': position.unrealized_pnl
            }
        }

    def _risk_level_to_score(self, risk_level: RiskLevel) -> float:
        """將風險等級轉換為評分"""
        mapping = {
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 1.0
        }
        return mapping.get(risk_level, 0.5)

    def validate_position_size(self, contract: CBSCContract,
                              proposed_quantity: int,
                              portfolio_value: float) -> Dict[str, Any]:
        """驗證持倉規模"""
        if portfolio_value <= 0:
            return {
                'valid': False,
                'max_allowed_quantity': 0,
                'reason': 'Invalid portfolio value'
            }

        # 計算倉位價值
        position_value = proposed_quantity * contract.call_price  # 使用收回價作為保守估計
        position_ratio = position_value / portfolio_value

        # 檢查倉位限制
        if position_ratio > self.max_single_position:
            max_quantity = int(portfolio_value * self.max_single_position / contract.call_price)
            return {
                'valid': False,
                'max_allowed_quantity': max_quantity,
                'reason': f'Position size {position_ratio:.1%} exceeds maximum {self.max_single_position:.1%}',
                'position_ratio': position_ratio,
                'max_ratio': self.max_single_position
            }

        # 檢查槓桿限制
        if contract.leverage_ratio > 15:  # 非常高槓桿的產品
            if position_ratio > self.max_leverage_ratio:
                max_quantity = int(portfolio_value * self.max_leverage_ratio / contract.call_price)
                return {
                    'valid': False,
                    'max_allowed_quantity': max_quantity,
                    'reason': f'High leverage product requires smaller position: max {self.max_leverage_ratio:.1%}',
                    'position_ratio': position_ratio,
                    'max_ratio': self.max_leverage_ratio,
                    'leverage_ratio': contract.leverage_ratio
                }

        return {
            'valid': True,
            'max_allowed_quantity': proposed_quantity,
            'reason': 'Position size acceptable',
            'position_ratio': position_ratio
        }

    def generate_risk_report(self, positions: List[CBSCPortfolioPosition],
                            current_date: date,
                            sentiment_data: Optional[List[WarrantSentiment]] = None) -> Dict[str, Any]:
        """生成風險報告"""
        if not positions:
            return {
                'total_positions': 0,
                'overall_portfolio_risk': RiskLevel.LOW,
                'high_risk_positions': [],
                'recommendations': ['No positions to analyze']
            }

        position_risks = []
        high_risk_positions = []
        critical_positions = []

        total_portfolio_value = sum(
            pos.quantity * (pos.current_price or pos.entry_price)
            for pos in positions
        )

        for position in positions:
            risk_analysis = self.calculate_comprehensive_risk(
                position, current_date, sentiment_data
            )

            position_risks.append({
                'ticker': position.contract.ticker,
                'risk_score': risk_analysis['overall_risk_score'],
                'risk_level': risk_analysis['risk_level'],
                'recommendation': risk_analysis['recommendation']
            })

            if risk_analysis['risk_level'] == RiskLevel.HIGH:
                high_risk_positions.append(position.contract.ticker)
            elif risk_analysis['risk_level'] == RiskLevel.CRITICAL:
                critical_positions.append(position.contract.ticker)

        # 計算組合整體風險
        avg_risk_score = np.mean([risk['risk_score'] for risk in position_risks])

        if avg_risk_score >= 0.7:
            portfolio_risk = RiskLevel.CRITICAL
        elif avg_risk_score >= 0.5:
            portfolio_risk = RiskLevel.HIGH
        elif avg_risk_score >= 0.3:
            portfolio_risk = RiskLevel.MEDIUM
        else:
            portfolio_risk = RiskLevel.LOW

        # 生成建議
        recommendations = []
        if critical_positions:
            recommendations.append(f"URGENT: Liquidate critical positions: {', '.join(critical_positions)}")
        if high_risk_positions:
            recommendations.append(f"HIGH PRIORITY: Reduce exposure to high risk positions: {', '.join(high_risk_positions)}")
        if len(positions) > 10:
            recommendations.append("Consider reducing position count for better risk management")
        if avg_risk_score > 0.6:
            recommendations.append("Portfolio risk is elevated - consider reducing overall exposure")

        return {
            'report_date': current_date,
            'total_positions': len(positions),
            'total_portfolio_value': total_portfolio_value,
            'overall_portfolio_risk': portfolio_risk,
            'average_risk_score': avg_risk_score,
            'position_risks': position_risks,
            'high_risk_positions': high_risk_positions,
            'critical_positions': critical_positions,
            'recommendations': recommendations,
            'risk_distribution': {
                'low': sum(1 for r in position_risks if r['risk_level'] == RiskLevel.LOW),
                'medium': sum(1 for r in position_risks if r['risk_level'] == RiskLevel.MEDIUM),
                'high': sum(1 for r in position_risks if r['risk_level'] == RiskLevel.HIGH),
                'critical': sum(1 for r in position_risks if r['risk_level'] == RiskLevel.CRITICAL)
            }
        }

# 工廠函數
def create_cbsc_risk_manager(**config) -> CBSCRiskManager:
    """創建CBSC風險管理器"""
    default_config = {
        'max_leverage_ratio': 0.1,
        'call_price_buffer': 0.05,
        'max_single_position': 0.05,
        'min_distance_to_call': 0.02,
        'time_decay_threshold': 0.1,
        'volatility_window': 20,
        'extreme_volatility_threshold': 0.03
    }

    default_config.update(config)
    return CBSCRiskManager(default_config)

if __name__ == "__main__":
    # 測試代碼
    print("=== CBSC Risk Manager 測試 ===")

    from datetime import date
    from models.cbsc_models import create_sample_cbsc_contract, CBSCPortfolioPosition

    # 創建風險管理器
    risk_manager = create_cbsc_risk_manager()
    print(f"CBSC風險管理器創建成功")

    # 創建測試倉位
    contract = create_sample_cbsc_contract()
    position = CBSCPortfolioPosition(
        contract=contract,
        quantity=10000,
        entry_price=2.5,
        entry_date=datetime.now(),
        current_price=2.6
    )

    # 測試風險計算
    current_date = date.today()
    comprehensive_risk = risk_manager.calculate_comprehensive_risk(position, current_date)
    print(f"綜合風險評分: {comprehensive_risk['overall_risk_score']:.3f}")
    print(f"風險等級: {comprehensive_risk['risk_level']}")
    print(f"建議: {comprehensive_risk['recommendation']}")

    # 測試倉位規模驗證
    validation = risk_manager.validate_position_size(contract, 50000, 1000000)
    print(f"倉位驗證: {validation['valid']}")
    if not validation['valid']:
        print(f"  最大允許數量: {validation['max_allowed_quantity']}")
        print(f"  原因: {validation['reason']}")

    # 測試風險報告
    risk_report = risk_manager.generate_risk_report([position], current_date)
    print(f"風險報告生成完成")
    print(f"  總體風險: {risk_report['overall_portfolio_risk']}")
    print(f"  建議數量: {len(risk_report['recommendations'])}")

    print("CBSC Risk Manager 測試完成！")