"""
黑人RAW DATA适配器测试

测试RawDataAdapter的各种功能，包括数据读取、转换、验证等。
"""

import pytest
import asyncio
import tempfile
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from src.data_adapters.raw_data_adapter import RawDataAdapter, RawDataAdapterConfig
from src.data_adapters.base_adapter import DataSourceType, DataQuality


class TestRawDataAdapter:
    """RawDataAdapter测试类"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """创建临时数据目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def sample_data_file(self, temp_data_dir):
        """创建示例数据文件"""
        data = {
            'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'symbol': ['0001.HK', '0001.HK', '0001.HK'],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [104.0, 105.0, 106.0],
            'volume': [1000000, 1100000, 1200000],
            'market_cap': [1000000000, 1050000000, 1100000000],
            'pe_ratio': [15.5, 16.0, 16.5]
        }
        
        df = pd.DataFrame(data)
        file_path = Path(temp_data_dir) / "0001.HK.csv"
        df.to_csv(file_path, index=False)
        
        return str(file_path)
    
    @pytest.fixture
    def adapter_config(self, temp_data_dir):
        """创建适配器配置"""
        return RawDataAdapterConfig(
            data_directory=temp_data_dir,
            file_pattern="*.csv",
            encoding="utf-8",
            delimiter=",",
            date_column="date",
            symbol_column="symbol",
            price_columns={
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume"
            },
            market_cap_column="market_cap",
            pe_ratio_column="pe_ratio",
            update_frequency=60,
            max_retries=3,
            timeout=30,
            cache_enabled=True,
            cache_ttl=300,
            quality_threshold=0.8
        )
    
    @pytest.fixture
    def adapter(self, adapter_config):
        """创建适配器实例"""
        return RawDataAdapter(adapter_config)
    
    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter is not None
        assert adapter.config.source_type == DataSourceType.RAW_DATA
        assert adapter.config.cache_enabled is True
    
    @pytest.mark.asyncio
    async def test_connect_success(self, adapter, sample_data_file):
        """测试成功连接"""
        result = await adapter.connect()
        assert result is True
        assert len(adapter._data_files) > 0
        assert "0001.HK" in adapter._data_files
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, temp_data_dir):
        """测试连接失败"""
        config = RawDataAdapterConfig(
            data_directory="/nonexistent/path",
            file_pattern="*.csv"
        )
        adapter = RawDataAdapter(config)
        
        result = await adapter.connect()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self, adapter, sample_data_file):
        """测试断开连接"""
        await adapter.connect()
        result = await adapter.disconnect()
        
        assert result is True
        assert len(adapter._data_files) == 0
        assert len(adapter._file_cache) == 0
    
    @pytest.mark.asyncio
    async def test_get_market_data_success(self, adapter, sample_data_file):
        """测试成功获取市场数据"""
        await adapter.connect()
        
        data = await adapter.get_market_data("0001.HK")
        
        assert len(data) == 3
        assert data[0].symbol == "0001.HK"
        assert data[0].open_price == Decimal("100.0")
        assert data[0].high_price == Decimal("105.0")
        assert data[0].low_price == Decimal("99.0")
        assert data[0].close_price == Decimal("104.0")
        assert data[0].volume == 1000000
        assert data[0].market_cap == Decimal("1000000000")
        assert data[0].pe_ratio == Decimal("15.5")
    
    @pytest.mark.asyncio
    async def test_get_market_data_with_date_range(self, adapter, sample_data_file):
        """测试按日期范围获取数据"""
        await adapter.connect()
        
        start_date = date(2024, 1, 2)
        end_date = date(2024, 1, 3)
        
        data = await adapter.get_market_data("0001.HK", start_date, end_date)
        
        assert len(data) == 2
        assert data[0].timestamp.date() >= start_date
        assert data[-1].timestamp.date() <= end_date
    
    @pytest.mark.asyncio
    async def test_get_market_data_nonexistent_symbol(self, adapter, sample_data_file):
        """测试获取不存在股票的数据"""
        await adapter.connect()
        
        data = await adapter.get_market_data("NONEXISTENT")
        
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_data_validation_success(self, adapter, sample_data_file):
        """测试数据验证成功"""
        await adapter.connect()
        
        data = await adapter.get_market_data("0001.HK")
        validation_result = await adapter.validate_data(data)
        
        assert validation_result.is_valid is True
        assert validation_result.quality_score > 0.8
        assert validation_result.quality_level in [DataQuality.EXCELLENT, DataQuality.GOOD]
        assert len(validation_result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_data_validation_with_errors(self, adapter):
        """测试数据验证发现错误"""
        from src.data_adapters.base_adapter import RealMarketData
        
        # 创建有错误的数据
        invalid_data = [
            RealMarketData(
                symbol="TEST",
                timestamp=datetime.now(),
                open_price=Decimal("100.0"),
                high_price=Decimal("99.0"),  # 最高价低于最低价
                low_price=Decimal("101.0"),
                close_price=Decimal("102.0"),
                volume=-1000,  # 负成交量
                data_source="test",
                quality_score=0.5
            )
        ]
        
        validation_result = await adapter.validate_data(invalid_data)
        
        assert validation_result.is_valid is False
        assert len(validation_result.errors) > 0
        assert len(validation_result.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, adapter, sample_data_file):
        """测试缓存功能"""
        await adapter.connect()
        
        # 第一次获取数据（应该从文件读取）
        data1 = await adapter.get_market_data("0001.HK")
        
        # 第二次获取数据（应该从缓存读取）
        data2 = await adapter.get_market_data("0001.HK")
        
        assert len(data1) == len(data2)
        assert data1[0].symbol == data2[0].symbol
        
        # 验证缓存键存在
        cache_key = adapter.get_cache_key("0001.HK")
        assert cache_key in adapter._cache
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, adapter, sample_data_file):
        """测试缓存失效"""
        await adapter.connect()
        
        # 获取数据
        await adapter.get_market_data("0001.HK")
        
        # 清空缓存
        adapter.clear_cache()
        
        # 验证缓存已清空
        cache_key = adapter.get_cache_key("0001.HK")
        cached_data = adapter.get_cache(cache_key)
        assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_health_check(self, adapter, sample_data_file):
        """测试健康检查"""
        await adapter.connect()
        
        health_status = await adapter.health_check()
        
        assert "status" in health_status
        assert "source_type" in health_status
        assert "last_update" in health_status
        assert "cache_size" in health_status
        assert "config" in health_status
    
    @pytest.mark.asyncio
    async def test_get_available_symbols(self, adapter, sample_data_file):
        """测试获取可用股票代码"""
        await adapter.connect()
        
        symbols = await adapter.get_available_symbols()
        
        assert len(symbols) > 0
        assert "0001.HK" in symbols
    
    @pytest.mark.asyncio
    async def test_refresh_data_files(self, adapter, sample_data_file):
        """测试刷新数据文件"""
        await adapter.connect()
        
        initial_count = len(adapter._data_files)
        result = await adapter.refresh_data_files()
        
        assert result is True
        assert len(adapter._data_files) == initial_count
    
    @pytest.mark.asyncio
    async def test_transform_data_dataframe(self, adapter):
        """测试转换DataFrame数据"""
        # 创建测试DataFrame
        df = pd.DataFrame({
            'date': ['2024-01-01'],
            'symbol': ['TEST'],
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [104.0],
            'volume': [1000000]
        })
        df['date'] = pd.to_datetime(df['date'])
        
        # 转换数据
        result = await adapter.transform_data(df)
        
        assert len(result) == 1
        assert result[0].symbol == "TEST"
        assert result[0].open_price == Decimal("100.0")
    
    @pytest.mark.asyncio
    async def test_transform_data_list(self, adapter):
        """测试转换列表数据"""
        from src.data_adapters.base_adapter import RealMarketData
        
        test_data = [
            RealMarketData(
                symbol="TEST",
                timestamp=datetime.now(),
                open_price=Decimal("100.0"),
                high_price=Decimal("105.0"),
                low_price=Decimal("99.0"),
                close_price=Decimal("104.0"),
                volume=1000000,
                data_source="test",
                quality_score=1.0
            )
        ]
        
        result = await adapter.transform_data(test_data)
        
        assert len(result) == 1
        assert result[0].symbol == "TEST"
    
    @pytest.mark.asyncio
    async def test_calculate_quality_score(self, adapter):
        """测试质量评分计算"""
        from src.data_adapters.base_adapter import RealMarketData
        
        # 高质量数据
        high_quality_data = [
            RealMarketData(
                symbol="TEST",
                timestamp=datetime.now(),
                open_price=Decimal("100.0"),
                high_price=Decimal("105.0"),
                low_price=Decimal("99.0"),
                close_price=Decimal("104.0"),
                volume=1000000,
                data_source="test",
                quality_score=1.0
            )
        ]
        
        score = adapter.calculate_quality_score(high_quality_data)
        assert score > 0.8
        
        # 低质量数据
        low_quality_data = [
            RealMarketData(
                symbol="TEST",
                timestamp=datetime.now(),
                open_price=Decimal("100.0"),
                high_price=Decimal("99.0"),  # 错误：最高价低于最低价
                low_price=Decimal("101.0"),
                close_price=Decimal("104.0"),
                volume=-1000,  # 错误：负成交量
                data_source="test",
                quality_score=0.3
            )
        ]
        
        score = adapter.calculate_quality_score(low_quality_data)
        assert score < 0.5
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_file(self, temp_data_dir):
        """测试处理无效文件"""
        # 创建无效的CSV文件
        invalid_file = Path(temp_data_dir) / "invalid.csv"
        with open(invalid_file, 'w') as f:
            f.write("invalid,csv,data\n")
            f.write("missing,columns\n")
        
        config = RawDataAdapterConfig(
            data_directory=temp_data_dir,
            file_pattern="*.csv"
        )
        adapter = RawDataAdapter(config)
        
        result = await adapter.connect()
        # 连接应该成功，但扫描文件时应该跳过无效文件
        assert result is True
    
    @pytest.mark.asyncio
    async def test_config_validation(self, temp_data_dir):
        """测试配置验证"""
        # 测试无效配置
        with pytest.raises(Exception):
            RawDataAdapterConfig(
                data_directory="",  # 空目录
                update_frequency=0,  # 无效频率
                max_retries=15,  # 超出范围
                quality_threshold=1.5  # 超出范围
            )
