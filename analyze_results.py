#!/usr/bin/env python3
"""Analyze experiment results to see actual seat counts."""
import pickle
import numpy as np
from pathlib import Path

def calculate_seats(gdf, districts, n_districts):
    """Calculate which coalition wins each district."""
    left_seats = 0
    right_seats = 0

    results = []

    for d in range(n_districts):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]

        left_votes = district_gdf['coalition_left'].sum()
        right_votes = district_gdf['coalition_right'].sum()

        winner = 'LEFT' if left_votes > right_votes else 'RIGHT'
        if left_votes > right_votes:
            left_seats += 1
        else:
            right_seats += 1

        results.append({
            'district': d,
            'left_votes': left_votes,
            'right_votes': right_votes,
            'winner': winner,
            'margin': abs(left_votes - right_votes)
        })

    return left_seats, right_seats, results

# Load and analyze each experiment
result_files = list(Path('results/data').glob('*.pkl'))

print("="*80)
print("GERRYMANDERING RESULTS ANALYSIS")
print("="*80)

for pkl_file in sorted(result_files):
    print(f"\n\n{'='*80}")
    print(f"Experiment: {pkl_file.stem}")
    print('='*80)

    with open(pkl_file, 'rb') as f:
        data = pickle.load(f)

    gdf = data['gdf']
    initial_districts = data['history'][0]['districts']
    final_districts = data['best_districts']

    # Calculate initial seats
    init_left, init_right, init_details = calculate_seats(gdf, initial_districts, 11)

    # Calculate final seats
    final_left, final_right, final_details = calculate_seats(gdf, final_districts, 11)

    print(f"\nINITIAL DISTRICTING:")
    print(f"  Left seats:  {init_left}/11")
    print(f"  Right seats: {init_right}/11")

    print(f"\nFINAL DISTRICTING:")
    print(f"  Left seats:  {final_left}/11")
    print(f"  Right seats: {final_right}/11")

    print(f"\nCHANGE:")
    print(f"  Left:  {final_left - init_left:+d} seats ({((final_left - init_left)/init_left * 100) if init_left > 0 else 0:.1f}%)")
    print(f"  Right: {final_right - init_right:+d} seats ({((final_right - init_right)/init_right * 100) if init_right > 0 else 0:.1f}%)")

    print(f"\nFINAL DISTRICT BREAKDOWN:")
    print(f"{'District':<10} {'Left Votes':<15} {'Right Votes':<15} {'Winner':<10} {'Margin':<15}")
    print("-" * 70)
    for d in final_details:
        print(f"D{d['district']:<9} {d['left_votes']:<15,.0f} {d['right_votes']:<15,.0f} {d['winner']:<10} {d['margin']:<15,.0f}")

    # Calculate total votes
    total_left = gdf['coalition_left'].sum()
    total_right = gdf['coalition_right'].sum()
    total_votes = total_left + total_right

    left_pct = (total_left / total_votes) * 100
    right_pct = (total_right / total_votes) * 100

    proportional_left = round((total_left / total_votes) * 11)
    proportional_right = 11 - proportional_left

    print(f"\nOVERALL VOTE SHARES:")
    print(f"  Left:  {left_pct:.1f}% (proportional seats: {proportional_left}/11)")
    print(f"  Right: {right_pct:.1f}% (proportional seats: {proportional_right}/11)")

    print(f"\nSEAT BONUS:")
    print(f"  Left:  {final_left - proportional_left:+d} seats vs proportional")
    print(f"  Right: {final_right - proportional_right:+d} seats vs proportional")

print(f"\n\n{'='*80}")
print("SUMMARY")
print('='*80)
print("\nCan you successfully gerrymander in Italy?")
print("Answer: Check the seat bonuses above!")
