"""
Quick script to run only the left-wing goal.
"""
from gerrymander import GerrymanderSimulator

sim = GerrymanderSimulator()

print("\n" + "="*70)
print("TARGET: Left-wing wins 8+ seats (one more than IRL's 7)")
print("="*70)

# Run with more aggressive parameters
sim.sweep_until_goal('left', 8, max_attempts=50, n_iterations=200000)
