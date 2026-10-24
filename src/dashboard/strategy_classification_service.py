#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略分類服務
為CBSC策略Dashboard提供策略分類和篩選功能
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import json
from datetime import datetime
import pandas as pd

class StrategyCategory(Enum):
    """策略類別枚舉"""
    MONTHLY_LOW_FREQUENCY = "monthly_low_frequency"
    MULTI_STRATEGY_VALIDATION = "multi_strategy_validation"
    MULTI_FACTOR_MODEL = "multi_factor_model"
    CORE_CBSC_TECHNICAL = "core_cbsc_technical"
    CORE_CBSC_SENTIMENT = "core_cbsc_sentiment"
    CORE_CBSC_AGGRESSIVE = "core_cbsc_aggressive"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"

class StrategyGrade(Enum):
    """策略評級枚舉"""
    EXCELLENT = "A+"  # 90-100分
    GOOD = "A"        # 80-89分
    VERY_GOOD = "B+"   # 70-79分
    GOOD_B = "B"       # 60-69分
    AVERAGE_C = "C+"   # 50-59分
    AVERAGE = "C"      # 40-49分
    POOR_D = "D+"      # 30-39分
    POOR = "D"         # 20-29分
    VERY_POOR = "F"    # 0-19分

@dataclass
class StrategyInfo:
    """策略信息數據類"""
    name: str
    category: StrategyCategory
    subcategory: str
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    grade: StrategyGrade
    description: str
    status: str = "active"
    last_updated: datetime = None
    risk_level: str = "medium"
    trading_frequency: str = "medium"
    confidence_score: float = 0.0

