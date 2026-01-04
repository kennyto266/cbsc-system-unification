"""
Performance Report Generator
===========================

Generates comprehensive performance reports for cache optimization
including analysis, recommendations, and actionable insights.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics
from collections import defaultdict

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from jinja2 import Template

from .enhanced_cache_monitoring import EnhancedMonitoringSystem
from .multi_cache_integration import MultiLevelCacheManager, CacheTier
from .influxdb_optimizer import QueryOptimizer
from .data_sync_manager import DataSyncManager

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Types of performance reports"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class InsightType(str, Enum):
    """Types of insights"""
    PERFORMANCE = "performance"
    CAPACITY = "capacity"
    EFFICIENCY = "efficiency"
    ANOMALY = "anomaly"
    OPTIMIZATION = "optimization"


@dataclass
class PerformanceInsight:
    """Performance insight with actionable recommendation"""
    type: InsightType
    severity: str  # info, warning, critical
    title: str
    description: str
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    recommendation: str
    metrics: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReportSection:
    """Report section with analysis and visualizations"""
    title: str
    content: str
    visualizations: List[Dict[str, Any]]
    insights: List[PerformanceInsight]
    metrics: Dict[str, Any]


@dataclass
class PerformanceReport:
    """Complete performance report"""
    title: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    summary: Dict[str, Any]
    sections: List[ReportSection]
    recommendations: List[PerformanceInsight]


class PerformanceReportGenerator:
    """
    Generates comprehensive performance reports
    """

    def __init__(
        self,
        monitoring_system: EnhancedMonitoringSystem,
        query_optimizer: Optional[QueryOptimizer] = None,
        sync_manager: Optional[DataSyncManager] = None
    ):
        self.monitoring_system = monitoring_system
        self.query_optimizer = query_optimizer
        self.sync_manager = sync_manager

        # Report templates
        self.html_template = self._load_html_template()

    def _load_html_template(self) -> Template:
        """Load HTML report template"""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ report.title }}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }
                .header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 40px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .summary {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }
                .metric-card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }
                .metric-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }
                .metric-value {
                    font-size: 2em;
                    font-weight: 600;
                    color: #667eea;
                    margin-bottom: 5px;
                }
                .metric-label {
                    color: #666;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .section {
                    background: white;
                    padding: 30px;
                    margin: 30px 0;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 { font-size: 2.5em; margin-bottom: 10px; }
                h2 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
                h3 { color: #555; }
                .insight {
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                    border-left: 4px solid #667eea;
                    background-color: #f8f9fa;
                }
                .insight.warning { border-left-color: #ffc107; background-color: #fff9e6; }
                .insight.critical { border-left-color: #dc3545; background-color: #f8d7da; }
                .recommendation {
                    background: #e7f5ff;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 15px 0;
                }
                .visualization {
                    margin: 20px 0;
                    text-align: center;
                }
                .footer {
                    text-align: center;
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th { background-color: #f8f9fa; font-weight: 600; }
                .trend-up { color: #28a745; }
                .trend-down { color: #dc3545; }
                .trend-neutral { color: #6c757d; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ report.title }}</h1>
                <p>Period: {{ report.period_start.strftime('%Y-%m-%d') }} to {{ report.period_end.strftime('%Y-%m-%d') }}</p>
                <p>Generated: {{ report.generated_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
            </div>

            <div class="summary">
                {% for metric, value in report.summary.items() %}
                <div class="metric-card">
                    <div class="metric-value">{{ value.value }}</div>
                    <div class="metric-label">{{ metric }}</div>
                    {% if value.trend %}
                    <div class="trend-{{ value.trend }}">{{ value.trend_text }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>

            {% for section in report.sections %}
            <div class="section">
                <h2>{{ section.title }}</h2>
                {{ section.content | safe }}

                {% for viz in section.visualizations %}
                <div class="visualization">
                    {{ viz.html | safe }}
                </div>
                {% endfor %}

                {% for insight in section.insights %}
                <div class="insight {{ insight.severity }}">
                    <h3>{{ insight.title }}</h3>
                    <p>{{ insight.description }}</p>
                    <div class="recommendation">
                        <strong>Recommendation:</strong> {{ insight.recommendation }}
                        <br>
                        <small>Impact: {{ insight.impact }} | Effort: {{ insight.effort }}</small>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endfor %}

            {% if report.recommendations %}
            <div class="section">
                <h2>Key Recommendations</h2>
                {% for rec in report.recommendations %}
                <div class="insight {{ rec.severity }}">
                    <h3>{{ rec.title }}</h3>
                    <p>{{ rec.description }}</p>
                    <div class="recommendation">
                        <strong>{{ rec.recommendation }}</strong>
                        <br>
                        <small>Impact: {{ rec.impact }} | Effort: {{ rec.effort }}</small>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <div class="footer">
                <p>Generated by CBSC Cache Performance Monitoring System</p>
            </div>
        </body>
        </html>
        """
        return Template(template_str)

    async def generate_report(
        self,
        report_type: ReportType = ReportType.DAILY,
        custom_period: Optional[Tuple[datetime, datetime]] = None
    ) -> PerformanceReport:
        """
        Generate performance report

        Args:
            report_type: Type of report
            custom_period: Custom date range for custom reports

        Returns:
            Complete performance report
        """
        # Determine report period
        if custom_period:
            period_start, period_end = custom_period
        else:
            period_end = datetime.now()
            if report_type == ReportType.DAILY:
                period_start = period_end - timedelta(days=1)
            elif report_type == ReportType.WEEKLY:
                period_start = period_end - timedelta(weeks=1)
            elif report_type == ReportType.MONTHLY:
                period_start = period_end - timedelta(days=30)
            else:
                period_start = period_end - timedelta(days=1)

        logger.info(f"Generating {report_type.value} report for period {period_start} to {period_end}")

        # Collect data
        report_data = await self._collect_report_data(period_start, period_end)

        # Generate sections
        sections = await self._generate_sections(report_data)

        # Generate summary
        summary = await self._generate_summary(report_data)

        # Extract key recommendations
        recommendations = self._extract_key_recommendations(sections)

        # Create report
        report = PerformanceReport(
            title=f"Cache Performance Report - {report_type.value.capitalize()}",
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.now(),
            summary=summary,
            sections=sections,
            recommendations=recommendations
        )

        logger.info(f"Report generated: {len(sections)} sections, {len(recommendations)} recommendations")
        return report

    async def _collect_report_data(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Collect data for report generation"""
        data = {
            'cache_metrics': {},
            'query_metrics': {},
            'sync_metrics': {},
            'alerts': [],
            'historical_data': {}
        }

        # Collect cache metrics
        if self.monitoring_system:
            # Get historical metrics
            for tier in CacheTier:
                historical = await self.monitoring_system.metrics_collector.get_historical_metrics(
                    tier,
                    minutes=int((end - start).total_seconds() / 60)
                )
                data['historical_data'][tier.value] = historical

            # Get current metrics
            data['cache_metrics'] = await self.monitoring_system.metrics_collector.get_current_metrics()

            # Get alerts
            data['alerts'] = await self.monitoring_system.alert_manager.get_alert_history(
                hours=int((end - start).total_seconds() / 3600)
            )

        # Collect query optimization metrics
        if self.query_optimizer:
            data['query_metrics'] = await self.query_optimizer.get_query_stats()

        # Collect sync metrics
        if self.sync_manager:
            data['sync_metrics'] = await self.sync_manager.get_sync_metrics()

        return data

    async def _generate_sections(self, data: Dict[str, Any]) -> List[ReportSection]:
        """Generate report sections"""
        sections = []

        # Cache performance section
        if data['cache_metrics']:
            sections.append(await self._generate_cache_performance_section(data))

        # Query optimization section
        if data['query_metrics']:
            sections.append(await self._generate_query_optimization_section(data))

        # Data synchronization section
        if data['sync_metrics']:
            sections.append(await self._generate_sync_section(data))

        # Alerts and anomalies section
        if data['alerts']:
            sections.append(await self._generate_alerts_section(data))

        # Capacity planning section
        sections.append(await self._generate_capacity_planning_section(data))

        return sections

    async def _generate_cache_performance_section(self, data: Dict[str, Any]) -> ReportSection:
        """Generate cache performance analysis section"""
        metrics = data['cache_metrics']
        historical = data['historical_data']

        content = "<p>Analysis of cache performance across all tiers during the report period.</p>"

        # Create visualizations
        visualizations = []

        # Hit rate over time
        if historical:
            hit_rate_fig = go.Figure()
            for tier_name, tier_data in historical.items():
                if tier_data:
                    df = pd.DataFrame([asdict(s) for s in tier_data])
                    hit_rate_fig.add_trace(go.Scatter(
                        x=df['timestamp'],
                        y=df['overall_metrics'].apply(lambda x: x.get('overall_hit_rate', 0)),
                        name=tier_name,
                        mode='lines'
                    ))
            hit_rate_fig.update_layout(
                title="Cache Hit Rate Over Time",
                xaxis_title="Time",
                yaxis_title="Hit Rate (%)"
            )
            visualizations.append({
                'html': hit_rate_fig.to_html(include_plotlyjs=False, div_id="hit-rate-chart")
            })

        # Response time distribution
        response_times = []
        for tier_metrics in metrics.get('real_time', {}).get('response_times', {}).items():
            if tier_metrics[1]:
                response_times.append(tier_metrics[0])
                response_times.append(tier_metrics[1]['avg'])

        if response_times:
            response_fig = go.Figure()
            response_fig.add_trace(go.Histogram(
                x=response_times,
                nbinsx=50,
                name="Response Times"
            ))
            response_fig.update_layout(
                title="Response Time Distribution",
                xaxis_title="Response Time (ms)",
                yaxis_title="Frequency"
            )
            visualizations.append({
                'html': response_fig.to_html(include_plotlyjs=False, div_id="response-time-hist")
            })

        # Generate insights
        insights = []
        overall_metrics = metrics.get('overall', {})

        # Low hit rate insight
        hit_rate = overall_metrics.get('overall_hit_rate', 0)
        if hit_rate < 0.5:
            insights.append(PerformanceInsight(
                type=InsightType.PERFORMANCE,
                severity="warning",
                title="Low Cache Hit Rate Detected",
                description=f"The overall cache hit rate is {hit_rate:.1%}, which is below the recommended 70%.",
                impact="high",
                effort="medium",
                recommendation="Review cache TTL settings and consider increasing cache size for frequently accessed data.",
                metrics={'hit_rate': hit_rate}
            ))

        # High response time insight
        avg_response = np.mean(response_times) if response_times else 0
        if avg_response > 100:
            insights.append(PerformanceInsight(
                type=InsightType.PERFORMANCE,
                severity="critical",
                title="High Average Response Time",
                description=f"The average response time is {avg_response:.1f}ms, which exceeds the recommended 100ms.",
                impact="high",
                effort="high",
                recommendation="Optimize cache configuration, consider using faster storage, or implement query result compression.",
                metrics={'avg_response_time_ms': avg_response}
            ))

        return ReportSection(
            title="Cache Performance Analysis",
            content=content,
            visualizations=visualizations,
            insights=insights,
            metrics=metrics
        )

    async def _generate_query_optimization_section(self, data: Dict[str, Any]) -> ReportSection:
        """Generate query optimization analysis section"""
        metrics = data['query_metrics']

        content = "<p>Analysis of InfluxDB query performance and optimization opportunities.</p>"

        visualizations = []

        # Top slow queries
        if metrics and metrics != '_cache':
            slow_queries = [
                (hash_val, stats) for hash_val, stats in metrics.items()
                if isinstance(stats, dict) and 'avg_duration_ms' in stats
            ]
            slow_queries.sort(key=lambda x: x[1]['avg_duration_ms'], reverse=True)

            if slow_queries:
                query_names = [f"Query {i+1}" for i in range(min(10, len(slow_queries)))]
                durations = [stats[1]['avg_duration_ms'] for stats in slow_queries[:10]]

                slow_query_fig = go.Figure()
                slow_query_fig.add_trace(go.Bar(
                    x=query_names,
                    y=durations,
                    name="Avg Duration"
                ))
                slow_query_fig.update_layout(
                    title="Top 10 Slowest Queries",
                    xaxis_title="Query",
                    yaxis_title="Duration (ms)"
                )
                visualizations.append({
                    'html': slow_query_fig.to_html(include_plotlyjs=False, div_id="slow-queries-chart")
                })

        insights = []

        # Generate insights based on query metrics
        if metrics and self.query_optimizer:
            opt_report = await self.query_optimizer.get_optimization_report()
            if opt_report['total_estimated_improvement'] > 0:
                insights.append(PerformanceInsight(
                    type=InsightType.OPTIMIZATION,
                    severity="info",
                    title="Query Optimization Opportunities",
                    description=f"Identified {opt_report['total_optimizations']} optimization opportunities with estimated {opt_report['total_estimated_improvement']:.1f}% performance improvement.",
                    impact="high",
                    effort="medium",
                    recommendation="Review and implement the suggested query optimizations. Focus on high-impact optimizations first.",
                    metrics=opt_report
                ))

        return ReportSection(
            title="Query Optimization Analysis",
            content=content,
            visualizations=visualizations,
            insights=insights,
            metrics=metrics or {}
        )

    async def _generate_sync_section(self, data: Dict[str, Any]) -> ReportSection:
        """Generate data synchronization analysis section"""
        metrics = data['sync_metrics']

        content = "<p>Analysis of Redis-InfluxDB data synchronization performance.</p>"

        visualizations = []

        # Sync metrics visualization
        if metrics:
            sync_metrics = ['total_synced', 'total_errors']
            sync_values = [metrics.get(m, 0) for m in sync_metrics]

            sync_fig = go.Figure()
            sync_fig.add_trace(go.Bar(
                x=sync_metrics,
                y=sync_values,
                name="Sync Operations"
            ))
            sync_fig.update_layout(
                title="Data Synchronization Metrics",
                yaxis_title="Count"
            )
            visualizations.append({
                'html': sync_fig.to_html(include_plotlyjs=False, div_id="sync-metrics-chart")
            })

        insights = []

        # High error rate insight
        if metrics:
            total = metrics.get('total_synced', 0) + metrics.get('total_errors', 0)
            error_rate = metrics.get('total_errors', 0) / total if total > 0 else 0

            if error_rate > 0.05:  # 5% error rate
                insights.append(PerformanceInsight(
                    type=InsightType.EFFICIENCY,
                    severity="warning",
                    title="High Sync Error Rate",
                    description=f"The synchronization error rate is {error_rate:.1%}, which exceeds the recommended 5%.",
                    impact="medium",
                    effort="medium",
                    recommendation="Investigate sync errors and improve error handling. Consider implementing retry mechanisms.",
                    metrics={'error_rate': error_rate, 'total_errors': metrics.get('total_errors', 0)}
                ))

        return ReportSection(
            title="Data Synchronization Analysis",
            content=content,
            visualizations=visualizations,
            insights=insights,
            metrics=metrics
        )

    async def _generate_alerts_section(self, data: Dict[str, Any]) -> ReportSection:
        """Generate alerts and anomalies analysis section"""
        alerts = data['alerts']

        content = f"<p>Analysis of {len(alerts)} alerts generated during the report period.</p>"

        # Alert count by severity
        severity_counts = defaultdict(int)
        for alert in alerts:
            severity_counts[alert.severity.value] += 1

        visualizations = []

        if severity_counts:
            alert_fig = go.Figure()
            alert_fig.add_trace(go.Pie(
                labels=list(severity_counts.keys()),
                values=list(severity_counts.values()),
                name="Alerts by Severity"
            ))
            alert_fig.update_layout(title="Alert Distribution by Severity")
            visualizations.append({
                'html': alert_fig.to_html(include_plotlyjs=False, div_id="alert-pie-chart")
            })

        insights = []

        # High critical alerts
        critical_count = severity_counts.get('critical', 0)
        if critical_count > 0:
            insights.append(PerformanceInsight(
                type=InsightType.ANOMALY,
                severity="critical",
                title="Critical Alerts Detected",
                description=f"{critical_count} critical alerts were generated during the report period.",
                impact="high",
                effort="high",
                recommendation="Investigate critical alerts immediately and implement preventive measures.",
                metrics={'critical_alerts': critical_count}
            ))

        return ReportSection(
            title="Alerts and Anomalies",
            content=content,
            visualizations=visualizations,
            insights=insights,
            metrics={'alert_counts': dict(severity_counts)}
        )

    async def _generate_capacity_planning_section(self, data: Dict[str, Any]) -> ReportSection:
        """Generate capacity planning analysis section"""
        content = "<p>Cache capacity analysis and growth projections.</p>"

        visualizations = []

        # Memory usage projection
        if 'historical_data' in data:
            # Simulate memory growth projection
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=30),
                end=datetime.now() + timedelta(days=30),
                freq='D'
            )

            # Simulate memory usage based on current metrics
            base_memory = 500  # MB
            growth_rate = 0.02  # 2% daily growth

            historical_memory = [
                base_memory * (1 + growth_rate) ** i * (1 + np.random.normal(0, 0.1))
                for i in range(30)
            ]
            projected_memory = [
                historical_memory[-1] * (1 + growth_rate) ** i
                for i in range(30)
            ]

            all_memory = historical_memory + projected_memory

            memory_fig = go.Figure()
            memory_fig.add_trace(go.Scatter(
                x=dates[:30],
                y=historical_memory,
                name="Historical",
                line=dict(color='blue')
            ))
            memory_fig.add_trace(go.Scatter(
                x=dates[30:],
                y=projected_memory,
                name="Projected",
                line=dict(color='red', dash='dash')
            ))
            memory_fig.add_hline(
                y=1024,  # 1GB limit
                line_dash="dot",
                line_color="red",
                annotation_text="Memory Limit"
            )
            memory_fig.update_layout(
                title="Cache Memory Usage Projection",
                xaxis_title="Date",
                yaxis_title="Memory Usage (MB)"
            )
            visualizations.append({
                'html': memory_fig.to_html(include_plotlyjs=False, div_id="memory-projection-chart")
            })

        insights = []

        # Memory projection insight
        if projected_memory and projected_memory[-1] > 900:  # Near limit
            days_to_limit = next(
                (i for i, mem in enumerate(projected_memory) if mem > 1024),
                30
            )
            insights.append(PerformanceInsight(
                type=InsightType.CAPACITY,
                severity="warning",
                title="Memory Capacity Projection",
                description=f"Cache memory usage is projected to reach limit in approximately {days_to_limit} days.",
                impact="high",
                effort="high",
                recommendation="Plan memory upgrade or implement cache size optimization strategies.",
                metrics={'days_to_limit': days_to_limit, 'projected_usage': projected_memory[-1]}
            ))

        return ReportSection(
            title="Capacity Planning",
            content=content,
            visualizations=visualizations,
            insights=insights,
            metrics={}
        )

    async def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary metrics"""
        summary = {}

        # Overall cache metrics
        if data['cache_metrics']:
            overall = data['cache_metrics'].get('overall', {})
            summary['Total Operations'] = {
                'value': f"{overall.get('total_hits', 0) + overall.get('total_misses', 0):,}",
                'trend': 'up' if overall.get('total_hits', 0) > overall.get('total_misses', 0) else 'down',
                'trend_text': f"Hit rate: {overall.get('overall_hit_rate', 0):.1%}"
            }

            summary['Cache Hit Rate'] = {
                'value': f"{overall.get('overall_hit_rate', 0):.1%}",
                'trend': 'up' if overall.get('overall_hit_rate', 0) > 0.7 else 'down',
                'trend_text': 'Good' if overall.get('overall_hit_rate', 0) > 0.7 else 'Needs Improvement'
            }

            summary['Cache Size'] = {
                'value': f"{overall.get('total_size_mb', 0):.1f} MB",
                'trend': 'neutral',
                'trend_text': 'Current usage'
            }

        # Query metrics
        if data['query_metrics'] and data['query_metrics'] != '_cache':
            summary['Optimizations'] = {
                'value': f"{data['query_metrics'].get('pending_optimizations', 0)}",
                'trend': 'down' if data['query_metrics'].get('pending_optimizations', 0) < 5 else 'up',
                'trend_text': 'Pending optimizations'
            }

        # Sync metrics
        if data['sync_metrics']:
            summary['Sync Errors'] = {
                'value': f"{data['sync_metrics'].get('total_errors', 0)}",
                'trend': 'down' if data['sync_metrics'].get('total_errors', 0) < 10 else 'up',
                'trend_text': 'Error count'
            }

        # Alerts
        if data['alerts']:
            critical_alerts = sum(1 for a in data['alerts'] if a.severity.value == 'critical')
            summary['Critical Alerts'] = {
                'value': f"{critical_alerts}",
                'trend': 'up' if critical_alerts > 0 else 'neutral',
                'trend_text': 'Requires attention' if critical_alerts > 0 else 'No critical issues'
            }

        return summary

    def _extract_key_recommendations(self, sections: List[ReportSection]) -> List[PerformanceInsight]:
        """Extract highest impact recommendations from all sections"""
        all_recommendations = []

        for section in sections:
            all_recommendations.extend(section.insights)

        # Sort by impact and severity
        priority_order = {'critical': 3, 'warning': 2, 'info': 1}
        all_recommendations.sort(
            key=lambda x: (
                priority_order.get(x.severity, 0),
                {'high': 3, 'medium': 2, 'low': 1}.get(x.impact, 0)
            ),
            reverse=True
        )

        # Return top 5 recommendations
        return all_recommendations[:5]

    async def save_report_html(
        self,
        report: PerformanceReport,
        filename: Optional[str] = None
    ) -> str:
        """
        Save report as HTML file

        Args:
            report: Performance report to save
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cache_performance_report_{report.report_type.value}_{timestamp}.html"

        # Render HTML
        html_content = self.html_template.render(report=report)

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Report saved to: {filename}")
        return filename

    async def save_report_json(
        self,
        report: PerformanceReport,
        filename: Optional[str] = None
    ) -> str:
        """
        Save report as JSON file

        Args:
            report: Performance report to save
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cache_performance_report_{report.report_type.value}_{timestamp}.json"

        # Convert to JSON-serializable format
        report_dict = asdict(report)
        report_dict['generated_at'] = report.generated_at.isoformat()
        report_dict['period_start'] = report.period_start.isoformat()
        report_dict['period_end'] = report.period_end.isoformat()

        # Convert sections
        for i, section in enumerate(report_dict['sections']):
            section['insights'] = [asdict(insight) for insight in report.sections[i].insights]
            section['insights'] = [
                {**insight, 'timestamp': insight['timestamp'].isoformat()}
                for insight in section['insights']
            ]

        # Convert recommendations
        report_dict['recommendations'] = [
            {**asdict(rec), 'timestamp': rec.timestamp.isoformat()}
            for rec in report.recommendations
        ]

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"Report saved to: {filename}")
        return filename


