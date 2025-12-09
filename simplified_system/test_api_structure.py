#!/usr / bin / env python3
"""
Test HKMA API structure
"""

import json

import requests


def test_monetary_base_api():
    """Test monetary base API structure"""
    url = "https://api.hkma.gov.hk / public / market - data - and - statistics / daily - monetary - statistics / daily - figures - monetary - base"

    print(f"Testing: {url}")

    try:
        response = requests.get(url, timeout = 30, headers={"Accept": "application / json"})
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Top - level keys: {list(data.keys())}")

            # Check structure
            if "result" in data:
                print(f"Result type: {type(data['result'])}")
                if isinstance(data["result"], list):
                    print(f"Number of result records: {len(data['result'])}")
                    if data["result"]:
                        print(f"Sample record keys: {list(data['result'][0].keys())}")
                        print(
                            f"Sample record: {json.dumps(data['result'][0], indent = 2)}"
                        )
                elif isinstance(data["result"], dict):
                    print(f"Result dict keys: {list(data['result'].keys())}")

            if "header" in data:
                print(f"Header info: {data['header']}")

        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    test_monetary_base_api()
