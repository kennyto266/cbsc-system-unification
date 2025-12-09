#!/usr/bin/env python3
"""
Data Cleaning Tools Demo / 數據清理工具演示
Data Cleaning Tools Integration System for Simplified System

This script demonstrates the integration of data cleaning tools
with the Simplified System quantitative trading platform.

此腳本演示數據清理工具與Simplified System量化交易平台的集成。
"""

import sys
import os
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.append('.')
sys.path.append('src')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path

class DataCleaningToolsDemo:
    """數據清理工具演示類 / Data Cleaning Tools Demo Class"""

    def __init__(self):
        self.data_loaded = False
        self.stock_data = None
        self.tools_available = self._check_tools_availability()

    def _check_tools_availability(self):
        """檢查工具可用性 / Check tools availability"""
        tools = {}

        try:
            import ydata_profiling
            tools['ydata_profiling'] = True
            print("[OK] ydata-profiling available")
        except ImportError:
            tools['ydata_profiling'] = False
            print("[ERROR] ydata-profiling not available (install with: pip install ydata-profiling)")

        try:
            import missingno
            tools['missingno'] = True
            print("[OK] missingno available")
        except ImportError:
            tools['missingno'] = False
            print("[ERROR] missingno not available (install with: pip install missingno)")

        try:
            import sweetviz
            tools['sweetviz'] = True
            print("[OK] sweetviz available")
        except ImportError:
            tools['sweetviz'] = False
            print("[ERROR] sweetviz not available (install with: pip install sweetviz)")

        return tools

    def load_0700_hk_data(self):
        """加載0700.HK數據 / Load 0700.HK data"""
        print("Loading 0700.HK data...")

        try:
            # Method 1: Try to load from Simplified System API
            try:
                from src.api.stock_api import get_stock_prices_dataframe
                print("  Loading from Simplified System API...")
                data = get_stock_prices_dataframe('0700.HK', 1095)
                if data is not None:
                    self.stock_data = self._standardize_data(data)
                    self.data_loaded = True
                    print("  [SUCCESS] Successfully loaded from API")
                    return self.stock_data
            except Exception as e:
                print(f"  [WARNING] API loading failed: {e}")

            # Method 2: Try to load from local files
            local_sources = [
                '0700_results_20251125_181239.csv',
                '0700_results_20251125_181639.csv',
                'data/0700_hk.csv',
            ]

            for source in local_sources:
                if Path(source).exists():
                    print(f"  Loading from local file: {source}")
                    data = pd.read_csv(source, index_col=0, parse_dates=True)
                    self.stock_data = self._standardize_data(data)
                    self.data_loaded = True
                    print("  [SUCCESS] Successfully loaded from local file")
                    return self.stock_data

            # Method 3: Generate sample data
            print("  [WARNING] No real data found, generating sample data...")
            self.stock_data = self._generate_sample_data()
            self.data_loaded = True
            print("  [SUCCESS] Sample data generated")
            return self.stock_data

        except Exception as e:
            print(f"  [ERROR] Error loading data: {e}")
            return None

    def _standardize_data(self, data):
        """標準化數據格式 / Standardize data format"""
        df = data.copy()

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            else:
                df.index = pd.to_datetime(df.index)

        # Standardize column names
        column_mapping = {
            'Price': 'Close', 'price': 'Close',
            'Volume': 'Volume', 'volume': 'Volume',
            'Open': 'Open', 'open': 'Open',
            'High': 'High', 'high': 'High',
            'Low': 'Low', 'low': 'Low'
        }

        df = df.rename(columns=column_mapping)

        # Ensure required columns exist
        if 'Close' not in df.columns:
            if len(df.columns) > 0:
                df['Close'] = df.iloc[:, 0]
            else:
                raise ValueError("No price data found")

        # Add missing OHLCV columns
        for col in ['Open', 'High', 'Low']:
            if col not in df.columns:
                df[col] = df['Close'] * (1 + np.random.normal(0, 0.01, len(df)))

        if 'Volume' not in df.columns:
            df['Volume'] = np.random.randint(10000000, 30000000, len(df))

        return df.sort_index()

    def _generate_sample_data(self):
        """生成示例數據 / Generate sample data"""
        np.random.seed(42)
        dates = pd.date_range('2022-01-01', '2025-11-24', freq='D')

        base_price = 400
        trend = np.linspace(base_price, base_price * 1.7, len(dates))
        volatility = np.random.randn(len(dates)) * 12
        price = trend + volatility
        price = np.maximum(price, 50)

        data = pd.DataFrame({
            'Open': price * (1 + np.random.randn(len(dates)) * 0.015),
            'High': price * (1 + np.random.rand(len(dates)) * 0.025),
            'Low': price * (1 - np.random.rand(len(dates)) * 0.025),
            'Close': price,
            'Volume': np.random.randint(15000000, 35000000, len(dates))
        }, index=dates)

        return data

    def basic_data_analysis(self):
        """基礎數據分析 / Basic Data Analysis"""
        if not self.data_loaded:
            print("[ERROR] No data loaded. Please run load_0700_hk_data() first.")
            return

        print("\nBasic Data Analysis / 基礎數據分析")
        print("=" * 60)

        data = self.stock_data

        # Basic statistics
        print(f"[INFO] Data shape: {data.shape}")
        print(f"[INFO] Date range: {data.index[0].date()} to {data.index[-1].date()}")
        print(f"[INFO] Price range: {data['Close'].min():.2f} - {data['Close'].max():.2f} HKD")
        print(f"[INFO] Average volume: {data['Volume'].mean():,.0f}")

        # Missing values
        missing_values = data.isnull().sum()
        total_missing = missing_values.sum()
        print(f"[INFO] Missing values: {total_missing} ({total_missing/data.size*100:.2f}%)")

        # Data types
        print("\n[INFO] Data types:")
        print(data.dtypes)

        # Basic statistics
        print("\n[INFO] Basic statistics:")
        print(data.describe())

    def demonstrate_missingno(self):
        """演示missingno功能 / Demonstrate missingno functionality"""
        if not self.data_loaded:
            print("[ERROR] No data loaded. Please run load_0700_hk_data() first.")
            return

        if not self.tools_available['missingno']:
            print("[ERROR] missingno not available. Install with: pip install missingno")
            return

        print("\nMissing Data Visualization with missingno")
        print("=" * 60)

        import missingno as msno
        data = self.stock_data

        # Add some artificial missing data for demonstration
        data_demo = data.copy()
        # Randomly introduce some missing values
        for col in ['Open', 'High', 'Low']:
            mask = np.random.random(len(data_demo)) < 0.05  # 5% missing
            data_demo.loc[mask, col] = np.nan

        print("[INFO] Creating missing data visualizations...")

        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Missing Data Analysis / 缺失值分析', fontsize=16)

        # Matrix plot
        msno.matrix(data_demo, ax=axes[0, 0], sparkline=False)
        axes[0, 0].set_title('Missing Data Matrix / 缺失值矩陣')

        # Bar plot
        msno.bar(data_demo, ax=axes[0, 1])
        axes[0, 1].set_title('Missing Data Bar Chart / 缺失值條形圖')

        # Heatmap
        msno.heatmap(data_demo, ax=axes[1, 0])
        axes[1, 0].set_title('Missing Data Correlation / 缺失值相關性')

        # Dendrogram
        msno.dendrogram(data_demo, ax=axes[1, 1])
        axes[1, 1].set_title('Missing Data Dendrogram / 缺失值樹狀圖')

        plt.tight_layout()
        plt.show()

        print("[SUCCESS] Missing data analysis completed!")

    def demonstrate_pandas_profiling(self):
        """演示pandas-profiling功能 / Demonstrate pandas-profiling functionality"""
        if not self.data_loaded:
            print("[ERROR] No data loaded. Please run load_0700_hk_data() first.")
            return

        if not self.tools_available['ydata_profiling']:
            print("[ERROR] ydata-profiling not available. Install with: pip install ydata-profiling")
            return

        print("\nGenerating pandas-profiling report...")
        print("=" * 60)

        from ydata_profiling import ProfileReport

        # Create profile report
        profile = ProfileReport(
            self.stock_data,
            title="0700.HK Data Analysis Report / 0700.HK 數據分析報告",
            explorative=True
        )

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"0700_hk_profiling_report_{timestamp}.html"

        profile.to_file(report_file)
        print(f"[SUCCESS] Report saved as: {report_file}")

        return profile, report_file

    def demonstrate_sweetviz(self):
        """演示sweetviz功能 / Demonstrate sweetviz functionality"""
        if not self.data_loaded:
            print("[ERROR] No data loaded. Please run load_0700_hk_data() first.")
            return

        if not self.tools_available['sweetviz']:
            print("[ERROR] sweetviz not available. Install with: pip install sweetviz")
            return

        print("\nGenerating sweetviz comparison report...")
        print("=" * 60)

        import sweetviz as sv

        # Create processed data for comparison
        processed_data = self.stock_data.copy()
        processed_data['Returns'] = processed_data['Close'].pct_change()
        processed_data['MA5'] = processed_data['Close'].rolling(5).mean()
        processed_data['MA20'] = processed_data['Close'].rolling(20).mean()
        processed_data['Volatility'] = processed_data['Returns'].rolling(20).std()

        # Remove NaN values
        processed_data = processed_data.dropna()

        print(f"[INFO] Original data: {self.stock_data.shape}")
        print(f"[INFO] Processed data: {processed_data.shape}")

        # Generate comparison report
        report = sv.compare(
            [self.stock_data, "Original Data"],
            [processed_data, "Processed Data"]
        )

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"0700_hk_comparison_report_{timestamp}.html"

        report.show_html(report_file)
        print(f"[SUCCESS] Comparison report saved as: {report_file}")

        return report, report_file

    def run_full_demo(self):
        """運行完整演示 / Run full demonstration"""
        print("Starting Data Cleaning Tools Full Demo")
        print("=" * 60)

        # Step 1: Load data
        print("\n[INFO] Step 1: Loading 0700.HK data...")
        self.load_0700_hk_data()

        if not self.data_loaded:
            print("[ERROR] Demo failed: Could not load data")
            return

        # Step 2: Basic analysis
        print("\n[INFO] Step 2: Basic data analysis...")
        self.basic_data_analysis()

        # Step 3: Missing data analysis
        print("\n[INFO] Step 3: Missing data visualization...")
        if self.tools_available['missingno']:
            self.demonstrate_missingno()
        else:
            print("[WARNING] Skipping missingno demo - tool not available")

        # Step 4: Profiling report
        print("\n[INFO] Step 4: Generating profiling report...")
        if self.tools_available['ydata_profiling']:
            self.demonstrate_pandas_profiling()
        else:
            print("[WARNING] Skipping profiling demo - tool not available")

        # Step 5: Comparison report
        print("\n[INFO] Step 5: Generating comparison report...")
        if self.tools_available['sweetviz']:
            self.demonstrate_sweetviz()
        else:
            print("[WARNING] Skipping comparison demo - tool not available")

        # Summary
        print("\nDemo Summary / 演示總結")
        print("=" * 60)
        print("[SUCCESS] Data loading: Successful")
        print("[SUCCESS] Basic analysis: Completed")
        print(f"[{'SUCCESS' if self.tools_available['missingno'] else 'ERROR'}] Missing data analysis: {'Completed' if self.tools_available['missingno'] else 'Skipped'}")
        print(f"[{'SUCCESS' if self.tools_available['ydata_profiling'] else 'ERROR'}] Profiling report: {'Generated' if self.tools_available['ydata_profiling'] else 'Skipped'}")
        print(f"[{'SUCCESS' if self.tools_available['sweetviz'] else 'ERROR'}] Comparison report: {'Generated' if self.tools_available['sweetviz'] else 'Skipped'}")

        print("\n[INFO] To install missing tools:")
        print("pip install -r enhanced_requirements.txt")

        print("\n[SUCCESS] Data Cleaning Tools Demo Completed!")


def main():
    """主函數 / Main function"""
    print("Data Cleaning Tools Integration Demo")
    print("數據清理工具包集成演示")
    print("=" * 60)

    # Create demo instance
    demo = DataCleaningToolsDemo()

    # Check tools availability
    print(f"\nTools Available:")
    for tool, available in demo.tools_available.items():
        status = "[OK] Available" if available else "[ERROR] Not Available"
        print(f"   {tool}: {status}")

    # Run full demo
    demo.run_full_demo()


if __name__ == "__main__":
    main()