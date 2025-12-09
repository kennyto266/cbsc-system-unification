#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 4: 結果分析和可視化系統
實現策略回測結果的深度分析和交互式可視化
"""

import pandas as pd
import numpy as np
import json
import os
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 設置中文字體支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft JhengHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

@dataclass
class StrategyStatistics:
    """策略統計信息"""
    total_strategies: int
    successful_strategies: int
    failed_strategies: int
    success_rate: float

    # 性能指標
    avg_sharpe: float
    max_sharpe: float
    min_sharpe: float
    median_sharpe: float

    # 回報指標
    avg_return: float
    max_return: float
    min_return: float
    median_return: float

    # 風險指標
    avg_max_drawdown: float
    worst_max_drawdown: float
    best_max_drawdown: float

    # 交易頻率
    avg_trade_frequency: float
    max_trade_frequency: float
    min_trade_frequency: float

@dataclass
class ParameterEfficiency:
    """參數效率分析"""
    parameter_name: str
    efficiency_score: float
    optimal_range: Tuple[float, float]
    correlation_with_sharpe: float
    total_combinations_tested: int

class ResultsAnalyzer:
    """結果分析器 - 深度分析策略回測結果"""

    def __init__(self):
        self.raw_results = []
        self.statistics = None
        self.parameter_efficiency = {}
        self.best_strategies = []
        self.worst_strategies = []

    def load_results(self, file_path: str = None) -> bool:
        """加載回測結果"""
        try:
            if file_path and os.path.exists(file_path):
                # 從文件加載
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 適配不同的結果文件格式
                if 'top_strategies' in data:
                    # massive_nonprice_ta 格式
                    self.raw_results = self._convert_massive_format(data)
                elif 'results' in data:
                    # 標準格式
                    self.raw_results = data.get('results', [])
                else:
                    # 直接是結果列表
                    self.raw_results = data if isinstance(data, list) else []
            else:
                # 查找最新的結果文件
                latest_file = self._find_latest_results_file()
                if latest_file:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'top_strategies' in data:
                            self.raw_results = self._convert_massive_format(data)
                        elif 'results' in data:
                            self.raw_results = data.get('results', [])
                        else:
                            self.raw_results = data if isinstance(data, list) else []
                else:
                    print("未找到回測結果文件")
                    return False

            print(f"已加載 {len(self.raw_results)} 個策略結果")
            return True

        except Exception as e:
            print(f"加載結果失敗: {str(e)}")
            return False

    def _convert_massive_format(self, data: Dict) -> List[Dict]:
        """轉換massive_nonprice_ta格式為標準格式"""
        results = []

        # 獲取所有策略，優先使用完整結果列表
        if 'results' in data:
            all_strategies = data.get('results', [])
        elif 'all_strategies' in data:
            all_strategies = data.get('all_strategies', [])
        else:
            all_strategies = data.get('top_strategies', [])

        print(f"從結果文件中找到 {len(all_strategies)} 個策略")

        for strategy in all_strategies:
            # 轉換格式
            converted_strategy = {
                'success': strategy.get('success', True),
                'strategy_type': strategy.get('indicator_type', 'Unknown'),
                'data_source': strategy.get('data_source', 'Unknown'),
                'sharpe_ratio': strategy.get('sharpe_ratio', 0),
                'total_return': strategy.get('total_return', 0),
                'max_drawdown': strategy.get('max_drawdown', 0),
                'volatility': strategy.get('volatility', 0),
                'trade_count': strategy.get('trade_count', 0),
                'quality_score': strategy.get('quality_score', 0),
                'parameters': self._extract_parameters(strategy),
                'strategy_id': strategy.get('strategy_id', 'Unknown')
            }

            # 計算交易頻率 (如果沒有直接提供)
            if 'trade_frequency' not in converted_strategy:
                # 根據交易數量和持倉天數估算頻率
                trade_count = strategy.get('trade_count', 0)
                data_points = data.get('summary', {}).get('price_data_points', 245)
                if trade_count > 0 and data_points > 0:
                    converted_strategy['trade_frequency'] = trade_count / data_points * 252  # 年化頻率
                else:
                    converted_strategy['trade_frequency'] = 0

            results.append(converted_strategy)

        return results

    def _extract_parameters(self, strategy: Dict) -> Dict:
        """從策略中提取參數"""
        params = strategy.get('params', [])
        indicator_type = strategy.get('indicator_type', '')

        if indicator_type == 'RSI' and len(params) >= 1:
            return {'rsi_period': params[0]}
        elif indicator_type == 'MACD' and len(params) >= 3:
            return {'macd_fast': params[0], 'macd_slow': params[1], 'macd_signal': params[2]}
        elif indicator_type == 'KDJ' and len(params) >= 2:
            return {'k_period': params[0], 'd_period': params[1]}
        elif indicator_type == 'BOLLINGER_BANDS' and len(params) >= 2:
            return {'period': params[0], 'std_dev': params[1]}
        else:
            return {'params': params}

    def _find_latest_results_file(self) -> Optional[str]:
        """查找最新的結果文件"""
        import glob

        # 查找可能的结果文件
        patterns = [
            "massive_nonprice_ta_results_*.json",
            "phase3_optimization_results_*.json",
            "relaxed_optimization_results_*.json",
            "optimization_results_*.json"
        ]

        latest_file = None
        latest_time = 0

        for pattern in patterns:
            files = glob.glob(pattern)
            for file in files:
                file_time = os.path.getctime(file)
                if file_time > latest_time:
                    latest_time = file_time
                    latest_file = file

        return latest_file

    def analyze_statistics(self) -> StrategyStatistics:
        """計算基本統計信息"""
        if not self.raw_results:
            raise ValueError("沒有可分析的結果數據")

        # 過滤成功的結果
        successful_results = [r for r in self.raw_results if r.get('success', False)]
        failed_results = [r for r in self.raw_results if not r.get('success', False)]

        if not successful_results:
            print("警告: 沒有成功的策略結果")
            return None

        # 提取數值
        sharpe_values = [r.get('sharpe_ratio', 0) for r in successful_results if r.get('sharpe_ratio') is not None]
        return_values = [r.get('total_return', 0) for r in successful_results if r.get('total_return') is not None]
        drawdown_values = [r.get('max_drawdown', 0) for r in successful_results if r.get('max_drawdown') is not None]
        frequency_values = [r.get('trade_frequency', 0) for r in successful_results if r.get('trade_frequency') is not None]

        # 創建統計對象
        self.statistics = StrategyStatistics(
            total_strategies=len(self.raw_results),
            successful_strategies=len(successful_results),
            failed_strategies=len(failed_results),
            success_rate=len(successful_results) / len(self.raw_results),

            # Sharpe比率統計
            avg_sharpe=np.mean(sharpe_values) if sharpe_values else 0,
            max_sharpe=np.max(sharpe_values) if sharpe_values else 0,
            min_sharpe=np.min(sharpe_values) if sharpe_values else 0,
            median_sharpe=np.median(sharpe_values) if sharpe_values else 0,

            # 回報統計
            avg_return=np.mean(return_values) if return_values else 0,
            max_return=np.max(return_values) if return_values else 0,
            min_return=np.min(return_values) if return_values else 0,
            median_return=np.median(return_values) if return_values else 0,

            # 回撤統計
            avg_max_drawdown=np.mean(drawdown_values) if drawdown_values else 0,
            worst_max_drawdown=np.min(drawdown_values) if drawdown_values else 0,
            best_max_drawdown=np.max(drawdown_values) if drawdown_values else 0,

            # 交易頻率統計
            avg_trade_frequency=np.mean(frequency_values) if frequency_values else 0,
            max_trade_frequency=np.max(frequency_values) if frequency_values else 0,
            min_trade_frequency=np.min(frequency_values) if frequency_values else 0
        )

        return self.statistics

    def find_best_strategies(self, top_n: int = 10) -> List[Dict]:
        """找到表現最好的策略"""
        successful_results = [r for r in self.raw_results if r.get('success', False)]

        # 按Sharpe比率排序
        sorted_results = sorted(
            successful_results,
            key=lambda x: x.get('sharpe_ratio', 0),
            reverse=True
        )

        self.best_strategies = sorted_results[:top_n]
        return self.best_strategies

    def find_worst_strategies(self, bottom_n: int = 10) -> List[Dict]:
        """找到表現最差的策略"""
        successful_results = [r for r in self.raw_results if r.get('success', False)]

        # 按Sharpe比率排序
        sorted_results = sorted(
            successful_results,
            key=lambda x: x.get('sharpe_ratio', 0)
        )

        self.worst_strategies = sorted_results[:bottom_n]
        return self.worst_strategies

    def analyze_parameter_efficiency(self) -> Dict[str, ParameterEfficiency]:
        """分析參數效率"""
        if not self.raw_results:
            return {}

        successful_results = [r for r in self.raw_results if r.get('success', False)]

        # 分析各個參數的效率
        parameter_analysis = {}

        # 提取所有參數名
        all_params = set()
        for result in successful_results:
            params = result.get('parameters', {})
            if params:  # 確保parameters不為空
                all_params.update(params.keys())

        for param_name in all_params:
            param_values = []
            sharpe_values = []

            for result in successful_results:
                params = result.get('parameters', {})
                if params and param_name in params:  # 雙重檢查
                    param_val = params[param_name]
                    if param_val is not None:  # 確保參數值不為None
                        param_values.append(param_val)
                        sharpe_values.append(result.get('sharpe_ratio', 0))

            if len(param_values) > 5 and len(param_values) == len(sharpe_values):  # 確保數據長度一致
                try:
                    # 計算相關性
                    if len(param_values) > 1:
                        param_array = np.array(param_values, dtype=float)
                        sharpe_array = np.array(sharpe_values, dtype=float)

                        # 檢查數組有效性
                        if np.isfinite(param_array).all() and np.isfinite(sharpe_array).all():
                            if np.std(param_array) > 0 and np.std(sharpe_array) > 0:  # 確保有變異
                                correlation = np.corrcoef(param_array, sharpe_array)[0, 1]
                            else:
                                correlation = 0.0
                        else:
                            correlation = 0.0
                    else:
                        correlation = 0.0

                    # 找到最佳範圍
                    best_sharpe_idx = np.argmax(sharpe_values)
                    optimal_value = param_values[best_sharpe_idx]

                    # 計算效率分數 (基於相關性和最佳表現)
                    max_sharpe = max(sharpe_values) if sharpe_values else 0
                    efficiency_score = abs(correlation) * max_sharpe

                    parameter_analysis[param_name] = ParameterEfficiency(
                        parameter_name=param_name,
                        efficiency_score=efficiency_score,
                        optimal_range=(float(optimal_value) * 0.9, float(optimal_value) * 1.1),  # 10%範圍
                        correlation_with_sharpe=correlation,
                        total_combinations_tested=len(param_values)
                    )
                except Exception as e:
                    print(f"參數 {param_name} 分析失敗: {str(e)}")
                    continue

        self.parameter_efficiency = parameter_analysis
        return parameter_analysis

class InteractiveDashboard:
    """交互式可視化儀表板"""

    def __init__(self, analyzer: ResultsAnalyzer):
        self.analyzer = analyzer
        self.figures = {}

    def create_performance_distribution(self) -> go.Figure:
        """創建性能分布圖"""
        if not self.analyzer.raw_results:
            return None

        successful_results = [r for r in self.analyzer.raw_results if r.get('success', False)]

        sharpe_values = [r.get('sharpe_ratio', 0) for r in successful_results if r.get('sharpe_ratio') is not None]
        return_values = [r.get('total_return', 0) for r in successful_results if r.get('total_return') is not None]

        # 創建子圖
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Sharpe Ratio Distribution', 'Total Return Distribution',
                          'Sharpe vs Return Scatter', 'Max Drawdown Distribution'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # Sharpe分布
        fig.add_trace(
            go.Histogram(x=sharpe_values, name='Sharpe Ratio', nbinsx=50),
            row=1, col=1
        )

        # 回報分布
        fig.add_trace(
            go.Histogram(x=[r*100 for r in return_values], name='Total Return (%)', nbinsx=50),
            row=1, col=2
        )

        # Sharpe vs Return散點圖
        fig.add_trace(
            go.Scatter(
                x=sharpe_values,
                y=[r*100 for r in return_values],
                mode='markers',
                name='Strategies',
                text=[f"Strategy: {r.get('strategy_type', 'Unknown')}" for r in successful_results],
                hovertemplate='Sharpe: %{x:.3f}<br>Return: %{y:.2f}%<br>%{text}'
            ),
            row=2, col=1
        )

        # 最大回撤分布
        drawdown_values = [r.get('max_drawdown', 0) for r in successful_results if r.get('max_drawdown') is not None]
        fig.add_trace(
            go.Histogram(x=[dd*100 for dd in drawdown_values], name='Max Drawdown (%)', nbinsx=50),
            row=2, col=2
        )

        fig.update_layout(
            title="Strategy Performance Analysis Dashboard",
            height=800,
            showlegend=True
        )

        self.figures['performance_distribution'] = fig
        return fig

    def create_parameter_analysis(self) -> go.Figure:
        """創建參數分析圖"""
        if not self.analyzer.parameter_efficiency:
            return None

        params = list(self.analyzer.parameter_efficiency.keys())
        efficiency_scores = [pe.efficiency_score for pe in self.analyzer.parameter_efficiency.values()]
        correlations = [pe.correlation_with_sharpe for pe in self.analyzer.parameter_efficiency.values()]

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Parameter Efficiency Scores', 'Parameter Correlation with Sharpe'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )

        # 效率分數條形圖
        fig.add_trace(
            go.Bar(x=params, y=efficiency_scores, name='Efficiency Score'),
            row=1, col=1
        )

        # 相關性條形圖
        fig.add_trace(
            go.Bar(x=params, y=correlations, name='Correlation with Sharpe'),
            row=1, col=2
        )

        fig.update_layout(
            title="Parameter Efficiency Analysis",
            height=500,
            showlegend=True
        )

        self.figures['parameter_analysis'] = fig
        return fig

    def create_best_strategies_table(self) -> go.Figure:
        """創建最佳策略表格"""
        if not self.analyzer.best_strategies:
            return None

        # 準備表格數據
        strategy_data = []
        for i, strategy in enumerate(self.analyzer.best_strategies[:10], 1):
            strategy_data.append([
                i,
                strategy.get('strategy_type', 'Unknown'),
                f"{strategy.get('sharpe_ratio', 0):.3f}",
                f"{strategy.get('total_return', 0):.2%}",
                f"{strategy.get('max_drawdown', 0):.2%}",
                f"{strategy.get('trade_frequency', 0):.2%}",
                str(strategy.get('parameters', {}))
            ])

        # 創建表格
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=['Rank', 'Strategy', 'Sharpe', 'Return', 'Max DD', 'Freq', 'Parameters'],
                fill_color='lightblue',
                align='left'
            ),
            cells=dict(
                values=list(zip(*strategy_data)) if strategy_data else [],
                fill_color='lightgrey',
                align='left'
            )
        )])

        fig.update_layout(
            title="Top 10 Best Performing Strategies",
            height=600
        )

        self.figures['best_strategies'] = fig
        return fig

class ReportGenerator:
    """自動報告生成器"""

    def __init__(self, analyzer: ResultsAnalyzer, dashboard: InteractiveDashboard):
        self.analyzer = analyzer
        self.dashboard = dashboard

    def generate_comprehensive_report(self, output_path: str = None) -> str:
        """生成綜合分析報告"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"comprehensive_analysis_report_{timestamp}.html"

        # 生成報告內容
        html_content = self._generate_html_report()

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"綜合分析報告已保存至: {output_path}")
        return output_path

    def _generate_html_report(self) -> str:
        """生成HTML格式的報告"""
        stats = self.analyzer.statistics

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>策略回測綜合分析報告</title>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: 'Microsoft JhengHei', sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 10px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
                .metric-label {{ font-size: 14px; color: #7f8c8d; }}
                .success {{ color: #27ae60; }}
                .warning {{ color: #f39c12; }}
                .danger {{ color: #e74c3c; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>策略回測綜合分析報告</h1>
                <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="section">
                <h2>總體統計摘要</h2>
                <div class="metric">
                    <div class="metric-value {'success' if stats.success_rate > 0.8 else 'warning' if stats.success_rate > 0.6 else 'danger'}">{stats.success_rate:.1%}</div>
                    <div class="metric-label">成功率</div>
                </div>
                <div class="metric">
                    <div class="metric-value {stats.successful_strategies}</div>
                    <div class="metric-label">成功策略數</div>
                </div>
                <div class="metric">
                    <div class="metric-value {stats.total_strategies}</div>
                    <div class="metric-label">總策略數</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'success' if stats.max_sharpe > 2.0 else 'warning' if stats.max_sharpe > 1.0 else 'danger'}">{stats.max_sharpe:.3f}</div>
                    <div class="metric-label">最高Sharpe</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'success' if stats.avg_sharpe > 1.0 else 'warning' if stats.avg_sharpe > 0.5 else 'danger'}">{stats.avg_sharpe:.3f}</div>
                    <div class="metric-label">平均Sharpe</div>
                </div>
                <div class="metric">
                    <div class="metric-value {stats.max_return:.1%}</div>
                    <div class="metric-label">最高回報</div>
                </div>
                <div class="metric">
                    <div class="metric-value {stats.avg_return:.1%}</div>
                    <div class="metric-label">平均回報</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'danger' if stats.worst_max_drawdown < -0.2 else 'warning' if stats.worst_max_drawdown < -0.1 else 'success'}">{stats.worst_max_drawdown:.1%}</div>
                    <div class="metric-label">最差回撤</div>
                </div>
            </div>

            <div class="section">
                <h2>性能分布分析</h2>
                <div id="performance-distribution"></div>
                <script>
                    {self._get_plotly_json('performance_distribution')}
                </script>
            </div>

            <div class="section">
                <h2>參數效率分析</h2>
                <div id="parameter-analysis"></div>
                <script>
                    {self._get_plotly_json('parameter_analysis')}
                </script>
            </div>

            <div class="section">
                <h2>頂級策略表現</h2>
                <div id="best-strategies"></div>
                <script>
                    {self._get_plotly_json('best_strategies')}
                </script>
            </div>

            <div class="section">
                <h2>參數效率詳細分析</h2>
                {self._generate_parameter_efficiency_table()}
            </div>

            <div class="section">
                <h2>建議與結論</h2>
                {self._generate_recommendations()}
            </div>
        </body>
        </html>
        """

        return html

    def _get_plotly_json(self, figure_name: str) -> str:
        """獲取Plotly圖表的JSON"""
        if figure_name in self.dashboard.figures:
            fig = self.dashboard.figures[figure_name]
            return f"Plotly.newPlot('{figure_name}', {fig.to_json()});"
        return ""

    def _generate_parameter_efficiency_table(self) -> str:
        """生成參數效率表格"""
        if not self.analyzer.parameter_efficiency:
            return "<p>無參數效率數據</p>"

        table_html = """
        <table>
            <tr>
                <th>參數名稱</th>
                <th>效率分數</th>
                <th>與Sharpe相關性</th>
                <th>最佳範圍</th>
                <th>測試組合數</th>
            </tr>
        """

        for param_name, efficiency in self.analyzer.parameter_efficiency.items():
            table_html += f"""
            <tr>
                <td>{param_name}</td>
                <td>{efficiency.efficiency_score:.4f}</td>
                <td>{efficiency.correlation_with_sharpe:.4f}</td>
                <td>({efficiency.optimal_range[0]:.2f}, {efficiency.optimal_range[1]:.2f})</td>
                <td>{efficiency.total_combinations_tested}</td>
            </tr>
            """

        table_html += "</table>"
        return table_html

    def _generate_recommendations(self) -> str:
        """生成建議和結論"""
        stats = self.analyzer.statistics
        recommendations = []

        # 基於成功率給出建議
        if stats.success_rate < 0.6:
            recommendations.append("成功率偏低，建議放寬進場條件或檢查數據質量")
        elif stats.success_rate < 0.8:
            recommendations.append("成功率中等，考慮優化參數範圍或策略邏輯")
        else:
            recommendations.append("成功率良好，當前策略設定有效")

        # 基於Sharpe比率給出建議
        if stats.max_sharpe < 1.0:
            recommendations.append("最高Sharpe比率偏低，建議尋找更有效的策略組合")
        elif stats.max_sharpe < 2.0:
            recommendations.append("Sharpe比率中等，有進一步優化空間")
        else:
            recommendations.append("發現高Sharpe策略，具有實際應用潛力")

        # 基於回撤控制給出建議
        if stats.worst_max_drawdown < -0.3:
            recommendations.append("最大回撤過大，必須加強風險控制")
        elif stats.worst_max_drawdown < -0.2:
            recommendations.append("回撤較大，建議優化止損策略")
        else:
            recommendations.append("回撤控制良好")

        # 參數效率建議
        if self.analyzer.parameter_efficiency:
            best_param = max(self.analyzer.parameter_efficiency.items(),
                           key=lambda x: x[1].efficiency_score)
            recommendations.append(f"參數 {best_param[0]} 具有最高效率分數 {best_param[1].efficiency_score:.4f}")

            # 相關性分析
            high_corr_params = [(name, pe) for name, pe in self.analyzer.parameter_efficiency.items()
                              if abs(pe.correlation_with_sharpe) > 0.3]
            if high_corr_params:
                recommendations.append(f"發現 {len(high_corr_params)} 個與Sharpe高相關的參數")

        recommendations_html = "<ul>"
        for rec in recommendations:
            recommendations_html += f"<li>{rec}</li>"
        recommendations_html += "</ul>"

        return recommendations_html

def main():
    """主函數 - 演示完整的分析和可視化流程"""
    print("=" * 80)
    print("PHASE 4: 結果分析和可視化系統")
    print("=" * 80)

    # 1. 初始化分析器
    print("\n[STEP 1] 初始化結果分析器...")
    analyzer = ResultsAnalyzer()

    # 2. 加載結果
    print("[STEP 2] 加載回測結果...")
    # 使用最新的結果文件
    latest_file = "massive_nonprice_ta_results_20251124_002218.json"
    if not analyzer.load_results(latest_file):
        print("無法加載結果，退出...")
        return

    # 3. 統計分析
    print("[STEP 3] 進行統計分析...")
    stats = analyzer.analyze_statistics()
    if stats:
        print(f"分析完成:")
        print(f"  總策略數: {stats.total_strategies}")
        print(f"  成功策略: {stats.successful_strategies}")
        print(f"  成功率: {stats.success_rate:.1%}")
        print(f"  平均Sharpe: {stats.avg_sharpe:.3f}")
        print(f"  最高Sharpe: {stats.max_sharpe:.3f}")
        print(f"  平均回報: {stats.avg_return:.2%}")
        print(f"  最差回撤: {stats.worst_max_drawdown:.2%}")

    # 4. 找到最佳和最差策略
    print("\n[STEP 4] 識別頂級和表現較差策略...")
    best_strategies = analyzer.find_best_strategies(10)
    worst_strategies = analyzer.find_worst_strategies(10)

    print(f"最佳策略 (前3名):")
    for i, strategy in enumerate(best_strategies[:3], 1):
        print(f"  {i}. {strategy.get('strategy_type', 'Unknown')}: "
              f"Sharpe={strategy.get('sharpe_ratio', 0):.3f}, "
              f"Return={strategy.get('total_return', 0):.2%}")

    # 5. 參數效率分析
    print("\n[STEP 5] 進行參數效率分析...")
    param_efficiency = analyzer.analyze_parameter_efficiency()
    if param_efficiency:
        print(f"分析了 {len(param_efficiency)} 個參數的效率")
        for param_name, efficiency in list(param_efficiency.items())[:3]:
            print(f"  {param_name}: 效率分數={efficiency.efficiency_score:.4f}, "
                  f"相關性={efficiency.correlation_with_sharpe:.4f}")

    # 6. 創建可視化儀表板
    print("\n[STEP 6] 創建交互式儀表板...")
    dashboard = InteractiveDashboard(analyzer)

    # 生成各種圖表
    performance_fig = dashboard.create_performance_distribution()
    parameter_fig = dashboard.create_parameter_analysis()
    best_strategies_fig = dashboard.create_best_strategies_table()

    print("圖表創建完成:")
    print(f"  性能分布圖: {'OK' if performance_fig else 'FAIL'}")
    print(f"  參數分析圖: {'OK' if parameter_fig else 'FAIL'}")
    print(f"  最佳策略表: {'OK' if best_strategies_fig else 'FAIL'}")

    # 7. 生成綜合報告
    print("\n[STEP 7] 生成綜合分析報告...")
    report_generator = ReportGenerator(analyzer, dashboard)
    report_path = report_generator.generate_comprehensive_report()

    # 8. 保存分析結果
    print("\n[STEP 8] 保存分析結果...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 保存統計結果
    results_summary = {
        'timestamp': timestamp,
        'statistics': asdict(stats) if stats else None,
        'best_strategies': best_strategies[:5] if best_strategies else [],
        'parameter_efficiency': {
            name: asdict(eff) for name, eff in param_efficiency.items()
        } if param_efficiency else {},
        'analysis_summary': {
            'total_parameters_analyzed': len(param_efficiency) if param_efficiency else 0,
            'high_efficiency_parameters': len([p for p in param_efficiency.values()
                                            if p.efficiency_score > 0.5]) if param_efficiency else 0,
            'recommendations': "Detailed recommendations available in HTML report"
        }
    }

    summary_path = f"phase4_analysis_summary_{timestamp}.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)

    print(f"分析摘要已保存至: {summary_path}")

    # 9. 完成總結
    print("\n" + "=" * 80)
    print("PHASE 4 完成總結")
    print("=" * 80)

    print(f"[OK] 統計分析完成 - {stats.successful_strategies}/{stats.total_strategies} 成功策略")
    print(f"[OK] 頂級策略識別 - 最高Sharpe: {stats.max_sharpe:.3f}")
    print(f"[OK] 參數效率分析 - {len(param_efficiency)} 個參數已分析")
    print(f"[OK] 交互式儀表板 - 3 個主要可視化圖表")
    print(f"[OK] 綜合分析報告 - {report_path}")

    success_indicators = [
        stats.success_rate > 0.7,
        stats.max_sharpe > 1.5,
        len(param_efficiency) > 0,
        stats.avg_max_drawdown > -0.3
    ]

    overall_success = sum(success_indicators) >= 3

    print(f"\nPHASE 4 {'PASSED' if overall_success else 'NEEDS ATTENTION'}")
    print(f"成功指標: {sum(success_indicators)}/4")

    if overall_success:
        print("[SUCCESS] 結果分析和可視化系統實現完成！")
        print("系統具備完整的策略分析和洞察發現能力。")
    else:
        print("[WARNING] 部分功能需要改進，請檢查上述輸出。")

    return overall_success

if __name__ == "__main__":
    main()