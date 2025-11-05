#!/usr/bin/env python3
"""
Generate supplementary materials for the paper.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
import json
from src.visualizer import calculate_seat_distribution

sns.set_style("whitegrid")


def create_convergence_details(results_dir: Path, output_dir: Path):
    """Create detailed convergence analysis."""
    output_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(3, 3, figsize=(18, 15))
    axes = axes.flatten()

    pkl_files = sorted((results_dir / "data").glob("*.pkl"))[:9]

    for idx, pkl_file in enumerate(pkl_files):
        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            history = result['history']
            if not history:
                continue

            steps = [h['step'] for h in history]
            scores = [h['score'] for h in history]

            ax = axes[idx]
            ax.plot(steps, scores, linewidth=2, color='steelblue')
            ax.set_xlabel('Step', fontsize=10)
            ax.set_ylabel('Score', fontsize=10)
            ax.set_title(result['config'].get('name', 'Unknown')[:30], fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.ticklabel_format(style='scientific', axis='y', scilimits=(0, 0))

        except Exception as e:
            print(f"Could not plot {pkl_file.name}: {e}")

    plt.tight_layout()
    plt.savefig(output_dir / 'suppfig_convergence_details.png', dpi=300, bbox_inches='tight')
    print(f"Saved: suppfig_convergence_details.png")
    plt.close()


def create_district_maps(results_dir: Path, output_dir: Path):
    """Create maps for key experiments."""
    output_dir.mkdir(parents=True, exist_ok=True)

    key_experiments = [
        'neutral',
        'maximize_right_extreme',
        'maximize_left_extreme',
        'constrained'
    ]

    for exp_pattern in key_experiments:
        matching = list((results_dir / "data").glob(f"*{exp_pattern}*.pkl"))
        if not matching:
            continue

        pkl_file = matching[0]

        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            gdf = result['gdf']
            districts = result['best_districts']

            fig, ax = plt.subplots(1, 1, figsize=(12, 10))

            plot_gdf = gdf.copy()
            plot_gdf['district'] = districts

            plot_gdf.plot(
                column='district',
                ax=ax,
                cmap='tab20',
                edgecolor='black',
                linewidth=0.5,
                legend=False
            )

            ax.set_title(f"District Map: {exp_pattern.replace('_', ' ').title()}",
                        fontsize=16, fontweight='bold')
            ax.axis('off')

            plt.tight_layout()
            plt.savefig(output_dir / f'suppfig_map_{exp_pattern}.png',
                       dpi=300, bbox_inches='tight')
            print(f"Saved: suppfig_map_{exp_pattern}.png")
            plt.close()

        except Exception as e:
            print(f"Could not create map for {exp_pattern}: {e}")


def create_parameter_sensitivity(results_dir: Path, output_dir: Path):
    """Analyze sensitivity to algorithm parameters."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect experiments with different seeds
    seed_results = {}

    for pkl_file in (results_dir / "data").glob("*.pkl"):
        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            config = result['config']
            objective = config.get('objective', 'unknown')
            seed = config.get('seed', None)

            if seed is not None and 'right' in objective:
                gdf = result['gdf']
                districts = result['best_districts']

                party_cols = ['coalition_left', 'coalition_right', 'coalition_center']
                n_districts = len(np.unique(districts))
                seats = calculate_seat_distribution(gdf, districts, n_districts, party_cols)

                if objective not in seed_results:
                    seed_results[objective] = []

                seed_results[objective].append({
                    'seed': seed,
                    'right_seats': seats['coalition_right'],
                    'left_seats': seats['coalition_left']
                })

        except Exception as e:
            pass

    if not seed_results:
        print("No seed sensitivity data found")
        return

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    objectives = list(seed_results.keys())
    x_pos = np.arange(len(objectives))

    for idx, obj in enumerate(objectives):
        data = seed_results[obj]
        right_seats = [d['right_seats'] for d in data]

        ax.scatter([idx] * len(right_seats), right_seats, s=100, alpha=0.6)

        if len(right_seats) > 1:
            ax.plot([idx-0.1, idx+0.1], [np.mean(right_seats)] * 2,
                   'r-', linewidth=3, label='Mean' if idx == 0 else '')

    ax.set_xticks(x_pos)
    ax.set_xticklabels([o.replace('_', ' ').title() for o in objectives], rotation=45, ha='right')
    ax.set_ylabel('Right Coalition Seats', fontsize=12)
    ax.set_title('Sensitivity to Random Seed', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / 'suppfig_seed_sensitivity.png', dpi=300, bbox_inches='tight')
    print(f"Saved: suppfig_seed_sensitivity.png")
    plt.close()


