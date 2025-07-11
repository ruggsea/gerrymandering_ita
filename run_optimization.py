#!/usr/bin/env python3
"""
Script to run Italian gerrymandering optimization experiments.

This script replicates the experiments found in the logs with the exact parameters used.
"""

import os
import sys
import logging
from datetime import datetime
from gerrymandering_optimizer import (
    OptimizationConfig, 
    run_optimization_experiment,
    ItalianVotingData,
    GerrymanderingOptimizer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/optimization_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_emilia_romagna_experiment():
    """Run the Emilia-Romagna experiment with parameters from the logs."""
    
    # Parameters from the log files: emilia_11_9_1000_0.01_0.99_1_1_1000_*
    # Format: region_num_districts_initial_temp_cooling_rate_pop_weight_compact_weight_partisan_weight_max_steps_seed
    config = OptimizationConfig(
        num_districts=11,
        initial_temperature=1000.0,
        cooling_rate=0.99,
        min_temperature=0.01,
        max_steps=1000,
        population_weight=1.0,
        compactness_weight=1.0,
        partisan_fairness_weight=1.0
    )
    
    logger.info("Starting Emilia-Romagna gerrymandering optimization experiment")
    logger.info(f"Configuration: {config}")
    
    # Check if data files exist
    required_files = [
        "politiche_2022_raw_votes.csv",
        "gerrymandering_base.geojson"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"Required file not found: {file_path}")
            return None
    
    # Optional population file
    population_file = "POSAS_2024_it_Comuni.csv" if os.path.exists("POSAS_2024_it_Comuni.csv") else None
    
    try:
        # Run optimization
        optimizer = run_optimization_experiment(
            votes_file="politiche_2022_raw_votes.csv",
            geo_file="gerrymandering_base.geojson",
            population_file=population_file,
            config=config,
            output_dir="emilia_romagna_results"
        )
        
        logger.info(f"Optimization completed successfully!")
        logger.info(f"Best score achieved: {optimizer.best_score}")
        
        # Print final statistics
        if optimizer.best_map:
            populations = [stats['population'] for stats in optimizer.best_map.district_stats.values()]
            logger.info(f"Final district populations: {populations}")
            logger.info(f"Population standard deviation: {optimizer.history['population_stds'][-1] if optimizer.history['population_stds'] else 'N/A'}")
            logger.info(f"Final seat deviation: {optimizer.history['seat_deviations'][-1] if optimizer.history['seat_deviations'] else 'N/A'}")
        
        return optimizer
        
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        return None


def run_multiple_experiments(num_runs: int = 5):
    """Run multiple optimization experiments with different random seeds."""
    
    logger.info(f"Running {num_runs} optimization experiments")
    
    results = []
    
    for run in range(num_runs):
        logger.info(f"Starting experiment run {run + 1}/{num_runs}")
        
        # Set random seed for reproducibility
        import random
        import numpy as np
        seed = random.randint(100000, 999999)
        random.seed(seed)
        np.random.seed(seed)
        
        config = OptimizationConfig(
            num_districts=11,
            initial_temperature=1000.0,
            cooling_rate=0.99,
            min_temperature=0.01,
            max_steps=1000,
            population_weight=1.0,
            compactness_weight=1.0,
            partisan_fairness_weight=1.0
        )
        
        try:
            optimizer = run_optimization_experiment(
                votes_file="politiche_2022_raw_votes.csv",
                geo_file="gerrymandering_base.geojson",
                population_file="POSAS_2024_it_Comuni.csv" if os.path.exists("POSAS_2024_it_Comuni.csv") else None,
                config=config,
                output_dir=f"experiment_run_{run + 1}_seed_{seed}"
            )
            
            results.append({
                'run': run + 1,
                'seed': seed,
                'best_score': optimizer.best_score,
                'final_population_std': optimizer.history['population_stds'][-1] if optimizer.history['population_stds'] else None,
                'final_seat_deviation': optimizer.history['seat_deviations'][-1] if optimizer.history['seat_deviations'] else None
            })
            
            logger.info(f"Run {run + 1} completed with score: {optimizer.best_score}")
            
        except Exception as e:
            logger.error(f"Run {run + 1} failed: {str(e)}")
            results.append({
                'run': run + 1,
                'seed': seed,
                'best_score': None,
                'final_population_std': None,
                'final_seat_deviation': None,
                'error': str(e)
            })
    
    # Print summary
    logger.info("Experiment Summary:")
    successful_runs = [r for r in results if r['best_score'] is not None]
    if successful_runs:
        scores = [r['best_score'] for r in successful_runs]
        logger.info(f"Successful runs: {len(successful_runs)}/{num_runs}")
        logger.info(f"Best score: {min(scores)}")
        logger.info(f"Worst score: {max(scores)}")
        logger.info(f"Average score: {sum(scores) / len(scores)}")
    else:
        logger.info("No successful runs")
    
    return results


def analyze_existing_results():
    """Analyze existing results from the logs directory."""
    
    logger.info("Analyzing existing experiment results")
    
    if not os.path.exists("logs"):
        logger.warning("No logs directory found")
        return
    
    log_files = [f for f in os.listdir("logs") if f.endswith('.log')]
    
    if not log_files:
        logger.warning("No log files found in logs directory")
        return
    
    logger.info(f"Found {len(log_files)} log files")
    
    for log_file in log_files:
        logger.info(f"Analyzing log file: {log_file}")
        
        # Parse filename to extract parameters
        # Format: emilia_11_9_1000_0.01_0.99_1_1_1000_536189.log
        parts = log_file.replace('.log', '').split('_')
        
        if len(parts) >= 9:
            try:
                region = parts[0]
                num_districts = int(parts[1])
                initial_temp = float(parts[3])
                cooling_rate = float(parts[4])
                max_steps = int(parts[8])
                seed = int(parts[9]) if len(parts) > 9 else None
                
                logger.info(f"  Region: {region}")
                logger.info(f"  Districts: {num_districts}")
                logger.info(f"  Initial temperature: {initial_temp}")
                logger.info(f"  Cooling rate: {cooling_rate}")
                logger.info(f"  Max steps: {max_steps}")
                logger.info(f"  Seed: {seed}")
                
            except (ValueError, IndexError):
                logger.warning(f"  Could not parse parameters from filename: {log_file}")
        
        # Read log file to extract final results
        try:
            with open(os.path.join("logs", log_file), 'r') as f:
                lines = f.readlines()
                
                # Find final score
                final_score = None
                for line in reversed(lines):
                    if "current score:" in line:
                        try:
                            final_score = float(line.split("current score:")[1].strip())
                            break
                        except (ValueError, IndexError):
                            continue
                
                if final_score is not None:
                    logger.info(f"  Final score: {final_score}")
                
        except Exception as e:
            logger.error(f"  Error reading log file: {str(e)}")


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Analyze existing results first
    analyze_existing_results()
    
    # Run single experiment
    logger.info("=" * 50)
    logger.info("Running single optimization experiment")
    logger.info("=" * 50)
    
    result = run_emilia_romagna_experiment()
    
    if result:
        logger.info("Single experiment completed successfully!")
        
        # Ask if user wants to run multiple experiments
        try:
            response = input("\nDo you want to run multiple experiments? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                num_runs = int(input("How many experiments? (default 5): ") or "5")
                logger.info("=" * 50)
                logger.info(f"Running {num_runs} optimization experiments")
                logger.info("=" * 50)
                run_multiple_experiments(num_runs)
        except (ValueError, KeyboardInterrupt):
            logger.info("Multiple experiments skipped")
    else:
        logger.error("Single experiment failed!")