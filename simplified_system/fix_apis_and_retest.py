#!/usr / bin / env python3
"""
修复失败的API并重新测试
"""

import asyncio

import aiohttp


async def test_efbn_api():
    """测试EFBN API - 需要segment参数"""
    url = "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - indicative - price"

    params = {
        "lang": "en",
        "limit": "10",
        "segment": "IndicativePrice",  # 添加必需的segment参数
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params = params) as response:
            print(f"EFBN Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"EFBN Success: {data['header']['success']}")
                return True, data
            else:
                error_text = await response.text()
                print(f"EFBN Error: {error_text}")
                return False, None


async def test_institutional_bond_api():
    """测试机构债券API - 需要segment参数"""
    url = "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / efbn - closing"

    params = {"lang": "en", "limit": "10", "segment": "Bills"}  # 添加必需的segment参数

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params = params) as response:
            print(f"Institutional Bond Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                print(f"Institutional Bond Success: {data['header']['success']}")
                return True, data
            else:
                error_text = await response.text()
                print(f"Institutional Bond Error: {error_text}")
                return False, None


async def main():
    print("Testing Fixed APIs...")
    print("=" * 40)

    # 测试EFBN API
    print("\n1. Testing EFBN API with segment parameter...")
    efbn_success, efbn_data = await test_efbn_api()

    # 测试机构债券API
    print("\n2. Testing Institutional Bond API with segment parameter...")
    bond_success, bond_data = await test_institutional_bond_api()

    # 汇总结果
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    print(f"EFBN API: {'SUCCESS' if efbn_success else 'FAILED'}")
    print(f"Institutional Bond API: {'SUCCESS' if bond_success else 'FAILED'}")

    if efbn_success:
        print(f"\nEFBN Data Preview:")
        if "result" in efbn_data and "records" in efbn_data["result"]:
            print(f"Records count: {len(efbn_data['result']['records'])}")
            if efbn_data["result"]["records"]:
                print(f"Latest record: {efbn_data['result']['records'][0]}")

    if bond_success:
        print(f"\nInstitutional Bond Data Preview:")
        if "result" in bond_data and "records" in bond_data["result"]:
            print(f"Records count: {len(bond_data['result']['records'])}")
            if bond_data["result"]["records"]:
                print(f"Latest record: {bond_data['result']['records'][0]}")

    return efbn_success, bond_success


if __name__ == "__main__":
    asyncio.run(main())
