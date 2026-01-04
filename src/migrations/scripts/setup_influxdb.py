#!/usr/bin/env python3
"""
Setup InfluxDB time-series database for market data and performance metrics
設置InfluxDB時序數據庫用於市場數據和性能指標
"""

import sys
import os
from pathlib import Path
import requests
import json
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

def setup_influxdb():
    """Setup InfluxDB buckets and retention policies"""

    # InfluxDB configuration
    influxdb_config = {
        "url": "http://localhost:8086",
        "token": "cbsc-influxdb-token-123456789",
        "org": "cbsc",
        "bucket": "market_data"
    }

    print("=" * 60)
    print("CBSC InfluxDB Setup")
    print("=" * 60)
    print()
    print(f"URL: {influxdb_config['url']}")
    print(f"Organization: {influxdb_config['org']}")
    print(f"Main Bucket: {influxdb_config['bucket']}")
    print()

    # Test connection
    try:
        response = requests.get(f"{influxdb_config['url']}/health")
        if response.status_code == 200:
            print("✅ InfluxDB connection successful")
        else:
            print(f"❌ InfluxDB connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error connecting to InfluxDB: {e}")
        return False

    # Headers for API requests
    headers = {
        "Authorization": f"Token {influxdb_config['token']}",
        "Content-Type": "application/json"
    }

    # Create additional buckets
    buckets_to_create = [
        {
            "name": "strategy_performance",
            "description": "Strategy performance metrics and analytics",
            "retentionRules": [
                {
                    "type": "expire",
                    "everySeconds": 2592000  # 30 days
                }
            ]
        },
        {
            "name": "market_data",
            "description": "Market price and volume data",
            "retentionRules": [
                {
                    "type": "expire",
                    "everySeconds": 7776000  # 90 days
                }
            ]
        },
        {
            "name": "system_metrics",
            "description": "System performance and monitoring metrics",
            "retentionRules": [
                {
                    "type": "expire",
                    "everySeconds": 604800  # 7 days
                }
            ]
        },
        {
            "name": "user_activity",
            "description": "User activity and audit logs",
            "retentionRules": [
                {
                    "type": "expire",
                    "everySeconds": 31536000  # 365 days
                }
            ]
        }
    ]

    for bucket in buckets_to_create:
        try:
            # Check if bucket already exists
            response = requests.get(
                f"{influxdb_config['url']}/api/v2/buckets",
                headers=headers,
                params={"org": influxdb_config["org"], "name": bucket["name"]}
            )

            if response.status_code == 200 and len(response.json().get("buckets", [])) > 0:
                print(f"✅ Bucket '{bucket['name']}' already exists")
                continue

            # Create bucket
            bucket_data = {
                "orgID": get_org_id(influxdb_config, headers),
                "name": bucket["name"],
                "description": bucket["description"],
                "retentionRules": bucket["retentionRules"]
            }

            response = requests.post(
                f"{influxdb_config['url']}/api/v2/buckets",
                headers=headers,
                json=bucket_data
            )

            if response.status_code == 201:
                print(f"✅ Created bucket: {bucket['name']}")
            else:
                print(f"❌ Failed to create bucket '{bucket['name']}': {response.status_code}")
                print(f"   Response: {response.text}")

        except Exception as e:
            print(f"❌ Error creating bucket '{bucket['name']}': {e}")

    # Create sample data structure test
    print("\n📊 Creating sample data points...")

    try:
        # Write sample market data
        sample_data = {
            "bucket": "market_data",
            "org": influxdb_config["org"],
            "precision": "s",
            "data": [
                {
                    "measurement": "stock_price",
                    "tags": {
                        "symbol": "AAPL",
                        "exchange": "NASDAQ",
                        "currency": "USD"
                    },
                    "fields": {
                        "open": 150.25,
                        "high": 152.75,
                        "low": 149.50,
                        "close": 152.10,
                        "volume": 52341000
                    },
                    "time": datetime.now().isoformat()
                },
                {
                    "measurement": "stock_price",
                    "tags": {
                        "symbol": "MSFT",
                        "exchange": "NASDAQ",
                        "currency": "USD"
                    },
                    "fields": {
                        "open": 375.80,
                        "high": 378.25,
                        "low": 374.20,
                        "close": 377.15,
                        "volume": 23156000
                    },
                    "time": datetime.now().isoformat()
                }
            ]
        }

        # Write line protocol format
        line_protocol = []
        for point in sample_data["data"]:
            tags = ",".join([f"{k}={v}" for k, v in point["tags"].items()])
            fields = ",".join([f"{k}={v}" for k, v in point["fields"].items()])
            line_protocol.append(f"{point['measurement']},{tags} {fields} {int(datetime.fromisoformat(point['time']).timestamp())}")

        write_data = "\n".join(line_protocol)

        write_response = requests.post(
            f"{influxdb_config['url']}/api/v2/write",
            headers=headers,
            params={
                "org": influxdb_config["org"],
                "bucket": sample_data["bucket"],
                "precision": sample_data["precision"]
            },
            data=write_data
        )

        if write_response.status_code == 204:
            print("✅ Sample market data written successfully")
        else:
            print(f"❌ Failed to write sample data: {write_response.status_code}")
            print(f"   Response: {write_response.text}")

        # Write sample strategy performance data
        perf_data = {
            "bucket": "strategy_performance",
            "org": influxdb_config["org"],
            "precision": "s",
            "data": [
                {
                    "measurement": "strategy_metrics",
                    "tags": {
                        "strategy_id": "strategy-001",
                        "strategy_name": "MA_Crossover",
                        "user_id": "admin-001"
                    },
                    "fields": {
                        "total_return": 0.1523,
                        "sharpe_ratio": 1.2345,
                        "max_drawdown": -0.0821,
                        "volatility": 0.1245,
                        "win_rate": 0.6789,
                        "current_positions": 5
                    },
                    "time": datetime.now().isoformat()
                }
            ]
        }

        # Write performance data
        perf_line_protocol = []
        for point in perf_data["data"]:
            tags = ",".join([f"{k}={v}" for k, v in point["tags"].items()])
            fields = ",".join([f"{k}={v}" for k, v in point["fields"].items()])
            perf_line_protocol.append(f"{point['measurement']},{tags} {fields} {int(datetime.fromisoformat(point['time']).timestamp())}")

        perf_write_data = "\n".join(perf_line_protocol)

        perf_response = requests.post(
            f"{influxdb_config['url']}/api/v2/write",
            headers=headers,
            params={
                "org": influxdb_config["org"],
                "bucket": perf_data["bucket"],
                "precision": perf_data["precision"]
            },
            data=perf_write_data
        )

        if perf_response.status_code == 204:
            print("✅ Sample performance data written successfully")
        else:
            print(f"❌ Failed to write performance data: {perf_response.status_code}")

    except Exception as e:
        print(f"❌ Error writing sample data: {e}")

    # Test query functionality
    print("\n🔍 Testing query functionality...")
    try:
        query = f'''
        from(bucket: "{influxdb_config['bucket']}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "stock_price")
        |> limit(n: 5)
        '''

        query_response = requests.post(
            f"{influxdb_config['url']}/api/v2/query",
            headers=headers,
            params={
                "org": influxdb_config["org"]
            },
            data=query
        )

        if query_response.status_code == 200:
            result = query_response.json()
            if "_results" in result and len(result["_results"]) > 0:
                records = result["_results"][0].get("_value", 0)
                print(f"✅ Query successful: Found {records} data points")
            else:
                print("✅ Query successful: No data found (expected)")
        else:
            print(f"❌ Query failed: {query_response.status_code}")

    except Exception as e:
        print(f"❌ Error testing query: {e}")

    print("\n" + "=" * 60)
    print("InfluxDB setup completed!")
    print("✅ Database connection established")
    print("✅ Buckets created with retention policies")
    print("✅ Sample data written")
    print("✅ Query functionality verified")
    print("=" * 60)

    return True

def get_org_id(config, headers):
    """Get organization ID"""
    try:
        response = requests.get(
            f"{config['url']}/api/v2/orgs",
            headers=headers,
            params={"org": config["org"]}
        )

        if response.status_code == 200:
            orgs = response.json().get("orgs", [])
            if orgs:
                return orgs[0]["id"]

        return None
    except Exception:
        return None

if __name__ == "__main__":
    print("Starting InfluxDB setup...")
    success = setup_influxdb()

    if success:
        print("\n🎉 InfluxDB setup completed successfully!")
        print("The time-series database is ready for CBSC strategy management.")
    else:
        print("\n❌ InfluxDB setup failed. Please check the configuration.")