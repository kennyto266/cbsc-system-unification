#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
from datetime import datetime
from pathlib import Path

def fix_immigration_csv():
    """Fix immigration CSV encoding and create English column names"""

    input_file = Path("daily_data/immigration_daily_data_20251121.csv")
    output_file = Path("daily_data/immigration_daily_data_20251121_fixed.csv")

    if not input_file.exists():
        print("Input file not found")
        return False

    try:
        # Read with UTF-8 BOM signature
        print("Reading immigration data...")
        df = pd.read_csv(input_file, encoding='utf-8-sig')

        print(f"Data shape: {df.shape}")

        # Create English column names
        new_columns = ['date', 'control_point', 'direction', 'hk_residents', 'mainland_visitors', 'other_visitors', 'total']
        df.columns = new_columns

        print(f"Columns renamed: {list(df.columns)}")

        # Convert date column
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')

        # Add metadata
        df['data_source'] = 'Hong Kong Immigration Department'
        df['crawl_date'] = datetime.now().strftime('%Y-%m-%d')
        df['encoding_fixed'] = True

        # Save fixed file
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"Fixed file saved: {output_file}")
        print(f"Total records: {len(df)}")

        # Show sample data
        print("\nSample of latest records:")
        latest = df[df['date'] == df['date'].max()]
        if not latest.empty:
            print(latest[['date', 'control_point', 'direction', 'hk_residents', 'mainland_visitors', 'other_visitors', 'total']].head(5).to_string())

        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = fix_immigration_csv()
    if success:
        print("SUCCESS: Immigration CSV encoding fixed!")
    else:
        print("FAILED: Could not fix immigration CSV")