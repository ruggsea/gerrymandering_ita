#!/usr/bin/env python3
"""
Analyze and compare results from gerrymandering experiments.
"""
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from src.visualizer import calculate_seat_distribution


def load_experiment_results(data_dir: Path):
    """Load all experiment results."""
    results = []

    for json_file in data_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
            results.append(data)

    return results


def analyze_seat_distributions(results_dir: Path):
    """Analyze seat distributions for each experiment."""
    analysis = []

    for pkl_file in sorted((results_dir / "data").glob("*.pkl")):
        print(f"Analyzing {pkl_file.name}...")

        with open(pkl_file, 'rb') as f:
            data = pickle.load(f)

        gdf = data['gdf']
        best_districts = data['best_districts']
        config = data['config']

        # Calculate final seat distribution
        party_cols = ['coalition_left', 'coalition_right', 'coalition_center']
        seats = calculate_seat_distribution(
            gdf,
            best_districts,
            config['n_districts'],
            party_cols
        )

        # Calculate proportional representation baseline
        proportional = {}
        total_votes = sum(gdf[p].sum() for p in party_cols)
        for party in party_cols:
            party_votes = gdf[party].sum()
            proportional[party] = (party_votes / total_votes) * config['n_districts']

        analysis.append({
            'experiment': pkl_file.stem,
            'goal': config['goal'],
            'strength': config.get('strength', 'moderate'),
            'left_seats': seats['coalition_left'],
            'right_seats': seats['coalition_right'],
            'center_seats': seats['coalition_center'],
            'left_proportional': proportional['coalition_left'],
            'right_proportional': proportional['coalition_right'],
            'center_proportional': proportional['coalition_center'],
            'left_advantage': seats['coalition_left'] - proportional['coalition_left'],
            'right_advantage': seats['coalition_right'] - proportional['coalition_right'],
            'center_advantage': seats['coalition_center'] - proportional['coalition_center']
        })

    return pd.DataFrame(analysis)


