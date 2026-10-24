#!/usr/bin/env python3
"""
CBBC Data Synchronization Script
Automatically syncs CBBC data from HKEX or other sources
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import aiohttp
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from services.cbbc_data_reader import CBBCDataReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/cbbc_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class CBBCDataSynchronizer:
    """Synchronizes CBBC data from various sources"""

    def __init__(self, config_path: str = "config/cbbc_sync_config.json"):
        """
        Initialize synchronizer

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.data_dir = Path(self.config.get("data_directory", "acquired_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create logs directory
        Path("logs").mkdir(exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {
                "data_sources": ["file"],
                "sync_interval_minutes": 60,
                "data_directory": "acquired_data",
                "hkex": {
                    "base_url": "https://www.hkex.com.hk",
                    "endpoints": {
                        "cbbc_daily": "/Market-Data/Securities-Prices/Equities/Callable-Bulls-Bears-and-Structured-Products?sc_lang=en"
                    }
                },
                "file": {
                    "path_pattern": "acquired_data/cbsc_real_data_*.csv"
                }
            }

    async def sync_data(self) -> bool:
        """
        Synchronize data from all configured sources

        Returns:
            bool: True if sync successful
        """
        try:
            logger.info("Starting CBSC data synchronization...")

            # Sync from each source
            success = True
            for source in self.config["data_sources"]:
                try:
                    if source == "hkex":
                        success &= await self._sync_from_hkex()
                    elif source == "file":
                        success &= await self._sync_from_file()
                    else:
                        logger.warning(f"Unknown data source: {source}")

                except Exception as e:
                    logger.error(f"Error syncing from {source}: {str(e)}")
                    success = False

            if success:
                logger.info("Data synchronization completed successfully")
            else:
                logger.error("Data synchronization completed with errors")

            return success

        except Exception as e:
            logger.error(f"Fatal error in data sync: {str(e)}")
            return False

    async def _sync_from_hkex(self) -> bool:
        """Sync data from HKEX website"""
        try:
            # TODO: Implement HKEX web scraping
            # This would require:
            # 1. HTTP client with session management
            # 2. Parsing HTML/JSON responses
            # 3. Handling anti-bot measures
            # 4. Data transformation

            logger.info("HKEX sync not implemented yet")
            return True

        except Exception as e:
            logger.error(f"Failed to sync from HKEX: {str(e)}")
            return False

    async def _sync_from_file(self) -> bool:
        """Sync data from local file"""
        try:
            # Find the latest data file
            file_pattern = self.config["file"]["path_pattern"]
            data_files = list(Path(".").glob(file_pattern))

            if not data_files:
                logger.warning(f"No data files found matching pattern: {file_pattern}")
                return False

            # Get the most recent file
            latest_file = max(data_files, key=os.path.getctime)
            logger.info(f"Found latest data file: {latest_file}")

            # Check if file has been updated since last sync
            sync_marker_path = self.data_dir / "last_sync.txt"
            last_sync_time = None

            if sync_marker_path.exists():
                with open(sync_marker_path, 'r') as f:
                    last_sync_time = datetime.fromisoformat(f.read().strip())

            file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime)

            if last_sync_time and file_mtime <= last_sync_time:
                logger.info("Data file not updated since last sync")
                return True

            # Load and validate data
            data = pd.read_csv(latest_file)
            if data.empty:
                logger.error(f"Data file is empty: {latest_file}")
                return False

            # Check for required columns
            required_columns = ['Date', 'HSIF_Close']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False

            # Create backup of existing data
            backup_path = self.data_dir / f"cbsc_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            current_data_path = self.data_dir / "cbsc_real_data_latest.csv"

            if current_data_path.exists():
                import shutil
                shutil.copy2(current_data_path, backup_path)
                logger.info(f"Created backup: {backup_path}")

            # Copy new data
            import shutil
            shutil.copy2(latest_file, current_data_path)

            # Create data summary
            summary_path = self.data_dir / f"data_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            summary = {
                "source": latest_file.name,
                "acquisition_timestamp": datetime.now().isoformat(),
                "total_records": len(data),
                "date_range": {
                    "start": data['Date'].iloc[0],
                    "end": data['Date'].iloc[-1]
                },
                "columns": list(data.columns),
                "file_size": latest_file.stat().st_size
            }

            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)

            # Update sync marker
            with open(sync_marker_path, 'w') as f:
                f.write(datetime.now().isoformat())

            logger.info(f"Successfully synced data from {latest_file.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to sync from file: {str(e)}")
            return False

    async def validate_data(self) -> Dict:
        """
        Validate the synchronized data

        Returns:
            Dict: Validation results
        """
        try:
            data_path = self.data_dir / "cbsc_real_data_latest.csv"
            if not data_path.exists():
                return {"valid": False, "error": "No data file found"}

            data = pd.read_csv(data_path)

            validation_results = {
                "valid": True,
                "checks": [],
                "statistics": {},
                "issues": []
            }

            # Check 1: Basic data integrity
            if data.empty:
                validation_results["valid"] = False
                validation_results["issues"].append("Data file is empty")
            else:
                validation_results["checks"].append("✓ Data file not empty")

            # Check 2: Required columns
            required_columns = ['Date', 'HSIF_Close', 'Bull_Price', 'Bear_Price', 'Bull_Bear_Ratio']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                validation_results["valid"] = False
                validation_results["issues"].append(f"Missing columns: {missing_columns}")
            else:
                validation_results["checks"].append("✓ All required columns present")

            # Check 3: Date column format
            try:
                pd.to_datetime(data['Date'])
                validation_results["checks"].append("✓ Date column format valid")
            except:
                validation_results["valid"] = False
                validation_results["issues"].append("Invalid date format")

            # Check 4: Numeric data validation
            numeric_columns = ['HSIF_Close', 'Bull_Price', 'Bear_Price', 'Bull_Bear_Ratio']
            for col in numeric_columns:
                if col in data.columns:
                    non_numeric = data[col].apply(lambda x: not isinstance(x, (int, float)) and pd.notna(x)).sum()
                    if non_numeric > 0:
                        validation_results["issues"].append(f"{col}: {non_numeric} non-numeric values")
                    else:
                        validation_results["checks"].append(f"✓ {col}: All numeric values")

            # Calculate statistics
            validation_results["statistics"] = {
                "total_records": len(data),
                "date_range": {
                    "start": data['Date'].iloc[0] if not data.empty else None,
                    "end": data['Date'].iloc[-1] if not data.empty else None
                },
                "data_completeness": {
                    col: (data[col].notna().sum() / len(data) * 100) for col in required_columns if col in data.columns
                }
            }

            # Save validation report
            report_path = self.data_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(validation_results, f, indent=2)

            return validation_results

        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            return {"valid": False, "error": str(e)}

    async def run_continuous_sync(self):
        """Run continuous synchronization"""
        logger.info(f"Starting continuous sync (interval: {self.config['sync_interval_minutes']} minutes)")

        while True:
            try:
                # Sync data
                await self.sync_data()

                # Validate data
                validation = await self.validate_data()
                if not validation.get("valid", False):
                    logger.error("Data validation failed")

                # Wait for next sync
                await asyncio.sleep(self.config["sync_interval_minutes"] * 60)

            except Exception as e:
                logger.error(f"Error in continuous sync: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    def schedule_sync(self):
        """Schedule the sync to run at regular intervals"""
        import schedule
        import time

        # Schedule sync
        interval = self.config["sync_interval_minutes"]
        schedule.every(interval).minutes.do(
            lambda: asyncio.run(self.sync_data())
        )

        logger.info(f"Sync scheduled every {interval} minutes")

        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="CBBC Data Synchronization")
    parser.add_argument("--config", default="config/cbbc_sync_config.json", help="Configuration file path")
    parser.add_argument("--continuous", action="store_true", help="Run continuous sync")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing data")
    args = parser.parse_args()

    # Initialize synchronizer
    synchronizer = CBBCDataSynchronizer(args.config)

    if args.validate_only:
        # Only validate existing data
        validation = await synchronizer.validate_data()
        print("\nValidation Results:")
        print(json.dumps(validation, indent=2))
        return

    if args.continuous:
        # Run continuous sync
        await synchronizer.run_continuous_sync()
    else:
        # Run single sync
        success = await synchronizer.sync_data()
        if success:
            validation = await synchronizer.validate_data()
            print("\nValidation Results:")
            print(json.dumps(validation, indent=2))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())