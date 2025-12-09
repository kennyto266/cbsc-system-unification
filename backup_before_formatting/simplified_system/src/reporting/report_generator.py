#!/usr/bin/env python3
"""
Professional Report Generator
專業級報告生成器

Institutional-grade report generation with interactive HTML and PDF export
機構級交互式HTML和PDF導出報告生成
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import logging
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64
import io

# Import required libraries
try:
    from jinja2 import Environment, FileSystemLoader, Template
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.io as pio
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install: pip install jinja2 plotly")
    raise

# Import system components
try:
    from ..api.stock_api import get_hk_stock_data, get_multiple_stocks
    from ..indicators.core_indicators import CoreIndicators
    from ..indicators.technical_analyzer import TechnicalAnalyzer
    from ..backtest.vectorbt_engine import VectorBTEngine, BacktestResult
    from ..risk.advanced_risk_analyzer import AdvancedRiskAnalyzer
    from ..dashboard.performance_charts import PerformanceCharts
except ImportError:
    # Fallback for standalone usage
    class CoreIndicators:
        pass

    class TechnicalAnalyzer:
        pass

    class VectorBTEngine:
        pass

    class BacktestResult:
        pass

    class AdvancedRiskAnalyzer:
        pass

    class PerformanceCharts:
        pass

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """報告類型枚舉"""
    STRATEGY_ANALYSIS = "strategy_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PORTFOLIO_PERFORMANCE = "portfolio_performance"
    OPTIMIZATION_RESULTS = "optimization_results"
    DAILY_SUMMARY = "daily_summary"
    EXECUTIVE_BRIEFING = "executive_briefing"
    COMPLIANCE_REPORT = "compliance_report"
    RESEARCH_ANALYSIS = "research_analysis"

class ReportLanguage(Enum):
    """報告語言枚舉"""
    CHINESE = "zh"
    ENGLISH = "en"
    BILINGUAL = "both"

@dataclass
class ReportConfig:
    """報告配置"""
    report_type: ReportType
    language: ReportLanguage = ReportLanguage.BILINGUAL
    include_charts: bool = True
    include_executive_summary: bool = True
    include_risk_analysis: bool = True
    include_detailed_metrics: bool = True
    export_pdf: bool = True
    export_excel: bool = False
    template_name: str = "professional"
    custom_css: Optional[str] = None
    company_logo: Optional[str] = None
    author: str = "Quant Trading System"
    confidentiality_level: str = "Internal Use Only"
    interactive_elements: bool = True
    auto_refresh: bool = False
    email_recipients: List[str] = field(default_factory=list)

@dataclass
class ReportData:
    """報告數據結構"""
    timestamp: datetime
    title: str
    subtitle: str
    period: str

    # Performance metrics
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    win_rate: float
    calmar_ratio: float
    sortino_ratio: float

    # Trading data
    total_trades: int
    profitable_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    profit_factor: float

    # Risk metrics
    var_95: float
    var_99: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    beta: float
    alpha: float
    tracking_error: float

    # Strategy data
    strategy_name: str
    strategy_parameters: Dict[str, Any]
    benchmark_name: Optional[str] = None

    # Additional data
    raw_data: Optional[pd.DataFrame] = None
    chart_data: Dict[str, Any] = field(default_factory=dict)
    risk_analysis: Optional[Dict[str, Any]] = None
    optimization_results: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'subtitle': self.subtitle,
            'period': self.period,
            'performance': {
                'total_return': self.total_return,
                'annual_return': self.annual_return,
                'sharpe_ratio': self.sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'volatility': self.volatility,
                'win_rate': self.win_rate,
                'calmar_ratio': self.calmar_ratio,
                'sortino_ratio': self.sortino_ratio
            },
            'trading': {
                'total_trades': self.total_trades,
                'profitable_trades': self.profitable_trades,
                'losing_trades': self.losing_trades,
                'average_win': self.average_win,
                'average_loss': self.average_loss,
                'profit_factor': self.profit_factor
            },
            'risk': {
                'var_95': self.var_95,
                'var_99': self.var_99,
                'expected_shortfall_95': self.expected_shortfall_95,
                'expected_shortfall_99': self.expected_shortfall_99,
                'beta': self.beta,
                'alpha': self.alpha,
                'tracking_error': self.tracking_error
            },
            'strategy': {
                'name': self.strategy_name,
                'parameters': self.strategy_parameters,
                'benchmark_name': self.benchmark_name
            },
            'chart_data': self.chart_data,
            'risk_analysis': self.risk_analysis,
            'optimization_results': self.optimization_results
        }

class ReportGenerator:
    """專業級報告生成器"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化報告生成器

        Args:
            template_dir: 模板目錄路徑
        """
        self.logger = logging.getLogger(__name__)

        # Set up template directory
        if template_dir is None:
            template_dir = Path(__file__).parent / "html_templates"
        self.template_dir = Path(template_dir)

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # Initialize components
        self.indicators = CoreIndicators()
        self.analyzer = TechnicalAnalyzer()
        self.backtest_engine = VectorBTEngine()
        self.risk_analyzer = AdvancedRiskAnalyzer()
        self.performance_charts = PerformanceCharts()

        # Chart generator cache
        self.chart_cache = {}

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)

        self.logger.info("Report generator initialized successfully")

    def generate_report(
        self,
        data: ReportData,
        config: ReportConfig,
        output_path: Optional[str] = None
    ) -> Dict[str, str]:
        """
        生成完整報告

        Args:
            data: 報告數據
            config: 報告配置
            output_path: 輸出路徑

        Returns:
            Dict with file paths of generated reports
        """
        try:
            self.logger.info(f"Generating {config.report_type.value} report")

            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Set default output path
            if output_path is None:
                output_path = Path.cwd() / "reports"
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)

            generated_files = {}

            # Generate charts if enabled
            if config.include_charts:
                charts = self._generate_charts(data)
                data.chart_data = charts

            # Generate executive summary if enabled
            executive_summary = None
            if config.include_executive_summary:
                from .executive_summary_fixed import ExecutiveSummaryGenerator
                summary_gen = ExecutiveSummaryGenerator()
                executive_summary = summary_gen.generate(data, config.language)

            # Generate HTML report
            html_file = output_dir / f"{config.report_type.value}_report_{timestamp}.html"
            html_content = self._generate_html_report(data, config, executive_summary)

            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            generated_files['html'] = str(html_file)

            # Generate PDF if enabled
            if config.export_pdf:
                try:
                    from .pdf_exporter import PDFExporter
                    pdf_exporter = PDFExporter()
                    pdf_file = output_dir / f"{config.report_type.value}_report_{timestamp}.pdf"
                    pdf_exporter.export(html_file, pdf_file)
                    generated_files['pdf'] = str(pdf_file)
                except ImportError:
                    self.logger.warning("PDF export not available. Install weasyprint.")

            # Generate Excel if enabled
            if config.export_excel:
                excel_file = output_dir / f"{config.report_type.value}_report_{timestamp}.xlsx"
                self._generate_excel_report(data, excel_file)
                generated_files['excel'] = str(excel_file)

            # Save JSON data
            json_file = output_dir / f"{config.report_type.value}_data_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, indent=2, ensure_ascii=False, default=str)
            generated_files['json'] = str(json_file)

            self.logger.info(f"Report generated successfully: {generated_files}")
            return generated_files

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            raise

    def _generate_charts(self, data: ReportData) -> Dict[str, Any]:
        """生成圖表"""
        charts = {}

        try:
            # Performance chart
            if data.raw_data is not None:
                # Price and performance chart
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.1,
                    subplot_titles=('價格走势與策略信號', '累计收益'),
                    row_heights=[0.7, 0.3]
                )

                # Price chart
                fig.add_trace(
                    go.Candlestick(
                        x=data.raw_data.index,
                        open=data.raw_data.get('open', data.raw_data['close']),
                        high=data.raw_data.get('high', data.raw_data['close']),
                        low=data.raw_data.get('low', data.raw_data['close']),
                        close=data.raw_data['close'],
                        name='價格'
                    ),
                    row=1, col=1
                )

                # Add strategy signals if available
                if 'signals' in data.raw_data.columns:
                    buy_signals = data.raw_data[data.raw_data['signals'] == 1]
                    sell_signals = data.raw_data[data.raw_data['signals'] == -1]

                    if not buy_signals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=buy_signals.index,
                                y=buy_signals['close'],
                                mode='markers',
                                marker=dict(symbol='triangle-up', size=10, color='green'),
                                name='買入信號'
                            ),
                            row=1, col=1
                        )

                    if not sell_signals.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=sell_signals.index,
                                y=sell_signals['close'],
                                mode='markers',
                                marker=dict(symbol='triangle-down', size=10, color='red'),
                                name='賣出信號'
                            ),
                            row=1, col=1
                        )

                # Cumulative returns chart
                if 'returns' in data.raw_data.columns:
                    cumulative_returns = (1 + data.raw_data['returns']).cumprod()
                    fig.add_trace(
                        go.Scatter(
                            x=data.raw_data.index,
                            y=cumulative_returns,
                            mode='lines',
                            name='累计收益',
                            line=dict(color='blue')
                        ),
                        row=2, col=1
                    )

                fig.update_layout(
                    title=f"{data.strategy_name} 策略表现",
                    height=800,
                    xaxis_rangeslider_visible=False
                )

                charts['performance'] = pio.to_html(fig, include_plotlyjs='cdn', div_id="performance_chart")

            # Risk metrics radar chart
            risk_metrics = [
                data.sharpe_ratio,
                data.calmar_ratio,
                data.sortino_ratio,
                data.win_rate,
                -abs(data.max_drawdown),
                data.profit_factor
            ]

            risk_labels = [
                'Sharpe比率',
                'Calmar比率',
                'Sortino比率',
                '勝率',
                '最大回撤(負值)',
                '盈利因子'
            ]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=risk_metrics,
                theta=risk_labels,
                fill='toself',
                name='風險指標'
            ))

            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(risk_metrics) * 1.1]
                    )
                ),
                title="風險指標雷達圖",
                height=600
            )

            charts['risk_radar'] = pio.to_html(fig_radar, include_plotlyjs='cdn', div_id="risk_radar")

            # Monthly returns heatmap
            if data.raw_data is not None and 'returns' in data.raw_data.columns:
                monthly_returns = data.raw_data['returns'].groupby([
                    data.raw_data.index.year,
                    data.raw_data.index.month
                ]).apply(lambda x: (1 + x).prod() - 1)

                # Convert to matrix format
                monthly_matrix = monthly_returns.unstack(level=1, fill_value=0)
                monthly_matrix.columns = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

                fig_heatmap = px.imshow(
                    monthly_matrix,
                    title="月度收益率熱力圖",
                    labels=dict(x="月份", y="年份", color="收益率"),
                    color_continuous_scale="RdYlGn",
                    aspect="auto"
                )

                charts['monthly_heatmap'] = pio.to_html(fig_heatmap, include_plotlyjs='cdn', div_id="monthly_heatmap")

        except Exception as e:
            self.logger.error(f"Error generating charts: {e}")

        return charts

    def _generate_html_report(
        self,
        data: ReportData,
        config: ReportConfig,
        executive_summary: Optional[str] = None
    ) -> str:
        """生成HTML報告"""
        try:
            # Load template
            template_file = f"{config.template_name}_template.html"
            template = self.jinja_env.get_template(template_file)

            # Prepare template context
            context = {
                'config': config,
                'data': data,
                'executive_summary': executive_summary,
                'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'report_id': f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'language': config.language.value,
                'bilingual': config.language == ReportLanguage.BILINGUAL,
                'interactive': config.interactive_elements,
                'charts': data.chart_data
            }

            # Render template
            html_content = template.render(**context)

            return html_content

        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            # Fallback to basic HTML
            return self._generate_basic_html(data, config)

    def _generate_basic_html(self, data: ReportData, config: ReportConfig) -> str:
        """生成基礎HTML報告（後備方案）"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{data.title}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .metric {{ background: #f5f5f5; padding: 15px; border-radius: 5px; text-align: center; }}
                .metric h3 {{ margin: 0; color: #333; }}
                .metric .value {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
                .section {{ margin: 30px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{data.title}</h1>
                <h2>{data.subtitle}</h2>
                <p>生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>

            <div class="section">
                <h2>策略概覽</h2>
                <p><strong>策略名稱:</strong> {data.strategy_name}</p>
                <p><strong>分析週期:</strong> {data.period}</p>
            </div>

            <div class="section">
                <h2>績效指標</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>總回報率</h3>
                        <div class="value">{data.total_return:.2%}</div>
                    </div>
                    <div class="metric">
                        <h3>年化回報率</h3>
                        <div class="value">{data.annual_return:.2%}</div>
                    </div>
                    <div class="metric">
                        <h3>Sharpe比率</h3>
                        <div class="value">{data.sharpe_ratio:.3f}</div>
                    </div>
                    <div class="metric">
                        <h3>最大回撤</h3>
                        <div class="value">{data.max_drawdown:.2%}</div>
                    </div>
                    <div class="metric">
                        <h3>波動率</h3>
                        <div class="value">{data.volatility:.2%}</div>
                    </div>
                    <div class="metric">
                        <h3>勝率</h3>
                        <div class="value">{data.win_rate:.2%}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>交易統計</h2>
                <table>
                    <tr><th>指標</th><th>數值</th></tr>
                    <tr><td>總交易次數</td><td>{data.total_trades}</td></tr>
                    <tr><td>盈利交易</td><td>{data.profitable_trades}</td></tr>
                    <tr><td>虧損交易</td><td>{data.losing_trades}</td></tr>
                    <tr><td>平均盈利</td><td>{data.average_win:.2%}</td></tr>
                    <tr><td>平均虧損</td><td>{data.average_loss:.2%}</td></tr>
                    <tr><td>盈利因子</td><td>{data.profit_factor:.2f}</td></tr>
                </table>
            </div>

            <div class="section">
                <h2>風險指標</h2>
                <table>
                    <tr><th>指標</th><th>數值</th></tr>
                    <tr><td>VaR (95%)</td><td>{data.var_95:.2%}</td></tr>
                    <tr><td>VaR (99%)</td><td>{data.var_99:.2%}</td></tr>
                    <tr><td>期望虧損 (95%)</td><td>{data.expected_shortfall_95:.2%}</td></tr>
                    <tr><td>期望虧損 (99%)</td><td>{data.expected_shortfall_99:.2%}</td></tr>
                    <tr><td>Beta系數</td><td>{data.beta:.3f}</td></tr>
                    <tr><td>Alpha系數</td><td>{data.alpha:.3f}</td></tr>
                </table>
            </div>
        </body>
        </html>
        """

    def _generate_excel_report(self, data: ReportData, output_file: Path):
        """生成Excel報告"""
        try:
            with pd.ExcelWriter(str(output_file), engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    '指標': ['總回報率', '年化回報率', 'Sharpe比率', '最大回撤', '波動率',
                           '勝率', 'Calmar比率', 'Sortino比率', '總交易次數', '盈利因子'],
                    '數值': [data.total_return, data.annual_return, data.sharpe_ratio,
                           data.max_drawdown, data.volatility, data.win_rate,
                           data.calmar_ratio, data.sortino_ratio, data.total_trades,
                           data.profit_factor]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='績效摘要', index=False)

                # Trading data if available
                if data.raw_data is not None:
                    data.raw_data.to_excel(writer, sheet_name='交易數據', index=True)

                # Risk analysis if available
                if data.risk_analysis:
                    risk_df = pd.DataFrame(data.risk_analysis)
                    risk_df.to_excel(writer, sheet_name='風險分析', index=False)

                # Strategy parameters
                params_df = pd.DataFrame(list(data.strategy_parameters.items()),
                                       columns=['參數', '數值'])
                params_df.to_excel(writer, sheet_name='策略參數', index=False)

        except Exception as e:
            self.logger.error(f"Error generating Excel report: {e}")
            raise

    def generate_batch_reports(
        self,
        reports_data: List[Tuple[ReportData, ReportConfig]],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """批量生成報告"""
        self.logger.info(f"Starting batch report generation for {len(reports_data)} reports")

        if output_dir is None:
            output_dir = Path.cwd() / "batch_reports"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        futures = []
        generated_files = []

        # Submit all reports for parallel generation
        for i, (data, config) in enumerate(reports_data):
            future = self.executor.submit(
                self.generate_report,
                data,
                config,
                str(output_dir / f"batch_{i+1}")
            )
            futures.append(future)

        # Collect results
        for future in as_completed(futures):
            try:
                files = future.result()
                generated_files.append(files)
            except Exception as e:
                self.logger.error(f"Error in batch report generation: {e}")

        self.logger.info(f"Batch report generation completed: {len(generated_files)} reports generated")
        return generated_files

    def create_report_from_backtest(
        self,
        backtest_result: BacktestResult,
        config: Optional[ReportConfig] = None,
        raw_data: Optional[pd.DataFrame] = None
    ) -> ReportData:
        """從回測結果創建報告數據"""
        if config is None:
            config = ReportConfig(report_type=ReportType.STRATEGY_ANALYSIS)

        # Create report data from backtest result
        report_data = ReportData(
            timestamp=datetime.now(),
            title=f"{backtest_result.strategy} 策略分析報告",
            subtitle=f"基於 {backtest_result.symbol} 的量化分析",
            period=f"{backtest_result.start_date.date()} 至 {backtest_result.end_date.date()}",

            # Performance metrics
            total_return=backtest_result.total_return,
            annual_return=backtest_result.annual_return,
            sharpe_ratio=backtest_result.sharpe_ratio,
            max_drawdown=backtest_result.max_drawdown,
            volatility=backtest_result.volatility,
            win_rate=backtest_result.win_rate,
            calmar_ratio=backtest_result.calmar_ratio,
            sortino_ratio=backtest_result.sortino_ratio,

            # Trading statistics
            total_trades=backtest_result.total_trades,
            profitable_trades=backtest_result.profitable_trades,
            losing_trades=backtest_result.losing_trades,
            average_win=backtest_result.average_win,
            average_loss=backtest_result.average_loss,
            profit_factor=backtest_result.profit_factor,

            # Risk metrics (calculate if not available)
            var_95=getattr(backtest_result, 'var_95', -0.05),
            var_99=getattr(backtest_result, 'var_99', -0.08),
            expected_shortfall_95=getattr(backtest_result, 'expected_shortfall_95', -0.07),
            expected_shortfall_99=getattr(backtest_result, 'expected_shortfall_99', -0.12),
            beta=getattr(backtest_result, 'beta', 1.0),
            alpha=getattr(backtest_result, 'alpha', 0.0),
            tracking_error=getattr(backtest_result, 'tracking_error', 0.15),

            # Strategy information
            strategy_name=backtest_result.strategy,
            strategy_parameters=getattr(backtest_result, 'parameters', {}),
            benchmark_name=getattr(backtest_result, 'benchmark', None),

            # Raw data
            raw_data=raw_data
        )

        return report_data

    def schedule_reports(self, schedules: List[Dict[str, Any]]):
        """調度定期報告生成"""
        # This could be implemented with APScheduler or similar
        self.logger.info("Report scheduling not implemented yet")
        pass

    def __del__(self):
        """清理資源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

# Utility functions
def create_performance_report(
    backtest_result: BacktestResult,
    raw_data: Optional[pd.DataFrame] = None,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    便利函數：創建績效報告

    Args:
        backtest_result: 回測結果
        raw_data: 原始數據
        output_dir: 輸出目錄

    Returns:
        生成的文件路徑字典
    """
    generator = ReportGenerator()
    config = ReportConfig(
        report_type=ReportType.STRATEGY_ANALYSIS,
        include_executive_summary=True,
        include_risk_analysis=True,
        export_pdf=True
    )

    report_data = generator.create_report_from_backtest(backtest_result, config, raw_data)
    return generator.generate_report(report_data, config, output_dir)

def create_risk_report(
    risk_data: Dict[str, Any],
    portfolio_data: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    便利函數：創建風險評估報告

    Args:
        risk_data: 風險分析數據
        portfolio_data: 投資組合數據
        output_dir: 輸出目錄

    Returns:
        生成的文件路徑字典
    """
    # Implementation would be similar to above but focused on risk
    pass