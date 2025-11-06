#!/usr/bin/env python3
"""
Simple batch experiment runner: 4 experiments only.
- 2 algorithms × 2 objectives = 4 experiments
- Only LEFT vs RIGHT (no center)
"""
import logging
import json
import pickle
import importlib
from pathlib import Path
from datetime import datetime

from src.data_loader import load_and_prepare_data
from src.visualizer_simple import create_animation_simple, plot_final_comparison_simple
from experiments.simple_experiments import (
    ALGORITHMS, OBJECTIVES, SIMPLE_EXPERIMENTS
)


def setup_logging(log_dir: Path, experiment_name: str):
    """Setup logging to file and console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{experiment_name}.log"

    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ],
        force=True
    )


def run_single_experiment(
    experiment_config: dict,
    gdf,
    output_dir: Path,
    n_districts: int = 11
):
    """Run a single experiment."""

    name = experiment_config['name']
    algorithm_name = experiment_config['algorithm']
    objective_name = experiment_config['objective']
    steps = experiment_config['steps']
    seed = experiment_config.get('seed', None)
    create_gif = experiment_config.get('create_gif', False)

    # Get algorithm and objective config
    algo_config = ALGORITHMS[algorithm_name]
    obj_config = OBJECTIVES[objective_name]

    # Create experiment name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    experiment_name = f"{name}_{timestamp}_seed{seed}"

    # Setup directories
    log_dir = output_dir / 'logs'
    gif_dir = output_dir / 'gifs'
    data_dir = output_dir / 'data'

    for d in [log_dir, gif_dir, data_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Setup logging
    setup_logging(log_dir, experiment_name)

    logging.info("="*80)
    logging.info(f"Experiment: {name}")
    logging.info(f"Algorithm: {algorithm_name}")
    logging.info(f"Objective: {objective_name} - {obj_config['description']}")
    logging.info(f"Steps: {steps}")
    logging.info(f"Random seed: {seed}")
    logging.info("="*80)

    # Import and instantiate algorithm
    module = importlib.import_module(algo_config['module'])
    OptimizerClass = getattr(module, algo_config['class'])

    # Create optimizer
    optimizer = OptimizerClass(
        gdf=gdf,
        n_districts=n_districts,
        target_party=obj_config['target_party'],
        objective_weights=obj_config['weights'],
        random_seed=seed,
        **algo_config.get('init_params', {})
    )

    # Run optimization
    logging.info("Starting optimization...")
    try:
        optimize_params = algo_config.get('optimize_params', {})
        best_districts, history = optimizer.optimize(
            steps=steps,
            save_frequency=max(1, steps // 100),
            **optimize_params
        )
    except Exception as e:
        logging.error(f"Optimization failed: {e}")
        raise

    # Save results
    results = {
        'experiment_name': experiment_name,
        'name': name,
        'algorithm': algorithm_name,
        'objective': objective_name,
        'objective_description': obj_config['description'],
        'n_districts': n_districts,
        'steps': steps,
        'seed': seed,
        'target_party': obj_config['target_party'],
        'weights': obj_config['weights'],
        'best_districts': best_districts.tolist(),
        'history': [
            {k: v.tolist() if hasattr(v, 'tolist') else v
             for k, v in h.items() if k != 'districts'}
            for h in history
        ]
    }

    results_file = data_dir / f"{experiment_name}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Results saved to {results_file}")

    # Save pickle with full history
    pickle_file = data_dir / f"{experiment_name}.pkl"
    with open(pickle_file, 'wb') as f:
        pickle.dump({
            'gdf': gdf,
            'history': history,
            'best_districts': best_districts,
            'config': experiment_config,
            'algorithm': algorithm_name,
            'objective': objective_name
        }, f)
    logging.info(f"Full results saved to {pickle_file}")

    # Create visualizations
    logging.info("Creating visualizations...")

    # Comparison plot (LEFT vs RIGHT only)
    comparison_file = output_dir / f"{experiment_name}_comparison.png"
    initial_districts = history[0]['districts']
    plot_final_comparison_simple(
        gdf=gdf,
        initial_districts=initial_districts,
        final_districts=best_districts,
        output_path=str(comparison_file),
        n_districts=n_districts
    )

    # Animated GIF (LEFT vs RIGHT only)
    if create_gif and len(history) > 1:
        gif_file = gif_dir / f"{experiment_name}.gif"
        try:
            create_animation_simple(
                gdf=gdf,
                history=history,
                output_path=str(gif_file),
                fps=3,
                dpi=80
            )
        except Exception as e:
            logging.warning(f"GIF creation failed: {e}")

    logging.info("="*80)
    logging.info("Experiment complete!")
    logging.info(f"Results: {results_file}")
    logging.info(f"Comparison: {comparison_file}")
    if create_gif:
        logging.info(f"Animation: {gif_file}")
    logging.info("="*80)

    return results


def main():
    # Load data once
    print("="*80)
    print("SIMPLE GERRYMANDERING EXPERIMENTS")
    print("4 experiments: 2 algorithms × 2 objectives (LEFT vs RIGHT only)")
    print("="*80)
    print("\nLoading Emilia-Romagna data...")
    gdf = load_and_prepare_data(region='emilia', data_dir='.')
    print(f"Loaded {len(gdf)} communes\n")

    output_dir = Path('results')
    results_summary = []

    for i, exp_config in enumerate(SIMPLE_EXPERIMENTS, 1):
        print(f"\n[{i}/{len(SIMPLE_EXPERIMENTS)}] Starting experiment: {exp_config['name']}")
        print("-"*80)

        try:
            result = run_single_experiment(
                experiment_config=exp_config,
                gdf=gdf,
                output_dir=output_dir,
                n_districts=11
            )
            results_summary.append({
                'name': exp_config['name'],
                'status': 'success',
                'result_file': result.get('experiment_name')
            })
        except Exception as e:
            print(f"ERROR: Experiment {exp_config['name']} failed: {e}")
            import traceback
            traceback.print_exc()
            results_summary.append({
                'name': exp_config['name'],
                'status': 'failed',
                'error': str(e)
            })
            continue

    # Save summary
    print("\n" + "="*80)
    print("ALL EXPERIMENTS COMPLETE")
    print("="*80)

    summary_file = output_dir / 'experiments_summary.json'
    with open(summary_file, 'w') as f:
        json.dump({
            'total_experiments': len(SIMPLE_EXPERIMENTS),
            'successful': sum(1 for r in results_summary if r['status'] == 'success'),
            'failed': sum(1 for r in results_summary if r['status'] == 'failed'),
            'experiments': results_summary
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")
    print(f"Successful: {sum(1 for r in results_summary if r['status'] == 'success')}/{len(SIMPLE_EXPERIMENTS)}")
    print(f"Failed: {sum(1 for r in results_summary if r['status'] == 'failed')}/{len(SIMPLE_EXPERIMENTS)}")


if __name__ == '__main__':
    main()
