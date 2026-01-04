"""
Tests for ReportGenerator
"""
import pytest
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch

from ..report_generator import ReportGenerator


class TestReportGenerator:
    """Test cases for ReportGenerator"""

    @pytest.fixture
    def sample_backtest_result(self):
        """Create sample backtest result"""
        import numpy as np
        import pandas as pd

        # Generate sample data
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        portfolio_values = np.cumprod(1 + np.random.randn(100) * 0.01) * 100000
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

        return {
            "strategy_name": "Test Strategy",
            "start_date": "2023-01-01",
            "end_date": "2023-04-10",
            "initial_capital": 100000,
            "final_capital": portfolio_values[-1],
            "total_return": (portfolio_values[-1] - 100000) / 100000,
            "annualized_return": ((portfolio_values[-1] / 100000) ** (252 / 100)) - 1,
            "sharpe_ratio": 1.23,
            "max_drawdown": -0.15,
            "metrics": {
                "volatility": 0.18,
                "sortino_ratio": 1.45,
                "calmar_ratio": 0.82,
                "information_ratio": 0.65,
                "total_trades": 25,
                "winning_trades": 15,
                "losing_trades": 10,
                "win_rate": 0.60,
                "profit_factor": 1.5,
                "avg_win": 1000.0,
                "avg_loss": -500.0,
                "total_commission": 250.0,
                "total_slippage": 150.0,
                "var_95": -0.025,
                "var_99": -0.040,
                "expected_shortfall_95": -0.032,
                "max_drawdown_duration": 20,
                "omega_ratio": 1.35,
                "beta": 0.95,
                "alpha": 0.045,
                "treynor_ratio": 0.155,
                "jensen_alpha": 0.038
            },
            "trades": [
                {
                    "date": "2023-01-15",
                    "symbol": "TEST",
                    "action": "BUY",
                    "quantity": 100,
                    "price": 50.0,
                    "commission": 5.0,
                    "slippage": 2.0,
                    "pnl": 500.0
                }
            ],
            "portfolio_values": portfolio_values.tolist(),
            "daily_returns": daily_returns.tolist()
        }

    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_initialization(self, temp_output_dir):
        """Test ReportGenerator initialization"""
        generator = ReportGenerator(output_dir=temp_output_dir)

        assert generator.output_dir == temp_output_dir
        assert os.path.exists(temp_output_dir)

    def test_generate_json_report(self, sample_backtest_result, temp_output_dir):
        """Test JSON report generation"""
        generator = ReportGenerator(output_dir=temp_output_dir)

        report_path = generator.generate_report(
            backtest_result=sample_backtest_result,
            format="json",
            include_charts=False
        )

        assert os.path.exists(report_path)
        assert report_path.endswith('.json')

        # Verify JSON content
        import json
        with open(report_path, 'r') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'summary' in data
        assert 'performance' in data
        assert 'risk' in data
        assert data['metadata']['strategy_name'] == 'Test Strategy'

    def test_generate_html_report(self, sample_backtest_result, temp_output_dir):
        """Test HTML report generation"""
        generator = ReportGenerator(output_dir=temp_output_dir)

        report_path = generator.generate_report(
            backtest_result=sample_backtest_result,
            format="html",
            include_charts=False
        )

        assert os.path.exists(report_path)
        assert report_path.endswith('.html')

        # Verify HTML content
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        assert 'Test Strategy' in html_content
        assert 'Backtest Performance Report' in html_content
        assert '<!DOCTYPE html>' in html_content

    def test_unsupported_format(self, sample_backtest_result, temp_output_dir):
        """Test unsupported format raises error"""
        generator = ReportGenerator(output_dir=temp_output_dir)

        with pytest.raises(ValueError, match="Unsupported format"):
            generator.generate_report(
                backtest_result=sample_backtest_result,
                format="xml"
            )

    def test_prepare_template_data(self, sample_backtest_result):
        """Test template data preparation"""
        generator = ReportGenerator()

        template_data = generator._prepare_template_data(sample_backtest_result)

        assert 'title' in template_data
        assert 'summary' in template_data
        assert 'metrics' in template_data
        assert 'trades' in template_data
        assert template_data['summary']['strategy_name'] == 'Test Strategy'

    @patch('src.backtest.report_generator.PDF_AVAILABLE', False)
    def test_pdf_generation_without_dependency(self, sample_backtest_result, temp_output_dir):
        """Test PDF generation fails without ReportLab"""
        generator = ReportGenerator(output_dir=temp_output_dir)

        with pytest.raises(ImportError, match="ReportLab is required"):
            generator.generate_report(
                backtest_result=sample_backtest_result,
                format="pdf"
            )

    @patch('src.backtest.report_generator.EXCEL_AVAILABLE', False)
    def test_excel_generation_without_dependency(self, sample_backtest_result, temp_output_dir):
        """Test Excel generation fails without OpenPyXL"""
        generator = ReportGenerator(output_dir=temp_output_dir)

        with pytest.raises(ImportError, match="OpenPyXL is required"):
            generator.generate_report(
                backtest_result=sample_backtest_result,
                format="excel"
            )

    def test_create_summary_table(self, sample_backtest_result):
        """Test summary table creation"""
        generator = ReportGenerator()
        table = generator._create_summary_table(sample_backtest_result)

        # Verify table structure (this is a ReportLab Table object)
        assert hasattr(table, 'data')
        assert len(table.data) > 1  # Should have header and data rows
        assert table.data[0][0] == 'Metric'  # First header
        assert table.data[1][0] == 'Strategy Name'  # First data row

    def test_create_metrics_table(self, sample_backtest_result):
        """Test metrics table creation"""
        generator = ReportGenerator()
        table = generator._create_metrics_table(sample_backtest_result)

        assert hasattr(table, 'data')
        assert table.data[0][0] == 'Performance Metric'
        # Check if volatility is in the table
        vol_found = any('Volatility' in row[0] for row in table.data)
        assert vol_found

    def test_create_risk_table(self, sample_backtest_result):
        """Test risk metrics table creation"""
        generator = ReportGenerator()
        table = generator._create_risk_table(sample_backtest_result)

        assert hasattr(table, 'data')
        assert table.data[0][0] == 'Risk Metric'
        # Check if VaR is in the table
        var_found = any('VaR' in row[0] for row in table.data)
        assert var_found

    def test_create_trading_table(self, sample_backtest_result):
        """Test trading statistics table creation"""
        generator = ReportGenerator()
        table = generator._create_trading_table(sample_backtest_result)

        assert hasattr(table, 'data')
        assert table.data[0][0] == 'Trading Statistic'
        # Check if total trades is in the table
        trades_found = any('Total Trades' in row[0] for row in table.data)
        assert trades_found

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_portfolio_value_chart(self, mock_close, mock_savefig, sample_backtest_result):
        """Test portfolio value chart generation"""
        mock_savefig.return_value = None

        generator = ReportGenerator()
        chart_path = generator._create_portfolio_value_chart(
            sample_backtest_result['portfolio_values'],
            sample_backtest_result['daily_returns']
        )

        assert chart_path is not None
        assert chart_path.endswith('.png')
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_returns_distribution_chart(self, mock_close, mock_savefig, sample_backtest_result):
        """Test returns distribution chart generation"""
        mock_savefig.return_value = None

        generator = ReportGenerator()
        chart_path = generator._create_returns_distribution_chart(
            sample_backtest_result['daily_returns']
        )

        assert chart_path is not None
        assert chart_path.endswith('.png')
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_drawdown_chart(self, mock_close, mock_savefig, sample_backtest_result):
        """Test drawdown chart generation"""
        mock_savefig.return_value = None

        generator = ReportGenerator()
        chart_path = generator._create_drawdown_chart(
            sample_backtest_result['portfolio_values']
        )

        assert chart_path is not None
        assert chart_path.endswith('.png')
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_monthly_returns_heatmap(self, mock_close, mock_savefig, sample_backtest_result):
        """Test monthly returns heatmap generation"""
        mock_savefig.return_value = None

        generator = ReportGenerator()
        chart_path = generator._create_monthly_returns_heatmap(
            sample_backtest_result['daily_returns']
        )

        assert chart_path is not None
        assert chart_path.endswith('.png')
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()

    def test_cleanup_chart_files(self, temp_output_dir):
        """Test chart file cleanup"""
        generator = ReportGenerator()

        # Create temporary chart files
        chart1_path = os.path.join(temp_output_dir, "temp_chart1.png")
        chart2_path = os.path.join(temp_output_dir, "temp_chart2.png")

        # Create dummy files
        with open(chart1_path, 'w') as f:
            f.write("dummy")
        with open(chart2_path, 'w') as f:
            f.write("dummy")

        charts = {
            'chart1': chart1_path,
            'chart2': chart2_path
        }

        # Verify files exist
        assert os.path.exists(chart1_path)
        assert os.path.exists(chart2_path)

        # Cleanup
        generator._cleanup_chart_files(charts)

        # Verify files are deleted
        assert not os.path.exists(chart1_path)
        assert not os.path.exists(chart2_path)

    def test_get_default_html_template(self):
        """Test default HTML template"""
        generator = ReportGenerator()
        template = generator._get_default_html_template()

        assert isinstance(template, str)
        assert '<!DOCTYPE html>' in template
        assert '<html>' in template
        assert '</html>' in template
        assert '{{ title }}' in template

    @patch('src.backtest.report_generator.EXCEL_AVAILABLE', True)
    @patch('openpyxl.Workbook')
    def test_create_summary_sheet(self, mock_workbook, sample_backtest_result):
        """Test Excel summary sheet creation"""
        from unittest.mock import MagicMock

        # Mock workbook and worksheet
        mock_ws = MagicMock()
        mock_wb = MagicMock()
        mock_wb.create_sheet.return_value = mock_ws
        mock_workbook.return_value = mock_wb

        generator = ReportGenerator()
        generator._create_summary_sheet(mock_wb, sample_backtest_result)

        # Verify worksheet creation and cell writing
        mock_wb.create_sheet.assert_called_once_with("Summary", 0)
        assert mock_ws.cell.called

    def test_empty_trades_data(self):
        """Test handling of empty trades data in Excel sheet creation"""
        from unittest.mock import MagicMock

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.create_sheet.return_value = mock_ws

        generator = ReportGenerator()
        result = {
            'trades': [],
            'metrics': {}
        }

        generator._create_trades_sheet(mock_wb, result)

        # Should write "No trades data available" message
        mock_ws.cell.assert_called_with(row=1, column=1, value="No trades data available")

    def test_empty_returns_data(self):
        """Test handling of empty returns data in monthly returns sheet"""
        from unittest.mock import MagicMock
        import pandas as pd

        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.create_sheet.return_value = mock_ws

        generator = ReportGenerator()
        result = {
            'daily_returns': [],
            'metrics': {}
        }

        generator._create_monthly_returns_sheet(mock_wb, result)

        # Should write "No returns data available" message
        mock_ws.cell.assert_called_with(row=1, column=1, value="No returns data available")