#!/usr/bin/env python3
"""
Run gerrymandering experiments with different objectives.

Usage:
    python run_experiment.py --goal neutral
    python run_experiment.py --goal maximize_left --strength extreme
    python run_experiment.py --goal maximize_right --strength moderate
"""
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
import pickle

from src.data_loader import load_and_prepare_data
from src.gerrymander import GerrymanderOptimizer
from src.visualizer_improved import create_animation_improved, plot_final_comparison_improved


def setup_logging(log_dir: Path, experiment_name: str):
    """Setup logging to file and console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{experiment_name}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def get_objective_weights(goal: str, strength: str = "moderate") -> dict:
    """
    Get objective function weights for different goals.

    Args:
        goal: One of 'neutral', 'maximize_left', 'maximize_right'
        strength: One of 'mild', 'moderate', 'extreme'

    Returns:
        Dictionary of weights
    """
    strength_multipliers = {
        'mild': 1.0,
        'moderate': 5.0,
        'extreme': 50.0
    }

    multiplier = strength_multipliers.get(strength, 1.0)

    if goal == 'neutral':
        return {
            'population_balance': 1.0,
            'seat_deviation': 1.0,
            'partisan_advantage': 0.0
        }
    elif goal == 'maximize_left':
        return {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': multiplier
        }
    elif goal == 'maximize_right':
        return {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': multiplier
        }
    else:
        raise ValueError(f"Unknown goal: {goal}")


def main():
    parser = argparse.ArgumentParser(
        description='Run gerrymandering experiment'
    )
    parser.add_argument(
        '--goal',
        type=str,
        required=True,
        choices=['neutral', 'maximize_left', 'maximize_right'],
        help='Optimization goal'
    )
    parser.add_argument(
        '--strength',
        type=str,
        default='moderate',
        choices=['mild', 'moderate', 'extreme'],
        help='How strongly to pursue partisan goal'
    )
    parser.add_argument(
        '--n_districts',
        type=int,
        default=11,
        help='Number of districts to create'
    )
    parser.add_argument(
        '--steps',
        type=int,
        default=1000,
        help='Number of optimization steps'
    )
    parser.add_argument(
        '--initial_temp',
        type=float,
        default=1000.0,
        help='Initial temperature for simulated annealing'
    )
    parser.add_argument(
        '--cooling_rate',
        type=float,
        default=0.99,
        help='Cooling rate'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--data_dir',
        type=str,
        default='.',
        help='Directory containing data files'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='results',
        help='Directory for output files'
    )
    parser.add_argument(
        '--create_gif',
        action='store_true',
        help='Create animated GIF of optimization'
    )

    args = parser.parse_args()

    # Create experiment name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    experiment_name = f"{args.goal}_{args.strength}_{args.n_districts}d_{args.steps}s_{timestamp}"
    if args.seed is not None:
        experiment_name += f"_seed{args.seed}"

    # Setup directories
    output_dir = Path(args.output_dir)
    log_dir = output_dir / 'logs'
    gif_dir = output_dir / 'gifs'
    data_dir = output_dir / 'data'

    for d in [log_dir, gif_dir, data_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Setup logging
    setup_logging(log_dir, experiment_name)

    logging.info("="*80)
    logging.info(f"Starting experiment: {experiment_name}")
    logging.info(f"Goal: {args.goal} (strength: {args.strength})")
    logging.info(f"Districts: {args.n_districts}")
    logging.info(f"Steps: {args.steps}")
    logging.info(f"Initial temp: {args.initial_temp}")
    logging.info(f"Cooling rate: {args.cooling_rate}")
    logging.info(f"Random seed: {args.seed}")
    logging.info("="*80)

    # Load data
    logging.info("Loading data...")
    gdf = load_and_prepare_data(region='emilia', data_dir=args.data_dir)
    logging.info(f"Loaded {len(gdf)} communes")

    # Get objective weights
    weights = get_objective_weights(args.goal, args.strength)
    logging.info(f"Objective weights: {weights}")

    # Determine target party
    target_party = None
    if args.goal == 'maximize_left':
        target_party = 'coalition_left'
    elif args.goal == 'maximize_right':
        target_party = 'coalition_right'

    # Create optimizer
    optimizer = GerrymanderOptimizer(
        gdf=gdf,
        n_districts=args.n_districts,
        target_party=target_party,
        objective_weights=weights,
        random_seed=args.seed
    )

    # Run optimization
    logging.info("Starting optimization...")
    best_districts, history = optimizer.optimize(
        initial_temp=args.initial_temp,
        final_temp=0.01,
        cooling_rate=args.cooling_rate,
        steps=args.steps,
        save_frequency=max(1, args.steps // 100)
    )

    # Save results
    results = {
        'experiment_name': experiment_name,
        'goal': args.goal,
        'strength': args.strength,
        'weights': weights,
        'n_districts': args.n_districts,
        'steps': args.steps,
        'initial_temp': args.initial_temp,
        'cooling_rate': args.cooling_rate,
        'seed': args.seed,
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
            'config': vars(args)
        }, f)
    logging.info(f"Full results saved to {pickle_file}")

    # Create visualizations
    logging.info("Creating visualizations...")

    # Define party colors
    party_colors = {
        'coalition_left': '#E74C3C',      # Red
        'coalition_right': '#3498DB',     # Blue
        'coalition_center': '#F39C12'     # Orange
    }
    party_cols = ['coalition_left', 'coalition_right', 'coalition_center']

    # Comparison plot
    comparison_file = output_dir / f"{experiment_name}_comparison.png"
    initial_districts = history[0]['districts']
    plot_final_comparison_improved(
        gdf=gdf,
        initial_districts=initial_districts,
        final_districts=best_districts,
        party_cols=party_cols,
        party_colors=party_colors,
        output_path=str(comparison_file),
        n_districts=args.n_districts
    )

    # Animated GIF
    if args.create_gif:
        gif_file = gif_dir / f"{experiment_name}.gif"
        create_animation_improved(
            gdf=gdf,
            history=history,
            output_path=str(gif_file),
            party_cols=party_cols,
            party_colors=party_colors,
            fps=3,
            dpi=80
        )

    logging.info("="*80)
    logging.info("Experiment complete!")
    logging.info(f"Results: {results_file}")
    logging.info(f"Comparison: {comparison_file}")
    if args.create_gif:
        logging.info(f"Animation: {gif_file}")
    logging.info("="*80)


if __name__ == '__main__':
    main()
