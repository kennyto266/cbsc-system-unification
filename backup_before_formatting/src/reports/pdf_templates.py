"""
报告模板系统

提供预定义的报告模板，包括：
- 性能分析模板
- 风险评估模板
- 策略对比模板
- 执行摘要模板
- 技术附录模板
"""

from pathlib import Path
from typing import Any, Dict, List

from jinja2 import BaseLoader, Environment, Template


class ReportTemplates:
    """
    报告模板管理器

    管理和渲染各种报告模板
    """

    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """加载预定义模板"""

        # 执行摘要模板
        self.templates["executive_summary"] = self._create_executive_summary_template()

        # 性能分析模板
        self.templates["performance_analysis"] = self._create_performance_template()

        # 风险评估模板
        self.templates["risk_assessment"] = self._create_risk_template()

        # 策略对比模板
        self.templates["strategy_comparison"] = (
            self._create_strategy_comparison_template()
        )

        # 技术附录模板
        self.templates["technical_appendix"] = (
            self._create_technical_appendix_template()
        )

    def _create_executive_summary_template(self) -> Template:
        """创建执行摘要模板"""
        template_str = """
        <para>
        <b>报告概述</b><br/>
        本报告分析了{{ symbol }}在{{ period }}期间的投资表现。整体来看，{% if total_return > 0 %}该投资实现了{{ total_return }}%的正收益{% else %}该投资出现了{{ total_return }}%的亏损{% endif %}，年化收益率为{{ annual_return }}%。
        </para>

        <para>
        <b>关键发现</b><br/>
        • 最大回撤为{{ max_drawdown }}%，发生在{{ max_drawdown_date }}<br/>
        • 夏普比率为{{ sharpe_ratio }}，{% if sharpe_ratio > 1.0 %}表现优秀{% elif sharpe_ratio > 0.5 %}表现良好{% else %}表现一般{% endif %}<br/>
        • 总共执行了{{ total_trades }}笔交易，胜率为{{ win_rate }}%<br/>
        • 波动率为{{ volatility }}%，年化波动率为{{ annual_volatility }}%
        </para>

        <para>
        <b>投资建议</b><br/>
        {% if recommendation == 'buy' %}
        基于分析结果，建议<font color="green">买入</font>该股票。技术指标显示上升趋势，且风险可控。
        {% elif recommendation == 'hold' %}
        基于分析结果，建议<font color="blue">持有</font>该股票。当前价格处于合理区间，建议等待更好的入场时机。
        {% else %}
        基于分析结果，建议<font color="red">卖出</font>该股票。技术指标显示下降趋势，建议规避风险。
        {% endif %}
        </para>
        """
        return Template(template_str)

    def _create_performance_template(self) -> Template:
        """创建性能分析模板"""
        template_str = """
        <para>
        <b>收益表现</b><br/>
        </para>

        <para>
        <b>收益率分析</b><br/>
        • 累计收益率：{{ total_return }}%<br/>
        • 年化收益率：{{ annual_return }}%<br/>
        • 月平均收益率：{{ monthly_avg_return }}%<br/>
        • 最佳单月收益：{{ best_month }}%<br/>
        • 最差单月收益：{{ worst_month }}%
        </para>

        <para>
        <b>风险指标</b><br/>
        • 年化波动率：{{ annual_volatility }}%<br/>
        • 夏普比率：{{ sharpe_ratio }}<br/>
        • 索提诺比率：{{ sortino_ratio }}<br/>
        • 最大回撤：{{ max_drawdown }}%<br/>
        • 回撤持续时间：{{ max_drawdown_duration }}天
        </para>

        <para>
        <b>交易统计</b><br/>
        • 总交易次数：{{ total_trades }}<br/>
        • 胜率：{{ win_rate }}%<br/>
        • 平均持仓时间：{{ avg_holding_period }}天<br/>
        • 盈亏比：{{ profit_loss_ratio }}
        </para>
        """
        return Template(template_str)

    def _create_risk_template(self) -> Template:
        """创建风险评估模板"""
        template_str = """
        <para>
        <b>风险概览</b><br/>
        本节对投资组合进行全面的风险评估，包括市场风险、流动性风险和操作风险等。
        </para>

        <para>
        <b>市场风险</b><br/>
        • 贝塔系数：{{ beta }} (市场敏感度)<br/>
        • 价值at风险(VaR)：{{ var_95 }}% (95 % 置信度)<br/>
        • 条件风险价值(CVaR)：{{ cvar_95 }}%<br/>
        • 下行风险：{{ downside_risk }}%
        </para>

        <para>
        <b>风险分散</b><br/>
        • 行业集中度：{{ sector_concentration }}%<br/>
        • 前五大持仓占比：{{ top5_holdings }}%<br/>
        • 股票数量：{{ num_stocks }}<br/>
        • 有效组合数：{{ effective_portfolio }}
        </para>

        <para>
        <b>流动性风险</b><br/>
        • 平均日成交额：{{ avg_daily_volume }}万<br/>
        • 持仓换手率：{{ turnover_rate }}%<br/>
        • 流动性得分：{{ liquidity_score }}/10
        </para>

        <para>
        {% if risk_level == 'high' %}
        <b><font color="red">风险警告</font></b><br/>
        当前投资组合风险等级为高。建议适当降低仓位或增加对冲工具。
        {% elif risk_level == 'medium' %}
        <b><font color="orange">风险提示</font></b><br/>
        当前投资组合风险等级为中。建议持续监控市场变化。
        {% else %}
        <b><font color="green">风险可控</font></b><br/>
        当前投资组合风险等级为低。投资组合结构合理。
        {% endif %}
        </para>
        """
        return Template(template_str)

    def _create_strategy_comparison_template(self) -> Template:
        """创建策略对比模板"""
        template_str = """
        <para>
        <b>策略对比分析</b><br/>
        本节对比分析不同投资策略在相同时间段内的表现。
        </para>

        <para>
        <b>策略收益对比</b><br/>
        {% for strategy in strategies %}
        • {{ strategy.name }}：累计收益{{ strategy.total_return }}%，夏普比率{{ strategy.sharpe_ratio }}<br/>
        {% endfor %}
        </para>

        <para>
        <b>风险收益特征</b><br/>
        {% for strategy in strategies %}
        {{ strategy.name }}：<br/>
        &nbsp;&nbsp;- 波动率：{{ strategy.volatility }}%<br/>
        &nbsp;&nbsp;- 最大回撤：{{ strategy.max_drawdown }}%<br/>
        &nbsp;&nbsp;- 胜率：{{ strategy.win_rate }}%<br/>
        {% endfor %}
        </para>

        <para>
        <b>综合评价</b><br/>
        {% set best_sharpe = strategies | sort(attribute='sharpe_ratio', reverse=True) | first %}
        {% set best_return = strategies | sort(attribute='total_return', reverse=True) | first %}
        从夏普比率来看，{{ best_sharpe.name }}策略表现最佳({{ best_sharpe.sharpe_ratio }})。<br/>
        从累计收益来看，{{ best_return.name }}策略表现最佳({{ best_return.total_return }}%)。<br/>
        综合考虑风险收益比，推荐使用{{ best_sharpe.name }}策略。
        </para>
        """
        return Template(template_str)

    def _create_technical_appendix_template(self) -> Template:
        """创建技术附录模板"""
        template_str = """
        <para>
        <b>技术指标说明</b><br/>
        </para>

        <para>
        <b>移动平均线(MA)</b><br/>
        移动平均线是技术分析中最基础的指标之一，用于平滑价格波动，识别趋势方向。<br/>
        计算方法：MA(n) = (C1 + C2 + ... + Cn) / n<br/>
        其中C为收盘价，n为周期数。
        </para>

        <para>
        <b>相对强弱指数(RSI)</b><br/>
        RSI是一种动量指标，用于衡量价格变动的速度和幅度。<br/>
        公式：RSI = 100 - 100 / (1 + RS)<br/>
        其中RS为平均上涨幅度与平均下跌幅度的比值。
        </para>

        <para>
        <b>MACD指标</b><br/>
        MACD(指数平滑异同移动平均线)由快线DIF、慢线DEA和MACD柱状图组成。<br/>
        DIF = EMA(12) - EMA(26)<br/>
        DEA = EMA(DIF, 9)<br/>
        MACD = 2 * (DIF - DEA)
        </para>

        <para>
        <b>布林带(BB)</b><br/>
        布林带由上轨、中轨和下轨组成，用于判断价格的高低估状态。<br/>
        中轨 = MA(n)<br/>
        上轨 = MA(n) + k * σ<br/>
        下轨 = MA(n) - k * σ<br/>
        其中σ为标准差，k为倍数(通常为2)。
        </para>

        <para>
        <b>数据来源</b><br/>
        本报告中的所有数据均来自公开市场数据源，包括但不限于：<br/>
        • 港交所(HKEX)官方数据<br/>
        • Yahoo Finance<br/>
        • Alpha Vantage<br/>
        • 其他第三方数据提供商
        </para>

        <para>
        <b>免责声明</b><br/>
        本报告仅供参考，不构成投资建议。投资有风险，入市需谨慎。过往表现不代表未来结果。
        </para>
        """
        return Template(template_str)

    def get_template(self, name: str) -> Template:
        """获取模板"""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return list(self.templates.keys())

    def add_template(self, name: str, template_str: str) -> None:
        """添加自定义模板"""
        self.templates[name] = Template(template_str)

    def render_template(
        self,
        template_name: str,
        **kwargs: Any,
    ) -> str:
        """
        渲染模板

        Args:
            template_name: 模板名称
            **kwargs: 模板变量

        Returns:
            渲染后的HTML字符串
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板 {template_name} 不存在")

        return template.render(**kwargs)
