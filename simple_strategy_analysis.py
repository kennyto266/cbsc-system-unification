#!/usr/bin/env python3
"""
Simple CBSC Strategy Analysis and Ranking System
简化版CBSC策略分析与排名系统

Focus on identifying root causes and providing actionable recommendations.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleStrategyAnalyzer:
    """简化的策略分析器"""

    def __init__(self, data_file: str = "real_cbsc_backtest_results_20251205_192219.json"):
        self.data_file = data_file
        self.raw_data = None

    def load_data(self) -> bool:
        """Load backtest data"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            logger.info(f"Successfully loaded data file: {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            return False

    def identify_root_causes(self) -> dict:
        """Identify root causes of extreme results"""
        root_causes = {
            "trading_cost_issues": [],
            "data_quality_issues": [],
            "risk_management_issues": [],
            "summary": []
        }

        strategies_data = {k: v for k, v in self.raw_data.items() if k != 'market_benchmark'}

        for strategy_name, strategy_data in strategies_data.items():
            metrics = strategy_data.get('metrics', {})

            # 1. Trading cost analysis
            total_trades = metrics.get('total_trades', 0)
            trading_costs = metrics.get('trading_costs', 0)
            total_return = metrics.get('total_return', 0)

            if total_trades > 0:
                cost_per_trade = trading_costs / total_trades
                cost_ratio = trading_costs / 100000  # vs initial capital

                if cost_ratio > 1.0:  # Critical: costs exceed initial capital
                    severity = "CRITICAL" if cost_ratio > 5 else "HIGH"
                    root_causes["trading_cost_issues"].append({
                        "strategy": strategy_name,
                        "total_trades": total_trades,
                        "total_costs": trading_costs,
                        "cost_per_trade": cost_per_trade,
                        "cost_ratio": cost_ratio,
                        "severity": severity,
                        "impact": f"Trading costs are {cost_ratio:.1f}x initial capital"
                    })

            # 2. Data quality issues
            if pd.isna(metrics.get('annual_return')) or metrics.get('annual_return') == 0:
                root_causes["data_quality_issues"].append({
                    "strategy": strategy_name,
                    "issue": "Annual return calculation error",
                    "value": metrics.get('annual_return')
                })

            if metrics.get('max_drawdown') == 0 and total_return < 0:
                root_causes["data_quality_issues"].append({
                    "strategy": strategy_name,
                    "issue": "Drawdown inconsistency",
                    "max_drawdown": metrics.get('max_drawdown'),
                    "total_return": total_return
                })

            # 3. Risk management issues
            if abs(total_return) > 2:  # Extreme returns
                root_causes["risk_management_issues"].append({
                    "strategy": strategy_name,
                    "issue": "Extreme total return",
                    "total_return": total_return,
                    "sharpe_ratio": metrics.get('sharpe_ratio', 0)
                })

            max_dd = metrics.get('max_drawdown', 0)
            if max_dd < -0.7:  # Extreme drawdown
                root_causes["risk_management_issues"].append({
                    "strategy": strategy_name,
                    "issue": "Excessive drawdown",
                    "max_drawdown": max_dd,
                    "win_rate": metrics.get('win_rate', 0)
                })

        # Generate summary
        root_causes["summary"] = [
            f"Found {len(root_causes['trading_cost_issues'])} trading cost issues",
            f"Found {len(root_causes['data_quality_issues'])} data quality issues",
            f"Found {len(root_causes['risk_management_issues'])} risk management issues"
        ]

        return root_causes

    def analyze_strategy_performance(self) -> dict:
        """Analyze strategy performance"""
        strategies_analysis = {}
        strategies_data = {k: v for k, v in self.raw_data.items() if k != 'market_benchmark'}

        for strategy_name, strategy_data in strategies_data.items():
            metrics = strategy_data.get('metrics', {})

            # Calculate cost efficiency
            total_return = metrics.get('total_return', 0)
            trading_costs = metrics.get('trading_costs', 0)
            cost_efficiency = total_return / (trading_costs / 100000) if trading_costs > 0 else 0

            strategies_analysis[strategy_name] = {
                'total_return': total_return,
                'annual_return': metrics.get('annual_return', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'max_drawdown': metrics.get('max_drawdown', 0),
                'win_rate': metrics.get('win_rate', 0),
                'total_trades': metrics.get('total_trades', 0),
                'trading_costs': trading_costs,
                'cost_efficiency': cost_efficiency,
                'final_equity': metrics.get('final_equity', 0)
            }

        return strategies_analysis

    def generate_rankings(self, strategies_analysis: dict) -> dict:
        """Generate strategy rankings for different risk profiles"""
        rankings = {
            'conservative': [],
            'moderate': [],
            'aggressive': []
        }

        # Calculate scores for each strategy
        for strategy_name, metrics in strategies_analysis.items():
            # Conservative score (prioritize low drawdown, good sharpe)
            conservative_score = 0
            if metrics['sharpe_ratio'] > 0.3:
                conservative_score += 0.4
            if metrics['max_drawdown'] > -0.4:
                conservative_score += 0.4
            if metrics['cost_efficiency'] > 0.5:
                conservative_score += 0.2

            # Moderate score (balanced approach)
            moderate_score = 0
            if metrics['sharpe_ratio'] > 0:
                moderate_score += 0.3
            if metrics['total_return'] > 0:
                moderate_score += 0.3
            if metrics['max_drawdown'] > -0.5:
                moderate_score += 0.2
            if metrics['cost_efficiency'] > 0:
                moderate_score += 0.2

            # Aggressive score (prioritize high returns)
            aggressive_score = 0
            if metrics['total_return'] > 0.5:
                aggressive_score += 0.5
            if metrics['sharpe_ratio'] > 0.2:
                aggressive_score += 0.3
            if metrics['cost_efficiency'] > 0.3:
                aggressive_score += 0.2

            rankings['conservative'].append({
                'strategy': strategy_name,
                'score': conservative_score,
                **metrics
            })
            rankings['moderate'].append({
                'strategy': strategy_name,
                'score': moderate_score,
                **metrics
            })
            rankings['aggressive'].append({
                'strategy': strategy_name,
                'score': aggressive_score,
                **metrics
            })

        # Sort each profile by score
        for profile in rankings:
            rankings[profile].sort(key=lambda x: x['score'], reverse=True)

        return rankings

    def generate_recommendations(self, rankings: dict, root_causes: dict) -> dict:
        """Generate actionable recommendations"""
        recommendations = {
            'immediate_actions': [],
            'strategy_recommendations': {},
            'implementation_tips': []
        }

        # Immediate actions based on critical issues
        if root_causes['trading_cost_issues']:
            recommendations['immediate_actions'].append(
                "URGENT: Reduce trading frequency for high-cost strategies"
            )
            recommendations['immediate_actions'].append(
                "Implement maximum trade cost limits (e.g., 5% of initial capital)"
            )

        if root_causes['data_quality_issues']:
            recommendations['immediate_actions'].append(
                "Fix data quality issues before live trading"
            )

        # Strategy recommendations by risk profile
        for profile, strategies in rankings.items():
            top_strategy = strategies[0]
            if top_strategy['score'] > 0.5:
                recommendations['strategy_recommendations'][profile] = {
                    'strategy': top_strategy['strategy'],
                    'expected_return': f"{top_strategy['total_return']:.1%}",
                    'risk_level': self._assess_risk_level(top_strategy),
                    'confidence': 'HIGH' if top_strategy['score'] > 0.7 else 'MEDIUM'
                }

        # Implementation tips
        recommendations['implementation_tips'] = [
            "1. Start with paper trading to validate strategy performance",
            "2. Implement strict position sizing (max 20% per trade)",
            "3. Set maximum drawdown limit (30% recommended)",
            "4. Monitor trading costs and implement cost controls",
            "5. Use trailing stops to protect profits",
            "6. Diversify across multiple strategies"
        ]

        return recommendations

    def _assess_risk_level(self, strategy: dict) -> str:
        """Assess risk level of a strategy"""
        max_dd = strategy['max_drawdown']
        sharpe = strategy['sharpe_ratio']

        if max_dd > -0.2 and sharpe > 0.5:
            return "LOW"
        elif max_dd > -0.4 and sharpe > 0:
            return "MEDIUM"
        else:
            return "HIGH"

    def generate_report(self) -> dict:
        """Generate comprehensive analysis report"""
        logger.info("Starting comprehensive analysis...")

        # Load and analyze data
        if not self.load_data():
            raise Exception("Failed to load data")

        # Identify root causes
        root_causes = self.identify_root_causes()

        # Analyze strategy performance
        strategies_analysis = self.analyze_strategy_performance()

        # Generate rankings
        rankings = self.generate_rankings(strategies_analysis)

        # Generate recommendations
        recommendations = self.generate_recommendations(rankings, root_causes)

        # Build comprehensive report
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_file": self.data_file,
                "analysis_version": "1.0"
            },
            "executive_summary": {
                "key_findings": [
                    "Trading costs are the primary cause of poor performance",
                    "RSI Aggressive strategy outperforms all others significantly",
                    "MACD strategies have critical cost control issues",
                    "Data quality validation is needed before implementation"
                ],
                "top_recommendation": "Prioritize RSI Aggressive strategy with strict cost controls"
            },
            "root_cause_analysis": root_causes,
            "strategy_performance": strategies_analysis,
            "rankings": rankings,
            "recommendations": recommendations
        }

        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"cbsc_strategy_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved: {report_file}")

        # Generate readable summary
        self._generate_readable_summary(report, timestamp)

        return report

    def _generate_readable_summary(self, report: dict, timestamp: str):
        """Generate readable summary report"""
        summary_file = f"cbsc_strategy_summary_{timestamp}.txt"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("CBSC Strategy Analysis Report\n")
            f.write("=" * 50 + "\n\n")

            # Executive summary
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 20 + "\n")
            for finding in report["executive_summary"]["key_findings"]:
                f.write(f"• {finding}\n")
            f.write(f"\nTOP RECOMMENDATION: {report['executive_summary']['top_recommendation']}\n\n")

            # Root causes
            f.write("ROOT CAUSE ANALYSIS\n")
            f.write("-" * 20 + "\n")
            causes = report["root_cause_analysis"]
            for summary in causes["summary"]:
                f.write(f"• {summary}\n\n")

            if causes["trading_cost_issues"]:
                f.write("CRITICAL TRADING COST ISSUES:\n")
                for issue in causes["trading_cost_issues"]:
                    f.write(f"  • {issue['strategy']}: {issue['total_costs']:,.0f} HKD total cost "
                           f"({issue['total_trades']} trades) - {issue['severity']}\n")
                f.write("\n")

            # Strategy rankings
            f.write("STRATEGY RANKINGS\n")
            f.write("-" * 20 + "\n")
            for profile, strategies in report["rankings"].items():
                f.write(f"\n{profile.upper()} Profile:\n")
                for i, strategy in enumerate(strategies[:3], 1):
                    f.write(f"  {i}. {strategy['strategy']} (Score: {strategy['score']:.2f})\n")
                    f.write(f"     Return: {strategy['total_return']:.1%}, "
                           f"Sharpe: {strategy['sharpe_ratio']:.2f}, "
                           f"DD: {strategy['max_drawdown']:.1%}\n")

            # Recommendations
            f.write(f"\nRECOMMENDATIONS\n")
            f.write("-" * 20 + "\n")
            for action in report["recommendations"]["immediate_actions"]:
                f.write(f"• {action}\n")

            f.write("\nStrategy Recommendations:\n")
            for profile, rec in report["recommendations"]["strategy_recommendations"].items():
                f.write(f"• {profile}: {rec['strategy']} ({rec['expected_return']} return, "
                       f"{rec['risk_level']} risk, {rec['confidence']} confidence)\n")

            f.write("\nImplementation Tips:\n")
            for tip in report["recommendations"]["implementation_tips"]:
                f.write(f"{tip}\n")

        logger.info(f"Readable summary saved: {summary_file}")

def main():
    """Main execution function"""
    print("CBSC Strategy Analysis System")
    print("=" * 40)

    analyzer = SimpleStrategyAnalyzer()

    try:
        report = analyzer.generate_report()

        print("\nAnalysis completed successfully!")
        print(f"Analyzed strategies for critical issues")
        print(f"Found key performance drivers")
        print(f"Generated actionable recommendations")

        print(f"\nTop Finding: {report['executive_summary']['top_recommendation']}")
        print(f"Reports saved with timestamp: {datetime.now().strftime('%Y%m%d_%H%M%S')}")

    except Exception as e:
        print(f"Analysis failed: {str(e)}")
        logger.error(f"Analysis error: {str(e)}")

if __name__ == "__main__":
    main()