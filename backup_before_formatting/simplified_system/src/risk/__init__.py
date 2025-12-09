#!/usr/bin/env python3
"""
Risk Analysis Module
風險分析模塊

Comprehensive risk analysis and monitoring tools
綜合風險分析和監控工具

This module provides institutional-grade risk analysis capabilities including:
- Advanced risk analytics engine
- Stress testing and scenario analysis
- Monte Carlo VaR calculation
- Liquidity risk analysis
- Risk monitoring and alerting
"""

from .advanced_risk_analyzer import (
    AdvancedRiskAnalyzer,
    RiskLevel,
    RiskCategory,
    RiskThreshold,
    RiskAlert,
    RiskDecomposition,
    RegulatoryReport,
    analyze_portfolio_risk
)

from .stress_test_engine import (
    StressTestEngine,
    StressTestType,
    StressSeverity,
    StressScenario,
    StressTestResult,
    StressTestReport,
    quick_stress_test
)

from .monte_carlo_var import (
    MonteCarloVaRCalculator,
    VaRConfig,
    VaRResult,
    MonteCarloResult,
    DistributionType,
    CopulaType,
    VarianceReduction,
    quick_var_calculation
)

from .liquidity_risk import (
    LiquidityRiskAnalyzer,
    LiquidityType,
    AssetLiquidityClass,
    LiquidityRiskLevel,
    LiquidityMetrics,
    FundingLiquidityMetrics,
    LiquidityRiskResult,
    LiquidityStressTestResult,
    quick_liquidity_assessment
)

# Import base risk metrics from backtest module
try:
    # Try to import from the backtest module
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backtest'))
    from risk_metrics import (
        AdvancedRiskMetrics,
        RiskMetrics,
        RiskMetricsConfig,
        calculate_risk_metrics,
        calculate_portfolio_risk
    )
except ImportError:
    # Fallback for standalone usage
    pass

__version__ = "1.0.0"
__author__ = "Claude Code Assistant"

# Module-level convenience functions
def comprehensive_risk_analysis(
    returns_data,
    portfolio_positions=None,
    market_data=None,
    funding_data=None,
    config=None
):
    """
    便利函數：綜合風險分析

    整合所有風險分析工具，提供完整的風險評估報告

    Args:
        returns_data: 回報率數據
        portfolio_positions: 投資組合持倉
        market_data: 市場數據
        funding_data: 融資數據
        config: 配置參數

    Returns:
        Dict: 綜合風險分析報告
    """
    try:
        results = {}

        # 1. 基礎風險指標
        if hasattr(calculate_risk_metrics, '__call__'):
            basic_risk = calculate_risk_metrics(returns_data)
            results['basic_risk_metrics'] = basic_risk.to_dict() if hasattr(basic_risk, 'to_dict') else basic_risk

        # 2. 高級風險分析
        advanced_analyzer = AdvancedRiskAnalyzer(config)
        if portfolio_positions is not None:
            advanced_results = advanced_analyzer.analyze_comprehensive_risk(
                returns_data, portfolio_positions, market_data
            )
            results['advanced_risk_analysis'] = advanced_results

        # 3. 壓力測試
        stress_engine = StressTestEngine()
        if portfolio_positions is not None:
            portfolio_data = {
                'current_value': portfolio_positions.get('market_value', pd.Series()).sum(),
                'returns': returns_data,
                'positions': portfolio_positions
            }
            stress_results = stress_engine.run_stress_tests(portfolio_data)
            results['stress_test_results'] = stress_results

        # 4. Monte Carlo VaR
        mc_calculator = MonteCarloVaRCalculator()
        mc_results = mc_calculator.calculate_var(returns_data, portfolio_positions.get('market_value', pd.Series()).sum())
        results['monte_carlo_var'] = mc_calculator.generate_var_report(mc_results)

        # 5. 流動性風險分析
        if portfolio_positions is not None and market_data is not None:
            liquidity_analyzer = LiquidityRiskAnalyzer()
            liquidity_results = liquidity_analyzer.analyze_liquidity_risk(
                portfolio_positions, market_data, funding_data
            )
            results['liquidity_risk_analysis'] = liquidity_results

            # 流動性壓力測試
            liquidity_stress = liquidity_analyzer.run_liquidity_stress_test(
                portfolio_positions, market_data, funding_data
            )
            results['liquidity_stress_test'] = liquidity_stress

        # 生成綜合報告
        results['summary'] = {
            'analysis_timestamp': returns_data.index[-1].isoformat() if hasattr(returns_data, 'index') else None,
            'data_points': len(returns_data),
            'risk_modules_completed': list(results.keys()),
            'overall_risk_assessment': _assess_overall_risk(results)
        }

        return results

    except Exception as e:
        return {
            'error': f'Comprehensive risk analysis failed: {str(e)}',
            'partial_results': results if 'results' in locals() else {}
        }