class StrategyClassificationService:
    def __init__(self):
        self.strategies: Dict[str, StrategyInfo] = {}
        self.category_metadata = self._initialize_category_metadata()
        self._load_all_strategies()

    def _initialize_category_metadata(self) -> Dict[StrategyCategory, Dict[str, Any]]:
        """初始化類別元數據"""
        return {
            StrategyCategory.MONTHLY_LOW_FREQUENCY: {
                "display_name": "月度低頻策略",
                "description": "專門設計的月度或更低頻率交易策略",
                "color": "#4CAF50",
                "icon": "calendar_month",
                "count": 6
            },
            StrategyCategory.MULTI_STRATEGY_VALIDATION: {
                "display_name": "多策略驗證系統",
                "description": "使用認證框架測試的多種策略組合",
                "color": "#2196F3",
                "icon": "verified",
                "count": 6
            },
            StrategyCategory.MULTI_FACTOR_MODEL: {
                "display_name": "多因子模型",
                "description": "結合技術、情緒、宏觀、風險因子的量化模型",
                "color": "#FF9800",
                "icon": "analytics",
                "count": 1
            },
            StrategyCategory.CORE_CBSC_TECHNICAL: {
                "display_name": "核心CBSC技術分析",
                "description": "基於傳統技術指標的CBSC交易策略",
                "color": "#9C27B0",
                "icon": "trending_up",
                "count": 4
            },
            StrategyCategory.CORE_CBSC_SENTIMENT: {
                "display_name": "核心CBSC情緒分析",
                "description": "基於市場情緒分析的高級CBSC策略",
                "color": "#F44336",
                "icon": "psychology",
                "count": 4
            },
            StrategyCategory.CORE_CBSC_AGGRESSIVE: {
                "display_name": "核心CBSC激進策略",
                "description": "高收益高風險的激進CBSC交易策略",
                "color": "#E91E63",
                "icon": "speed",
                "count": 3
            },
            StrategyCategory.PORTFOLIO_OPTIMIZATION: {
                "display_name": "投資組合優化",
                "description": "多策略組合優化和風險管理",
                "color": "#00BCD4",
                "icon": "pie_chart",
                "count": 1
            }
        }

    def _load_all_strategies(self):
        """加載所有策略數據"""
        # 1. 加載月度低頻策略
        self._load_monthly_strategies()

        # 2. 加載多策略驗證系統
        self._load_multi_strategies()

        # 3. 加載多因子模型
        self._load_multi_factor_model()

        # 4. 加載核心CBSC技術分析策略
        self._load_cbsc_technical_strategies()

        # 5. 加載核心CBSC情緒分析策略
        self._load_cbsc_sentiment_strategies()

        # 6. 加載核心CBSC激進策略
        self._load_cbsc_aggressive_strategies()

        # 7. 加載投資組合優化
        self._load_portfolio_optimization()

    def _load_monthly_strategies(self):
        """加載月度低頻策略"""
        monthly_strategies = [
            {
                "name": "Seasonal_Quarterly",
                "subcategory": "季節性策略",
                "annual_return": 0.0024,
                "sharpe_ratio": -2.22,
                "max_drawdown": -0.0138,
                "win_rate": 0.0116,
                "description": "基於季節性因子的季度交易策略",
                "risk_level": "low"
            },
            {
                "name": "Quarterly_Reversal",
                "subcategory": "季度反轉策略",
                "annual_return": 0.0072,
                "sharpe_ratio": -0.18,
                "max_drawdown": -0.2387,
                "win_rate": 0.0698,
                "description": "季度均值回歸策略",
                "risk_level": "medium"
            },
            {
                "name": "Dividend_Yield",
                "subcategory": "股息收益策略",
                "annual_return": 0.0356,
                "sharpe_ratio": 0.07,
                "max_drawdown": -0.2858,
                "win_rate": 0.4186,
                "description": "基於股息率的價值投資策略",
                "risk_level": "medium"
            },
            {
                "name": "Risk_Parity",
                "subcategory": "風險平價策略",
                "annual_return": 0.0338,
                "sharpe_ratio": 0.04,
                "max_drawdown": -0.4619,
                "win_rate": 0.5291,
                "description": "風險平價配置策略",
                "risk_level": "low"
            },
            {
                "name": "Valuation_Based",
                "subcategory": "評價基礎策略",
                "annual_return": 0.0243,
                "sharpe_ratio": -0.01,
                "max_drawdown": -0.4045,
                "win_rate": 0.1919,
                "description": "基於估值指標的基本面策略",
                "risk_level": "medium"
            },
            {
                "name": "Monthly_Momentum",
                "subcategory": "月度動量策略",
                "annual_return": -0.0267,
                "sharpe_ratio": -0.43,
                "max_drawdown": -0.4566,
                "win_rate": 0.1395,
                "description": "月度動量策略，表現不佳",
                "risk_level": "high"
            }
        ]

        for strategy_data in monthly_strategies:
            grade = self._calculate_grade(strategy_data["sharpe_ratio"], strategy_data["annual_return"])

            self.strategies[strategy_data["name"]] = StrategyInfo(
                name=strategy_data["name"],
                category=StrategyCategory.MONTHLY_LOW_FREQUENCY,
                subcategory=strategy_data["subcategory"],
                annual_return=strategy_data["annual_return"],
                sharpe_ratio=strategy_data["sharpe_ratio"],
                max_drawdown=strategy_data["max_drawdown"],
                win_rate=strategy_data["win_rate"],
                grade=grade,
                description=strategy_data["description"],
                risk_level=strategy_data["risk_level"],
                trading_frequency="low",
                last_updated=datetime.now()
            )

    def _load_multi_strategies(self):
        """加載多策略驗證系統"""
        multi_strategies = [
            {
                "name": "Sentiment_Based",
                "subcategory": "情緒分析策略",
                "annual_return": 0.0,
                "sharpe_ratio": -4647520984502543.0,  # 異常值，實際無交易
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "description": "基於市場情緒的分析策略，未觸發交易信號",
                "risk_level": "low"
            },
            {
                "name": "RSI_Low_Frequency",
                "subcategory": "低頻RSI策略",
                "annual_return": 0.0151,
                "sharpe_ratio": 0.06,
                "max_drawdown": -0.6269,
                "win_rate": 0.4814,
                "description": "RSI低頻交易策略，風險控制較差",
                "risk_level": "medium"
            },
            {
                "name": "Bollinger_Low_Freq",
                "subcategory": "低頻布林策略",
                "annual_return": -0.0110,
                "sharpe_ratio": -0.08,
                "max_drawdown": -0.4921,
                "win_rate": 0.4910,
                "description": "布林帶低頻策略，表現不佳",
                "risk_level": "medium"
            },
            {
                "name": "Trend_Following_Monthly",
                "subcategory": "月度趨勢跟蹤",
                "annual_return": -0.0279,
                "sharpe_ratio": -0.16,
                "max_drawdown": -0.5992,
                "win_rate": 0.5084,
                "description": "月度趨勢跟蹤策略，虧損較大",
                "risk_level": "high"
            },
            {
                "name": "Mean_Reversion",
                "subcategory": "均值回歸策略",
                "annual_return": -0.0137,
                "sharpe_ratio": -0.25,
                "max_drawdown": -0.4214,
                "win_rate": 0.4657,
                "description": "均值回歸策略，波動性較大",
                "risk_level": "high"
            },
            {
                "name": "Volatility_Based",
                "subcategory": "波動率策略",
                "annual_return": -0.0015,
                "sharpe_ratio": -0.02,
                "max_drawdown": -0.4644,
                "win_rate": 0.5255,
                "description": "基於波動率的交易策略",
                "risk_level": "medium"
            }
        ]

        for strategy_data in multi_strategies:
            grade = self._calculate_grade(strategy_data["sharpe_ratio"], strategy_data["annual_return"])

            self.strategies[f"Multi_{strategy_data['name']}"] = StrategyInfo(
                name=f"Multi_{strategy_data['name']}",
                category=StrategyCategory.MULTI_STRATEGY_VALIDATION,
                subcategory=strategy_data["subcategory"],
                annual_return=strategy_data["annual_return"],
                sharpe_ratio=strategy_data["sharpe_ratio"],
                max_drawdown=strategy_data["max_drawdown"],
                win_rate=strategy_data["win_rate"],
                grade=grade,
                description=strategy_data["description"],
                risk_level=strategy_data["risk_level"],
                trading_frequency="medium",
                last_updated=datetime.now()
            )

    def _load_multi_factor_model(self):
        """加載多因子模型"""
        strategy_data = {
            "name": "Multi_Factor_Model",
            "subcategory": "多因子量化模型",
            "annual_return": 0.0372,
            "sharpe_ratio": 0.16,
            "max_drawdown": -0.5349,
            "win_rate": 0.4671,
            "description": "綜合技術、情緒、宏觀、風險因子的量化模型",
            "risk_level": "medium"
        }

        grade = self._calculate_grade(strategy_data["sharpe_ratio"], strategy_data["annual_return"])

        self.strategies[strategy_data["name"]] = StrategyInfo(
            name=strategy_data["name"],
            category=StrategyCategory.MULTI_FACTOR_MODEL,
            subcategory=strategy_data["subcategory"],
            annual_return=strategy_data["annual_return"],
            sharpe_ratio=strategy_data["sharpe_ratio"],
            max_drawdown=strategy_data["max_drawdown"],
            win_rate=strategy_data["win_rate"],
            grade=grade,
            description=strategy_data["description"],
            risk_level=strategy_data["risk_level"],
            trading_frequency="medium",
            last_updated=datetime.now()
        )

    def _load_cbsc_technical_strategies(self):
        """加載核心CBSC技術分析策略"""
        technical_strategies = [
            {
                "name": "RSI_Aggressive",
                "subcategory": "激進RSI策略",
                "annual_return": 0.1435,
                "sharpe_ratio": 0.63,
                "max_drawdown": -0.3901,
                "win_rate": 0.4500,
                "description": "激進RSI策略，最佳表現策略",
                "risk_level": "high"
            },
            {
                "name": "RSI_Conservative",
                "subcategory": "保守RSI策略",
                "annual_return": -0.0733,
                "sharpe_ratio": -0.16,
                "max_drawdown": -0.7720,
                "win_rate": 0.3000,
                "description": "保守RSI策略，虧損較大",
                "risk_level": "medium"
            },
            {
                "name": "Bollinger_Breakout",
                "subcategory": "布林突破策略",
                "annual_return": -0.0396,
                "sharpe_ratio": -0.06,
                "max_drawdown": -0.5805,
                "win_rate": 0.3500,
                "description": "布林帶突破策略，表現不佳",
                "risk_level": "medium"
            },
            {
                "name": "MACD_Standard",
                "subcategory": "標準MACD策略",
                "annual_return": 0.0,
                "sharpe_ratio": -0.41,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "description": "標準MACD策略，存在數據質量問題",
                "risk_level": "medium"
            }
        ]

        for strategy_data in technical_strategies:
            grade = self._calculate_grade(strategy_data["sharpe_ratio"], strategy_data["annual_return"])

            self.strategies[f"CBSC_Tech_{strategy_data['name']}"] = StrategyInfo(
                name=strategy_data["name"],
                category=StrategyCategory.CORE_CBSC_TECHNICAL,
                subcategory=strategy_data["subcategory"],
                annual_return=strategy_data["annual_return"],
                sharpe_ratio=strategy_data["sharpe_ratio"],
                max_drawdown=strategy_data["max_drawdown"],
                win_rate=strategy_data["win_rate"],
                grade=grade,
                description=strategy_data["description"],
                risk_level=strategy_data["risk_level"],
                trading_frequency="high",
                last_updated=datetime.now()
            )

    def _load_cbsc_sentiment_strategies(self):
        """加載核心CBSC情緒分析策略"""
        sentiment_strategies = [
            {
                "name": "SentimentMomentumStrategy",
                "subcategory": "情緒動量策略",
                "annual_return": 0.0477,
                "sharpe_ratio": 2.26,
                "max_drawdown": -0.0053,
                "win_rate": 0.6500,
                "description": "MACD風格的情緒變化率分析，捕捉情緒轉折點",
                "risk_level": "medium"
            },
            {
                "name": "DirectRSIStrategy",
                "subcategory": "直接RSI情緒策略",
                "annual_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "description": "對牛熊比例直接計算RSI，識別極端情緒信號",
                "risk_level": "low"
            },
            {
                "name": "CompositeIndexStrategy",
                "subcategory": "複合指標策略",
                "annual_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "description": "多維度情緒綜合，布林帶風格的情緒區間分析",
                "risk_level": "medium"
            },
            {
                "name": "VolatilityAdjustedStrategy",
                "subcategory": "波動率調整策略",
                "annual_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "description": "成交量加權的情緒分析，考慮市場信心度",
                "risk_level": "medium"
            }
        ]

        for strategy_data in sentiment_strategies:
            grade = self._calculate_grade(strategy_data["sharpe_ratio"], strategy_data["annual_return"])

            self.strategies[f"CBSC_Sentiment_{strategy_data['name']}"] = StrategyInfo(
                name=strategy_data["name"],
                category=StrategyCategory.CORE_CBSC_SENTIMENT,
                subcategory=strategy_data["subcategory"],
                annual_return=strategy_data["annual_return"],
                sharpe_ratio=strategy_data["sharpe_ratio"],
                max_drawdown=strategy_data["max_drawdown"],
                win_rate=strategy_data["win_rate"],
                grade=grade,
                description=strategy_data["description"],
                risk_level=strategy_data["risk_level"],
                trading_frequency="medium",
                last_updated=datetime.now()
            )

    def _load_cbsc_aggressive_strategies(self):
        """加載核心CBSC激進策略"""
        aggressive_strategies = [
            {
                "name": "Risk_Adjusted_Bollinger_Aggressive",
                "subcategory": "風險調整布林",
                "annual_return": 0.1191,
                "sharpe_ratio": 3.58,
                "max_drawdown": -0.0065,
                "win_rate": 0.7000,
                "description": "風險調整的布林帶策略，優秀表現",
                "risk_level": "high"
            },
            {
                "name": "Time_Decay_Momentum_Aggressive",
                "subcategory": "時間衰減動量",
                "annual_return": 0.0716,
                "sharpe_ratio": 3.14,
                "max_drawdown": -0.0038,
                "win_rate": 0.6500,
                "description": "時間衰減動量策略，穩定獲利",
                "risk_level": "high"
            },
            {
                "name": "Volume_Reversal_Aggressive",
                "subcategory": "成交量反轉",
                "annual_return": 0.0061,
                "sharpe_ratio": 0.29,
                "max_drawdown": -0.0075,
                "win_rate": 0.5500,
                "description": "成交量反轉策略，保守但穩定",
                "risk_level": "medium"
            }
        ]

        for strategy_data in aggressive_strategies:
            grade = self._calculate_grade(strategy_data["sharpe_ratio"], strategy_data["annual_return"])

            self.strategies[f"CBSC_Aggressive_{strategy_data['name']}"] = StrategyInfo(
                name=strategy_data["name"],
                category=StrategyCategory.CORE_CBSC_AGGRESSIVE,
                subcategory=strategy_data["subcategory"],
                annual_return=strategy_data["annual_return"],
                sharpe_ratio=strategy_data["sharpe_ratio"],
                max_drawdown=strategy_data["max_drawdown"],
                win_rate=strategy_data["win_rate"],
                grade=grade,
                description=strategy_data["description"],
                risk_level=strategy_data["risk_level"],
                trading_frequency="high",
                last_updated=datetime.now()
            )

    def _load_portfolio_optimization(self):
        """加載投資組合優化"""
        strategy_data = {
            "name": "Max_Sharpe_Portfolio",
            "subcategory": "最大夏普比率組合",
            "annual_return": 0.30,
            "sharpe_ratio": 1.88,
            "max_drawdown": -0.1460,
            "win_rate": 0.6500,
            "description": "最佳投資組合，夏普比率1.88，年化收益30%",
            "risk_level": "medium"
        }

        grade = self._calculate_grade(strategy_data["sharpe_ratio"], strategy_data["annual_return"])

        self.strategies[strategy_data["name"]] = StrategyInfo(
            name=strategy_data["name"],
            category=StrategyCategory.PORTFOLIO_OPTIMIZATION,
            subcategory=strategy_data["subcategory"],
            annual_return=strategy_data["annual_return"],
            sharpe_ratio=strategy_data["sharpe_ratio"],
            max_drawdown=strategy_data["max_drawdown"],
            win_rate=strategy_data["win_rate"],
            grade=grade,
            description=strategy_data["description"],
            risk_level=strategy_data["risk_level"],
            trading_frequency="low",
            last_updated=datetime.now()
        )

    def _calculate_grade(self, sharpe_ratio: float, annual_return: float) -> StrategyGrade:
        """計算策略評級"""
        # 異常值處理
        if abs(sharpe_ratio) > 100 or sharpe_ratio == float('-inf'):
            return StrategyGrade.VERY_POOR

        score = 0

        # 夏普比率評分 (0-50分)
        if sharpe_ratio > 3.0:
            score += 50
        elif sharpe_ratio > 2.0:
            score += 40
        elif sharpe_ratio > 1.5:
            score += 35
        elif sharpe_ratio > 1.0:
            score += 30
        elif sharpe_ratio > 0.8:
            score += 25
        elif sharpe_ratio > 0.6:
            score += 20
        elif sharpe_ratio > 0.4:
            score += 15
        elif sharpe_ratio > 0.2:
            score += 10
        elif sharpe_ratio > 0:
            score += 5

        # 年化收益率評分 (0-30分)
        if annual_return > 0.3:  # 30%以上
            score += 30
        elif annual_return > 0.2:  # 20%以上
            score += 25
        elif annual_return > 0.15:  # 15%以上
            score += 20
        elif annual_return > 0.1:  # 10%以上
            score += 15
        elif annual_return > 0.05:  # 5%以上
            score += 10
        elif annual_return > 0:  # 正收益
            score += 5

        # 風險調整 (負分)
        if sharpe_ratio < -1.0:
            score -= 20
        elif sharpe_ratio < -0.5:
            score -= 10
        elif sharpe_ratio < 0:
            score -= 5

        score = max(0, min(100, score))

        # 根據分數返回評級
        if score >= 90:
            return StrategyGrade.EXCELLENT
        elif score >= 80:
            return StrategyGrade.GOOD
        elif score >= 70:
            return StrategyGrade.VERY_GOOD
        elif score >= 60:
            return StrategyGrade.GOOD_B
        elif score >= 50:
            return StrategyGrade.AVERAGE_C
        elif score >= 40:
            return StrategyGrade.AVERAGE
        elif score >= 30:
            return StrategyGrade.POOR_D
        elif score >= 20:
            return StrategyGrade.POOR
        else:
            return StrategyGrade.VERY_POOR

    def get_strategies_by_category(self, category: StrategyCategory) -> List[StrategyInfo]:
        """根據類別獲取策略列表"""
        return [strategy for strategy in self.strategies.values() if strategy.category == category]

    def get_all_categories(self) -> List[Dict[str, Any]]:
        """獲取所有類別及其元數據"""
        categories = []
        for category_enum in StrategyCategory:
            category_strategies = self.get_strategies_by_category(category_enum)
            metadata = self.category_metadata[category_enum].copy()
            metadata["category"] = category_enum.value
            metadata["strategies_count"] = len(category_strategies)
            metadata["strategies"] = [
                {
                    "name": strategy.name,
                    "grade": strategy.grade.value,
                    "annual_return": strategy.annual_return,
                    "sharpe_ratio": strategy.sharpe_ratio,
                    "risk_level": strategy.risk_level
                }
                for strategy in category_strategies
            ]

            # 計算類別統計
            if category_strategies:
                avg_return = sum(s.annual_return for s in category_strategies) / len(category_strategies)
                avg_sharpe = sum(s.sharpe_ratio for s in category_strategies if abs(s.sharpe_ratio) < 100) / len([s for s in category_strategies if abs(s.sharpe_ratio) < 100])

                grade_distribution = {}
                for strategy in category_strategies:
                    grade = strategy.grade.value
                    grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

                metadata["statistics"] = {
                    "avg_annual_return": avg_return,
                    "avg_sharpe_ratio": avg_sharpe,
                    "grade_distribution": grade_distribution,
                    "best_strategy": max(category_strategies, key=lambda s: s.sharpe_ratio if abs(s.sharpe_ratio) < 100 else -1000).name
                }

            categories.append(metadata)

        return categories

    def filter_strategies(self,
                          categories: Optional[List[str]] = None,
                          grades: Optional[List[str]] = None,
                          risk_levels: Optional[List[str]] = None,
                          trading_frequencies: Optional[List[str]] = None,
                          min_sharpe: Optional[float] = None,
                          min_return: Optional[float] = None) -> List[StrategyInfo]:
        """根據多種條件篩選策略"""
        filtered_strategies = list(self.strategies.values())

        # 類別篩選
        if categories:
            category_enums = [StrategyCategory(cat) for cat in categories]
            filtered_strategies = [s for s in filtered_strategies if s.category in category_enums]

        # 評級篩選
        if grades:
            grade_enums = [StrategyGrade(grade) for grade in grades]
            filtered_strategies = [s for s in filtered_strategies if s.grade in grade_enums]

        # 風險級別篩選
        if risk_levels:
            filtered_strategies = [s for s in filtered_strategies if s.risk_level in risk_levels]

        # 交易頻率篩選
        if trading_frequencies:
            filtered_strategies = [s for s in filtered_strategies if s.trading_frequency in trading_frequencies]

        # 夏普比率篩選
        if min_sharpe is not None:
            filtered_strategies = [s for s in filtered_strategies if s.sharpe_ratio >= min_sharpe]

        # 年化收益篩選
        if min_return is not None:
            filtered_strategies = [s for s in filtered_strategies if s.annual_return >= min_return]

        return filtered_strategies

    def get_strategy_summary(self) -> Dict[str, Any]:
        """獲取策略總結統計"""
        all_strategies = list(self.strategies.values())

        if not all_strategies:
            return {}

        # 基本統計
        total_count = len(all_strategies)

        # 評級分佈
        grade_distribution = {}
        for strategy in all_strategies:
            grade = strategy.grade.value
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        # 類別分佈
        category_distribution = {}
        for strategy in all_strategies:
            category = strategy.category.value
            category_distribution[category] = category_distribution.get(category, 0) + 1

        # 性能統計
        valid_strategies = [s for s in all_strategies if abs(s.sharpe_ratio) < 100]
        if valid_strategies:
            avg_sharpe = sum(s.sharpe_ratio for s in valid_strategies) / len(valid_strategies)
            avg_return = sum(s.annual_return for s in valid_strategies) / len(valid_strategies)
            max_sharpe = max(valid_strategies, key=lambda s: s.sharpe_ratio)
            min_sharpe = min(valid_strategies, key=lambda s: s.sharpe_ratio)
        else:
            avg_sharpe = avg_return = max_sharpe = min_sharpe = 0

        # 最佳策略
        best_strategy = max(all_strategies, key=lambda s: s.sharpe_ratio if abs(s.sharpe_ratio) < 100 else -1000)

        return {
            "total_strategies": total_count,
            "grade_distribution": grade_distribution,
            "category_distribution": category_distribution,
            "performance_stats": {
                "avg_sharpe_ratio": avg_sharpe,
                "avg_annual_return": avg_return,
                "best_sharpe_strategy": max_sharpe.name if max_sharpe else "N/A",
                "worst_sharpe_strategy": min_sharpe.name if min_sharpe else "N/A",
                "best_overall_strategy": best_strategy.name
            },
            "last_updated": datetime.now().isoformat()
        }