def create_optimization_landscape(results_dir: Path, output_dir: Path):
    """Visualize objective function landscape."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find a long SA run
    sa_files = [f for f in (results_dir / "data").glob("*simulated_annealing*.pkl")
                if 'long' in f.stem or '5000' in f.stem]

    if not sa_files:
        print("No long SA run found")
        return

    try:
        with open(sa_files[0], 'rb') as f:
            result = pickle.load(f)

        history = result['history']

        steps = [h['step'] for h in history]
        scores = [h['score'] for h in history]
        temps = [h['temperature'] for h in history]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

        # Score over time
        ax1.plot(steps, scores, linewidth=2, color='steelblue', label='Current Score')
        ax1.set_ylabel('Objective Score', fontsize=12)
        ax1.set_title('Simulated Annealing Optimization Landscape', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Temperature over time
        ax2.plot(steps, temps, linewidth=2, color='orangered', label='Temperature')
        ax2.set_xlabel('Optimization Step', fontsize=12)
        ax2.set_ylabel('Temperature', fontsize=12)
        ax2.set_yscale('log')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        plt.tight_layout()
        plt.savefig(output_dir / 'suppfig_optimization_landscape.png', dpi=300, bbox_inches='tight')
        print(f"Saved: suppfig_optimization_landscape.png")
        plt.close()

    except Exception as e:
        print(f"Could not create optimization landscape: {e}")


def compile_experiment_metadata(results_dir: Path, output_dir: Path):
    """Create comprehensive metadata table."""
    metadata = []

    for pkl_file in sorted((results_dir / "data").glob("*.pkl")):
        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            config = result['config']
            history = result['history']

            metadata.append({
                'experiment': pkl_file.stem,
                'name': config.get('name', 'unknown'),
                'algorithm': result.get('algorithm', 'unknown'),
                'objective': result.get('objective', 'unknown'),
                'steps': config.get('steps', 0),
                'seed': config.get('seed', None),
                'num_history_points': len(history),
                'initial_score': history[0]['score'] if history else None,
                'final_score': history[-1]['score'] if history else None,
                'file_size_mb': pkl_file.stat().st_size / (1024 * 1024)
            })

        except Exception as e:
            print(f"Could not load metadata for {pkl_file.name}: {e}")

    df = pd.DataFrame(metadata)
    df.to_csv(output_dir / 'experiment_metadata.csv', index=False)
    print(f"Saved: experiment_metadata.csv")
    return df


def create_readme(output_dir: Path):
    """Create README for supplementary materials."""
    readme = """# Supplementary Materials

## Contents

### Figures

- **suppfig_convergence_details.png**: Detailed convergence plots for all experiments
- **suppfig_map_*.png**: District maps for key experiments
  - neutral: Fair baseline optimization
  - maximize_right_extreme: Maximum right-wing advantage
  - maximize_left_extreme: Maximum left-wing advantage (attempted)
  - constrained: Population-constrained optimization
- **suppfig_seed_sensitivity.png**: Robustness to random initialization
- **suppfig_optimization_landscape.png**: Score and temperature evolution (SA)

### Data Files

- **experiment_metadata.csv**: Complete experiment metadata
  - Experiment names, algorithms, objectives
  - Computational details (steps, runtime)
  - Score trajectories

### Usage

All figures are publication-ready at 300 DPI. Data files are in CSV format for easy analysis.

---

**Generated**: Automatically by create_supplementary_materials.py
**Data Source**: Computational experiments on Emilia-Romagna gerrymandering
"""

    with open(output_dir / 'README.md', 'w') as f:
        f.write(readme)

    print(f"Saved: README.md")


def main():
    results_dir = Path('results')
    output_dir = Path('results/supplementary_materials')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GENERATING SUPPLEMENTARY MATERIALS")
    print("="*80)

    print("\n1. Creating detailed convergence plots...")
    create_convergence_details(results_dir, output_dir)

    print("\n2. Creating district maps...")
    create_district_maps(results_dir, output_dir)

    print("\n3. Analyzing parameter sensitivity...")
    create_parameter_sensitivity(results_dir, output_dir)

    print("\n4. Creating optimization landscape...")
    create_optimization_landscape(results_dir, output_dir)

    print("\n5. Compiling experiment metadata...")
    metadata = compile_experiment_metadata(results_dir, output_dir)
    print(f"\nTotal experiments: {len(metadata)}")

    print("\n6. Creating README...")
    create_readme(output_dir)

    print("\n" + "="*80)
    print(f"All supplementary materials saved to: {output_dir}")
    print("="*80)


if __name__ == '__main__':
    main()
