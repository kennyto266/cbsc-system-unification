#!/usr/bin/env python3
"""
Personal Trading System Configuration
个人交易系统配置
基于现有YAML配置的简化版本
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class HKMAConfig:
    """HKMA数据源配置"""
    hibor_url: str
    monetary_base_url: str
    exchange_rate_url: str
    timeout: int = 30
    use_cache: bool = True
    cache_dir: str = "data"


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 100000
    commission: float = 0.001
    freq: str = '1D'
    slippage: float = 0.001
    risk_free_rate: float = 0.03  # 3% 无风险利率


@dataclass
class StockConfig:
    """股票配置"""
    default_symbols: List[str]
    api_endpoint: str
    timeout: int = 30


@dataclass
class SystemConfig:
    """系统配置"""
    hkma: HKMAConfig
    backtest: BacktestConfig
    stock: StockConfig
    log_level: str = "INFO"
    cache_enabled: bool = True


class PersonalTradingConfig:
    """
    个人交易系统配置管理器
    提供简化的配置加载和管理功能
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认使用内置配置
        """
        self.config_file = config_file
        self.config: SystemConfig = self._load_config()

    def _load_config(self) -> SystemConfig:
        """加载配置"""
        if self.config_file and Path(self.config_file).exists():
            logger.info(f"加载配置文件: {self.config_file}")
            return self._load_from_file()
        else:
            logger.info("使用默认配置")
            return self._get_default_config()

    def _load_from_file(self) -> SystemConfig:
        """从文件加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            return self._parse_config(config_data)

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.warning("使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> SystemConfig:
        """获取默认配置"""
        return SystemConfig(
            hkma=HKMAConfig(
                hibor_url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
                monetary_base_url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
                exchange_rate_url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily",
                timeout=30,
                use_cache=True,
                cache_dir="data"
            ),
            backtest=BacktestConfig(
                initial_capital=100000,
                commission=0.001,
                freq='1D',
                slippage=0.001,
                risk_free_rate=0.03
            ),
            stock=StockConfig(
                default_symbols=[
                    "0700.HK",  # 腾讯
                    "0941.HK",  # 中国移动
                    "1398.HK",  # 工商银行
                    "0388.HK",  # 港交所
                    "2318.HK",  # 中国平安
                    "1299.HK",  # 友邦保险
                    "0005.HK",  # 汇丰控股
                    "0011.HK",  # 恒生银行
                    "0016.HK",  # 新鸿基地产
                    "0002.HK"   # 中电控股
                ],
                api_endpoint="http://18.180.162.113:9191/inst/getInst",
                timeout=30
            ),
            log_level="INFO",
            cache_enabled=True
        )

    def _parse_config(self, config_data: Dict[str, Any]) -> SystemConfig:
        """解析配置数据"""
        # 解析HKMA配置
        hkma_data = config_data.get('hkma_sources', {})
        hkma_config = HKMAConfig(
            hibor_url=hkma_data.get('hibor', {}).get('api_endpoint', ""),
            monetary_base_url=hkma_data.get('monetary_base', {}).get('api_endpoint', ""),
            exchange_rate_url=hkma_data.get('exchange_rate', {}).get('api_endpoint', ""),
            timeout=hkma_data.get('hibor', {}).get('timeout', 30),
            use_cache=True,
            cache_dir="data"
        )

        # 解析回测配置
        backtest_data = config_data.get('backtest', {})
        backtest_config = BacktestConfig(
            initial_capital=backtest_data.get('initial_capital', 100000),
            commission=backtest_data.get('commission', 0.001),
            freq=backtest_data.get('freq', '1D'),
            slippage=backtest_data.get('slippage', 0.001),
            risk_free_rate=0.03
        )

        # 解析股票配置
        stock_data = config_data.get('stock_sources', {})
        default_symbols = self._extract_hsi_constituents(config_data)
        stock_config = StockConfig(
            default_symbols=default_symbols,
            api_endpoint=stock_data.get('yahoo_finance_hk', {}).get('api_endpoint', ""),
            timeout=30
        )

        return SystemConfig(
            hkma=hkma_config,
            backtest=backtest_config,
            stock=stock_config,
            log_level=config_data.get('monitoring', {}).get('logging', {}).get('level', "INFO"),
            cache_enabled=config_data.get('cache', {}).get('memory_cache', {}).get('enabled', True)
        )

    def _extract_hsi_constituents(self, config_data: Dict[str, Any]) -> List[str]:
        """从配置中提取恒生指数成分股"""
        # 常用港股代码
        default_symbols = [
            "0700.HK",  # 腾讯
            "0941.HK",  # 中国移动
            "1398.HK",  # 工商银行
            "0388.HK",  # 港交所
            "2318.HK",  # 中国平安
            "1299.HK",  # 友邦保险
            "0005.HK",  # 汇丰控股
            "0011.HK",  # 恒生银行
            "0016.HK",  # 新鸿基地产
            "0002.HK"   # 中电控股
        ]

        return config_data.get('default_symbols', default_symbols)

    def save_config(self, filename: str = "personal_trading_config.yaml") -> None:
        """
        保存配置到文件

        Args:
            filename: 配置文件名
        """
        try:
            config_data = {
                'hkma_sources': {
                    'hibor': {
                        'api_endpoint': self.config.hkma.hibor_url,
                        'timeout': self.config.hkma.timeout
                    },
                    'monetary_base': {
                        'api_endpoint': self.config.hkma.monetary_base_url,
                        'timeout': self.config.hkma.timeout
                    },
                    'exchange_rate': {
                        'api_endpoint': self.config.hkma.exchange_rate_url,
                        'timeout': self.config.hkma.timeout
                    }
                },
                'backtest': {
                    'initial_capital': self.config.backtest.initial_capital,
                    'commission': self.config.backtest.commission,
                    'freq': self.config.backtest.freq,
                    'slippage': self.config.backtest.slippage
                },
                'stock_sources': {
                    'yahoo_finance_hk': {
                        'api_endpoint': self.config.stock.api_endpoint,
                        'timeout': self.config.stock.timeout
                    }
                },
                'default_symbols': self.config.stock.default_symbols,
                'cache': {
                    'memory_cache': {
                        'enabled': self.config.cache_enabled
                    }
                },
                'monitoring': {
                    'logging': {
                        'level': self.config.log_level
                    }
                }
            }

            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)

            logger.info(f"配置已保存到: {filename}")

        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    def get_hkma_urls(self) -> Dict[str, str]:
        """获取HKMA API URL配置"""
        return {
            'hibor': self.config.hkma.hibor_url,
            'monetary_base': self.config.hkma.monetary_base_url,
            'exchange_rate': self.config.hkma.exchange_rate_url
        }

    def get_backtest_config(self) -> BacktestConfig:
        """获取回测配置"""
        return self.config.backtest

    def get_default_symbols(self) -> List[str]:
        """获取默认股票列表"""
        return self.config.stock.default_symbols

    def update_symbol_list(self, symbols: List[str]) -> None:
        """
        更新默认股票列表

        Args:
            symbols: 新的股票代码列表
        """
        self.config.stock.default_symbols = symbols
        logger.info(f"更新默认股票列表: {symbols}")

    def update_risk_free_rate(self, rate: float) -> None:
        """
        更新无风险利率

        Args:
            rate: 新的无风险利率 (如 0.03 表示3%)
        """
        self.config.backtest.risk_free_rate = rate
        logger.info(f"更新无风险利率: {rate:.2%}")

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            'hkma_endpoints': len(self.get_hkma_urls()),
            'default_symbols': len(self.get_default_symbols()),
            'initial_capital': self.config.backtest.initial_capital,
            'commission': self.config.backtest.commission,
            'risk_free_rate': self.config.backtest.risk_free_rate,
            'cache_enabled': self.config.cache_enabled
        }


# 全局配置实例
_config_instance: Optional[PersonalTradingConfig] = None


def get_config() -> PersonalTradingConfig:
    """
    获取全局配置实例

    Returns:
        PersonalTradingConfig: 配置实例
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = PersonalTradingConfig()
    return _config_instance


def load_config_from_file(config_file: str) -> PersonalTradingConfig:
    """
    从文件加载配置并设为全局配置

    Args:
        config_file: 配置文件路径

    Returns:
        PersonalTradingConfig: 配置实例
    """
    global _config_instance
    _config_instance = PersonalTradingConfig(config_file)
    return _config_instance


def reset_config() -> None:
    """重置配置为默认值"""
    global _config_instance
    _config_instance = None
    logger.info("配置已重置为默认值")