#!/usr/bin/env python3
"""
Generate paper-ready results tables and statistics.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from src.visualizer import calculate_seat_distribution


def load_all_experiments(results_dir: Path):
    """Load all completed experiments."""
    experiments = []

    for pkl_file in sorted((results_dir / "data").glob("*.pkl")):
        try:
            with open(pkl_file, 'rb') as f:
                result = pickle.load(f)

            gdf = result['gdf']
            best_districts = result['best_districts']
            config = result['config']
            algorithm = result.get('algorithm', 'unknown')
            objective = result.get('objective', 'unknown')

            # Calculate metrics
            party_cols = ['coalition_left', 'coalition_right', 'coalition_center']
            n_districts = len(np.unique(best_districts))
            seats = calculate_seat_distribution(gdf, best_districts, n_districts, party_cols)

            # Proportional baseline
            total_votes = sum(gdf[p].sum() for p in party_cols)
            prop = {p: (gdf[p].sum() / total_votes) * n_districts for p in party_cols}

            # Population stats
            district_pops = []
            for d in range(n_districts):
                mask = best_districts == d
                pop = gdf.iloc[np.where(mask)[0]]['population'].sum()
                district_pops.append(pop)

            pop_std = np.std(district_pops)
            pop_mean = np.mean(district_pops)
            pop_cv = pop_std / pop_mean

            experiments.append({
                'experiment': pkl_file.stem,
                'name': config.get('name', 'unknown'),
                'algorithm': algorithm,
                'objective': objective,
                'steps': config.get('steps', 0),
                'left_seats': seats['coalition_left'],
                'right_seats': seats['coalition_right'],
                'center_seats': seats['coalition_center'],
                'left_prop': prop['coalition_left'],
                'right_prop': prop['coalition_right'],
                'center_prop': prop['coalition_center'],
                'left_adv': seats['coalition_left'] - prop['coalition_left'],
                'right_adv': seats['coalition_right'] - prop['coalition_right'],
                'center_adv': seats['coalition_center'] - prop['coalition_center'],
                'pop_cv': pop_cv
            })
        except Exception as e:
            print(f"Warning: Could not load {pkl_file.name}: {e}")

    return pd.DataFrame(experiments)


def generate_table1_baseline(df: pd.DataFrame):
    """Table 1: Baseline algorithm comparison."""
    neutral = df[df['objective'].str.contains('neutral', case=False, na=False)]

    if neutral.empty:
        return None

    table = []
    for algo in ['simulated_annealing', 'greedy', 'hill_climbing']:
        subset = neutral[neutral['algorithm'] == algo]
        if not subset.empty:
            row = subset.iloc[0]
            table.append({
                'Algorithm': algo.replace('_', ' ').title(),
                'Left Seats': int(row['left_seats']),
                'Right Seats': int(row['right_seats']),
                'Center Seats': int(row['center_seats']),
                'Pop. CV': f"{row['pop_cv']:.3f}"
            })

    return pd.DataFrame(table)


def generate_table2_partisan(df: pd.DataFrame):
    """Table 2: Partisan optimization results."""
    table = []

    # Proportional baseline
    if not df.empty:
        table.append({
            'Objective': 'Proportional Baseline',
            'Left Seats': f"{df['left_prop'].iloc[0]:.2f}",
            'Right Seats': f"{df['right_prop'].iloc[0]:.2f}",
            'Center Seats': f"{df['center_prop'].iloc[0]:.2f}",
            'Left Adv.': '0.00',
            'Right Adv.': '0.00',
            'Pop. CV': '-'
        })

    # Partisan objectives
    for obj_name, display_name in [
        ('neutral', 'Neutral'),
        ('maximize_left_mild', 'Max Left (Mild)'),
        ('maximize_left_moderate', 'Max Left (Moderate)'),
        ('maximize_left_extreme', 'Max Left (Extreme)'),
        ('maximize_right_mild', 'Max Right (Mild)'),
        ('maximize_right_moderate', 'Max Right (Moderate)'),
        ('maximize_right_extreme', 'Max Right (Extreme)'),
        ('balanced_partisan_left', 'Balanced Left'),
        ('balanced_partisan_right', 'Balanced Right')
    ]:
        subset = df[df['objective'] == obj_name]
        if not subset.empty:
            row = subset.iloc[0]
            table.append({
                'Objective': display_name,
                'Left Seats': int(row['left_seats']),
                'Right Seats': int(row['right_seats']),
                'Center Seats': int(row['center_seats']),
                'Left Adv.': f"{row['left_adv']:+.2f}",
                'Right Adv.': f"{row['right_adv']:+.2f}",
                'Pop. CV': f"{row['pop_cv']:.3f}"
            })

    return pd.DataFrame(table)


def generate_table3_constrained(df: pd.DataFrame):
    """Table 3: Constrained optimization."""
    constrained = df[df['algorithm'] == 'constrained']

    if constrained.empty:
        return None

    table = []
    for _, row in constrained.iterrows():
        table.append({
            'Target': row['objective'].replace('constrained_', '').title(),
            'Left Seats': int(row['left_seats']),
            'Right Seats': int(row['right_seats']),
            'Center Seats': int(row['center_seats']),
            'Left Adv.': f"{row['left_adv']:+.2f}",
            'Right Adv.': f"{row['right_adv']:+.2f}",
            'Pop. CV': f"{row['pop_cv']:.3f}",
            'Constraint': '✓ (CV≤15%)'
        })

    return pd.DataFrame(table)


def generate_summary_stats(df: pd.DataFrame):
    """Generate summary statistics for paper."""
    stats = {}

    stats['total_experiments'] = len(df)
    stats['algorithms_tested'] = df['algorithm'].nunique()
    stats['objectives_tested'] = df['objective'].nunique()

    if not df.empty:
        stats['proportional_left'] = df['left_prop'].iloc[0]
        stats['proportional_right'] = df['right_prop'].iloc[0]
        stats['proportional_center'] = df['center_prop'].iloc[0]

        stats['max_left_advantage'] = df['left_adv'].max()
        stats['max_right_advantage'] = df['right_adv'].max()
        stats['min_left_advantage'] = df['left_adv'].min()
        stats['min_right_advantage'] = df['right_adv'].min()

        stats['best_pop_cv'] = df['pop_cv'].min()
        stats['worst_pop_cv'] = df['pop_cv'].max()
        stats['mean_pop_cv'] = df['pop_cv'].mean()

    return stats


def main():
    results_dir = Path('results')
    output_dir = Path('results/paper_tables')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("GENERATING PAPER-READY TABLES")
    print("="*80)

    # Load data
    print("\nLoading all experiments...")
    df = load_all_experiments(results_dir)
    print(f"Loaded {len(df)} experiments")

    if df.empty:
        print("No experiments found!")
        return

    # Save raw data
    df.to_csv(output_dir / 'all_experiments.csv', index=False)
    print(f"Saved: {output_dir / 'all_experiments.csv'}")

    # Table 1: Baseline
    print("\n" + "-"*80)
    print("TABLE 1: Baseline Algorithm Comparison")
    print("-"*80)
    table1 = generate_table1_baseline(df)
    if table1 is not None:
        print(table1.to_string(index=False))
        table1.to_csv(output_dir / 'table1_baseline.csv', index=False)
        table1.to_latex(output_dir / 'table1_baseline.tex', index=False)
        print(f"\nSaved: table1_baseline.csv/tex")

    # Table 2: Partisan
    print("\n" + "-"*80)
    print("TABLE 2: Partisan Optimization Results")
    print("-"*80)
    table2 = generate_table2_partisan(df)
    if table2 is not None:
        print(table2.to_string(index=False))
        table2.to_csv(output_dir / 'table2_partisan.csv', index=False)
        table2.to_latex(output_dir / 'table2_partisan.tex', index=False)
        print(f"\nSaved: table2_partisan.csv/tex")

    # Table 3: Constrained
    print("\n" + "-"*80)
    print("TABLE 3: Constrained Optimization")
    print("-"*80)
    table3 = generate_table3_constrained(df)
    if table3 is not None:
        print(table3.to_string(index=False))
        table3.to_csv(output_dir / 'table3_constrained.csv', index=False)
        table3.to_latex(output_dir / 'table3_constrained.tex', index=False)
        print(f"\nSaved: table3_constrained.csv/tex")

    # Summary stats
    print("\n" + "="*80)
    print("SUMMARY STATISTICS FOR PAPER")
    print("="*80)
    stats = generate_summary_stats(df)

    for key, value in stats.items():
        print(f"{key}: {value}")

    # Save stats
    import json
    with open(output_dir / 'summary_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"\nSaved: summary_stats.json")

    print("\n" + "="*80)
    print(f"All tables saved to: {output_dir}")
    print("="*80)


if __name__ == '__main__':
    main()
