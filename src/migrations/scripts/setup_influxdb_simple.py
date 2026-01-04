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
            print("[OK] InfluxDB connection successful")
        else:
            print(f"[ERROR] InfluxDB connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Error connecting to InfluxDB: {e}")
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
                print(f"[OK] Bucket '{bucket['name']}' already exists")
                continue

            # Create bucket
            org_id = get_org_id(influxdb_config, headers)
            if not org_id:
                print(f"[ERROR] Could not get org ID for bucket '{bucket['name']}'")
                continue

            bucket_data = {
                "orgID": org_id,
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
                print(f"[OK] Created bucket: {bucket['name']}")
            else:
                print(f"[ERROR] Failed to create bucket '{bucket['name']}': {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Error creating bucket '{bucket['name']}': {e}")

    print("\nInfluxDB buckets setup completed!")
    print("Available buckets:")

    # List all buckets
    try:
        response = requests.get(
            f"{influxdb_config['url']}/api/v2/buckets",
            headers=headers,
            params={"org": influxdb_config["org"]}
        )

        if response.status_code == 200:
            buckets = response.json().get("buckets", [])
            for bucket in buckets:
                print(f"  - {bucket['name']}: {bucket['description']}")

    except Exception as e:
        print(f"[ERROR] Could not list buckets: {e}")

    print("\n" + "=" * 60)
    print("InfluxDB setup completed!")
    print("[OK] Database connection established")
    print("[OK] Buckets created with retention policies")
    print("=" * 60)

    return True

def get_org_id(config, headers):
    """Get organization ID"""
    try:
        response = requests.get(
            f"{config['url']}/api/v2/orgs",
            headers=headers
        )

        if response.status_code == 200:
            orgs = response.json().get("orgs", [])
            for org in orgs:
                if org["name"] == config["org"]:
                    return org["id"]

        return None
    except Exception:
        return None

if __name__ == "__main__":
    print("Starting InfluxDB setup...")
    success = setup_influxdb()

    if success:
        print("\n[SUCCESS] InfluxDB setup completed successfully!")
        print("The time-series database is ready for CBSC strategy management.")
    else:
        print("\n[FAILED] InfluxDB setup failed. Please check the configuration.")