#!/usr/bin/env python3
"""
Refactored Production System Runner
重構後生產系統運行器

Production-ready runner for the refactored technical analysis system.
"""

import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
sys.path.append('.')

from refactored_tech_analysis import (
    OptimizationOrchestrator,
    OptimizationConfig
)
from production_config import (
    get_production_config,
    ProductionDataValidator,
    ProductionErrorHandler
)


class ProductionSystemRunner:
    """Production system runner with monitoring and error handling"""

    def __init__(self):
        self.config = get_production_config()
        self.setup_logging()
        self.validator = ProductionDataValidator()
        self.error_handler = ProductionErrorHandler()

    def setup_logging(self):
        """Setup production logging"""
        log_dir = Path(self.config["monitoring"]["log_file"]).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, self.config["monitoring"]["log_level"]),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config["monitoring"]["log_file"]),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_optimization_config(self) -> OptimizationConfig:
        """Create optimization configuration from production settings"""
        return OptimizationConfig(
            max_workers=self.config["optimization"]["max_workers"],
            max_combinations=self.config["optimization"]["max_combinations"],
            target_strategies=self.config["optimization"]["target_strategies"],
            target_data_sources=self.config["optimization"]["target_data_sources"]
        )

    def run_production_optimization(self, max_combinations=None):
        """Run production optimization with monitoring"""
        self.logger.info("Starting production optimization run")
        start_time = time.time()

        try:
            # Create orchestrator with production configuration
            config = self.create_optimization_config()
            orchestrator = OptimizationOrchestrator(config)

            # Run optimization
            self.logger.info(f"Running optimization with max_combinations={max_combinations}")
            results = orchestrator.run_complete_optimization(max_combinations=max_combinations)

            # Validate results
            validated_results = self.validate_and_filter_results(results)

            # Save results
            output_file = self.save_results(validated_results)

            execution_time = time.time() - start_time
            self.log_summary(validated_results, execution_time, output_file)

            return validated_results

        except Exception as e:
            self.logger.error(f"Production optimization failed: {e}")
            self.error_handler.handle_data_error(e, "production_optimization")
            raise

    def validate_and_filter_results(self, results):
        """Validate and filter results according to production standards"""
        self.logger.info(f"Validating {len(results)} results")

        validated_results = []
        failed_validation = 0

        for result in results:
            try:
                # Validate strategy result structure
                if not self.validator.validate_strategy_results(result.__dict__):
                    self.logger.warning(f"Invalid result structure: {result.strategy_id}")
                    failed_validation += 1
                    continue

                # Validate Sharpe ratio
                if not self.validator.validate_sharpe_ratio(result.sharpe_ratio):
                    self.logger.warning(f"Suspicious Sharpe ratio: {result.strategy_id} - {result.sharpe_ratio:.3f}")
                    # Still include but flag for review

                # Validate data quality if available
                if hasattr(result, 'data_points'):
                    if not self.validator.validate_data_quality(result.data_points):
                        self.logger.warning(f"Insufficient data points: {result.strategy_id}")
                        failed_validation += 1
                        continue

                validated_results.append(result)

            except Exception as e:
                self.logger.error(f"Error validating result {getattr(result, 'strategy_id', 'unknown')}: {e}")
                failed_validation += 1

        self.logger.info(f"Validation complete: {len(validated_results)} passed, {failed_validation} failed")
        return validated_results

    def save_results(self, results):
        """Save results to production directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.config["results"]["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"production_optimization_results_{timestamp}.json"

        # Convert results to serializable format
        results_data = []
        for result in results:
            result_dict = {
                'strategy_id': result.strategy_id,
                'total_return': result.total_return,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'quality_score': result.quality_score,
                'success': result.success,
                'timestamp': timestamp
            }
            results_data.append(result_dict)

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Results saved to: {output_file}")

        # Backup if enabled
        if self.config["results"]["backup_enabled"]:
            self.backup_results(results_data, timestamp)

        return output_file

    def backup_results(self, results_data, timestamp):
        """Create backup of results"""
        backup_dir = Path(self.config["results"]["backup_dir"])
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_file = backup_dir / f"backup_optimization_results_{timestamp}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Backup created: {backup_file}")

    def log_summary(self, results, execution_time, output_file):
        """Log execution summary"""
        successful_results = [r for r in results if r.success]

        if successful_results:
            best_strategy = max(successful_results, key=lambda x: x.sharpe_ratio)
            best_sharpe = best_strategy.sharpe_ratio
            best_return = best_strategy.total_return
            best_quality = best_strategy.quality_score
        else:
            best_sharpe = best_return = best_quality = 0

        self.logger.info("=" * 60)
        self.logger.info("PRODUCTION OPTIMIZATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Execution Time: {execution_time:.2f} seconds")
        self.logger.info(f"Total Results: {len(results)}")
        self.logger.info(f"Successful: {len(successful_results)}")
        self.logger.info(f"Success Rate: {len(successful_results)/len(results)*100:.1f}%")
        self.logger.info(f"Best Strategy: {best_strategy.strategy_id if successful_results else 'None'}")
        self.logger.info(f"Best Sharpe Ratio: {best_sharpe:.3f}")
        self.logger.info(f"Best Total Return: {best_return:.2%}")
        self.logger.info(f"Best Quality Score: {best_quality:.1f}")
        self.logger.info(f"Results File: {output_file}")

        # Quality assessment
        if best_sharpe > 0.5 and best_sharpe < 3.0:
            self.logger.info("[OK] Sharpe ratios are in expected range")
        else:
            self.logger.warning("[WARNING] Best Sharpe ratio outside expected range")

        self.logger.info("=" * 60)


def main():
    """Main production runner"""
    print("REFACTORED PRODUCTION SYSTEM RUNNER")
    print("=" * 50)

    try:
        # Create production runner
        runner = ProductionSystemRunner()

        # Check for command line arguments
        max_combinations = None
        if len(sys.argv) > 1:
            try:
                max_combinations = int(sys.argv[1])
                print(f"Using max_combinations: {max_combinations}")
            except ValueError:
                print("Invalid max_combinations argument, using default")
                max_combinations = None

        # Run production optimization
        print("Starting production optimization...")
        results = runner.run_production_optimization(max_combinations=max_combinations)

        print(f"\nProduction optimization completed successfully!")
        print(f"Processed {len(results)} strategies")
        return True

    except Exception as e:
        print(f"Production runner failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)