# CLI interface
async def generate_performance_report_cli():
    """CLI interface for report generation"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate cache performance report")
    parser.add_argument("--type", choices=['daily', 'weekly', 'monthly', 'custom'], default='daily')
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--format", choices=['html', 'json', 'both'], default='html')
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD) for custom reports")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD) for custom reports")

    args = parser.parse_args()

    # Initialize components
    from .enhanced_cache_monitoring import get_monitoring_system
    from .multi_cache_integration import get_cache_manager

    cache_manager = await get_cache_manager()
    monitoring = await get_monitoring_system(cache_manager)

    # Create report generator
    generator = PerformanceReportGenerator(monitoring)

    # Generate report
    custom_period = None
    if args.type == 'custom' and args.start_date and args.end_date:
        custom_period = (
            datetime.strptime(args.start_date, '%Y-%m-%d'),
            datetime.strptime(args.end_date, '%Y-%m-%d')
        )

    report = await generator.generate_report(
        ReportType(args.type),
        custom_period
    )

    # Save report
    if args.format in ['html', 'both']:
        html_file = await generator.save_report_html(report, args.output)
        print(f"HTML report saved: {html_file}")

    if args.format in ['json', 'both']:
        json_file = await generator.save_report_json(report, args.output)
        print(f"JSON report saved: {json_file}")

    # Print summary
    print("\nReport Summary:")
    for metric, data in report.summary.items():
        print(f"{metric}: {data['value']}")
        if 'trend_text' in data:
            print(f"  {data['trend_text']}")

    print(f"\nTotal Recommendations: {len(report.recommendations)}")


if __name__ == "__main__":
    asyncio.run(generate_performance_report_cli())