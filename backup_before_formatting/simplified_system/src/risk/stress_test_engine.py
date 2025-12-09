#!/usr/bin/env python3
"""
Stress Testing Engine
壓力測試引擎

Comprehensive stress testing and scenario analysis for portfolios
投資組合綜合壓力測試和情景分析

Features:
- Historical crisis scenarios (2008 financial crisis, 2020 COVID crash, etc.)
- Custom stress scenarios
- Monte Carlo stress testing
- Factor shock analysis
- Reverse stress testing
- Portfolio resilience assessment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import logging
from datetime import datetime, timedelta
from scipy import stats
import warnings
from enum import Enum

logger = logging.getLogger(__name__)

class StressTestType(Enum):
    """壓力測試類型"""
    HISTORICAL = "歷史情景"
    HYPOTHETICAL = "假設情景"
    MONTE_CARLO = "蒙特卡羅"
    FACTOR_SHOCK = "因子沖擊"
    REVERSE = "反向壓力測試"
    EXTREME = "極端情景"

class StressSeverity(Enum):
    """壓力嚴重程度"""
    MILD = "輕度"
    MODERATE = "中度"
    SEVERE = "重度"
    EXTREME = "極端"

@dataclass
class StressScenario:
    """壓力測試情景"""
    scenario_id: str
    name: str
    description: str
    stress_type: StressTestType
    severity: StressSeverity
    market_shocks: Dict[str, float]  # Market factor shocks
    correlation_changes: Dict[str, float]  # Correlation adjustments
    liquidity_adjustments: Dict[str, float]  # Liquidity impact factors
    duration_days: int = 30
    probability: float = 0.01  # 1% probability for extreme events

@dataclass
class StressTestResult:
    """壓力測試結果"""
    scenario_id: str
    scenario_name: str
    portfolio_value_before: float
    portfolio_value_after: float
    portfolio_loss: float
    portfolio_loss_percentage: float
    max_drawdown: float
    var_95: float
    var_99: float
    expected_shortfall: float
    recovery_time_days: int
    liquidity_impact: float
    sector_impacts: Dict[str, float]
    asset_impacts: Dict[str, float]
    risk_contributions: Dict[str, float]
    worst_day_performance: float
    best_day_performance: float
    volatility_increase: float
    correlation_breakdown: bool

@dataclass
class StressTestReport:
    """壓力測試報告"""
    test_date: datetime
    portfolio_id: str
    base_portfolio_value: float
    scenarios_tested: List[str]
    worst_case_scenario: str
    worst_case_loss: float
    worst_case_loss_percentage: float
    average_loss: float
    median_loss: float
    stress_var: float
    stress_expected_shortfall: float
    portfolio_resilience_score: float
    risk_concentration_under_stress: Dict[str, float]
    recommendations: List[str]
    detailed_results: List[StressTestResult]

class StressTestEngine:
    """
    壓力測試引擎

    Comprehensive stress testing framework for portfolio risk assessment
    投資組合風險評估的綜合壓力測試框架
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化壓力測試引擎"""
        self.config = config or self._default_config()
        self.scenarios = self._initialize_scenarios()
        self.historical_crises = self._load_historical_crises()

        logger.info("Stress Test Engine initialized successfully")

    def _default_config(self) -> Dict[str, Any]:
        """默認配置"""
        return {
            'monte_carlo_simulations': 10000,
            'confidence_levels': [0.90, 0.95, 0.99],
            'stress_horizon_days': 30,
            'liquidity_impact_factor': 1.5,  # Liquidity worsens by 50% under stress
            'correlation_breakdown_factor': 0.3,  # Correlations increase by 30%
            'factor_shock_magnitude': 3.0,  # 3 standard deviation shocks
            'recovery_assumption_days': 90,
            'enable_reverse_stress_testing': True,
            'custom_scenarios': []
        }

    def _initialize_scenarios(self) -> List[StressScenario]:
        """初始化標準壓力測試情景"""
        scenarios = [
            # Historical scenarios
            StressScenario(
                scenario_id="2008_financial_crisis",
                name="2008年金融危機",
                description="全球金融危機，股市暴跌，信用收縮",
                stress_type=StressTestType.HISTORICAL,
                severity=StressSeverity.EXTREME,
                market_shocks={
                    'equity_market': -0.40,  # 40% equity market drop
                    'bond_market': 0.08,     # 8% bond market rally (flight to quality)
                    'real_estate': -0.35,    # 35% real estate drop
                    'commodities': -0.25,     # 25% commodities drop
                    'volatility': 2.5,        # Volatility increases 2.5x
                    'credit_spread': 0.05     # Credit spreads widen by 500bps
                },
                correlation_changes={
                    'equity_bond': -0.5,       # Equities and bonds become more correlated
                    'flight_to_quality': 0.8   # Strong flight to quality
                },
                liquidity_adjustments={
                    'equity_liquidity': -0.6,  # 60% reduction in liquidity
                    'bid_ask_spread': 2.0      # Bid-ask spreads double
                },
                duration_days=60,
                probability=0.02
            ),

            StressScenario(
                scenario_id="2020_covid_crash",
                name="2020年COVID-19市場崩潰",
                description="新冠疫情導致的快速市場下跌和流動性危機",
                stress_type=StressTestType.HISTORICAL,
                severity=StressSeverity.SEVERE,
                market_shocks={
                    'equity_market': -0.30,    # 30% equity market drop
                    'bond_market': 0.12,       # 12% bond rally
                    'travel_leisure': -0.50,   # 50% travel & leisure drop
                    'technology': -0.15,       # 15% tech drop
                    'healthcare': 0.20,        # 20% healthcare rally
                    'volatility': 3.0,         # Volatility triples
                    'credit_spread': 0.03
                },
                correlation_changes={
                    'sector_diversification': -0.3,  # Sector diversification reduces
                    'systemic_risk': 0.9             # High systemic risk
                },
                liquidity_adjustments={
                    'market_liquidity': -0.4,
                    'bid_ask_spread': 1.5
                },
                duration_days=45,
                probability=0.05
            ),

            # Hypothetical scenarios
            StressScenario(
                scenario_id="interest_rate_shock",
                name="利率急劇上升",
                description="央行大幅加息導致的市場震盪",
                stress_type=StressTestType.HYPOTHETICAL,
                severity=StressSeverity.SEVERE,
                market_shocks={
                    'interest_rates': 0.03,      # 300bps rate hike
                    'bond_prices': -0.15,        # 15% bond price drop
                    'equity_market': -0.20,      # 20% equity drop
                    'real_estate': -0.25,        # 25% real estate drop
                    'financial_stocks': -0.30,   # 30% financial stocks drop
                    'utilities': -0.35,          # 35% utilities drop
                    'volatility': 1.8,
                    'credit_spread': 0.02
                },
                correlation_changes={
                    'interest_sensitive': 0.7,   # Interest-sensitive assets correlate more
                    'growth_value': -0.2         # Growth and value divergence
                },
                liquidity_adjustments={
                    'bond_liquidity': -0.3,
                    'equity_liquidity': -0.2
                },
                duration_days=30,
                probability=0.10
            ),

            StressScenario(
                scenario_id="china_slowdown",
                name="中國經濟硬著陸",
                description="中國經濟大幅放緩對全球市場的影響",
                stress_type=StressTestType.HYPOTHETICAL,
                severity=StressSeverity.MODERATE,
                market_shocks={
                    'china_equities': -0.35,      # 35% China equities drop
                    'emerging_markets': -0.25,    # 25% emerging markets drop
                    'commodities': -0.30,         # 30% commodities drop
                    'global_equities': -0.15,     # 15% global equities drop
                    'luxury_goods': -0.20,        # 20% luxury goods drop
                    'volatility': 1.5,
                    'credit_spread': 0.015
                },
                correlation_changes={
                    'emerging_correlation': 0.8,  # Emerging markets correlate more
                    'commodity_correlation': 0.7  # Commodities correlate with equities
                },
                liquidity_adjustments={
                    'emerging_liquidity': -0.4,
                    'commodity_liquidity': -0.3
                },
                duration_days=40,
                probability=0.15
            ),

            # Factor shock scenarios
            StressScenario(
                scenario_id="volatility_spike",
                name="波動率急劇上升",
                description="VIX指數飆升，市場波動性大幅增加",
                stress_type=StressTestType.FACTOR_SHOCK,
                severity=StressSeverity.SEVERE,
                market_shocks={
                    'volatility': 4.0,           # Volatility quadruples
                    'equity_market': -0.25,       # 25% equity drop
                    'option_prices': 2.5,         # Option prices increase 2.5x
                    'risk_premium': 0.04,         # Risk premium increases 400bps
                    'credit_spread': 0.025
                },
                correlation_changes={
                    'risk_assets': 0.9,           # All risk assets correlate highly
                    'safe_havens': -0.8           # Safe havens move opposite
                },
                liquidity_adjustments={
                    'market_liquidity': -0.5,
                    'option_liquidity': -0.6
                },
                duration_days=20,
                probability=0.08
            )
        ]

        return scenarios

    def _load_historical_crises(self) -> Dict[str, Dict[str, Any]]:
        """加載歷史危機數據"""
        # 在實際應用中，這裡應該從真實數據源加載歷史危機數據
        # 這裡使用模擬數據
        historical_crises = {
            'dot_com_bubble_2000': {
                'start_date': '2000-03-10',
                'end_date': '2002-10-09',
                'market_drop': -0.78,  # 78% drop
                'duration_days': 942,
                'worst_sector': 'technology',
                'sector_impacts': {'technology': -0.85, 'telecom': -0.75, 'utilities': -0.20}
            },
            'asian_financial_crisis_1997': {
                'start_date': '1997-07-02',
                'end_date': '1998-12-31',
                'market_drop': -0.60,
                'duration_days': 542,
                'worst_sector': 'financial_services',
                'sector_impacts': {'financial_services': -0.70, 'real_estate': -0.65, 'exports': -0.50}
            },
            'european_debt_crisis_2011': {
                'start_date': '2010-04-01',
                'end_date': '2012-07-31',
                'market_drop': -0.35,
                'duration_days': 847,
                'worst_sector': 'banking',
                'sector_impacts': {'banking': -0.55, 'sovereign_debt': -0.40, 'peripheral_equities': -0.45}
            }
        }

        return historical_crises

    def run_stress_tests(
        self,
        portfolio_data: Dict[str, Any],
        scenario_ids: Optional[List[str]] = None,
        custom_scenarios: Optional[List[StressScenario]] = None
    ) -> StressTestReport:
        """
        運行壓力測試

        Args:
            portfolio_data: 投資組合數據，包含positions、returns、current_value等
            scenario_ids: 要測試的情景ID列表，如果為None則測試所有預設情景
            custom_scenarios: 自定義壓力測試情景

        Returns:
            StressTestReport: 綜合壓力測試報告
        """
        try:
            logger.info("Starting comprehensive stress testing")

            # 確定要測試的情景
            test_scenarios = []
            if scenario_ids:
                test_scenarios = [s for s in self.scenarios if s.scenario_id in scenario_ids]
            else:
                test_scenarios = self.scenarios

            if custom_scenarios:
                test_scenarios.extend(custom_scenarios)

            # 運行各個情景的壓力測試
            detailed_results = []
            for scenario in test_scenarios:
                result = self._run_single_stress_test(portfolio_data, scenario)
                detailed_results.append(result)

            # 生成綜合報告
            report = self._generate_stress_test_report(portfolio_data, detailed_results)

            logger.info("Stress testing completed successfully")
            return report

        except Exception as e:
            logger.error(f"Stress testing failed: {e}")
            raise

    def _run_single_stress_test(
        self,
        portfolio_data: Dict[str, Any],
        scenario: StressScenario
    ) -> StressTestResult:
        """運行單個壓力測試情景"""
        try:
            base_value = portfolio_data.get('current_value', 1000000)
            positions = portfolio_data.get('positions', pd.DataFrame())
            historical_returns = portfolio_data.get('returns', pd.Series())

            # 應用市場沖擊
            shocked_returns = self._apply_market_shocks(historical_returns, scenario)

            # 應用相關性變化
            shocked_returns = self._apply_correlation_changes(shocked_returns, scenario)

            # 應用流動性調整
            shocked_returns = self._apply_liquidity_adjustments(shocked_returns, scenario)

            # 計算壓力情景下的投資組合表現
            stressed_returns = self._calculate_stressed_portfolio_returns(
                positions, shocked_returns, scenario
            )

            # 計算壓力測試指標
            final_value = base_value * (1 + stressed_returns.sum())
            portfolio_loss = base_value - final_value
            portfolio_loss_percentage = portfolio_loss / base_value

            # 計算各種風險指標
            cumulative_returns = (1 + stressed_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()

            var_95 = np.percentile(stressed_returns, 5)
            var_99 = np.percentile(stressed_returns, 1)
            expected_shortfall = stressed_returns[stressed_returns <= var_95].mean()

            # 估算恢復時間
            recovery_time = self._estimate_recovery_time(cumulative_returns, scenario.duration_days)

            # 計算流動性影響
            liquidity_impact = self._calculate_liquidity_impact(positions, scenario)

            # 計算部門和資產影響
            sector_impacts = self._calculate_sector_impacts(positions, scenario)
            asset_impacts = self._calculate_asset_impacts(positions, scenario)

            # 風險貢獻分析
            risk_contributions = self._calculate_risk_contributions(
                positions, stressed_returns, scenario
            )

            # 其他指標
            worst_day = stressed_returns.min()
            best_day = stressed_returns.max()
            volatility_increase = stressed_returns.std() / historical_returns.std() if historical_returns.std() > 0 else 1.0
            correlation_breakdown = scenario.stress_type in [StressTestType.HISTORICAL, StressTestType.EXTREME]

            return StressTestResult(
                scenario_id=scenario.scenario_id,
                scenario_name=scenario.name,
                portfolio_value_before=base_value,
                portfolio_value_after=final_value,
                portfolio_loss=portfolio_loss,
                portfolio_loss_percentage=portfolio_loss_percentage,
                max_drawdown=max_drawdown,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                recovery_time_days=recovery_time,
                liquidity_impact=liquidity_impact,
                sector_impacts=sector_impacts,
                asset_impacts=asset_impacts,
                risk_contributions=risk_contributions,
                worst_day_performance=worst_day,
                best_day_performance=best_day,
                volatility_increase=volatility_increase,
                correlation_breakdown=correlation_breakdown
            )

        except Exception as e:
            logger.error(f"Single stress test failed for scenario {scenario.scenario_id}: {e}")
            raise

    def _apply_market_shocks(
        self,
        returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """應用市場沖擊到回報率序列"""
        shocked_returns = returns.copy()

        # 根據情景類型應用不同的沖擊模式
        if scenario.stress_type == StressTestType.HISTORICAL:
            shocked_returns = self._apply_historical_shock_pattern(shocked_returns, scenario)
        elif scenario.stress_type == StressTestType.HYPOTHETICAL:
            shocked_returns = self._apply_hypothetical_shock_pattern(shocked_returns, scenario)
        elif scenario.stress_type == StressTestType.FACTOR_SHOCK:
            shocked_returns = self._apply_factor_shock_pattern(shocked_returns, scenario)
        else:
            shocked_returns = self._apply_generic_shock_pattern(shocked_returns, scenario)

        return shocked_returns

    def _apply_historical_shock_pattern(
        self,
        returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """應用歷史沖擊模式"""
        # 模擬歷史危機的沖擊模式
        n_days = scenario.duration_days
        shocked_returns = returns.copy()

        # 生成沖擊路徑
        for i in range(min(n_days, len(returns))):
            day_factor = 1.0 - (i / n_days) * 0.5  # 沖擊隨時間遞減

            # 應用市場沖擊
            market_shock = scenario.market_shocks.get('equity_market', 0)
            shock_component = market_shock * day_factor / n_days

            # 添加隨機波動
            volatility_factor = scenario.market_shocks.get('volatility', 1.5)
            random_component = np.random.normal(0, returns.std() * volatility_factor * day_factor)

            shocked_returns.iloc[i] = returns.iloc[i] + shock_component + random_component

        return shocked_returns

    def _apply_hypothetical_shock_pattern(
        self,
        returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """應用假設沖擊模式"""
        n_days = scenario.duration_days
        shocked_returns = returns.copy()

        for i in range(min(n_days, len(returns))):
            # 逐步加劇的沖擊
            shock_intensity = (i / n_days) ** 0.5  # Concave increase

            # 基礎市場沖擊
            base_shock = scenario.market_shocks.get('equity_market', 0) * shock_intensity / n_days

            # 添加情景特定的沖擊
            if 'interest_rates' in scenario.market_shocks:
                rate_shock = scenario.market_shocks['interest_rates'] * shock_intensity * 0.5 / n_days
                shocked_returns.iloc[i] += base_shock + rate_shock
            else:
                shocked_returns.iloc[i] += base_shock

            # 波動率影響
            volatility_factor = scenario.market_shocks.get('volatility', 1.5)
            random_shock = np.random.normal(0, returns.std() * volatility_factor * shock_intensity)
            shocked_returns.iloc[i] += random_shock

        return shocked_returns

    def _apply_factor_shock_pattern(
        self,
        returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """應用因子沖擊模式"""
        shocked_returns = returns.copy()
        n_days = scenario.duration_days

        # 因子沖擊通常對特定因子影響更大
        if 'volatility' in scenario.market_shocks:
            volatility_multiplier = scenario.market_shocks['volatility']
            for i in range(min(n_days, len(returns))):
                # 高波動率環境下的回報模式
                shocked_returns.iloc[i] *= volatility_multiplier
                # 添加均值回歸傾向
                shocked_returns.iloc[i] += np.random.normal(-returns.mean(), returns.std())

        return shocked_returns

    def _apply_generic_shock_pattern(
        self,
        returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """應用通用沖擊模式"""
        n_days = scenario.duration_days
        shocked_returns = returns.copy()

        for i in range(min(n_days, len(returns))):
            # 線性沖擊模式
            shock_magnitude = scenario.market_shocks.get('equity_market', -0.20)
            daily_shock = shock_magnitude / n_days
            shocked_returns.iloc[i] += daily_shock

        return shocked_returns

    def _apply_correlation_changes(
        self,
        returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """應用相關性變化"""
        # 在壓力情景下，資產間相關性通常會增加（相關性崩潰）
        # 這裡簡化處理，增加系統性因子
        if not scenario.correlation_changes:
            return returns

        # 增加系統性風險因子
        systematic_factor = np.random.normal(0, 1, len(returns)) * 0.3
        shocked_returns = returns + systematic_factor * returns.std()

        return shocked_returns

    def _apply_liquidity_adjustments(
        self,
        returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """應用流動性調整"""
        if not scenario.liquidity_adjustments:
            return returns

        # 流動性風險通常表現為價格影響增加
        liquidity_impact = scenario.liquidity_adjustments.get('bid_ask_spread', 1.5)
        liquidity_cost = returns.abs() * (liquidity_impact - 1) * 0.5

        # 流動性成本通常是單向的（負向）
        liquidity_cost = np.where(returns < 0, liquidity_cost, -liquidity_cost * 0.3)

        return returns - liquidity_cost

    def _calculate_stressed_portfolio_returns(
        self,
        positions: pd.DataFrame,
        shocked_returns: pd.Series,
        scenario: StressScenario
    ) -> pd.Series:
        """計算壓力情景下的投資組合回報"""
        if positions.empty:
            # 如果沒有持倉數據，假設100%股權投資組合
            return shocked_returns

        # 根據持倉權重計算投資組合回報
        portfolio_returns = pd.Series(0, index=shocked_returns.index)

        for _, position in positions.iterrows():
            weight = position.get('weight', 0)
            asset_type = position.get('asset_type', 'equity')

            # 根據資產類型調整沖擊
            if asset_type.lower() in ['equity', 'stock']:
                asset_returns = shocked_returns
            elif asset_type.lower() in ['bond', 'fixed_income']:
                # 債券通常在危機中表現較好
                bond_shock = scenario.market_shocks.get('bond_market', 0.08)
                asset_returns = shocked_returns * 0.3 + bond_shock / scenario.duration_days
            elif asset_type.lower() in ['commodity']:
                # 商品通常下跌
                commodity_shock = scenario.market_shocks.get('commodities', -0.25)
                asset_returns = shocked_returns * 0.8 + commodity_shock / scenario.duration_days
            else:
                asset_returns = shocked_returns

            portfolio_returns += asset_returns * weight

        return portfolio_returns

    def _estimate_recovery_time(
        self,
        cumulative_returns: pd.Series,
        stress_duration_days: int
    ) -> int:
        """估算恢復時間"""
        # 找到最大回撤點
        max_drawdown_idx = cumulative_returns.idxmin()
        if pd.isna(max_drawdown_idx):
            return 0

        # 計算恢復時間
        recovery_mask = cumulative_returns.loc[max_drawdown_idx:] >= cumulative_returns.loc[max_drawdown_idx]

        if recovery_mask.any():
            recovery_idx = recovery_mask.idxmax()
            recovery_time = (recovery_idx - max_drawdown_idx).days
        else:
            # 如果在觀察期內沒有恢復，估算恢復時間
            recovery_time = stress_duration_days * 2  # 假設需要2倍壓力期恢復

        return min(recovery_time, 365)  # 最多1年

    def _calculate_liquidity_impact(
        self,
        positions: pd.DataFrame,
        scenario: StressScenario
    ) -> float:
        """計算流動性影響"""
        if positions.empty or not scenario.liquidity_adjustments:
            return 0.0

        total_liquidity_impact = 0.0

        for _, position in positions.iterrows():
            weight = position.get('weight', 0)

            # 根據資產類型計算流動性影響
            asset_type = position.get('asset_type', 'equity').lower()

            if asset_type in ['equity', 'stock']:
                liquidity_adjustment = scenario.liquidity_adjustments.get('equity_liquidity', -0.4)
            elif asset_type in ['bond', 'fixed_income']:
                liquidity_adjustment = scenario.liquidity_adjustments.get('bond_liquidity', -0.2)
            else:
                liquidity_adjustment = scenario.liquidity_adjustments.get('market_liquidity', -0.3)

            total_liquidity_impact += weight * liquidity_adjustment

        return total_liquidity_impact

    def _calculate_sector_impacts(
        self,
        positions: pd.DataFrame,
        scenario: StressScenario
    ) -> Dict[str, float]:
        """計算部門影響"""
        sector_impacts = {}

        if positions.empty or 'sector' not in positions.columns:
            return sector_impacts

        # 根據情景特點確定受影響最大的部門
        if scenario.scenario_id == "2020_covid_crash":
            sector_shocks = {
                'travel_leisure': -0.50,
                'technology': -0.15,
                'healthcare': 0.20,
                'retail': -0.30
            }
        elif scenario.scenario_id == "interest_rate_shock":
            sector_shocks = {
                'financial_stocks': -0.30,
                'utilities': -0.35,
                'real_estate': -0.25,
                'technology': -0.10
            }
        elif scenario.scenario_id == "china_slowdown":
            sector_shocks = {
                'commodities': -0.30,
                'luxury_goods': -0.20,
                'export_oriented': -0.25,
                'domestic_consumption': -0.10
            }
        else:
            # 通用沖擊
            sector_shocks = {
                'equity_market': scenario.market_shocks.get('equity_market', -0.20)
            }

        # 計算每個部門的加權影響
        for sector, sector_positions in positions.groupby('sector'):
            sector_weight = sector_positions['weight'].sum()
            sector_shock = sector_shocks.get(sector, sector_shocks.get('equity_market', -0.15))
            sector_impacts[sector] = sector_weight * sector_shock

        return sector_impacts

    def _calculate_asset_impacts(
        self,
        positions: pd.DataFrame,
        scenario: StressScenario
    ) -> Dict[str, float]:
        """計算個別資產影響"""
        asset_impacts = {}

        if positions.empty:
            return asset_impacts

        for _, position in positions.iterrows():
            asset_name = position.get('asset', 'unknown')
            weight = position.get('weight', 0)

            # 根據資產類型和情景計算影響
            base_impact = scenario.market_shocks.get('equity_market', -0.20)
            asset_impacts[asset_name] = weight * base_impact

        return asset_impacts

    def _calculate_risk_contributions(
        self,
        positions: pd.DataFrame,
        stressed_returns: pd.Series,
        scenario: StressScenario
    ) -> Dict[str, float]:
        """計算風險貢獻"""
        risk_contributions = {}

        if positions.empty:
            return risk_contributions

        total_volatility = stressed_returns.std()

        for _, position in positions.iterrows():
            asset_name = position.get('asset', 'unknown')
            weight = position.get('weight', 0)

            # 簡化的風險貢獻計算
            risk_contribution = abs(weight) * stressed_returns.std() / total_volatility
            risk_contributions[asset_name] = risk_contribution

        return risk_contributions

    def _generate_stress_test_report(
        self,
        portfolio_data: Dict[str, Any],
        detailed_results: List[StressTestResult]
    ) -> StressTestReport:
        """生成壓力測試報告"""
        base_portfolio_value = portfolio_data.get('current_value', 1000000)
        portfolio_id = portfolio_data.get('portfolio_id', 'default_portfolio')

        # 提取損失數據
        losses = [result.portfolio_loss for result in detailed_results]
        loss_percentages = [result.portfolio_loss_percentage for result in detailed_results]

        # 找到最壞情況
        worst_case_result = max(detailed_results, key=lambda x: x.portfolio_loss_percentage)

        # 計算統計指標
        average_loss = np.mean(losses)
        median_loss = np.median(losses)
        worst_case_loss = worst_case_result.portfolio_loss
        worst_case_loss_percentage = worst_case_result.portfolio_loss_percentage

        # 計算壓力VaR和Expected Shortfall
        stress_var = np.percentile(loss_percentages, 95)
        stress_expected_shortfall = np.mean([l for l in loss_percentages if l <= stress_var])

        # 計算投資組合韌性評分
        resilience_score = self._calculate_portfolio_resilience(detailed_results)

        # 計算壓力下的風險集中度
        risk_concentration = self._calculate_stress_risk_concentration(detailed_results)

        # 生成建議
        recommendations = self._generate_stress_test_recommendations(detailed_results)

        return StressTestReport(
            test_date=datetime.now(),
            portfolio_id=portfolio_id,
            base_portfolio_value=base_portfolio_value,
            scenarios_tested=[result.scenario_id for result in detailed_results],
            worst_case_scenario=worst_case_result.scenario_id,
            worst_case_loss=worst_case_loss,
            worst_case_loss_percentage=worst_case_loss_percentage,
            average_loss=average_loss,
            median_loss=median_loss,
            stress_var=stress_var,
            stress_expected_shortfall=stress_expected_shortfall,
            portfolio_resilience_score=resilience_score,
            risk_concentration_under_stress=risk_concentration,
            recommendations=recommendations,
            detailed_results=detailed_results
        )

    def _calculate_portfolio_resilience(self, detailed_results: List[StressTestResult]) -> float:
        """計算投資組合韌性評分"""
        if not detailed_results:
            return 0.0

        # 基於多個指標計算韌性評分
        resilience_factors = []

        # 1. 平均損失 (權重30%) - 損失越小韌性越高
        avg_loss_percentage = np.mean([r.portfolio_loss_percentage for r in detailed_results])
        loss_resilience = max(0, 1 - avg_loss_percentage / 0.5)  # 假設50%損失為0分
        resilience_factors.append(loss_resilience * 0.3)

        # 2. 最大回撤控制 (權重25%) - 回撤越小韌性越高
        max_drawdown_avg = np.mean([abs(r.max_drawdown) for r in detailed_results])
        drawdown_resilience = max(0, 1 - max_drawdown_avg / 0.4)  # 假設40%回撤為0分
        resilience_factors.append(drawdown_resilience * 0.25)

        # 3. 恢復時間 (權重20%) - 恢復越快韌性越高
        avg_recovery_time = np.mean([r.recovery_time_days for r in detailed_results])
        recovery_resilience = max(0, 1 - avg_recovery_time / 180)  # 假設180天恢復為0分
        resilience_factors.append(recovery_resilience * 0.2)

        # 4. 流動性影響 (權重15%) - 流動性影響越小韌性越高
        avg_liquidity_impact = np.mean([abs(r.liquidity_impact) for r in detailed_results])
        liquidity_resilience = max(0, 1 - avg_liquidity_impact / 0.5)  # 假設50%流動性影響為0分
        resilience_factors.append(liquidity_resilience * 0.15)

        # 5. 波動率增加控制 (權重10%) - 波動率增加越少韌性越高
        avg_volatility_increase = np.mean([r.volatility_increase for r in detailed_results])
        volatility_resilience = max(0, 1 - (avg_volatility_increase - 1) / 3)  # 假設4倍波動率為0分
        resilience_factors.append(volatility_resilience * 0.1)

        return sum(resilience_factors) * 100  # 轉換為100分制

    def _calculate_stress_risk_concentration(self, detailed_results: List[StressTestResult]) -> Dict[str, float]:
        """計算壓力下的風險集中度"""
        if not detailed_results:
            return {}

        # 聚合所有情景的風險貢獻
        total_risk_contributions = {}

        for result in detailed_results:
            for asset, contribution in result.risk_contributions.items():
                if asset not in total_risk_contributions:
                    total_risk_contributions[asset] = []
                total_risk_contributions[asset].append(contribution)

        # 計算平均風險貢獻
        concentration_risks = {}
        for asset, contributions in total_risk_contributions.items():
            avg_contribution = np.mean(contributions)
            concentration_risks[asset] = avg_contribution

        return concentration_risks

    def _generate_stress_test_recommendations(self, detailed_results: List[StressTestResult]) -> List[str]:
        """生成壓力測試建議"""
        recommendations = []

        if not detailed_results:
            return ["建議添加持倉數據以進行更準確的壓力測試"]

        # 分析最差情況
        worst_case = max(detailed_results, key=lambda x: x.portfolio_loss_percentage)

        if worst_case.portfolio_loss_percentage > 0.30:  # 損失超過30%
            recommendations.append("投資組合在壓力情景下損失較大，建議降低風險暴露")

        if worst_case.recovery_time_days > 90:  # 恢復時間超過90天
            recommendations.append("恢復時間較長，建議增加流動性資產配置")

        if worst_case.liquidity_impact < -0.3:  # 流動性影響超過30%
            recommendations.append("流動性風險較高，建議增加高流動性資產比重")

        # 分析風險集中度
        max_risk_contribution = 0
        for result in detailed_results:
            if result.risk_contributions:
                max_contribution = max(result.risk_contributions.values())
                max_risk_contribution = max(max_risk_contribution, max_contribution)

        if max_risk_contribution > 0.4:  # 單一資產風險貢獻超過40%
            recommendations.append("風險集中度較高，建議分散投資以降低集中度風險")

        # 添加通用建議
        avg_loss = np.mean([r.portfolio_loss_percentage for r in detailed_results])
        if avg_loss > 0.20:  # 平均損失超過20%
            recommendations.append("建議考慮增加對沖策略以降低下行風險")
            recommendations.append("定期進行壓力測試以監控投資組合韌性")

        if not recommendations:
            recommendations.append("投資組合在壓力測試中表現良好，當前風險水平適中")

        return recommendations

    # Monte Carlo stress testing
    def run_monte_carlo_stress_test(
        self,
        portfolio_data: Dict[str, Any],
        num_simulations: Optional[int] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        運行蒙特卡羅壓力測試

        使用隨機模擬生成壓力情景，評估投資組合在極端情況下的表現
        """
        try:
            num_simulations = num_simulations or self.config['monte_carlo_simulations']

            logger.info(f"Starting Monte Carlo stress test with {num_simulations} simulations")

            portfolio_value = portfolio_data.get('current_value', 1000000)
            historical_returns = portfolio_data.get('returns', pd.Series())

            # 蒙特卡羅模擬
            simulated_losses = []
            detailed_results = []

            for i in range(num_simulations):
                # 生成隨機壓力情景
                scenario = self._generate_random_stress_scenario(i)

                # 運行壓力測試
                result = self._run_single_stress_test(portfolio_data, scenario)
                detailed_results.append(result)
                simulated_losses.append(result.portfolio_loss_percentage)

            # 計算統計結果
            simulated_losses = np.array(simulated_losses)

            mc_results = {
                'monte_carlo_var': np.percentile(simulated_losses, (1 - confidence_level) * 100),
                'monte_carlo_expected_shortfall': np.mean(simulated_losses[simulated_losses <= np.percentile(simulated_losses, (1 - confidence_level) * 100)]),
                'worst_case_loss': np.max(simulated_losses),
                'average_loss': np.mean(simulated_losses),
                'loss_distribution': {
                    'mean': np.mean(simulated_losses),
                    'std': np.std(simulated_losses),
                    'skewness': stats.skew(simulated_losses),
                    'kurtosis': stats.kurtosis(simulated_losses),
                    'percentiles': {
                        '50th': np.percentile(simulated_losses, 50),
                        '75th': np.percentile(simulated_losses, 75),
                        '90th': np.percentile(simulated_losses, 90),
                        '95th': np.percentile(simulated_losses, 95),
                        '99th': np.percentile(simulated_losses, 99)
                    }
                },
                'tail_risk_measures': {
                    'conditional_var_95': np.mean(simulated_losses[simulated_losses <= np.percentile(simulated_losses, 5)]),
                    'conditional_var_99': np.mean(simulated_losses[simulated_losses <= np.percentile(simulated_losses, 1)]),
                    'expected_shortfall_95': np.mean(simulated_losses[simulated_losses <= np.percentile(simulated_losses, 5)]),
                    'expected_shortfall_99': np.mean(simulated_losses[simulated_losses <= np.percentile(simulated_losses, 1)])
                },
                'recommendations': self._generate_monte_carlo_recommendations(simulated_losses)
            }

            logger.info("Monte Carlo stress test completed successfully")
            return mc_results

        except Exception as e:
            logger.error(f"Monte Carlo stress test failed: {e}")
            raise

    def _generate_random_stress_scenario(self, seed: int) -> StressScenario:
        """生成隨機壓力測試情景"""
        np.random.seed(seed)

        # 隨機選擇沖擊類型
        shock_types = ['equity_market', 'interest_rate', 'volatility', 'credit', 'liquidity']
        primary_shock = np.random.choice(shock_types)

        # 生成隓機市場沖擊
        market_shocks = {}
        if primary_shock == 'equity_market':
            market_shocks['equity_market'] = np.random.uniform(-0.15, -0.45)  # 15% to 45% drop
            market_shocks['volatility'] = np.random.uniform(1.5, 3.0)
        elif primary_shock == 'interest_rate':
            market_shocks['interest_rates'] = np.random.uniform(0.02, 0.04)  # 200-400 bps
            market_shocks['bond_prices'] = np.random.uniform(-0.10, -0.25)
        elif primary_shock == 'volatility':
            market_shocks['volatility'] = np.random.uniform(2.0, 4.0)
            market_shocks['equity_market'] = np.random.uniform(-0.20, -0.35)

        # 生成隨機流動性調整
        liquidity_adjustments = {
            'market_liquidity': np.random.uniform(-0.2, -0.6),
            'bid_ask_spread': np.random.uniform(1.2, 2.5)
        }

        return StressScenario(
            scenario_id=f"mc_scenario_{seed}",
            name=f"蒙特卡羅情景 {seed}",
            description=f"隨機生成的壓力測試情景 {seed}",
            stress_type=StressTestType.MONTE_CARLO,
            severity=StressSeverity.SEVERE,
            market_shocks=market_shocks,
            correlation_changes={'systematic_risk': np.random.uniform(0.5, 0.9)},
            liquidity_adjustments=liquidity_adjustments,
            duration_days=np.random.randint(20, 60),
            probability=0.01
        )

    def _generate_monte_carlo_recommendations(self, simulated_losses: np.ndarray) -> List[str]:
        """生成蒙特卡羅壓力測試建議"""
        recommendations = []

        if np.percentile(simulated_losses, 95) > 0.25:  # 95% VaR > 25%
            recommendations.append("極端損失風險較高，建議加強風險管理")

        if np.mean(simulated_losses) > 0.15:  # 平均損失 > 15%
            recommendations.append("平均損失較大，建議調整投資組合配置")

        if np.std(simulated_losses) > 0.10:  # 損失標準差 > 10%
            recommendations.append("損失波動性較大，建議增加穩定性資產")

        tail_loss = simulated_losses[simulated_losses <= np.percentile(simulated_losses, 5)]
        if len(tail_loss) > 0 and np.mean(tail_loss) > 0.30:  # 尾部損失 > 30%
            recommendations.append("尾部風險較高，建議考慮尾部對沖策略")

        if not recommendations:
            recommendations.append("蒙特卡羅壓力測試結果良好，投資組合韌性較強")

        return recommendations

# 便利函數
def quick_stress_test(
    portfolio_value: float,
    returns: pd.Series,
    scenario_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """便利函數：快速壓力測試"""
    engine = StressTestEngine()

    portfolio_data = {
        'current_value': portfolio_value,
        'returns': returns,
        'portfolio_id': 'quick_test'
    }

    report = engine.run_stress_tests(portfolio_data, scenario_ids)

    return {
        'worst_case_loss_percentage': report.worst_case_loss_percentage,
        'worst_case_scenario': report.worst_case_scenario,
        'portfolio_resilience_score': report.portfolio_resilience_score,
        'recommendations': report.recommendations
    }