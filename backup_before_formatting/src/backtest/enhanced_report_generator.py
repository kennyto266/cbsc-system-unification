#!/usr/bin/env python3
"""
增強報告生成器 - 標準化HTML和JSON報告生成，包含質量指標和可視化
Enhanced Report Generator - Standardized HTML and JSON reporting with quality metrics and visualization
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import base64
import io

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template

logger = logging.getLogger(__name__)


@dataclass
class ReportSection:
    """報告章節"""
    title: str
    content: str
    priority: int = 0
    charts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ReportMetadata:
    """報告元數據"""
    report_id: str
    generation_time: datetime
    symbol: str
    data_quality_score: float
    authenticity_verified: bool
    total_strategies_tested: int
    execution_time_seconds: float
    system_version: str = "v1.0"


class EnhancedReportGenerator:
    """增強報告生成器"""
    
    def __init__(self, output_dir: str = "enhanced_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 配置matplotlib
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # 報告模板
        self.html_template = self._create_html_template()
        
        logger.info(f"Enhanced Report Generator initialized - Output: {self.output_dir}")
    
    def generate_comprehensive_report(self, 
                                    backtest_results: Dict[str, Any],
                                    quality_report: Dict[str, Any],
                                    performance_metrics: Dict[str, Any],
                                    execution_summary: Dict[str, Any]) -> Dict[str, str]:
        """
        生成綜合報告
        
        Returns:
            包含HTML和JSON報告文件路徑的字典
        """
        logger.info("🚀 Generating comprehensive enhanced report")
        
        # 創建報告元數據
        metadata = ReportMetadata(
            report_id=f"ENHANCED_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generation_time=datetime.now(),
            symbol=execution_summary.get('symbol', 'UNKNOWN'),
            data_quality_score=quality_report.get('overall_quality_score', 0),
            authenticity_verified=quality_report.get('authenticity_verified', False),
            total_strategies_tested=execution_summary.get('total_strategies', 0),
            execution_time_seconds=performance_metrics.get('total_execution_time', 0)
        )
        
        # 生成圖表
        charts = self._generate_charts(backtest_results, quality_report, performance_metrics)
        
        # 組織報告章節
        sections = self._create_report_sections(
            backtest_results, quality_report, performance_metrics, execution_summary, charts
        )
        
        # 生成HTML報告
        html_report = self._generate_html_report(metadata, sections)
        
        # 生成JSON報告
        json_report = self._generate_json_report(metadata, backtest_results, quality_report, performance_metrics)
        
        # 保存報告
        html_file = self.output_dir / f"{metadata.report_id}.html"
        json_file = self.output_dir / f"{metadata.report_id}.json"
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        with open(json_file, 'r', encoding='utf-8') as f:
            json_content = f.read()
        
        logger.info(f"✅ Reports generated: {html_file}, {json_file}")
        
        return {
            'html_report': str(html_file),
            'json_report': str(json_file)
        }
    
    def _generate_charts(self, 
                        backtest_results: Dict[str, Any],
                        quality_report: Dict[str, Any], 
                        performance_metrics: Dict[str, Any]) -> Dict[str, str]:
        """生成圖表並返回Base64編碼的圖像"""
        charts = {}
        
        try:
            # 1. 策略性能分佈圖
            charts['performance_distribution'] = self._create_performance_distribution_chart(backtest_results)
            
            # 2. Sharpe比率 vs 總回報散點圖
            charts['sharpe_return_scatter'] = self._create_sharpe_return_scatter(backtest_results)
            
            # 3. 數據質量指標儀表板
            charts['quality_dashboard'] = self._create_quality_dashboard(quality_report)
            
            # 4. 參數優化熱力圖
            charts['parameter_heatmap'] = self._create_parameter_heatmap(backtest_results)
            
            # 5. 執行性能圖表
            charts['execution_performance'] = self._create_execution_performance_chart(performance_metrics)
            
            # 6. 風險回撤圖
            charts['drawdown_analysis'] = self._create_drawdown_analysis(backtest_results)
            
            logger.info(f"✅ Generated {len(charts)} charts")
            
        except Exception as e:
            logger.error(f"❌ Chart generation failed: {e}")
        
        return charts
    
    def _create_performance_distribution_chart(self, backtest_results: Dict[str, Any]) -> str:
        """創建策略性能分佈圖"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Strategy Performance Distribution', fontsize=16, fontweight='bold')
        
        # 提取性能數據
        strategies = backtest_results.get('strategies', [])
        if not strategies:
            return ""
        
        df_metrics = pd.DataFrame([
            {
                'sharpe_ratio': s.get('sharpe_ratio', 0),
                'total_return': s.get('total_return', 0),
                'max_drawdown': s.get('max_drawdown', 0),
                'win_rate': s.get('win_rate', 0)
            } for s in strategies
        ])
        
        # Sharpe比率分佈
        axes[0, 0].hist(df_metrics['sharpe_ratio'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('Sharpe Ratio Distribution')
        axes[0, 0].set_xlabel('Sharpe Ratio')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].axvline(df_metrics['sharpe_ratio'].mean(), color='red', linestyle='--', 
                          label=f'Mean: {df_metrics["sharpe_ratio"].mean():.3f}')
        axes[0, 0].legend()
        
        # 總回報分佈
        axes[0, 1].hist(df_metrics['total_return'] * 100, bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[0, 1].set_title('Total Return Distribution (%)')
        axes[0, 1].set_xlabel('Total Return (%)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].axvline(df_metrics['total_return'].mean() * 100, color='red', linestyle='--',
                          label=f'Mean: {df_metrics["total_return"].mean() * 100:.1f}%')
        axes[0, 1].legend()
        
        # 最大回撤分佈
        axes[1, 0].hist(df_metrics['max_drawdown'] * -100, bins=30, alpha=0.7, color='salmon', edgecolor='black')
        axes[1, 0].set_title('Maximum Drawdown Distribution (%)')
        axes[1, 0].set_xlabel('Max Drawdown (%)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].axvline(df_metrics['max_drawdown'].mean() * -100, color='red', linestyle='--',
                          label=f'Mean: {df_metrics["max_drawdown"].mean() * -100:.1f}%')
        axes[1, 0].legend()
        
        # 勝率分佈
        axes[1, 1].hist(df_metrics['win_rate'] * 100, bins=30, alpha=0.7, color='gold', edgecolor='black')
        axes[1, 1].set_title('Win Rate Distribution (%)')
        axes[1, 1].set_xlabel('Win Rate (%)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].axvline(df_metrics['win_rate'].mean() * 100, color='red', linestyle='--',
                          label=f'Mean: {df_metrics["win_rate"].mean() * 100:.1f}%')
        axes[1, 1].legend()
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_sharpe_return_scatter(self, backtest_results: Dict[str, Any]) -> str:
        """創建Sharpe比率 vs 總回報散點圖"""
        strategies = backtest_results.get('strategies', [])
        if not strategies:
            return ""
        
        df_metrics = pd.DataFrame([
            {
                'sharpe_ratio': s.get('sharpe_ratio', 0),
                'total_return': s.get('total_return', 0) * 100,
                'strategy_name': s.get('parameters', {}).get('window', 'Unknown')
            } for s in strategies
        ])
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 創建散點圖
        scatter = ax.scatter(df_metrics['total_return'], df_metrics['sharpe_ratio'], 
                           alpha=0.6, s=50, c=df_metrics.index, cmap='viridis')
        
        # 添加最佳策略標記
        if len(df_metrics) > 0:
            best_idx = df_metrics['sharpe_ratio'].idxmax()
            ax.scatter(df_metrics.loc[best_idx, 'total_return'], 
                      df_metrics.loc[best_idx, 'sharpe_ratio'],
                      color='red', s=200, marker='*', label='Best Strategy', zorder=5)
        
        ax.set_xlabel('Total Return (%)', fontsize=12)
        ax.set_ylabel('Sharpe Ratio', fontsize=12)
        ax.set_title('Strategy Performance: Sharpe Ratio vs Total Return', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=1.0, color='green', linestyle='--', alpha=0.7, label='Sharpe = 1.0')
        ax.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='Zero Return')
        ax.legend()
        
        # 添加colorbar
        plt.colorbar(scatter, ax=ax, label='Strategy Index')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_quality_dashboard(self, quality_report: Dict[str, Any]) -> str:
        """創建數據質量儀表板"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Data Quality Dashboard', fontsize=16, fontweight='bold')
        
        # 總體質量分數
        overall_score = quality_report.get('overall_quality_score', 0)
        authenticity = quality_report.get('authenticity_verified', False)
        
        # 質量分數儀表
        axes[0, 0].pie([overall_score, 1-overall_score], 
                      labels=['Quality Score', 'Remaining'],
                      colors=['lightgreen', 'lightgray'],
                      autopct='%1.1f%%',
                      startangle=90)
        axes[0, 0].set_title(f'Overall Quality Score: {overall_score:.1%}')
        
        # 真實性驗證
        auth_colors = ['green' if authenticity else 'red', 'lightgray']
        auth_labels = ['Verified' if authenticity else 'Not Verified', '']
        axes[0, 1].pie([1, 0] if authenticity else [0, 1],
                      labels=auth_labels,
                      colors=auth_colors,
                      startangle=90)
        axes[0, 1].set_title('Data Authenticity')
        
        # 數據源狀態
        data_sources = quality_report.get('data_sources', {})
        if data_sources:
            source_names = list(data_sources.keys())
            source_scores = [data_sources[source].get('confidence_score', 0) for source in source_names]
            
            axes[1, 0].barh(source_names, source_scores, color='skyblue')
            axes[1, 0].set_xlim(0, 1)
            axes[1, 0].set_xlabel('Confidence Score')
            axes[1, 0].set_title('Data Source Quality')
        else:
            axes[1, 0].text(0.5, 0.5, 'No Data Sources', ha='center', va='center', transform=axes[1, 0].transAxes)
        
        # 警報統計
        alerts = quality_report.get('alerts', [])
        if alerts:
            alert_severities = [alert.severity for alert in alerts]
            severity_counts = pd.Series(alert_severities).value_counts()
            
            colors = {'CRITICAL': 'red', 'HIGH': 'orange', 'MEDIUM': 'yellow', 'LOW': 'blue'}
            bar_colors = [colors.get(sev, 'gray') for sev in severity_counts.index]
            
            axes[1, 1].bar(severity_counts.index, severity_counts.values, color=bar_colors)
            axes[1, 1].set_title('Quality Alerts by Severity')
            axes[1, 1].set_ylabel('Count')
        else:
            axes[1, 1].text(0.5, 0.5, 'No Alerts ✅', ha='center', va='center', transform=axes[1, 1].transAxes)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_parameter_heatmap(self, backtest_results: Dict[str, Any]) -> str:
        """創建參數優化熱力圖"""
        strategies = backtest_results.get('strategies', [])
        if not strategies:
            return ""
        
        # 創建參數-性能矩陣
        df_params = pd.DataFrame([
            {
                'window': s.get('parameters', {}).get('window', 0),
                'buy_threshold': s.get('parameters', {}).get('buy_threshold', 0),
                'sharpe_ratio': s.get('sharpe_ratio', 0)
            } for s in strategies
        ])
        
        if df_params.empty:
            return ""
        
        # 創建透視表
        pivot_table = df_params.pivot_table(
            values='sharpe_ratio', 
            index='window', 
            columns='buy_threshold',
            aggfunc='mean'
        )
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        sns.heatmap(pivot_table, 
                   annot=True, 
                   fmt='.2f', 
                   cmap='RdYlGn', 
                   center=0,
                   ax=ax)
        ax.set_title('Parameter Optimization Heatmap (Sharpe Ratio)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Buy Threshold')
        ax.set_ylabel('RSI Window')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_execution_performance_chart(self, performance_metrics: Dict[str, Any]) -> str:
        """創建執行性能圖表"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('System Execution Performance', fontsize=16, fontweight='bold')
        
        # 任務執行統計
        total_tasks = performance_metrics.get('total_tasks', 0)
        completed_tasks = performance_metrics.get('completed_tasks', 0)
        failed_tasks = performance_metrics.get('failed_tasks', 0)
        
        # 任務完成狀態
        task_labels = ['Completed', 'Failed', 'Remaining']
        task_sizes = [completed_tasks, failed_tasks, max(0, total_tasks - completed_tasks - failed_tasks)]
        task_colors = ['green', 'red', 'lightgray']
        
        axes[0, 0].pie(task_sizes[task_sizes > 0], labels=[task_labels[i] for i in range(len(task_sizes)) if task_sizes[i] > 0],
                      colors=[task_colors[i] for i in range(len(task_sizes)) if task_sizes[i] > 0],
                      autopct='%1.1f%%')
        axes[0, 0].set_title(f'Task Completion Status ({total_tasks} total)')
        
        # 平均任務時間
        avg_time = performance_metrics.get('average_task_time', 0)
        total_time = performance_metrics.get('total_execution_time', 0)
        
        time_metrics = ['Avg Task Time', 'Total Execution']
        time_values = [avg_time, total_time / 60]  # 轉換為分鐘
        
        axes[0, 1].bar(time_metrics, time_values, color=['skyblue', 'lightgreen'])
        axes[0, 1].set_ylabel('Time (seconds)')
        axes[0, 1].set_title('Execution Time Metrics')
        
        # 並行效率
        parallel_efficiency = performance_metrics.get('parallel_efficiency', 0)
        efficiency_data = ['Parallel Efficiency', 'Theoretical Max']
        efficiency_values = [parallel_efficiency * 100, 100]
        
        axes[1, 0].bar(efficiency_data, efficiency_values, color=['orange', 'gray'])
        axes[1, 0].set_ylabel('Efficiency (%)')
        axes[1, 0].set_ylim(0, 100)
        axes[1, 0].set_title(f'Parallel Efficiency: {parallel_efficiency:.1%}')
        
        # 任務執行速率
        if total_time > 0:
            tasks_per_second = completed_tasks / total_time
            tasks_per_minute = tasks_per_second * 60
        else:
            tasks_per_minute = 0
        
        axes[1, 1].text(0.5, 0.5, f'{tasks_per_minute:.1f}\nTasks/Minute', 
                       ha='center', va='center', fontsize=20, fontweight='bold',
                       transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('Processing Speed')
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _create_drawdown_analysis(self, backtest_results: Dict[str, Any]) -> str:
        """創建回撤分析圖表"""
        strategies = backtest_results.get('strategies', [])
        if not strategies:
            return ""
        
        # 提取前10個最佳策略進行回撤分析
        df_metrics = pd.DataFrame([
            {
                'strategy_name': f"Strategy_{i}",
                'sharpe_ratio': s.get('sharpe_ratio', 0),
                'max_drawdown': abs(s.get('max_drawdown', 0)) * 100,
                'total_return': s.get('total_return', 0) * 100,
                'calmar_ratio': s.get('calmar_ratio', 0)
            } for i, s in enumerate(strategies[:20])
        ])
        
        df_metrics = df_metrics.sort_values('sharpe_ratio', ascending=False).head(10)
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Top 10 Strategies - Risk Analysis', fontsize=16, fontweight='bold')
        
        # 回撤 vs 回報
        axes[0].scatter(df_metrics['max_drawdown'], df_metrics['total_return'], 
                      s=100, alpha=0.7, c=df_metrics['sharpe_ratio'], cmap='viridis')
        axes[0].set_xlabel('Max Drawdown (%)')
        axes[0].set_ylabel('Total Return (%)')
        axes[0].set_title('Return vs Drawdown')
        axes[0].grid(True, alpha=0.3)
        
        # 添加策略標籤
        for i, row in df_metrics.iterrows():
            axes[0].annotate(row['strategy_name'], 
                           (row['max_drawdown'], row['total_return']),
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # Calmar比率分佈
        valid_calmar = df_metrics[df_metrics['calmar_ratio'] != 0]
        if not valid_calmar.empty:
            axes[1].bar(range(len(valid_calmar)), valid_calmar['calmar_ratio'], color='skyblue')
            axes[1].set_xlabel('Strategy Rank')
            axes[1].set_ylabel('Calmar Ratio')
            axes[1].set_title('Calmar Ratio Distribution')
            axes[1].set_xticks(range(len(valid_calmar)))
            axes[1].set_xticklabels(valid_calmar['strategy_name'], rotation=45, ha='right')
        else:
            axes[1].text(0.5, 0.5, 'No valid Calmar ratios', ha='center', va='center', 
                       transform=axes[1].transAxes)
        
        plt.tight_layout()
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """將matplotlib圖表轉換為Base64字符串"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close(fig)
        return image_base64
    
    def _create_report_sections(self, 
                              backtest_results: Dict[str, Any],
                              quality_report: Dict[str, Any],
                              performance_metrics: Dict[str, Any],
                              execution_summary: Dict[str, Any],
                              charts: Dict[str, str]) -> List[ReportSection]:
        """創建報告章節"""
        sections = []
        
        # 1. 執行摘要
        sections.append(ReportSection(
            title="執行摘要 (Executive Summary)",
            content=self._create_executive_summary(execution_summary, quality_report, performance_metrics),
            priority=1
        ))
        
        # 2. 最佳策略
        sections.append(ReportSection(
            title="最佳策略表現 (Top Performing Strategies)",
            content=self._create_top_strategies_section(backtest_results),
            priority=2
        ))
        
        # 3. 數據質量報告
        sections.append(ReportSection(
            title="數據質量驗證 (Data Quality Verification)",
            content=self._create_quality_section(quality_report),
            priority=3,
            charts=[{'id': 'quality_dashboard', 'title': '數據質量儀表板'}]
        ))
        
        # 4. 性能分析
        sections.append(ReportSection(
            title="策略性能分析 (Strategy Performance Analysis)",
            content=self._create_performance_analysis_section(backtest_results),
            priority=4,
            charts=[
                {'id': 'performance_distribution', 'title': '性能指標分佈'},
                {'id': 'sharpe_return_scatter', 'title': 'Sharpe比率 vs 總回報'},
                {'id': 'drawdown_analysis', 'title': '風險回撤分析'}
            ]
        ))
        
        # 5. 參數優化
        sections.append(ReportSection(
            title="參數優化結果 (Parameter Optimization Results)",
            content=self._create_optimization_section(backtest_results),
            priority=5,
            charts=[{'id': 'parameter_heatmap', 'title': '參數優化熱力圖'}]
        ))
        
        # 6. 系統性能
        sections.append(ReportSection(
            title="系統執行性能 (System Execution Performance)",
            content=self._create_system_performance_section(performance_metrics),
            priority=6,
            charts=[{'id': 'execution_performance', 'title': '執行性能統計'}]
        ))
        
        # 7. 建議和結論
        sections.append(ReportSection(
            title="建議和結論 (Recommendations and Conclusions)",
            content=self._create_recommendations_section(backtest_results, quality_report),
            priority=7
        ))
        
        return sections
    
    def _create_executive_summary(self, execution_summary: Dict[str, Any], 
                                quality_report: Dict[str, Any],
                                performance_metrics: Dict[str, Any]) -> str:
        """創建執行摘要"""
        total_strategies = execution_summary.get('total_strategies', 0)
        success_rate = performance_metrics.get('completed_tasks', 0) / max(1, performance_metrics.get('total_tasks', 1))
        best_sharpe = execution_summary.get('best_sharpe', 0)
        
        return f"""
        <div class="executive-summary">
            <div class="summary-grid">
                <div class="summary-item">
                    <h4>測試策略總數</h4>
                    <p class="big-number">{total_strategies:,}</p>
                </div>
                <div class="summary-item">
                    <h4>執行成功率</h4>
                    <p class="big-number">{success_rate:.1%}</p>
                </div>
                <div class="summary-item">
                    <h4>最佳Sharpe比率</h4>
                    <p class="big-number">{best_sharpe:.3f}</p>
                </div>
                <div class="summary-item">
                    <h4>數據質量分數</h4>
                    <p class="big-number">{quality_report.get('overall_quality_score', 0):.1%}</p>
                </div>
            </div>
            <div class="key-findings">
                <h4>關鍵發現</h4>
                <ul>
                    <li><strong>數據真實性:</strong> {'✅ 已驗證' if quality_report.get('authenticity_verified') else '❌ 未通過'}</li>
                    <li><strong>並行效率:</strong> {performance_metrics.get('parallel_efficiency', 0):.1%}</li>
                    <li><strong>處理速度:</strong> {performance_metrics.get('completed_tasks', 0) / max(1, performance_metrics.get('total_execution_time', 1)):.1f} 任務/秒</li>
                    <li><strong>質量警報:</strong> {len(quality_report.get('alerts', []))} 個問題</li>
                </ul>
            </div>
        </div>
        """
    
    def _create_top_strategies_section(self, backtest_results: Dict[str, Any]) -> str:
        """創建最佳策略章節"""
        strategies = backtest_results.get('strategies', [])
        if not strategies:
            return "<p>無策略數據可用</p>"
        
        # 排序並獲取前10個策略
        sorted_strategies = sorted(strategies, key=lambda x: x.get('sharpe_ratio', 0), reverse=True)[:10]
        
        html = "<div class='top-strategies'><table class='results-table'>"
        html += """
        <thead>
            <tr>
                <th>排名</th>
                <th>RSI窗口</th>
                <th>買入閾值</th>
                <th>賣出閾值</th>
                <th>總回報</th>
                <th>Sharpe比率</th>
                <th>最大回撤</th>
                <th>勝率</th>
                <th>交易次數</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for i, strategy in enumerate(sorted_strategies):
            params = strategy.get('parameters', {})
            html += f"""
            <tr>
                <td>{i+1}</td>
                <td>{params.get('window', 'N/A')}</td>
                <td>{params.get('buy_threshold', 'N/A')}</td>
                <td>{params.get('sell_threshold', 'N/A')}</td>
                <td>{strategy.get('total_return', 0):.2%}</td>
                <td><strong>{strategy.get('sharpe_ratio', 0):.3f}</strong></td>
                <td>{strategy.get('max_drawdown', 0):.2%}</td>
                <td>{strategy.get('win_rate', 0):.1%}</td>
                <td>{strategy.get('num_trades', 0)}</td>
            </tr>
            """
        
        html += "</tbody></table></div>"
        return html
    
    def _create_quality_section(self, quality_report: Dict[str, Any]) -> str:
        """創建數據質量章節"""
        overall_score = quality_report.get('overall_quality_score', 0)
        authenticity = quality_report.get('authenticity_verified', False)
        alerts = quality_report.get('alerts', [])
        
        html = f"""
        <div class="quality-section">
            <div class="quality-overview">
                <h4>質量總覽</h4>
                <p><strong>總體質量分數:</strong> {overall_score:.1%}</p>
                <p><strong>真實性驗證:</strong> {'✅ 通過' if authenticity else '❌ 失敗'}</p>
                <p><strong>警報數量:</strong> {len(alerts)}</p>
            </div>
        """
        
        if alerts:
            html += "<h4>質量警報詳情</h4><ul>"
            for alert in alerts[:5]:  # 只顯示前5個警報
                html += f"<li class='alert-{alert.severity.lower()}'>{alert.description}</li>"
            if len(alerts) > 5:
                html += f"<li><em>... 還有 {len(alerts) - 5} 個警報</em></li>"
            html += "</ul>"
        
        html += "</div>"
        return html
    
    def _create_performance_analysis_section(self, backtest_results: Dict[str, Any]) -> str:
        """創建性能分析章節"""
        strategies = backtest_results.get('strategies', [])
        if not strategies:
            return "<p>無性能數據可用</p>"
        
        # 計算統計數據
        sharpe_ratios = [s.get('sharpe_ratio', 0) for s in strategies]
        returns = [s.get('total_return', 0) for s in strategies]
        drawdowns = [s.get('max_drawdown', 0) for s in strategies]
        
        html = f"""
        <div class="performance-analysis">
            <div class="performance-stats">
                <h4>性能統計</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <h5>Sharpe比率</h5>
                        <p>平均: {np.mean(sharpe_ratios):.3f}</p>
                        <p>標準差: {np.std(sharpe_ratios):.3f}</p>
                        <p>最佳: {np.max(sharpe_ratios):.3f}</p>
                    </div>
                    <div class="stat-item">
                        <h5>總回報</h5>
                        <p>平均: {np.mean(returns):.2%}</p>
                        <p>標準差: {np.std(returns):.2%}</p>
                        <p>最佳: {np.max(returns):.2%}</p>
                    </div>
                    <div class="stat-item">
                        <h5>最大回撤</h5>
                        <p>平均: {np.mean(drawdowns):.2%}</p>
                        <p>標準差: {np.std(drawdowns):.2%}</p>
                        <p>最小: {np.min(drawdowns):.2%}</p>
                    </div>
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _create_optimization_section(self, backtest_results: Dict[str, Any]) -> str:
        """創建參數優化章節"""
        strategies = backtest_results.get('strategies', [])
        if not strategies:
            return "<p>無優化數據可用</p>"
        
        # 分析最佳參數
        best_strategy = max(strategies, key=lambda x: x.get('sharpe_ratio', 0))
        best_params = best_strategy.get('parameters', {})
        
        # 參數分析
        windows = [s.get('parameters', {}).get('window', 0) for s in strategies]
        buy_thresholds = [s.get('parameters', {}).get('buy_threshold', 0) for s in strategies]
        
        html = f"""
        <div class="optimization-section">
            <div class="best-parameters">
                <h4>最佳參數組合</h4>
                <p><strong>RSI窗口:</strong> {best_params.get('window', 'N/A')}</p>
                <p><strong>買入閾值:</strong> {best_params.get('buy_threshold', 'N/A')}</p>
                <p><strong>賣出閾值:</strong> {best_params.get('sell_threshold', 'N/A')}</p>
                <p><strong>Sharpe比率:</strong> {best_strategy.get('sharpe_ratio', 0):.3f}</p>
            </div>
            <div class="parameter-analysis">
                <h4>參數分析</h4>
                <p><strong>RSI窗口範圍:</strong> {min(windows)} - {max(windows)}</p>
                <p><strong>買入閾值範圍:</strong> {min(buy_thresholds)} - {max(buy_thresholds)}</p>
            </div>
        </div>
        """
        
        return html
    
    def _create_system_performance_section(self, performance_metrics: Dict[str, Any]) -> str:
        """創建系統性能章節"""
        total_tasks = performance_metrics.get('total_tasks', 0)
        completed_tasks = performance_metrics.get('completed_tasks', 0)
        total_time = performance_metrics.get('total_execution_time', 0)
        efficiency = performance_metrics.get('parallel_efficiency', 0)
        
        html = f"""
        <div class="system-performance">
            <div class="execution-stats">
                <h4>執行統計</h4>
                <p><strong>總任務數:</strong> {total_tasks:,}</p>
                <p><strong>完成任務:</strong> {completed_tasks:,}</p>
                <p><strong>成功率:</strong> {completed_tasks/max(1,total_tasks):.1%}</p>
                <p><strong>總執行時間:</strong> {total_time:.2f}秒</p>
                <p><strong>並行效率:</strong> {efficiency:.1%}</p>
                <p><strong>處理速度:</strong> {completed_tasks/max(1,total_time):.1f} 任務/秒</p>
            </div>
        </div>
        """
        
        return html
    
    def _create_recommendations_section(self, backtest_results: Dict[str, Any], 
                                      quality_report: Dict[str, Any]) -> str:
        """創建建議章節"""
        recommendations = []
        
        # 基於策略結果的建議
        strategies = backtest_results.get('strategies', [])
        if strategies:
            best_sharpe = max(s.get('sharpe_ratio', 0) for s in strategies)
            avg_sharpe = np.mean([s.get('sharpe_ratio', 0) for s in strategies])
            
            if best_sharpe > 1.5:
                recommendations.append("✅ 發現高質量策略，Sharpe比率 > 1.5")
            elif best_sharpe > 1.0:
                recommendations.append("⚠️ 策略表現良好，但仍有優化空間")
            else:
                recommendations.append("❌ 建議重新評估策略參數，提高Sharpe比率")
        
        # 基於數據質量的建議
        quality_score = quality_report.get('overall_quality_score', 0)
        if quality_score < 0.8:
            recommendations.append("🔍 建議改善數據質量以提高回測可靠性")
        
        if not quality_report.get('authenticity_verified', False):
            recommendations.append("⚠️ 數據真實性未驗證，建議檢查數據源")
        
        # 基於執行性能的建議
        alerts = quality_report.get('alerts', [])
        if len(alerts) > 5:
            recommendations.append("📊 發現多個數據質量問題，建議進行數據清理")
        
        html = "<div class='recommendations'><h4>建議和結論</h4><ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        
        if not recommendations:
            html += "<li>✅ 所有指標表現良好，系統運行正常</li>"
        
        html += "</ul></div>"
        return html
    
    def _create_html_template(self) -> Template:
        """創建HTML模板"""
        template_str = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Enhanced Universal Backtest SOP Report - {{ metadata.symbol }}</title>
            <style>
                body {
                    font-family: 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif;
                    margin: 0;
                    padding: 20px;
                    line-height: 1.6;
                    background-color: #f8f9fa;
                    color: #333;
                }
                
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px;
                    text-align: center;
                }
                
                .header h1 {
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 700;
                }
                
                .header .subtitle {
                    margin-top: 10px;
                    opacity: 0.9;
                    font-size: 1.1em;
                }
                
                .metadata {
                    background: #f8f9fa;
                    padding: 20px 40px;
                    border-bottom: 1px solid #e9ecef;
                    display: flex;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 20px;
                }
                
                .metadata-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .metadata-label {
                    font-weight: 600;
                    color: #6c757d;
                }
                
                .metadata-value {
                    font-weight: 700;
                }
                
                .quality-badge {
                    background: {{ 'green' if metadata.authenticity_verified else 'red' }};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    font-weight: 600;
                }
                
                .content {
                    padding: 40px;
                }
                
                .section {
                    margin-bottom: 50px;
                    scroll-margin-top: 20px;
                }
                
                .section-title {
                    font-size: 1.8em;
                    font-weight: 700;
                    color: #2c3e50;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 3px solid #3498db;
                }
                
                .results-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                }
                
                .results-table th {
                    background: #34495e;
                    color: white;
                    padding: 15px 12px;
                    text-align: left;
                    font-weight: 600;
                }
                
                .results-table td {
                    padding: 12px;
                    border-bottom: 1px solid #ecf0f1;
                }
                
                .results-table tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                
                .results-table tr:hover {
                    background-color: #e3f2fd;
                }
                
                .chart-container {
                    margin: 30px 0;
                    text-align: center;
                }
                
                .chart-container img {
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }
                
                .chart-title {
                    font-size: 1.2em;
                    font-weight: 600;
                    margin-bottom: 15px;
                    color: #2c3e50;
                }
                
                .executive-summary {
                    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 12px;
                    margin: 20px 0;
                }
                
                .summary-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }
                
                .summary-item {
                    text-align: center;
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 8px;
                }
                
                .big-number {
                    font-size: 2.5em;
                    font-weight: 700;
                    margin: 10px 0 0 0;
                }
                
                .key-findings {
                    margin-top: 30px;
                }
                
                .key-findings ul {
                    list-style: none;
                    padding: 0;
                }
                
                .key-findings li {
                    background: rgba(255,255,255,0.1);
                    margin: 10px 0;
                    padding: 12px 15px;
                    border-radius: 6px;
                    border-left: 4px solid #fff;
                }
                
                .alert-critical { border-left-color: #e74c3c; }
                .alert-high { border-left-color: #f39c12; }
                .alert-medium { border-left-color: #3498db; }
                .alert-low { border-left-color: #95a5a6; }
                
                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }
                
                .stat-item {
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                }
                
                .stat-item h5 {
                    margin: 0 0 15px 0;
                    color: #2c3e50;
                    font-weight: 600;
                }
                
                .stat-item p {
                    margin: 5px 0;
                    color: #7f8c8d;
                }
                
                .quality-overview, .performance-analysis, .optimization-section {
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                
                .recommendations {
                    background: #e8f5e8;
                    border: 1px solid #4caf50;
                    padding: 25px;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                
                .recommendations h4 {
                    color: #2e7d32;
                    margin-top: 0;
                }
                
                .recommendations ul {
                    margin: 0;
                    padding-left: 20px;
                }
                
                .recommendations li {
                    margin: 10px 0;
                }
                
                .toc {
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0 40px 0;
                }
                
                .toc h3 {
                    margin-top: 0;
                    color: #2c3e50;
                }
                
                .toc ul {
                    list-style: none;
                    padding: 0;
                    margin: 10px 0 0 0;
                }
                
                .toc li {
                    padding: 5px 0;
                }
                
                .toc a {
                    text-decoration: none;
                    color: #3498db;
                    font-weight: 500;
                }
                
                .toc a:hover {
                    text-decoration: underline;
                }
                
                .footer {
                    background: #2c3e50;
                    color: white;
                    text-align: center;
                    padding: 30px;
                    margin-top: 50px;
                }
                
                @media (max-width: 768px) {
                    .container { margin: 10px; }
                    .header { padding: 30px 20px; }
                    .content { padding: 20px; }
                    .metadata { padding: 20px; flex-direction: column; }
                    .summary-grid { grid-template-columns: 1fr; }
                    .stats-grid { grid-template-columns: 1fr; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Enhanced Universal Backtest SOP Report</h1>
                    <div class="subtitle">
                        {{ metadata.symbol }} • Generated {{ metadata.generation_time.strftime('%Y-%m-%d %H:%M:%S') }} • 
                        Version {{ metadata.system_version }}
                    </div>
                </div>
                
                <div class="metadata">
                    <div class="metadata-item">
                        <span class="metadata-label">Report ID:</span>
                        <span class="metadata-value">{{ metadata.report_id }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Data Quality:</span>
                        <span class="metadata-value">{{ "%.1f"|format(metadata.data_quality_score * 100) }}%</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Authenticity:</span>
                        <span class="quality-badge">{{ '✅ Verified' if metadata.authenticity_verified else '❌ Not Verified' }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Strategies Tested:</span>
                        <span class="metadata-value">{{ "{:,}".format(metadata.total_strategies_tested) }}</span>
                    </div>
                    <div class="metadata-item">
                        <span class="metadata-label">Execution Time:</span>
                        <span class="metadata-value">{{ "%.2f"|format(metadata.execution_time_seconds) }}s</span>
                    </div>
                </div>
                
                <div class="content">
                    <div class="toc">
                        <h3>📋 Table of Contents</h3>
                        <ul>
                            {% for section in sections %}
                            <li><a href="#section-{{ loop.index }}">{{ section.title }}</a></li>
                            {% endfor %}
                        </ul>
                    </div>
                    
                    {% for section in sections %}
                    <div class="section" id="section-{{ loop.index }}">
                        <h2 class="section-title">{{ section.title }}</h2>
                        {{ section.content|safe }}
                        
                        {% for chart in section.charts %}
                        <div class="chart-container">
                            <div class="chart-title">{{ chart.title }}</div>
                            {% if charts[chart.id] %}
                            <img src="data:image/png;base64,{{ charts[chart.id] }}" alt="{{ chart.title }}">
                            {% else %}
                            <p>Chart not available</p>
                            {% endif %}
                        </div>
                        {% endfor %}
                    </div>
                    {% endfor %}
                </div>
                
                <div class="footer">
                    <p>Generated by Enhanced Universal Backtest SOP • 
                    System Version: {{ metadata.system_version }} • 
                    Data Quality: {{ "%.1f"|format(metadata.data_quality_score * 100) }}%</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return Template(template_str)
    
    def _generate_html_report(self, metadata: ReportMetadata, sections: List[ReportSection]) -> str:
        """生成HTML報告"""
        # 準備圖表數據
        charts = {}
        for section in sections:
            for chart in section.charts:
                charts[chart['id']] = chart.get('data', '')  # 這裡應該是base64圖表數據
        
        # 渲染HTML
        return self.html_template.render(
            metadata=metadata,
            sections=sections,
            charts=charts
        )
    
    def _generate_json_report(self, 
                            metadata: ReportMetadata,
                            backtest_results: Dict[str, Any],
                            quality_report: Dict[str, Any],
                            performance_metrics: Dict[str, Any]) -> str:
        """生成JSON報告"""
        json_report = {
            'metadata': {
                'report_id': metadata.report_id,
                'generation_time': metadata.generation_time.isoformat(),
                'symbol': metadata.symbol,
                'system_version': metadata.system_version
            },
            'data_quality': {
                'overall_score': metadata.data_quality_score,
                'authenticity_verified': metadata.authenticity_verified,
                'detailed_report': quality_report
            },
            'backtest_results': backtest_results,
            'performance_metrics': performance_metrics,
            'summary': {
                'total_strategies_tested': metadata.total_strategies_tested,
                'execution_time_seconds': metadata.execution_time_seconds,
                'best_sharpe_ratio': max([s.get('sharpe_ratio', 0) for s in backtest_results.get('strategies', [])]) if backtest_results.get('strategies') else 0,
                'data_quality_pass': metadata.data_quality_score > 0.7,
                'authenticity_pass': metadata.authenticity_verified
            }
        }
        
        # 保存JSON文件
        json_file = self.output_dir / f"{metadata.report_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False, default=str)
        
        return json.dumps(json_report, indent=2, ensure_ascii=False, default=str)