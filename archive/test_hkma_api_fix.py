"""
HKMA API Connection Fix Test
修复HKMA API连接问题的测试脚本
"""

import requests
import json
import time

def test_hkma_api_with_different_endpoints():
    """测试不同的HKMA API端点"""
    print("Testing HKMA API with different endpoints...")

    # 修复后的API端点配置
    api_endpoints = {
        'hibor_rates': {
            'name': 'HIBOR Rates',
            'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily',
            'params': {'pagesize': 10}
        },
        'exchange_rates': {
            'name': 'Exchange Rates',
            'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily',
            'params': {'pagesize': 10}
        }
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    results = {}

    for key, config in api_endpoints.items():
        print(f"\nTesting {config['name']}...")
        print(f"URL: {config['url']}")

        try:
            response = requests.get(
                config['url'],
                params=config['params'],
                headers=headers,
                timeout=30
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"JSON Response Keys: {list(data.keys())}")

                    if 'datas' in data:
                        records_count = len(data['datas'])
                        print(f"Records received: {records_count}")

                        if records_count > 0:
                            sample_record = data['datas'][0]
                            print(f"Sample record: {sample_record}")
                            results[key] = {
                                'success': True,
                                'records': records_count,
                                'sample': sample_record
                            }
                        else:
                            results[key] = {
                                'success': False,
                                'error': 'No data records received'
                            }
                    else:
                        print(f"Response structure: {json.dumps(data, indent=2)}")
                        results[key] = {
                            'success': False,
                            'error': 'Unexpected response structure'
                        }

                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    print(f"Raw Response: {response.text[:500]}...")
                    results[key] = {
                        'success': False,
                        'error': 'JSON decode failed'
                    }
            else:
                print(f"HTTP Error: {response.text}")
                results[key] = {
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                }

        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            results[key] = {
                'success': False,
                'error': str(e)
            }

        # 添加延迟避免API限制
        time.sleep(2)

    return results

def test_alternative_data_sources():
    """测试其他可能的数据源"""
    print("\n" + "="*60)
    print("Testing Alternative Data Sources...")
    print("="*60)

    # 测试备用端点
    alternative_endpoints = [
        {
            'name': 'HKMA API (Alternative)',
            'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base',
            'params': {'pagesize': 5}
        },
        {
            'name': 'HKMA API (Test)',
            'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/financial/economic-statistics',
            'params': {'pagesize': 5}
        }
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    for endpoint in alternative_endpoints:
        print(f"\nTesting {endpoint['name']}...")

        try:
            response = requests.get(
                endpoint['url'],
                params=endpoint['params'],
                headers=headers,
                timeout=20
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response structure: {list(data.keys())}")
                print(f"Data available: {len(str(data))} characters")

                if 'datas' in data:
                    print(f"Records: {len(data['datas'])}")
                    if len(data['datas']) > 0:
                        print(f"Sample: {data['datas'][0]}")
                        return True  # 找到可用的数据源

        except Exception as e:
            print(f"Error: {e}")

    return False

def create_mock_hkma_data():
    """创建模拟HKMA数据用于测试"""
    print("\n" + "="*60)
    print("Creating Mock HKMA Data for Testing...")
    print("="*60)

    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta

    # 创建模拟HIBOR数据
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')

    # 模拟真实的HIBOR利率特征
    hibor_data = []
    tenors = ['Overnight', '1 Week', '1 Month', '3 Months', '6 Months', '12 Months']

    for date in dates:
        base_rate = 3.0 + np.sin(date.timetuple().tm_yday / 365.25 * 2 * np.pi) * 0.8

        for i, tenor in enumerate(tenors):
            # 不同期限有不同的利率水平和波动性
            tenor_premium = i * 0.1
            volatility = 0.1 + i * 0.02

            rate = base_rate + tenor_premium + np.random.normal(0, volatility)
            rate = max(0.1, min(10.0, rate))  # 限制在合理范围

            hibor_data.append({
                'end_of_date': date.strftime('%Y-%m-%d'),
                'tenor': tenor,
                'rate': round(rate, 4)
            })

    # 创建模拟汇率数据
    fx_data = []
    currencies = ['USD', 'CNY', 'EUR', 'JPY', 'GBP']

    base_usd_hkd = 7.8000

    for date in dates:
        # 模拟汇率波动
        fx_variation = np.sin(date.timetuple().tm_yday / 100) * 0.02

        for currency in currencies:
            if currency == 'USD':
                rate = base_usd_hkd + fx_variation + np.random.normal(0, 0.01)
            elif currency == 'CNY':
                rate = base_usd_hkd * 0.87 + fx_variation + np.random.normal(0, 0.005)
            elif currency == 'EUR':
                rate = base_usd_hkd * 8.5 + fx_variation + np.random.normal(0, 0.02)
            elif currency == 'JPY':
                rate = base_usd_hkd * 0.052 + fx_variation + np.random.normal(0, 0.001)
            elif currency == 'GBP':
                rate = base_usd_hkd * 9.8 + fx_variation + np.random.normal(0, 0.03)

            rate = max(0.01, rate)  # 确保汇率为正

            fx_data.append({
                'end_of_date': date.strftime('%Y-%m-%d'),
                'currency': f'{currency}/HKD',
                'rate': round(rate, 4)
            })

    # 保存模拟数据
    mock_data = {
        'hibor_rates': hibor_data,
        'exchange_rates': fx_data
    }

    # 保存到文件
    import os
    os.makedirs('mock_data', exist_ok=True)

    with open('mock_data/mock_hibor_rates.json', 'w') as f:
        json.dump(hibor_data, f, indent=2)

    with open('mock_data/mock_exchange_rates.json', 'w') as f:
        json.dump(fx_data, f, indent=2)

    # 创建DataFrame
    hibor_df = pd.DataFrame(hibor_data)
    fx_df = pd.DataFrame(fx_data)

    print(f"Mock HIBOR data created: {len(hibor_df)} records")
    print(f"Mock FX data created: {len(fx_df)} records")

    # 显示样本数据
    print(f"\nHIBOR Sample:")
    print(hibor_df.head(10))

    print(f"\nFX Sample:")
    print(fx_df.head(10))

    # 保存为parquet格式
    hibor_df.to_parquet('mock_data/hibor_rates.parquet', index=False)
    fx_df.to_parquet('mock_data/exchange_rates.parquet', index=False)

    print(f"\nMock data saved to 'mock_data/' directory")
    print(f"Files created:")
    print(f"  - mock_hibor_rates.json")
    print(f"  - mock_exchange_rates.json")
    print(f"  - hibor_rates.parquet")
    print(f"  - exchange_rates.parquet")

    return mock_data

def main():
    """主测试函数"""
    print("HKMA API Connection Fix Test")
    print("="*60)

    # 步骤1: 测试真实API
    print("\nStep 1: Testing Real HKMA API...")
    api_results = test_hkma_api_with_different_endpoints()

    success_count = sum(1 for r in api_results.values() if r['success'])
    total_count = len(api_results)

    print(f"\nAPI Test Results: {success_count}/{total_count} successful")

    if success_count > 0:
        print("Real API is working!")
        for key, result in api_results.items():
            if result['success']:
                print(f"  {key}: {result['records']} records")
    else:
        print("Real API not accessible, testing alternatives...")

        # 步骤2: 测试备用数据源
        print("\nStep 2: Testing Alternative Data Sources...")
        alternative_works = test_alternative_data_sources()

        if alternative_works:
            print("Alternative data source found!")
        else:
            print("No alternative data sources available.")

        # 步骤3: 创建模拟数据
        print("\nStep 3: Creating Mock Data...")
        mock_data = create_mock_hkma_data()

        print("\nMock data created successfully for system testing!")

    return api_results

if __name__ == "__main__":
    results = main()