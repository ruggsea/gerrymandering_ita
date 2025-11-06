#!/usr/bin/env python3
"""EXTREME test - max aggression."""
import numpy as np
from src.data_loader import load_and_prepare_data
from src.gerrymander import GerrymanderOptimizer
import logging

logging.basicConfig(level=logging.WARNING)  # Less spam

gdf = load_and_prepare_data(region='emilia', data_dir='.')

best_left_seats = 0
best_right_seats = 0

# Try multiple seeds
for seed in [42, 123, 456, 789, 999]:
    print(f"\n{'='*60}")
    print(f"SEED {seed}")
    print('='*60)
    
    # Maximize LEFT - EXTREME
    print("Testing maximize LEFT (EXTREME)...")
    opt_left = GerrymanderOptimizer(
        gdf=gdf,
        n_districts=11,
        target_party='coalition_left',
        objective_weights={
            'population_balance': 0.001,  # Almost ignore population
            'seat_deviation': 0.0,
            'partisan_advantage': 1000.0  # MASSIVE weight
        },
        random_seed=seed
    )
    
    best_dist_left, _ = opt_left.optimize(
        initial_temp=50000.0,  # VERY high
        cooling_rate=0.9999,   # VERY slow cooling
        steps=5000,
        save_frequency=500
    )
    
    # Count seats
    left_seats = 0
    for d in range(11):
        mask = best_dist_left == d
        district_gdf = gdf.iloc[np.where(mask)[0]]
        left_v = district_gdf['coalition_left'].sum()
        right_v = district_gdf['coalition_right'].sum()
        center_v = district_gdf['coalition_center'].sum()
        if left_v >= max(right_v, center_v):
            left_seats += 1
    
    print(f"  Result: {left_seats}/11 left seats")
    best_left_seats = max(best_left_seats, left_seats)
    
    # Maximize RIGHT - EXTREME
    print("Testing maximize RIGHT (EXTREME)...")
    opt_right = GerrymanderOptimizer(
        gdf=gdf,
        n_districts=11,
        target_party='coalition_right',
        objective_weights={
            'population_balance': 0.001,
            'seat_deviation': 0.0,
            'partisan_advantage': 1000.0
        },
        random_seed=seed
    )
    
    best_dist_right, _ = opt_right.optimize(
        initial_temp=50000.0,
        cooling_rate=0.9999,
        steps=5000,
        save_frequency=500
    )
    
    # Count seats
    right_seats = 0
    for d in range(11):
        mask = best_dist_right == d
        district_gdf = gdf.iloc[np.where(mask)[0]]
        left_v = district_gdf['coalition_left'].sum()
        right_v = district_gdf['coalition_right'].sum()
        center_v = district_gdf['coalition_center'].sum()
        if right_v > max(left_v, center_v):
            right_seats += 1
    
    print(f"  Result: {right_seats}/11 right seats")
    best_right_seats = max(best_right_seats, right_seats)

print(f"\n{'='*60}")
print("BEST RESULTS ACROSS ALL SEEDS")
print('='*60)
print(f"Best LEFT:  {best_left_seats}/11 seats")
print(f"Best RIGHT: {best_right_seats}/11 seats")
print(f"\nTarget: 2+ left seats and 11/11 right seats")
if best_left_seats >= 2:
    print("✅ Achieved 2+ left seats!")
else:
    print(f"❌ Only got {best_left_seats} left seat(s)")
if best_right_seats == 11:
    print("✅ Achieved 11/11 right seats!")
else:
    print(f"❌ Only got {best_right_seats} right seats")
