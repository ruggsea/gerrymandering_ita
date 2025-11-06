#!/usr/bin/env python3
"""Test with EXTREME parameters and multiple random seeds."""
import numpy as np
from src.data_loader import load_and_prepare_data
from src.gerrymander import GerrymanderOptimizer

gdf = load_and_prepare_data(region='emilia', data_dir='.')
coalition_cols = ['coalition_left', 'coalition_right', 'coalition_center']

def count_seats(districts, target):
    seats = 0
    for d in range(11):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]
        target_votes = district_gdf[target].sum()
        max_votes = max(district_gdf[col].sum() for col in coalition_cols)
        if target_votes >= max_votes:
            seats += 1
    return seats

print("="*80)
print("EXTREME OPTIMIZATION TESTS")
print("="*80)

best_left_result = (0, None)
best_right_result = (0, None)

# Try multiple seeds
for seed in [42, 123, 456, 789, 999]:
    print(f"\n--- SEED {seed} ---")
    
    # Test LEFT
    print(f"  Maximizing LEFT...")
    opt_left = GerrymanderOptimizer(
        gdf=gdf,
        n_districts=11,
        target_party='coalition_left',
        objective_weights={
            'population_balance': 0.01,
            'seat_deviation': 0.0,
            'partisan_advantage': 1000.0  # EXTREME weight
        },
        random_seed=seed
    )
    
    districts_left, _ = opt_left.optimize(
        initial_temp=20000.0,  # Much higher temp
        cooling_rate=0.9998,   # Slower cooling
        steps=5000,
        save_frequency=1000
    )
    
    left_seats = count_seats(districts_left, 'coalition_left')
    print(f"    Result: {left_seats}/11 left seats")
    
    if left_seats > best_left_result[0]:
        best_left_result = (left_seats, seed)
    
    # Test RIGHT
    print(f"  Maximizing RIGHT...")
    opt_right = GerrymanderOptimizer(
        gdf=gdf,
        n_districts=11,
        target_party='coalition_right',
        objective_weights={
            'population_balance': 0.01,
            'seat_deviation': 0.0,
            'partisan_advantage': 1000.0
        },
        random_seed=seed
    )
    
    districts_right, _ = opt_right.optimize(
        initial_temp=20000.0,
        cooling_rate=0.9998,
        steps=5000,
        save_frequency=1000
    )
    
    right_seats = count_seats(districts_right, 'coalition_right')
    print(f"    Result: {right_seats}/11 right seats")
    
    if right_seats > best_right_result[0]:
        best_right_result = (right_seats, seed)

print("\n" + "="*80)
print("BEST RESULTS")
print("="*80)
print(f"LEFT:  {best_left_result[0]}/11 seats (seed {best_left_result[1]})")
print(f"RIGHT: {best_right_result[0]}/11 seats (seed {best_right_result[1]})")

if best_left_result[0] >= 2:
    print("\n✅ SUCCESS: Achieved 2+ left seats!")
else:
    print(f"\n❌ FAILED: Only got {best_left_result[0]} left seat(s)")

if best_right_result[0] >= 11:
    print("✅ SUCCESS: Achieved 11/11 right seats!")
else:
    print(f"❌ FAILED: Only got {best_right_result[0]} right seats")
