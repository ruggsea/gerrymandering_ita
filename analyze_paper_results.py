#!/usr/bin/env python3
"""
Comprehensive analysis script for paper results.
Generates tables, figures, and statistics for publication.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
import json
from typing import Dict, List
from src.visualizer import calculate_seat_distribution

sns.set_style("whitegrid")
sns.set_palette("colorblind")


def load_all_results(results_dir: Path) -> pd.DataFrame:
    """Load and consolidate all experiment results."""
    data = []

    for pkl_file in sorted((results_dir / "data").glob("*.pkl")):
        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            gdf = result['gdf']
            best_districts = result['best_districts']
            config = result['config']
            algorithm = result.get('algorithm', 'unknown')
            objective = result.get('objective', 'unknown')

            # Calculate seat distribution
            party_cols = ['coalition_left', 'coalition_right', 'coalition_center']
            n_districts = len(np.unique(best_districts))
            seats = calculate_seat_distribution(gdf, best_districts, n_districts, party_cols)

            # Calculate proportional baseline
            total_votes = sum(gdf[p].sum() for p in party_cols)
            prop = {}
            for party in party_cols:
                prop[party] = (gdf[party].sum() / total_votes) * n_districts

            # Calculate population statistics
            district_pops = []
            for d in range(n_districts):
                mask = best_districts == d
                pop = gdf.iloc[np.where(mask)[0]]['population'].sum()
                district_pops.append(pop)

            pop_std = np.std(district_pops)
            pop_mean = np.mean(district_pops)
            pop_cv = pop_std / pop_mean

            # Get convergence info
            history = result.get('history', [])
            if history:
                initial_score = history[0]['score']
                final_score = history[-1]['score']
                improvement = ((initial_score - final_score) / initial_score) * 100
                steps_to_95 = None
                target = initial_score - 0.95 * (initial_score - final_score)
                for h in history:
                    if h['score'] <= target:
                        steps_to_95 = h['step']
                        break
            else:
                initial_score = final_score = improvement = steps_to_95 = None

            data.append({
                'experiment': pkl_file.stem,
                'name': config.get('name', 'unknown'),
                'algorithm': algorithm,
                'objective': objective,
                'steps': config.get('steps', 0),
                'seed': config.get('seed', None),
                'left_seats': seats['coalition_left'],
                'right_seats': seats['coalition_right'],
                'center_seats': seats['coalition_center'],
                'left_prop': prop['coalition_left'],
                'right_prop': prop['coalition_right'],
                'center_prop': prop['coalition_center'],
                'left_advantage': seats['coalition_left'] - prop['coalition_left'],
                'right_advantage': seats['coalition_right'] - prop['coalition_right'],
                'center_advantage': seats['coalition_center'] - prop['coalition_center'],
                'pop_std': pop_std,
                'pop_mean': pop_mean,
                'pop_cv': pop_cv,
                'initial_score': initial_score,
                'final_score': final_score,
                'improvement_pct': improvement,
                'steps_to_95': steps_to_95
            })
        except Exception as e:
            print(f"Warning: Could not load {pkl_file.name}: {e}")

    return pd.DataFrame(data)


def create_algorithm_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create table comparing algorithm performance."""
    # Filter for neutral objective
    neutral = df[df['objective'].str.contains('neutral', case=False, na=False)]

    if neutral.empty:
        return pd.DataFrame()

    summary = neutral.groupby('algorithm').agg({
        'final_score': ['mean', 'std'],
        'improvement_pct': 'mean',
        'steps_to_95': 'mean',
        'pop_cv': 'mean',
        'left_advantage': 'mean',
        'right_advantage': 'mean'
    }).round(2)

    return summary


