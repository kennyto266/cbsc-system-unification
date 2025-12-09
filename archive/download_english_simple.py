#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import pandas as pd
from datetime import date
from pathlib import Path

def download_english_immigration():
    """Download English version immigration data"""

    english_url = "https://www.immd.gov.hk/opendata/eng/transport/immigration_clearance/statistics_on_daily_passenger_traffic.csv"

    try:
        # Download the data
        response = requests.get(english_url, timeout=30)

        if response.status_code == 200:
            # Save the file
            output_dir = Path("daily_data")
            output_dir.mkdir(exist_ok=True)

            today = date.today().strftime('%Y%m%d')
            output_file = output_dir / f"immigration_daily_data_{today}_english.csv"

            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write(response.text)

            print(f"SUCCESS: English immigration data downloaded to {output_file}")

            # Read and analyze
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))

            print(f"Data shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")

            return True

        else:
            print(f"FAILED: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = download_english_immigration()
    print("Download completed" if success else "Download failed")