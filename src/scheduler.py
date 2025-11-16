#!/usr/bin/env python3
"""
X402 Pipeline Scheduler
Automatically fetches and exports data on a daily schedule.
Can be run as a cron job, systemd service, or standalone daemon.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Add parent directory to path to import x402_pipeline
sys.path.insert(0, str(Path(__file__).parent))

try:
    from x402_pipeline import DuneDataPipeline, QUERY_IDS
except ImportError:
    print("Error: Could not import x402_pipeline. Make sure it's in the same directory.")
    sys.exit(1)


def setup_logging(log_dir: str = "logs"):
    """Set up logging for scheduled runs"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def run_daily_update(
    api_key: str = None,
    db_path: str = "data/databases/x402_data.db",
    output_dir: str = "data/exports",
    export_format: str = "both",
    log_dir: str = "data/logs"
):
    """
    Run a complete daily update: fetch all queries and export for Artemis.
    
    Args:
        api_key: Dune API key (if None, reads from DUNE_API_KEY env var)
        db_path: Path to SQLite database
        output_dir: Directory for exports
        export_format: Export format ("parquet", "csv", or "both")
        log_dir: Directory for log files
    """
    logger = setup_logging(log_dir)
    
    logger.info("="*60)
    logger.info("Starting daily X402 Pipeline update")
    logger.info("="*60)
    
    start_time = time.time()
    
    try:
        # Initialize pipeline
        logger.info("Initializing pipeline...")
        pipeline = DuneDataPipeline(db_path=db_path, api_key=api_key)
        logger.info("[OK] Pipeline initialized")
        
        # Fetch all queries
        logger.info("\nFetching all queries from Dune...")
        fetch_start = time.time()
        results = pipeline.fetch_all()
        fetch_duration = time.time() - fetch_start
        
        successful = sum(1 for r in results.values() if r is not None)
        total = len(QUERY_IDS)
        
        logger.info(f"\n[OK] Fetch complete: {successful}/{total} queries fetched successfully")
        logger.info(f"  Duration: {fetch_duration:.2f} seconds")
        
        # Export for Artemis
        logger.info("\nExporting data for Artemis Analytics...")
        export_start = time.time()
        summary = pipeline.export_for_artemis(
            output_dir=output_dir,
            format=export_format
        )
        export_duration = time.time() - export_start
        
        logger.info(f"[OK] Export complete: {summary['total_rows']} rows exported")
        logger.info(f"  Duration: {export_duration:.2f} seconds")
        logger.info(f"  Files created: {len(summary['files_created'])}")
        
        # Run dbt transformations
        logger.info("\nRunning dbt transformations...")
        dbt_start = time.time()
        dbt_success = pipeline.run_dbt_transforms()
        dbt_duration = time.time() - dbt_start
        
        if dbt_success:
            logger.info(f"[OK] dbt transformations completed")
            logger.info(f"  Duration: {dbt_duration:.2f} seconds")
        else:
            logger.warning(f"[WARN] dbt transformations failed or skipped")
            logger.warning(f"  Duration: {dbt_duration:.2f} seconds")
        
        total_duration = time.time() - start_time
        
        logger.info("\n" + "="*60)
        logger.info("DAILY UPDATE SUMMARY")
        logger.info("="*60)
        logger.info(f"Queries fetched: {successful}/{total}")
        logger.info(f"Rows exported: {summary['total_rows']}")
        logger.info(f"Files created: {len(summary['files_created'])}")
        logger.info(f"Total duration: {total_duration:.2f} seconds")
        logger.info(f"Status: [OK] SUCCESS")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n[ERROR] ERROR during daily update: {e}", exc_info=True)
        logger.error("="*60)
        return False


def run_continuous_scheduler(
    api_key: str = None,
    db_path: str = "data/databases/x402_data.db",
    output_dir: str = "data/exports",
    export_format: str = "both",
    interval_hours: int = 24,
    log_dir: str = "data/logs"
):
    """
    Run as a continuous daemon, updating every N hours.
    
    Args:
        api_key: Dune API key
        db_path: Path to SQLite database
        output_dir: Directory for exports
        export_format: Export format
        interval_hours: Hours between updates (default: 24)
        log_dir: Directory for log files
    """
    logger = setup_logging(log_dir)
    
    logger.info("="*60)
    logger.info("Starting X402 Pipeline Scheduler (Continuous Mode)")
    logger.info(f"Update interval: {interval_hours} hours")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)
    
    next_update = datetime.now()
    
    try:
        while True:
            now = datetime.now()
            
            if now >= next_update:
                logger.info(f"\nScheduled update triggered at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                
                success = run_daily_update(
                    api_key=api_key,
                    db_path=db_path,
                    output_dir=output_dir,
                    export_format=export_format,
                    log_dir=log_dir
                )
                
                if success:
                    next_update = now + timedelta(hours=interval_hours)
                    logger.info(f"\nNext update scheduled for: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    # Retry in 1 hour if update failed
                    next_update = now + timedelta(hours=1)
                    logger.warning(f"\nUpdate failed. Retrying in 1 hour at: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")
                
                logger.info(f"\nSleeping until next update...")
            
            # Sleep for 1 minute, then check again
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\n\nScheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n[ERROR] Fatal error in scheduler: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="X402 Pipeline Scheduler - Automated daily updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once (for cron jobs)
  python scheduler.py run-once
  
  # Run as continuous daemon (updates every 24 hours)
  python scheduler.py daemon
  
  # Run as daemon with custom interval (updates every 12 hours)
  python scheduler.py daemon --interval 12
  
  # Run once with custom settings
  python scheduler.py run-once --output-dir ./custom_output --format parquet
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["run-once", "daemon"],
        help="Scheduler mode: 'run-once' for single execution, 'daemon' for continuous"
    )
    
    parser.add_argument(
        "--api-key",
        help="Dune API key (overrides DUNE_API_KEY env var)"
    )
    
    parser.add_argument(
        "--db",
        default="data/databases/x402_data.db",
        help="Path to SQLite database (default: data/databases/x402_data.db)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="data/exports",
        help="Output directory for exports (default: data/exports)"
    )
    
    parser.add_argument(
        "--format",
        choices=["parquet", "csv", "both"],
        default="both",
        help="Export format (default: both)"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="Update interval in hours for daemon mode (default: 24)"
    )
    
    parser.add_argument(
        "--log-dir",
        default="data/logs",
        help="Directory for log files (default: data/logs)"
    )
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.getenv("DUNE_API_KEY")
    
    if not api_key:
        print("Error: Dune API key required. Set DUNE_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    if args.mode == "run-once":
        success = run_daily_update(
            api_key=api_key,
            db_path=args.db,
            output_dir=args.output_dir,
            export_format=args.format,
            log_dir=args.log_dir
        )
        sys.exit(0 if success else 1)
    
    elif args.mode == "daemon":
        run_continuous_scheduler(
            api_key=api_key,
            db_path=args.db,
            output_dir=args.output_dir,
            export_format=args.format,
            interval_hours=args.interval,
            log_dir=args.log_dir
        )


if __name__ == "__main__":
    main()

