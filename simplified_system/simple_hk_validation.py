#!/usr/bin/env python3
"""
簡化的香港專用系統驗證 - Simplified Hong Kong Exclusive System Validation
驗證文件結構和基本功能
"""

import json
import logging
from datetime import datetime
from pathlib import Path
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_file_structure():
    """驗證文件結構"""
    logger.info("驗證文件結構...")

    # 檢查香港專用文件是否存在
    hk_files = [
        'src/multi_asset/asset_models.py',
        'src/data/hk_market_data_manager.py',
        'src/api/hk_market_api.py',
        '../config/hk_market_config.json',
        '../config/hk_trading_symbols.json',
        '../config/hk_data_sources.yaml'
    ]

    existing_files = []
    missing_files = []

    for file_path in hk_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            existing_files.append(file_path)
            logger.info(f"✅ {file_path} 存在")
        else:
            missing_files.append(file_path)
            logger.error(f"❌ {file_path} 不存在")

    return len(missing_files) == 0

def validate_asset_models_content():
    """驗證資產模型內容"""
    logger.info("驗證資產模型內容...")

    try:
        asset_models_file = Path(__file__).parent / 'src/multi_asset/asset_models.py'

        if not asset_models_file.exists():
            logger.error("資產模型文件不存在")
            return False

        with open(asset_models_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 檢查是否移除了非香港交易所
        non_hk_exchanges = ['NYSE', 'NASDAQ', 'LSE', 'TSX']
        for exchange in non_hk_exchanges:
            if exchange in content:
                logger.error(f"發現非香港交易所: {exchange}")
                return False

        # 檢查是否包含香港專用內容
        hk_content = ['class Exchange(Enum):', 'HKEX = "HKEX"', '香港交易所']
        hk_count = sum(1 for item in hk_content if item in content)

        if hk_count < 2:
            logger.error("缺少香港專用內容")
            return False

        # 檢查資產類別
        if 'EQUITY = "equity"' not in content:
            logger.error("缺少股票資產類別")
            return False

        # 檢查parse_symbol函數
        if 'def parse_symbol' not in content:
            logger.error("缺少符號解析函數")
            return False

        # 檢查是否只返回香港交易所
        if 'exchange": Exchange.HKEX' not in content:
            logger.error("符號解析不返回香港交易所")
            return False

        logger.info("✅ 資產模型內容驗證通過")
        return True

    except Exception as e:
        logger.error(f"資產模型內容驗證失敗: {e}")
        return False

def validate_config_files():
    """驗證配置文件"""
    logger.info("驗證配置文件...")

    try:
        # 檢查JSON配置文件
        config_files = [
            '../config/hk_market_config.json',
            '../config/hk_trading_symbols.json'
        ]

        for config_file in config_files:
            config_path = Path(__file__).parent / config_file
            if not config_path.exists():
                logger.error(f"配置文件不存在: {config_file}")
                return False

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 檢查香港專用內容
            config_str = str(config_data).upper()
            if 'HONG KONG' not in config_str:
                logger.error(f"{config_file} 缺少香港專用配置")
                return False

            # 檢查是否包含非香港交易所
            if 'NASDAQ' in config_str or 'NYSE' in config_str:
                logger.error(f"{config_file} 包含非香港交易所")
                return False

        # 檢查YAML配置文件
        yaml_config = Path(__file__).parent / '../config/hk_data_sources.yaml'
        if yaml_config.exists():
            with open(yaml_config, 'r', encoding='utf-8') as f:
                yaml_content = f.read()

            if 'hkma_sources:' not in yaml_content:
                logger.error("YAML配置缺少HKMA數據源")
                return False

        logger.info("✅ 配置文件驗證通過")
        return True

    except Exception as e:
        logger.error(f"配置文件驗證失敗: {e}")
        return False

def validate_api_content():
    """驗證API內容"""
    logger.info("驗證API內容...")

    try:
        api_file = Path(__file__).parent / 'src/api/hk_market_api.py'

        if not api_file.exists():
            logger.error("API文件不存在")
            return False

        with open(api_file, 'r', encoding='utf-8') as f:
            api_content = f.read()

        # 檢查API標題
        if '香港市場量化交易API' not in api_content:
            logger.error("缺少香港專用API標題")
            return False

        # 檢查符號驗證函數
        if 'def validate_hk_symbol' not in api_content:
            logger.error("缺少香港符號驗證函數")
            return False

        # 檢查是否排除非香港交易所
        non_hk_check = 'not a valid Hong Kong stock symbol'
        if non_hk_check not in api_content:
            logger.error("API未排除非香港股票符號")
            return False

        # 檢查香港專用端點
        hk_endpoints = [
            'get_hk_stock_data',
            'get_hsi_constituents',
            'get_hkma_economic_data'
        ]

        for endpoint in hk_endpoints:
            if endpoint not in api_content:
                logger.error(f"缺少香港專用端點: {endpoint}")
                return False

        logger.info("✅ API內容驗證通過")
        return True

    except Exception as e:
        logger.error(f"API內容驗證失敗: {e}")
        return False

def validate_symbol_patterns():
    """驗證符號模式"""
    logger.info("驗證符號模式...")

    try:
        # 檢查符號配置文件
        symbols_file = Path(__file__).parent / '../config/hk_trading_symbols.json'
        if not symbols_file.exists():
            logger.error("符號配置文件不存在")
            return False

        with open(symbols_file, 'r', encoding='utf-8') as f:
            symbols_data = json.load(f)

        # 檢查是否只包含香港股票
        if 'meta' not in symbols_data:
            logger.error("缺少符號元數據")
            return False

        if symbols_data['meta']['market'] != 'Hong Kong Stock Exchange':
            logger.error("市場配置不正確")
            return False

        # 檢查股票符號格式
        for category in ['blue_chip_stocks', 'technology_stocks', 'etf_products', 'reit_products']:
            if category in symbols_data:
                for stock in symbols_data[category]:
                    symbol = stock['symbol']
                    if not (symbol.endswith('.HK') or (len(symbol) >= 4 and symbol.isdigit())):
                        logger.error(f"無效的香港股票符號: {symbol}")
                        return False

        logger.info("✅ 符號模式驗證通過")
        return True

    except Exception as e:
        logger.error(f"符號模式驗證失敗: {e}")
        return False

def run_validation():
    """運行所有驗證"""
    logger.info("開始簡化版香港專用系統驗證...")

    tests = [
        ('文件結構', validate_file_structure),
        ('資產模型內容', validate_asset_models_content),
        ('配置文件', validate_config_files),
        ('API內容', validate_api_content),
        ('符號模式', validate_symbol_patterns)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"執行測試: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"{test_name} {status}")
        except Exception as e:
            logger.error(f"{test_name} 異常: {e}")
            results.append((test_name, False))

    # 生成報告
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "="*60)
    print("香港專用系統驗證報告")
    print("Hong Kong Exclusive System Validation Report")
    print("="*60)
    print(f"測試結果: {passed}/{total} 通過 ({passed/total:.1%})")
    print(f"驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")

    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:15} {status}")

    print("="*60)

    # 總體結果
    if passed == total:
        logger.info("🎉 香港專用系統驗證全部通過！")
        return True
    else:
        logger.warning(f"⚠️  香港專用系統驗證部分失敗 ({passed}/{total})")
        return False

if __name__ == "__main__":
    success = run_validation()
    exit(0 if success else 1)