def create_objective_comparison_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create table comparing objectives."""
    # Filter for simulated annealing
    sa = df[df['algorithm'] == 'simulated_annealing']

    if sa.empty:
        return pd.DataFrame()

    summary = sa.groupby('objective').agg({
        'left_seats': 'mean',
        'right_seats': 'mean',
        'center_seats': 'mean',
        'left_advantage': 'mean',
        'right_advantage': 'mean',
        'pop_cv': 'mean',
        'final_score': 'mean'
    }).round(2)

    return summary


def plot_algorithm_convergence(df: pd.DataFrame, results_dir: Path, output_file: str):
    """Plot convergence curves for different algorithms."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Find neutral experiments for each algorithm
    algorithms = ['simulated_annealing', 'greedy', 'hill_climbing']

    for idx, algo in enumerate(algorithms):
        ax = axes[idx // 2, idx % 2]

        # Find experiment
        matching = df[(df['algorithm'] == algo) &
                     (df['objective'].str.contains('neutral', case=False, na=False))]

        if matching.empty:
            continue

        exp_name = matching.iloc[0]['experiment']
        pkl_file = results_dir / 'data' / f'{exp_name}.pkl'

        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            history = result['history']
            steps = [h['step'] for h in history]
            scores = [h['score'] for h in history]

            ax.plot(steps, scores, linewidth=2, label=algo.replace('_', ' ').title())
            ax.set_xlabel('Step', fontsize=11)
            ax.set_ylabel('Objective Score', fontsize=11)
            ax.set_title(f'{algo.replace("_", " ").title()} Convergence', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
        except Exception as e:
            print(f"Could not plot {algo}: {e}")

    # Fourth plot: comparison
    ax = axes[1, 1]
    for algo in algorithms:
        matching = df[(df['algorithm'] == algo) &
                     (df['objective'].str.contains('neutral', case=False, na=False))]

        if matching.empty:
            continue

        exp_name = matching.iloc[0]['experiment']
        pkl_file = results_dir / 'data' / f'{exp_name}.pkl'

        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            history = result['history']
            steps = [h['step'] for h in history]
            scores = [h['score'] for h in history]

            # Normalize scores to 0-100 scale
            initial = scores[0]
            final = scores[-1]
            normalized = [(initial - s) / (initial - final) * 100 if initial != final else 100
                         for s in scores]

            ax.plot(steps, normalized, linewidth=2, label=algo.replace('_', ' ').title())
        except Exception as e:
            pass

    ax.set_xlabel('Step', fontsize=11)
    ax.set_ylabel('Optimization Progress (%)', fontsize=11)
    ax.set_title('Algorithm Comparison (Normalized)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(0, 105)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Convergence plot saved to {output_file}")
    plt.close()


def plot_pareto_frontier(df: pd.DataFrame, output_file: str):
    """Plot population balance vs partisan advantage trade-off."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left partisan attempts
    left_data = df[df['objective'].str.contains('left', case=False, na=False)]
    if not left_data.empty:
        ax1.scatter(left_data['pop_cv'], left_data['left_advantage'],
                   s=100, alpha=0.6, label='Experiments')

        for _, row in left_data.iterrows():
            ax1.annotate(row['objective'].replace('maximize_left_', ''),
                        (row['pop_cv'], row['left_advantage']),
                        fontsize=8, alpha=0.7)

        ax1.set_xlabel('Population Imbalance (CV)', fontsize=11)
        ax1.set_ylabel('Left Coalition Advantage (seats)', fontsize=11)
        ax1.set_title('Left Coalition: Population Balance vs Partisan Gain',
                     fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    # Right partisan attempts
    right_data = df[df['objective'].str.contains('right', case=False, na=False)]
    if not right_data.empty:
        ax2.scatter(right_data['pop_cv'], right_data['right_advantage'],
                   s=100, alpha=0.6, color='blue', label='Experiments')

        for _, row in right_data.iterrows():
            ax2.annotate(row['objective'].replace('maximize_right_', ''),
                        (row['pop_cv'], row['right_advantage']),
                        fontsize=8, alpha=0.7)

        ax2.set_xlabel('Population Imbalance (CV)', fontsize=11)
        ax2.set_ylabel('Right Coalition Advantage (seats)', fontsize=11)
        ax2.set_title('Right Coalition: Population Balance vs Partisan Gain',
                     fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Pareto frontier plot saved to {output_file}")
    plt.close()


def generate_latex_tables(df: pd.DataFrame, output_dir: Path):
    """Generate LaTeX-formatted tables for paper."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Table 1: Algorithm comparison
    algo_table = create_algorithm_comparison_table(df)
    if not algo_table.empty:
        latex_file = output_dir / 'table_algorithm_comparison.tex'
        with open(latex_file, 'w') as f:
            f.write(algo_table.to_latex())
        print(f"LaTeX table saved to {latex_file}")

    # Table 2: Objective comparison
    obj_table = create_objective_comparison_table(df)
    if not obj_table.empty:
        latex_file = output_dir / 'table_objective_comparison.tex'
        with open(latex_file, 'w') as f:
            f.write(obj_table.to_latex())
        print(f"LaTeX table saved to {latex_file}")

    # Table 3: Summary statistics
    summary = df.describe().T[['mean', 'std', 'min', 'max']].round(2)
    latex_file = output_dir / 'table_summary_statistics.tex'
    with open(latex_file, 'w') as f:
        f.write(summary.to_latex())
    print(f"LaTeX table saved to {latex_file}")


def main():
    results_dir = Path('results')
    output_dir = Path('results/paper_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading all experimental results...")
    df = load_all_results(results_dir)

    if df.empty:
        print("No results found!")
        return

    print(f"Loaded {len(df)} experiments\n")

    # Save consolidated data
    csv_file = output_dir / 'all_results.csv'
    df.to_csv(csv_file, index=False)
    print(f"Consolidated results saved to {csv_file}\n")

    # Generate tables
    print("\n" + "="*80)
    print("ALGORITHM COMPARISON")
    print("="*80)
    algo_comp = create_algorithm_comparison_table(df)
    if not algo_comp.empty:
        print(algo_comp)

    print("\n" + "="*80)
    print("OBJECTIVE COMPARISON")
    print("="*80)
    obj_comp = create_objective_comparison_table(df)
    if not obj_comp.empty:
        print(obj_comp)

    # Generate plots
    print("\n" + "="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)

    plot_algorithm_convergence(df, results_dir,
                               str(output_dir / 'figure_algorithm_convergence.png'))

    plot_pareto_frontier(df, str(output_dir / 'figure_pareto_frontier.png'))

    # Generate LaTeX tables
    print("\n" + "="*80)
    print("GENERATING LATEX TABLES")
    print("="*80)
    generate_latex_tables(df, output_dir / 'latex')

    # Summary statistics
    print("\n" + "="*80)
    print("KEY FINDINGS FOR PAPER")
    print("="*80)

    print(f"\nTotal experiments analyzed: {len(df)}")
    print(f"Algorithms tested: {df['algorithm'].nunique()}")
    print(f"Objectives tested: {df['objective'].nunique()}")

    print("\nProportional baseline (11 districts):")
    if not df.empty:
        print(f"  Left:   {df['left_prop'].iloc[0]:.2f} seats")
        print(f"  Right:  {df['right_prop'].iloc[0]:.2f} seats")
        print(f"  Center: {df['center_prop'].iloc[0]:.2f} seats")

    print("\nMaximum advantages achieved:")
    print(f"  Left:   {df['left_advantage'].max():+.2f} seats")
    print(f"  Right:  {df['right_advantage'].max():+.2f} seats")

    print("\nPopulation balance:")
    print(f"  Best CV: {df['pop_cv'].min():.3f}")
    print(f"  Worst CV: {df['pop_cv'].max():.3f}")

    print("\n" + "="*80)
    print(f"All outputs saved to: {output_dir}")
    print("="*80)


if __name__ == '__main__':
    main()
