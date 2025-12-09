#!/usr/bin/env python3
"""
風險管理系統
基於MB_KDJ_[10,2]策略的風險控制參數
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class RiskManager:
    """風險管理器 - 實現基於proven策略的風險控制"""

    def __init__(self):
        # 基於MB_KDJ_[10,2]策略的風險參數
        self.config = {
            'position_sizing': {
                'base_position_percent': 0.10,  # 基礎倉位：10%
                'max_position_percent': 0.30,   # 最大倉位：30%
                'volatility_adjustment': True    # 啟用波動率調整
            },
            'drawdown_protection': {
                'individual_stop_loss': 0.10,   # 個股止損：10%
                'portfolio_max_drawdown': 0.0916,  # 投資組合最大回撤：9.16% (proven)
                'trailing_stop_enabled': True,  # 啟用移動止損
                'daily_loss_limit': 0.05        # 日損失限制：5%
            },
            'portfolio_constraints': {
                'max_correlation': 0.7,          # 最大相關性
                'min_diversification': 5,        # 最少股票數量
                'sector_concentration_limit': 0.4  # 行業集中度限制
            }
        }

        self.portfolio_state = {
            'total_value': 1000000,  # 初始資金100萬
            'available_cash': 1000000,
            'positions': {},
            'daily_pnl': 0,
            'current_drawdown': 0,
            'max_drawdown': 0,
            'last_update': datetime.now().isoformat()
        }

        self.risk_events = []

    def calculate_position_size(self, signal_strength: float, volatility: float = 0.3) -> float:
        """計算基於風險的倉位大小

        Args:
            signal_strength: 信號強度 (0-1)
            volatility: 股票波動率

        Returns:
            float: 建議倉位百分比 (0-0.30)
        """
        base_position = self.config['position_sizing']['base_position_percent']
        max_position = self.config['position_sizing']['max_position_percent']

        # 信號強度調整
        position = base_position * signal_strength

        # 波動率調整（波動率越高，倉位越小）
        if self.config['position_sizing']['volatility_adjustment']:
            volatility_factor = min(1.0, 0.25 / volatility)  # 目標波動率25%
            position *= volatility_factor

        # 應用最大倉位限制
        position = min(position, max_position)

        return max(0, position)  # 確保不為負數

    def check_stop_loss(self, current_price: float, entry_price: float, position_type: str = 'long') -> bool:
        """檢查是否觸發止損

        Args:
            current_price: 當前價格
            entry_price: 進場價格
            position_type: 倉位類型 ('long' or 'short')

        Returns:
            bool: 是否觸發止損
        """
        stop_loss_pct = self.config['drawdown_protection']['individual_stop_loss']

        if position_type == 'long':
            loss_pct = (entry_price - current_price) / entry_price
        else:  # short position
            loss_pct = (current_price - entry_price) / entry_price

        return loss_pct >= stop_loss_pct

    def check_portfolio_drawdown(self) -> Dict[str, Any]:
        """檢查投資組合回撤

        Returns:
            Dict: 回撤檢查結果
        """
        max_dd_limit = self.config['drawdown_protection']['portfolio_max_drawdown']
        current_dd = self.portfolio_state['current_drawdown']

        # 計算回撤狀態
        drawdown_ratio = current_dd / max_dd_limit if max_dd_limit > 0 else 0

        result = {
            'current_drawdown': current_dd,
            'max_allowed': max_dd_limit,
            'drawdown_ratio': drawdown_ratio,
            'risk_level': self._get_risk_level(drawdown_ratio),
            'action_required': drawdown_ratio >= 0.9  # 90%達極限時需要行動
        }

        return result

    def _get_risk_level(self, ratio: float) -> str:
        """根據比率獲取風險等級"""
        if ratio < 0.5:
            return "LOW"
        elif ratio < 0.75:
            return "MEDIUM"
        elif ratio < 0.9:
            return "HIGH"
        else:
            return "CRITICAL"

    def check_daily_loss_limit(self) -> Dict[str, Any]:
        """檢查日損失限制

        Returns:
            Dict: 日損失檢查結果
        """
        daily_loss = abs(self.portfolio_state['daily_pnl'])
        daily_limit = self.config['drawdown_protection']['daily_loss_limit']
        portfolio_value = self.portfolio_state['total_value']
        daily_loss_pct = daily_loss / portfolio_value

        result = {
            'daily_pnl': self.portfolio_state['daily_pnl'],
            'daily_loss_pct': daily_loss_pct,
            'daily_limit_pct': daily_limit,
            'limit_ratio': daily_loss_pct / daily_limit,
            'trading_suspended': daily_loss_pct >= daily_limit,
            'warning_issued': daily_loss_pct >= (daily_limit * 0.8)
        }

        return result

    def update_portfolio_value(self, market_data: Dict[str, float]):
        """更新投資組合價值

        Args:
            market_data: 市場數據 {symbol: current_price}
        """
        total_position_value = 0
        daily_pnl = 0

        # 更新各個持倉的價值
        for symbol, position in self.portfolio_state['positions'].items():
            if symbol in market_data:
                current_price = market_data[symbol]
                position_value = position['quantity'] * current_price
                position['current_value'] = position_value
                position['current_price'] = current_price
                position['pnl'] = position_value - position['cost_basis']

                total_position_value += position_value
                daily_pnl += position['pnl']

        # 更新投資組合狀態
        self.portfolio_state['total_value'] = self.portfolio_state['available_cash'] + total_position_value
        self.portfolio_state['daily_pnl'] = daily_pnl

        # 計算當前回撤
        if hasattr(self, 'peak_value'):
            self.portfolio_state['current_drawdown'] = (self.peak_value - self.portfolio_state['total_value']) / self.peak_value
            self.portfolio_state['max_drawdown'] = max(self.portfolio_state['max_drawdown'], self.portfolio_state['current_drawdown'])
        else:
            self.peak_value = self.portfolio_state['total_value']
            self.portfolio_state['current_drawdown'] = 0
            self.portfolio_state['max_drawdown'] = 0

        # 更新峰值
        if self.portfolio_state['total_value'] > self.peak_value:
            self.peak_value = self.portfolio_state['total_value']

        self.portfolio_state['last_update'] = datetime.now().isoformat()

    def get_risk_metrics(self) -> Dict[str, Any]:
        """獲取風險指標"""

        # 計算投資組合風險指標
        portfolio_risk = self.check_portfolio_drawdown()
        daily_risk = self.check_daily_loss_limit()

        # 計算倉位集中度
        position_concentration = self._calculate_position_concentration()

        risk_metrics = {
            'portfolio_drawdown': portfolio_risk,
            'daily_loss_check': daily_risk,
            'position_concentration': position_concentration,
            'overall_risk_score': self._calculate_overall_risk_score(portfolio_risk, daily_risk),
            'risk_recommendations': self._generate_risk_recommendations(portfolio_risk, daily_risk),
            'last_updated': datetime.now().isoformat()
        }

        return risk_metrics

    def _calculate_position_concentration(self) -> Dict[str, Any]:
        """計算倉位集中度"""
        positions = self.portfolio_state['positions']
        if not positions:
            return {'message': '無持倉'}

        total_value = sum(pos['current_value'] for pos in positions.values() if 'current_value' in pos)
        if total_value == 0:
            return {'message': '持倉價值為零'}

        concentrations = []
        for symbol, position in positions.items():
            if 'current_value' in position:
                concentration = position['current_value'] / total_value
                concentrations.append({
                    'symbol': symbol,
                    'concentration_pct': round(concentration * 100, 2),
                    'value': position['current_value']
                })

        concentrations.sort(key=lambda x: x['concentration_pct'], reverse=True)

        return {
            'max_concentration': concentrations[0] if concentrations else None,
            'top_3_concentration': concentrations[:3],
            'total_positions': len(concentrations)
        }

    def _calculate_overall_risk_score(self, portfolio_risk: Dict, daily_risk: Dict) -> float:
        """計算整體風險分數 (0-100)"""
        # 投資組合回撤風險權重 60%
        drawdown_score = portfolio_risk['drawdown_ratio'] * 60

        # 日損失風險權重 40%
        daily_score = daily_risk['limit_ratio'] * 40

        return min(100, drawdown_score + daily_score)

    def _generate_risk_recommendations(self, portfolio_risk: Dict, daily_risk: Dict) -> List[str]:
        """生成風險建議"""
        recommendations = []

        # 投資組合回撤建議
        if portfolio_risk['drawdown_ratio'] > 0.8:
            recommendations.append("⚠️ CRITICAL: 投資組合回撤接近極限，考慮減倉")
        elif portfolio_risk['drawdown_ratio'] > 0.6:
            recommendations.append("⚠️ WARNING: 投資組合回撤較高，謹慎操作")
        elif portfolio_risk['drawdown_ratio'] > 0.4:
            recommendations.append("ℹ️ INFO: 投資組合回撤正常，持續監控")

        # 日損失建議
        if daily_risk['trading_suspended']:
            recommendations.append("🛑 STOP: 已達日損失限制，暫停交易")
        elif daily_risk['warning_issued']:
            recommendations.append("⚠️ WARNING: 接近日損失限制，控制風險")

        # 整體風險建議
        overall_score = self._calculate_overall_risk_score(portfolio_risk, daily_risk)
        if overall_score > 80:
            recommendations.append("🔥 HIGH RISK: 系統風險過高，建議大幅減倉")
        elif overall_score > 60:
            recommendations.append("📊 MEDIUM RISK: 系統風險中等，謹慎操作")

        if not recommendations:
            recommendations.append("✅ LOW RISK: 風險可控，正常交易")

        return recommendations

    def log_risk_event(self, event_type: str, description: str, severity: str = "INFO"):
        """記錄風險事件"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'description': description,
            'severity': severity
        }

        self.risk_events.append(event)

        # 保持最近1000個事件
        if len(self.risk_events) > 1000:
            self.risk_events = self.risk_events[-1000:]

        logger.warning(f"風險事件: {severity} - {event_type}: {description}")

# 測�试程序
async def main():
    """測試風險管理系統"""
    print("🛡️ 啟動風險管理系統測試")
    print("📊 基於MB_KDJ_[10,2]策略風險參數")

    # 創建風險管理器
    risk_manager = RiskManager()

    # 測試倉位計算
    print("\n📏 測試倉位計算...")
    position_size = risk_manager.calculate_position_size(0.8, 0.25)
    print(f"信號強度80%，波動率25% -> 建議倉位: {position_size*100:.2f}%")

    # 測試止損檢查
    print("\n🛑 測試止損檢查...")
    should_stop = risk_manager.check_stop_loss(90, 100, 'long')
    print(f"進場價100，當前價90，是否觸發止損: {should_stop}")

    # 更新投資組合價值
    print("\n💼 更新投資組合價值...")
    market_data = {'0700.HK': 450, '0941.HK': 25}
    risk_manager.update_portfolio_value(market_data)

    # 獲取風險指標
    print("\n📊 獲取風險指標...")
    risk_metrics = risk_manager.get_risk_metrics()
    print(f"風險指標: {json.dumps(risk_metrics, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    asyncio.run(main())