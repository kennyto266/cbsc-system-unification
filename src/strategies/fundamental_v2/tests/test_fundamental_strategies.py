"""
Tests for Fundamental Strategies
測試基本面策略實現
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from uuid import uuid4

# Import strategies
from ..hibor_strategy import HIBORStrategy
from ..gdp_strategy import GDPGrowthStrategy
from ..pmi_strategy import PMIStrategy
from .base import BaseFundamentalStrategy
from ...enhanced_factory import StrategyMetadata, StrategyType


class TestFundamentalStrategies:
    """測試基本面策略"""

    @pytest.fixture
    def sample_market_data(self):
        """創建測試用市場數據"""
        dates = pd.date_range(start="2024-01-01", periods=365, freq="D")
        symbols = ["HSI", "HSCEI", "MCHI", "SPY", "QQQ"]

        data = {}
        for symbol in symbols:
            # 創建與基本面相關的價格數據
            base_price = 100
            if symbol == "HSI":
                growth_rate = 0.0005
                volatility = 0.015
            elif symbol == "HSCEI":
                growth_rate = 0.0003
                volatility = 0.018
            elif symbol == "MCHI":
                growth_rate = 0.0004
                volatility = 0.016
            else:  # US markets
                growth_rate = 0.0008
                volatility = 0.012

            prices = [base_price]
            np.random.seed(hash(symbol) % 2**32)

            for i in range(1, len(dates)):
                daily_return = np.random.normal(growth_rate, volatility)
                prices.append(prices[-1] * (1 + daily_return))

            ohlcv_data = []
            for i, (date, close) in enumerate(zip(dates, prices)):
                high = close * (1 + abs(np.random.normal(0, 0.01)))
                low = close * (1 - abs(np.random.normal(0, 0.01)))
                open_price = close * (1 + np.random.normal(0, 0.005))
                volume = np.random.randint(1000000, 10000000)

                ohlcv_data.append({
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                })

            df = pd.DataFrame(ohlcv_data, index=dates)
            data[symbol] = df

        return data

    @pytest.fixture
    def strategy_metadata(self):
        """創建策略元數據"""
        return StrategyMetadata(
            name="test_fundamental",
            strategy_type=StrategyType.FUNDAMENTAL,
            description="Test fundamental strategy",
            version="2.0.0",
            author="Test",
            parameters={}
        )

    @pytest.fixture
    def hibor_strategy(self, strategy_metadata):
        """HIBOR策略實例"""
        config = {
            "lookback_period": 30,
            "rate_threshold_high": 5.0,
            "rate_threshold_low": 2.0,
            "use_momentum": True,
            "use_rate_level": True,
            "signal_sensitivity": 1.0
        }
        return HIBORStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def gdp_strategy(self, strategy_metadata):
        """GDP增長策略實例"""
        config = {
            "growth_threshold_high": 0.05,
            "growth_threshold_low": 0.01,
            "lookback_quarters": 8,
            "use_acceleration": True,
            "use_year_over_year": True,
            "target_regions": ["US", "EU", "CN", "JP"]
        }
        return GDPGrowthStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    @pytest.fixture
    def pmi_strategy(self, strategy_metadata):
        """PMI策略實例"""
        config = {
            "expansion_threshold": 55,
            "contraction_threshold": 45,
            "lookback_months": 12,
            "use_trend": True,
            "weight_manufacturing": 0.5,
            "weight_services": 0.5,
            "target_regions": ["US", "EU", "CN"]
        }
        return PMIStrategy(
            instance_id=uuid4(),
            config=config,
            metadata=strategy_metadata
        )

    # 測試HIBOR策略
    def test_hibor_initialization(self, hibor_strategy):
        """測試HIBOR策略初始化"""
        assert hibor_strategy.STRATEGY_NAME == "hibor"
        assert hibor_strategy.STRATEGY_TYPE == StrategyType.FUNDAMENTAL
        assert hibor_strategy.rate_threshold_high == 5.0
        assert hibor_strategy.rate_threshold_low == 2.0
        assert hibor_strategy.target_symbols == ['HSI', 'HSCEI', 'MCHI']

    def test_hibor_data_fetching(self, hibor_strategy):
        """測試HIBOR數據獲取"""
        data = hibor_strategy.fetch_fundamental_data([])

        assert 'HIBOR' in data
        hibor_df = data['HIBOR']
        assert 'hibor_rate' in hibor_df.columns
        assert 'rate_change' in hibor_df.columns
        assert len(hibor_df) > 0

    def test_hibor_regime_detection(self, hibor_strategy):
        """測試HIBOR體系檢測"""
        data = hibor_strategy.fetch_fundamental_data([])
        regime = hibor_strategy.calculate_rate_regime(data['HIBOR'])

        assert 'regime' in regime
        assert 'strength' in regime
        assert 'current_rate' in regime
        assert regime['regime'] in ['low', 'moderate_low', 'moderate_high', 'high']

    def test_hibor_momentum_signals(self, hibor_strategy):
        """測試HIBOR動量信號"""
        data = hibor_strategy.fetch_fundamental_data([])
        momentum_signals = hibor_strategy.calculate_momentum_signals(data['HIBOR'])

        assert isinstance(momentum_signals, pd.Series)
        assert len(momentum_signals) > 0

    def test_hibor_level_signals(self, hibor_strategy):
        """測試HIBOR水平信號"""
        data = hibor_strategy.fetch_fundamental_data([])
        level_signals = hibor_strategy.calculate_level_signals(data['HIBOR'])

        assert isinstance(level_signals, pd.Series)
        assert len(level_signals) > 0

    def test_hibor_signal_generation(self, hibor_strategy, sample_market_data):
        """測試HIBOR信號生成"""
        # 添加HIBOR數據到市場數據中
        hibor_data = hibor_strategy.fetch_fundamental_data([])
        fundamental_data = {'HIBOR': hibor_data['HIBOR']}

        signals = hibor_strategy.generate_signals(fundamental_data)

        # 應該包含目標符號的信號
        assert isinstance(signals, pd.DataFrame)
        if len(signals) > 0:
            signal_cols = [col for col in signals.columns if 'signal' in col]
            assert len(signal_cols) > 0

    def test_hibor_analysis(self, hibor_strategy):
        """測試HIBOR分析"""
        analysis = hibor_strategy.get_hibor_analysis()

        assert 'strategy' in analysis
        assert 'parameters' in analysis
        assert 'data_status' in analysis

    # 測試GDP增長策略
    def test_gdp_initialization(self, gdp_strategy):
        """測試GDP增長策略初始化"""
        assert gdp_strategy.STRATEGY_NAME == "gdp_growth"
        assert gdp_strategy.STRATEGY_TYPE == StrategyType.FUNDAMENTAL
        assert gdp_strategy.growth_threshold_high == 0.05
        assert gdp_strategy.target_regions == ["US", "EU", "CN", "JP"]

    def test_gdp_data_fetching(self, gdp_strategy):
        """測試GDP數據獲取"""
        data = gdp_strategy.fetch_fundamental_data([])

        # 應該包含全球GDP和各區域GDP
        assert 'GDP_GLOBAL' in data
        for region in gdp_strategy.target_regions:
            assert f'GDP_{region}' in data

        # 檢查數據結構
        global_df = data['GDP_GLOBAL']
        assert 'composite_growth' in global_df.columns
        assert 'composite_trend' in global_df.columns
        assert len(global_df) > 0

    def test_gdp_growth_phase(self, gdp_strategy):
        """測試GDP增長階段判斷"""
        data = gdp_strategy.fetch_fundamental_data([])
        phase = gdp_strategy.calculate_growth_phase(data['GDP_GLOBAL'])

        assert 'phase' in phase
        assert 'strength' in phase
        assert 'current_growth' in phase
        assert phase['phase'] in ['expansion_accelerating', 'expansion_decelerating',
                                        'recovery_accelerating', 'recovery_decelerating',
                                        'slowdown_positive', 'contraction']

    def test_gdp_sector_signals(self, gdp_strategy):
        """測試GDP行業信號"""
        data = gdp_strategy.fetch_fundamental_data([])

        # 測試科技行業信號
        tech_signals = gdp_strategy.calculate_sector_signals(data['GDP_GLOBAL'], 'technology')
        assert isinstance(tech_signals, pd.Series)

        # 測試金融行業信號
        fin_signals = gdp_strategy.calculate_sector_signals(data['GDP_GLOBAL'], 'financials')
        assert isinstance(fin_signals, pd.Series)

    def test_gdp_signal_generation(self, gdp_strategy, sample_market_data):
        """測試GDP信號生成"""
        data = gdp_strategy.fetch_fundamental_data([])
        fundamental_data = {k: v for k, v in data.items() if k.startswith('GDP_')}

        signals = gdp_strategy.generate_signals(fundamental_data)

        assert isinstance(signals, pd.DataFrame)
        if len(signals) > 0:
            assert 'GLOBAL_EQUITY' in signals.columns or any('equity' in col.lower() for col in signals.columns)

    def test_gdp_analysis(self, gdp_strategy):
        """測試GDP分析"""
        analysis = gdp_strategy.get_gdp_analysis()

        assert 'strategy' in analysis
        assert 'parameters' in analysis
        assert 'data_status' in analysis
        assert 'sector_mapping' in analysis

    # 測試PMI策略
    def test_pmi_initialization(self, pmi_strategy):
        """測試PMI策略初始化"""
        assert pmi_strategy.STRATEGY_NAME == "pmi"
        assert pmi_strategy.STRATEGY_TYPE == StrategyType.FUNDAMENTAL
        assert pmi_strategy.expansion_threshold == 55
        assert pmi_strategy.contraction_threshold == 45
        assert pmi_strategy.use_trend == True

    def test_pmi_data_fetching(self, pmi_strategy):
        """測試PMI數據獲取"""
        data = pmi_strategy.fetch_fundamental_data([])

        # 應該包含全球PMI
        assert 'PMI_GLOBAL' in data
        global_df = data['PMI_GLOBAL']
        assert 'pmi_global' in global_df.columns

        # 應該包含PMI組成部分
        assert 'PMI_COMPONENTS' in data
        component_df = data['PMI_COMPONENTS']
        assert 'pmi_manufacturing' in component_df.columns
        assert 'pmi_services' in component_df.columns

    def test_pmi_regime_detection(self, pmi_strategy):
        """測試PMI體系檢測"""
        data = pmi_strategy.fetch_fundamental_data([])
        regime = pmi_strategy.calculate_pmi_regime(data['PMI_GLOBAL'])

        assert 'regime' in regime
        assert 'strength' in regime
        assert 'current_pmi' in regime
        assert regime['regime'] in ['strong_expansion', 'moderate_expansion', 'neutral',
                                        'moderate_contraction', 'strong_contraction']

    def test_pmi_trend_signals(self, pmi_strategy):
        """測試PMI趨勢信號"""
        data = pmi_strategy.fetch_fundamental_data([])
        component_data = data['PMI_COMPONENTS']

        # 測試製造業PMI趨勢
        man_trend = pmi_strategy.calculate_trend_signals(component_data, 'pmi_manufacturing')
        assert isinstance(man_trend, pd.Series)

        # 測試服務業PMI趨勢
        svc_trend = pmi_strategy.calculate_trend_signals(component_data, 'pmi_services')
        assert isinstance(svc_trend, pd.Series)

    def test_pmi_level_signals(self, pmi_strategy):
        """測試PMI水平信號"""
        data = pmi_strategy.fetch_fundamental_data([])
        component_data = data['PMI_COMPONENTS']

        # 測試製造業PMI水平
        man_level = pmi_strategy.calculate_level_signals(component_data, 'pmi_manufacturing')
        assert isinstance(man_level, pd.Series)

        # 測試服務業PMI水平
        svc_level = pmi_strategy.calculate_level_signals(component_data, 'pmi_services')
        assert isinstance(svc_level, pd.Series)

    def test_pmi_signal_generation(self, pmi_strategy, sample_market_data):
        """測試PMI信號生成"""
        data = pmi_strategy.fetch_fundamental_data([])
        fundamental_data = {k: v for k, v in data.items() if k.startswith('PMI_')}

        signals = pmi_strategy.generate_signals(fundamental_data)

        assert isinstance(signals, pd.DataFrame)
        if len(signals) > 0:
            assert 'GLOBAL_EQUITY' in signals.columns or any('equity' in col.lower() for col in signals.columns)

    def test_pmi_analysis(self, pmi_strategy):
        """測試PMI分析"""
        analysis = pmi_strategy.get_pmi_analysis()

        assert 'strategy' in analysis
        assert 'parameters' in analysis
        assert 'data_status' in analysis

    def test_pmi_economic_indicators(self, pmi_strategy):
        """測試PMI經濟指標"""
        data = pmi_strategy.fetch_fundamental_data([])
        indicators = pmi_strategy.get_economic_indicators_summary(data)

        if indicators:
            assert 'global_pmi' in indicators or 'components' in indicators

    # 測試基本面策略執行
    def test_fundamental_strategy_execution(self, hibor_strategy, sample_market_data):
        """測試基本面策略執行"""
        # 添加基本面數據
        hibor_data = hibor_strategy.fetch_fundamental_data([])
        combined_data = {'HIBOR': hibor_data['HIBOR']}
        combined_data.update(sample_market_data)

        result = hibor_strategy.execute(combined_data)

        # 檢查執行結果結構
        assert "strategy_id" in result
        assert "strategy_name" in result
        assert "execution_time" in result
        assert "results" in result

    def test_data_quality_validation(self, gdp_strategy):
        """測試數據質量驗證"""
        # 測試有效數據
        valid_data = pd.DataFrame({
            'gdp_growth': [0.02, 0.03, 0.01, 0.04, 0.02],
            'date': pd.date_range(start="2024-01-01", periods=5, freq="Q")
        })
        valid_data.set_index('date', inplace=True)

        assert gdp_strategy.validate_data_quality(valid_data) == True

        # 測試無效數據（太少數據點）
        invalid_data = pd.DataFrame({
            'gdp_growth': [0.02],
            'date': pd.date_range(start="2024-01-01", periods=1, freq="Q")
        })
        invalid_data.set_index('date', inplace=True)

        assert gdp_strategy.validate_data_quality(invalid_data) == False

        # 測試空數據
        empty_data = pd.DataFrame()
        assert gdp_strategy.validate_data_quality(empty_data) == False

    # 測試錯誤處理
    def test_fundamental_strategy_no_data(self, hibor_strategy):
        """測試無數據情況"""
        signals = hibor_strategy.generate_signals({})

        # 應該返回空的DataFrame或空信號
        assert isinstance(signals, pd.DataFrame)
        assert len(signals) == 0 or len(signals.columns) == 0

    def test_fundamental_strategy_malformed_data(self, hibor_strategy):
        """測試格式錯誤的數據"""
        malformed_data = {'INVALID': pd.DataFrame()}
        signals = hibor_strategy.generate_signals(malformed_data)

        # 應該能處理格式錯誤
        assert isinstance(signals, pd.DataFrame)

    # 測試基本功能
    def test_base_fundamental_strategy_interface(self):
        """測試基本面策略基類接口"""
        from ..base import BaseFundamentalStrategy

        # 嘗試直接實例化基類（應該失敗）
        with pytest.raises(TypeError):
            BaseFundamentalStrategy(uuid4(), {}, StrategyMetadata(
                name="test",
                strategy_type=StrategyType.FUNDAMENTAL,
                description="test",
                version="2.0",
                author="test",
                parameters={}
            ))