# API端點實現
def create_strategy_classification_api(app):
    """創建策略分類API端點"""

    @app.get("/api/strategies/classification/categories")
    async def get_strategy_categories():
        """獲取所有策略類別"""
        service = StrategyClassificationService()
        categories = service.get_all_categories()
        return {
            "success": True,
            "data": categories,
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/api/strategies/classification/summary")
    async def get_strategy_summary():
        """獲取策略總結"""
        service = StrategyClassificationService()
        summary = service.get_strategy_summary()
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/api/strategies/classification/filter")
    async def filter_strategies(
        categories: Optional[str] = None,
        grades: Optional[str] = None,
        risk_levels: Optional[str] = None,
        trading_frequencies: Optional[str] = None,
        min_sharpe: Optional[float] = None,
        min_return: Optional[float] = None
    ):
        """篩選策略"""
        service = StrategyClassificationService()

        # 解析查詢參數
        categories_list = categories.split(",") if categories else None
        grades_list = grades.split(",") if grades else None
        risk_levels_list = risk_levels.split(",") if risk_levels else None
        frequencies_list = trading_frequencies.split(",") if trading_frequencies else None

        filtered_strategies = service.filter_strategies(
            categories=categories_list,
            grades=grades_list,
            risk_levels=risk_levels_list,
            trading_frequencies=frequencies_list,
            min_sharpe=min_sharpe,
            min_return=min_return
        )

        return {
            "success": True,
            "data": [
                {
                    "name": strategy.name,
                    "category": strategy.category.value,
                    "subcategory": strategy.subcategory,
                    "annual_return": strategy.annual_return,
                    "sharpe_ratio": strategy.sharpe_ratio,
                    "max_drawdown": strategy.max_drawdown,
                    "win_rate": strategy.win_rate,
                    "grade": strategy.grade.value,
                    "risk_level": strategy.risk_level,
                    "trading_frequency": strategy.trading_frequency,
                    "description": strategy.description
                }
                for strategy in filtered_strategies
            ],
            "count": len(filtered_strategies),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 測試代碼
    service = StrategyClassificationService()

    print("策略分類服務測試")
    print("=" * 50)

    # 顯示所有類別
    categories = service.get_all_categories()
    for category in categories:
        print(f"\n【{category['display_name']}】")
        print(f"  描述: {category['description']}")
        print(f"  策略數量: {category['strategies_count']}")
        if 'statistics' in category:
            stats = category['statistics']
            print(f"  平均年化收益: {stats['avg_annual_return']:.2%}")
            print(f"  平均夏普比率: {stats['avg_sharpe_ratio']:.2f}")
            print(f"  最佳策略: {stats['best_strategy']}")

    # 顯示總結
    summary = service.get_strategy_summary()
    print(f"\n{'='*50}")
    print("總結統計")
    print(f"  總策略數: {summary['total_strategies']}")
    print(f"  評級分佈: {summary['grade_distribution']}")
    print(f"  最佳策略: {summary['performance_stats']['best_overall_strategy']}")

    # 測試篩選功能
    print(f"\n{'='*50}")
    print("篩選測試")

    # 篩選A級以上策略
    top_strategies = service.filter_strategies(grades=["A+", "A", "B+"])
    print(f"A級以上策略: {len(top_strategies)}個")
    for strategy in top_strategies:
        print(f"  - {strategy.name}: {strategy.grade.value} (夏普: {strategy.sharpe_ratio:.2f})")