def _assess_overall_risk(analysis_results):
    """評估整體風險水平"""
    try:
        risk_scores = []

        # 從不同模塊提取風險評分
        if 'advanced_risk_analysis' in analysis_results:
            overall_risk = analysis_results['advanced_risk_analysis'].get('overall_risk_level', 'MEDIUM')
            risk_scores.append(_convert_risk_level_to_score(overall_risk))

        if 'stress_test_results' in analysis_results:
            worst_loss = analysis_results['stress_test_results'].worst_case_loss_percentage
            risk_scores.append(min(100, worst_loss * 2))

        if 'monte_carlo_var' in analysis_results:
            var_99 = analysis_results['monte_carlo_var']['risk_metrics'].get('var_99', 0.02)
            risk_scores.append(min(100, var_99 * 500))

        if 'liquidity_risk_analysis' in analysis_results:
            liquidity_risk = analysis_results['liquidity_risk_analysis'].overall_liquidity_risk
            risk_scores.append(liquidity_risk)

        if risk_scores:
            avg_risk_score = sum(risk_scores) / len(risk_scores)
            return {
                'overall_score': avg_risk_score,
                'risk_level': _convert_score_to_risk_level(avg_risk_score),
                'confidence': len(risk_scores) / 4.0  # 4是最大模塊數
            }
        else:
            return {
                'overall_score': 50,
                'risk_level': 'MEDIUM',
                'confidence': 0.0
            }

    except Exception:
        return {
            'overall_score': 50,
            'risk_level': 'MEDIUM',
            'confidence': 0.0
        }

def _convert_risk_level_to_score(risk_level):
    """將風險等級轉換為評分"""
    level_scores = {
        'LOW': 25,
        'MEDIUM': 50,
        'HIGH': 75,
        'CRITICAL': 100,
        '極低': 10,
        '低': 30,
        '中等': 60,
        '高': 80,
        '極高': 95
    }
    return level_scores.get(risk_level.upper(), 50)

def _convert_score_to_risk_level(score):
    """將評分轉換為風險等級"""
    if score < 30:
        return 'LOW'
    elif score < 60:
        return 'MEDIUM'
    elif score < 80:
        return 'HIGH'
    else:
        return 'CRITICAL'

# Export all main classes and functions
__all__ = [
    # Advanced Risk Analytics
    'AdvancedRiskAnalyzer',
    'RiskLevel',
    'RiskCategory',
    'RiskThreshold',
    'RiskAlert',
    'RiskDecomposition',
    'RegulatoryReport',

    # Stress Testing
    'StressTestEngine',
    'StressTestType',
    'StressSeverity',
    'StressScenario',
    'StressTestResult',
    'StressTestReport',

    # Monte Carlo VaR
    'MonteCarloVaRCalculator',
    'VaRConfig',
    'VaRResult',
    'MonteCarloResult',
    'DistributionType',
    'CopulaType',
    'VarianceReduction',

    # Liquidity Risk
    'LiquidityRiskAnalyzer',
    'LiquidityType',
    'AssetLiquidityClass',
    'LiquidityRiskLevel',
    'LiquidityMetrics',
    'FundingLiquidityMetrics',
    'LiquidityRiskResult',
    'LiquidityStressTestResult',

    # Base Risk Metrics
    'AdvancedRiskMetrics',
    'RiskMetrics',
    'RiskMetricsConfig',

    # Convenience Functions
    'comprehensive_risk_analysis',
    'analyze_portfolio_risk',
    'quick_stress_test',
    'quick_var_calculation',
    'quick_liquidity_assessment',
    'calculate_risk_metrics',
    'calculate_portfolio_risk'
]

print(f"Risk Analysis Module v{__version__} loaded successfully")
print("Available components: Advanced Risk Analytics, Stress Testing, Monte Carlo VaR, Liquidity Risk Analysis")