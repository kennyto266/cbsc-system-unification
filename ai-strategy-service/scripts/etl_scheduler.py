#!/usr/bin/env python3
"""
ETL Scheduler - Automated data synchronization scheduler

This script runs the ETL sync pipeline on a scheduled basis using APScheduler.
"""

import os
import sys
import signal
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Import ETL sync module
try:
    from etl_sync import ETLSync
    from etl_config import SYNC_INTERVAL_SECONDS
except ImportError:
    print("❌ Failed to import ETL modules")
    print("Ensure you're running this script from the scripts/ directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None
etl_instance = None


def etl_job():
    """ETL sync job to be scheduled"""
    logger.info("="*60)
    logger.info("Running scheduled ETL sync job")
    logger.info("="*60)

    try:
        etl = ETLSync()
        success = etl.run_sync()

        if success:
            logger.info("✅ Scheduled ETL job completed successfully")
        else:
            logger.warning("⚠️  Scheduled ETL job completed with errors")

        return success
    except Exception as e:
        logger.error(f"❌ ETL job failed: {e}")
        return False


def job_executed_listener(event):
    """Listener for successful job execution"""
    logger.info(f"Job {event.job_id} executed successfully at {event.scheduled_run_time}")


def job_error_listener(event):
    """Listener for job execution errors"""
    logger.error(f"Job {event.job_id} failed at {event.scheduled_run_time}")
    logger.exception(event.exception)


def setup_scheduler():
    """Setup and configure the scheduler"""
    global scheduler

    scheduler = BlockingScheduler({
        'apscheduler.job_defaults.coalesce': 'true',
        'apscheduler.job_defaults.max_instances': '1',
        'apscheduler.timezone': 'UTC'
    })

    # Add ETL sync job
    scheduler.add_job(
        etl_job,
        trigger=IntervalTrigger(seconds=SYNC_INTERVAL_SECONDS),
        id='etl_sync_job',
        name='ETL Sync from PostgreSQL to ClickHouse',
        replace_existing=True
    )

    # Add event listeners
    scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
    scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)

    logger.info(f"✅ Scheduler configured with {SYNC_INTERVAL_SECONDS}s interval")
    logger.info(f"Next run: {scheduler.get_job('etl_sync_job').next_run_time}")

    return scheduler


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"\nReceived signal {signum}, shutting down gracefully...")

    if scheduler:
        scheduler.shutdown(wait=False)

    logger.info("👋 Scheduler stopped")
    sys.exit(0)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='ETL Scheduler - Automated PostgreSQL to ClickHouse sync'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run ETL job once and exit (for testing)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='Override sync interval in seconds'
    )
    args = parser.parse_args()

    print("="*60)
    print("ETL Scheduler")
    print("="*60)

    # Override interval if specified
    if args.interval:
        global SYNC_INTERVAL_SECONDS
        SYNC_INTERVAL_SECONDS = args.interval
        logger.info(f"Using custom interval: {SYNC_INTERVAL_SECONDS}s")

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.test:
        # Run once and exit
        logger.info("Running ETL job in test mode (once)")
        success = etl_job()
        sys.exit(0 if success else 1)

    # Setup and start scheduler
    scheduler = setup_scheduler()

    try:
        logger.info("\n" + "="*60)
        logger.info("Starting ETL Scheduler (Press Ctrl+C to stop)")
        logger.info("="*60 + "\n")

        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        # Graceful shutdown
        scheduler.shutdown(wait=False)
        logger.info("\n👋 Scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
        scheduler.shutdown(wait=False)
        sys.exit(1)


if __name__ == '__main__':
    main()
