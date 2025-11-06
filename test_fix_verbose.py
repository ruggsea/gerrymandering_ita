#!/usr/bin/env python3
"""Quick test with verbose output."""
import numpy as np
from src.data_loader import load_and_prepare_data
from src.gerrymander import GerrymanderOptimizer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

print("="*80)
print("TESTING WITH VERBOSE OUTPUT")
print("="*80)

# Load data
gdf = load_and_prepare_data(region='emilia', data_dir='.')

# Test maximize LEFT
print("\n[1/2] Testing MAXIMIZE LEFT...")
optimizer_left = GerrymanderOptimizer(
    gdf=gdf,
    n_districts=11,
    target_party='coalition_left',
    objective_weights={
        'population_balance': 0.1,
        'seat_deviation': 0.0,
        'partisan_advantage': 100.0
    },
    random_seed=42
)

best_left, history_left = optimizer_left.optimize(
    initial_temp=5000.0,
    cooling_rate=0.99,
    steps=200,
    save_frequency=20
)

# Test maximize RIGHT
print("\n[2/2] Testing MAXIMIZE RIGHT...")
optimizer_right = GerrymanderOptimizer(
    gdf=gdf,
    n_districts=11,
    target_party='coalition_right',
    objective_weights={
        'population_balance': 0.1,
        'seat_deviation': 0.0,
        'partisan_advantage': 100.0
    },
    random_seed=42
)

best_right, history_right = optimizer_right.optimize(
    initial_temp=5000.0,
    cooling_rate=0.99,
    steps=200,
    save_frequency=20
)

print("\n" + "="*80)
print("COMPARISON")
print("="*80)

# Count seats
def count_seats(gdf, districts, target):
    coalition_cols = ['coalition_left', 'coalition_right', 'coalition_center']
    seats = 0
    for d in range(11):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]
        target_votes = district_gdf[target].sum()
        max_votes = max(district_gdf[col].sum() for col in coalition_cols)
        if target_votes >= max_votes:
            seats += 1
    return seats

left_seats_in_left_opt = count_seats(gdf, best_left, 'coalition_left')
right_seats_in_left_opt = count_seats(gdf, best_left, 'coalition_right')

left_seats_in_right_opt = count_seats(gdf, best_right, 'coalition_left')
right_seats_in_right_opt = count_seats(gdf, best_right, 'coalition_right')

print(f"\nMaximize LEFT result:")
print(f"  Left seats:  {left_seats_in_left_opt}/11")
print(f"  Right seats: {right_seats_in_left_opt}/11")

print(f"\nMaximize RIGHT result:")
print(f"  Left seats:  {left_seats_in_right_opt}/11")
print(f"  Right seats: {right_seats_in_right_opt}/11")

if np.array_equal(best_left, best_right):
    print("\n❌ Districts are IDENTICAL!")
else:
    print("\n✅ Districts are DIFFERENT!")

if left_seats_in_left_opt > left_seats_in_right_opt:
    print("✅ Maximize LEFT got more left seats than maximize RIGHT")
else:
    print("❌ Maximize LEFT did NOT get more left seats")

if right_seats_in_right_opt > right_seats_in_left_opt:
    print("✅ Maximize RIGHT got more right seats than maximize LEFT")
else:
    print("❌ Maximize RIGHT did NOT get more right seats")