def create_summary_plot(df: pd.DataFrame, output_path: str):
    """Create summary comparison plot."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Seat distribution by experiment
    ax1 = axes[0, 0]
    x = range(len(df))
    width = 0.25

    ax1.bar([i - width for i in x], df['left_seats'], width, label='Left', color='#E74C3C')
    ax1.bar(x, df['right_seats'], width, label='Right', color='#3498DB')
    ax1.bar([i + width for i in x], df['center_seats'], width, label='Center', color='#F39C12')

    # Add proportional lines
    ax1.axhline(df['left_proportional'].iloc[0], color='#E74C3C', linestyle='--', alpha=0.5)
    ax1.axhline(df['right_proportional'].iloc[0], color='#3498DB', linestyle='--', alpha=0.5)
    ax1.axhline(df['center_proportional'].iloc[0], color='#F39C12', linestyle='--', alpha=0.5)

    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{row['goal']}\n{row['strength']}" for _, row in df.iterrows()],
                        rotation=45, ha='right', fontsize=9)
    ax1.set_ylabel('Seats Won', fontsize=12)
    ax1.set_title('Seat Distribution by Experiment\n(dashed lines = proportional)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Seat advantage (deviation from proportional)
    ax2 = axes[0, 1]
    ax2.bar([i - width for i in x], df['left_advantage'], width, label='Left', color='#E74C3C')
    ax2.bar(x, df['right_advantage'], width, label='Right', color='#3498DB')
    ax2.bar([i + width for i in x], df['center_advantage'], width, label='Center', color='#F39C12')

    ax2.axhline(0, color='black', linestyle='-', linewidth=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{row['goal']}\n{row['strength']}" for _, row in df.iterrows()],
                        rotation=45, ha='right', fontsize=9)
    ax2.set_ylabel('Seat Advantage (vs Proportional)', fontsize=12)
    ax2.set_title('Partisan Advantage Achieved', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Left coalition performance
    ax3 = axes[1, 0]
    ax3.plot(df.index, df['left_seats'], 'o-', color='#E74C3C', linewidth=2, markersize=8, label='Actual')
    ax3.axhline(df['left_proportional'].iloc[0], color='#E74C3C', linestyle='--', linewidth=2, label='Proportional')
    ax3.set_xticks(df.index)
    ax3.set_xticklabels([f"{row['goal']}\n{row['strength']}" for _, row in df.iterrows()],
                        rotation=45, ha='right', fontsize=9)
    ax3.set_ylabel('Left Coalition Seats', fontsize=12)
    ax3.set_title('Left Coalition Performance', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Right coalition performance
    ax4 = axes[1, 1]
    ax4.plot(df.index, df['right_seats'], 'o-', color='#3498DB', linewidth=2, markersize=8, label='Actual')
    ax4.axhline(df['right_proportional'].iloc[0], color='#3498DB', linestyle='--', linewidth=2, label='Proportional')
    ax4.set_xticks(df.index)
    ax4.set_xticklabels([f"{row['goal']}\n{row['strength']}" for _, row in df.iterrows()],
                        rotation=45, ha='right', fontsize=9)
    ax4.set_ylabel('Right Coalition Seats', fontsize=12)
    ax4.set_title('Right Coalition Performance', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Summary plot saved to {output_path}")


def main():
    results_dir = Path("results")

    print("Analyzing experiment results...\n")
    df = analyze_seat_distributions(results_dir)

    print("\n" + "="*80)
    print("SEAT DISTRIBUTION ANALYSIS")
    print("="*80)
    print(df.to_string(index=False))
    print()

    # Calculate key metrics
    print("="*80)
    print("KEY FINDINGS")
    print("="*80)

    # Proportional baseline
    print("\nProportional Representation Baseline (11 districts):")
    print(f"  Left:   {df['left_proportional'].iloc[0]:.2f} seats")
    print(f"  Right:  {df['right_proportional'].iloc[0]:.2f} seats")
    print(f"  Center: {df['center_proportional'].iloc[0]:.2f} seats")

    print("\nNeutral Optimization:")
    neutral = df[df['goal'] == 'neutral'].iloc[0]
    print(f"  Left:   {neutral['left_seats']} seats ({neutral['left_advantage']:+.2f})")
    print(f"  Right:  {neutral['right_seats']} seats ({neutral['right_advantage']:+.2f})")
    print(f"  Center: {neutral['center_seats']} seats ({neutral['center_advantage']:+.2f})")

    print("\nPartisan Optimization Results:")
    for _, row in df[df['goal'] != 'neutral'].iterrows():
        print(f"\n{row['goal'].replace('_', ' ').title()} ({row['strength']}):")
        print(f"  Left:   {row['left_seats']} seats ({row['left_advantage']:+.2f})")
        print(f"  Right:  {row['right_seats']} seats ({row['right_advantage']:+.2f})")
        print(f"  Center: {row['center_seats']} seats ({row['center_advantage']:+.2f})")

    # Maximum achievable advantages
    print("\n" + "="*80)
    print("GERRYMANDERING POTENTIAL")
    print("="*80)

    max_left_advantage = df['left_advantage'].max()
    max_right_advantage = df['right_advantage'].max()

    print(f"\nMaximum Left advantage achieved:  {max_left_advantage:+.2f} seats")
    print(f"Maximum Right advantage achieved: {max_right_advantage:+.2f} seats")

    if abs(max_left_advantage) > 1 or abs(max_right_advantage) > 1:
        print("\n✓ Significant partisan gerrymandering IS POSSIBLE in Emilia-Romagna")
        print("  Algorithm successfully created district boundaries favoring target coalitions")
    else:
        print("\n✗ Limited partisan gerrymandering potential in Emilia-Romagna")
        print("  Algorithm struggled to create significant partisan advantages")

    # Save detailed results
    csv_path = results_dir / "analysis_summary.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nDetailed results saved to: {csv_path}")

    # Create summary plot
    plot_path = results_dir / "experiments_summary.png"
    create_summary_plot(df, str(plot_path))

    print("\n" + "="*80)


if __name__ == '__main__':
    main()
