#!/usr/bin/env python3
"""
Debug HKMA API calls
"""

import requests
import json

def debug_api(url):
    print(f"Testing API: {url}")
    try:
        response = requests.get(url, timeout=30, headers={'Accept': 'application/json'})
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            data = response.json()
            print(f"JSON Keys: {list(data.keys())}")

            if 'records' in data:
                print(f"Number of records: {len(data['records'])}")
                if data['records']:
                    print(f"Sample record: {data['records'][0]}")
            else:
                print(f"Response structure: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error response: {response.text[:500]}...")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Test HKMA API endpoints
    endpoints = [
        "https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er/ir-er-dhk-daily-ihb",
        "https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base"
    ]

    for endpoint in endpoints:
        print("=" * 60)
        debug_api(endpoint)
        print()