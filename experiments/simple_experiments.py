#!/usr/bin/env python3
"""
Simplified experiment configuration: 4 experiments only
- 2 algorithms (Simulated Annealing, Greedy)
- 2 objectives (maximize left, maximize right)
"""

# Algorithm configurations
ALGORITHMS = {
    'simulated_annealing': {
        'module': 'src.gerrymander',
        'class': 'GerrymanderOptimizer',
        'init_params': {},
        'optimize_params': {
            'initial_temp': 1000.0,
            'final_temp': 0.01,
            'cooling_rate': 0.99
        }
    },
    'greedy': {
        'module': 'src.algorithms',
        'class': 'GreedyOptimizer',
        'init_params': {},
        'optimize_params': {}
    }
}

# Objective configurations (only left vs right, no center)
OBJECTIVES = {
    'maximize_left': {
        'description': 'Maximize left coalition seats',
        'target_party': 'coalition_left',
        'weights': {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': 50.0  # Strong partisan weight
        }
    },
    'maximize_right': {
        'description': 'Maximize right coalition seats',
        'target_party': 'coalition_right',
        'weights': {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': 50.0  # Strong partisan weight
        }
    }
}

# 4 experiments total
SIMPLE_EXPERIMENTS = [
    {
        'name': 'sa_maximize_left',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_left',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'sa_maximize_right',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_right',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'greedy_maximize_left',
        'algorithm': 'greedy',
        'objective': 'maximize_left',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'greedy_maximize_right',
        'algorithm': 'greedy',
        'objective': 'maximize_right',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    }
]
