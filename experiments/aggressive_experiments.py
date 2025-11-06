#!/usr/bin/env python3
"""
Aggressive experiment configuration for better gerrymandering.
Higher temperature, more steps, slower cooling.
"""

# Algorithm configurations - MORE AGGRESSIVE
ALGORITHMS = {
    'simulated_annealing_aggressive': {
        'module': 'src.gerrymander',
        'class': 'GerrymanderOptimizer',
        'init_params': {},
        'optimize_params': {
            'initial_temp': 10000.0,  # 10x higher
            'final_temp': 0.001,       # Lower final temp
            'cooling_rate': 0.9995     # Slower cooling
        }
    }
}

# Objective configurations
OBJECTIVES = {
    'maximize_left_extreme': {
        'description': 'Aggressively maximize left coalition seats',
        'target_party': 'coalition_left',
        'weights': {
            'population_balance': 0.01,     # Very low weight
            'seat_deviation': 0.0,
            'partisan_advantage': 500.0     # MUCH higher weight
        }
    },
    'maximize_right_extreme': {
        'description': 'Aggressively maximize right coalition seats',
        'target_party': 'coalition_right',
        'weights': {
            'population_balance': 0.01,     # Very low weight
            'seat_deviation': 0.0,
            'partisan_advantage': 500.0     # MUCH higher weight
        }
    }
}

# More aggressive experiments
AGGRESSIVE_EXPERIMENTS = [
    {
        'name': 'aggressive_left',
        'algorithm': 'simulated_annealing_aggressive',
        'objective': 'maximize_left_extreme',
        'steps': 10000,  # Much longer
        'seed': 42,
        'create_gif': False  # Faster without GIFs
    },
    {
        'name': 'aggressive_right',
        'algorithm': 'simulated_annealing_aggressive',
        'objective': 'maximize_right_extreme',
        'steps': 10000,
        'seed': 42,
        'create_gif': False
    }
]
