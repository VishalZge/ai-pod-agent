"""
Main Entry Point - Run the AI POD Agent System
"""

import argparse
import logging
from datetime import datetime
from orchestrator import Orchestrator
from utils.logger import app_logger
from utils.config import Config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI POD Agent System - Automated Design Generation & Upload",
    )

    parser.add_argument("--run-now", action="store_true", help="Run workflow immediately")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=24, help="Interval in hours")
    parser.add_argument("--test", action="store_true", help="Enable test mode")
    parser.add_argument("--dry-run", action="store_true", help="Dry run - no uploads")
    parser.add_argument("--config-check", action="store_true", help="Check configuration")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("🚀 AI POD Agent System - Aggressive Auto-Optimization Mode")
    print("=" * 80)
    print(f"Started at: {datetime.utcnow().isoformat()}\n")

    if args.config_check:
        is_valid, error = Config.validate()
        if is_valid:
            print("✓ Configuration is valid!\n")
        else:
            print(f"✗ Configuration invalid: {error}")
            return

    if args.dry_run:
        Config.POD_UPLOAD_ENABLED = False
        print("⊘ DRY RUN MODE\n")

    if args.test:
        Config.BATCH_SIZE = 2
        print("🧪 TEST MODE\n")

    try:
        orchestrator = Orchestrator()
        
        if args.run_now:
            results = orchestrator.run_daily_workflow()
            print_results(results)
        elif args.continuous:
            print(f"🔄 Running every {args.interval} hours...\n")
            orchestrator.run_continuous(interval_hours=args.interval)
        else:
            parser.print_help()

    except Exception as e:
        app_logger.error(f"Error: {str(e)}", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
        return 1

    print("\n" + "=" * 80)
    print("✓ Done!")
    print("=" * 80 + "\n")
    return 0


def print_results(results: dict):
    """Print workflow results."""
    print("\n📊 WORKFLOW RESULTS:")
    print("-" * 80)
    
    status = results.get("status", "unknown")
    print(f"Status: {status.upper()}")
    
    stages = results.get("stages", {})
    for stage_name, stage_data in stages.items():
        print(f"  ✓ {stage_name.upper()}")
    
    total_time = results.get("total_time_seconds", 0)
    print(f"\n⏱️  Total time: {total_time:.1f} seconds\n")


if __name__ == "__main__":
    exit(main())
