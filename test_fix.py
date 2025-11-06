#!/usr/bin/env python3
"""Quick test to verify the fixes work."""
import numpy as np
from src.data_loader import load_and_prepare_data
from src.gerrymander import GerrymanderOptimizer

print("="*80)
print("TESTING FIXED ALGORITHM")
print("="*80)

# Load data
print("\nLoading data...")
gdf = load_and_prepare_data(region='emilia', data_dir='.')
print(f"Loaded {len(gdf)} communes")

# Test maximize LEFT
print("\n" + "="*80)
print("TEST 1: Maximize LEFT coalition")
print("="*80)

optimizer = GerrymanderOptimizer(
    gdf=gdf,
    n_districts=11,
    target_party='coalition_left',
    objective_weights={
        'population_balance': 0.1,
        'seat_deviation': 0.0,
        'partisan_advantage': 100.0  # Strong weight
    },
    random_seed=42
)

# Run short optimization
best_districts, history = optimizer.optimize(
    initial_temp=5000.0,
    cooling_rate=0.995,
    steps=500,
    save_frequency=50
)

print("\n" + "="*80)
print("TEST 2: Maximize RIGHT coalition")
print("="*80)

optimizer2 = GerrymanderOptimizer(
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

best_districts2, history2 = optimizer2.optimize(
    initial_temp=5000.0,
    cooling_rate=0.995,
    steps=500,
    save_frequency=50
)

print("\n" + "="*80)
print("VERIFICATION")
print("="*80)
print("\nChecking if results are different (they should be!)...")

if np.array_equal(best_districts, best_districts2):
    print("❌ FAIL: Both experiments produced IDENTICAL districts!")
else:
    print("✅ SUCCESS: Experiments produced DIFFERENT districts!")

print("\nDone!")
