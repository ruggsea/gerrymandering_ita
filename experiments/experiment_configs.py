"""
Experiment configurations for the paper.
"""

# Algorithm configurations
ALGORITHMS = {
    'simulated_annealing': {
        'class': 'GerrymanderOptimizer',
        'module': 'src.gerrymander',
        'init_params': {},
        'optimize_params': {
            'initial_temp': 1000.0,
            'cooling_rate': 0.99,
            'final_temp': 0.01
        }
    },
    'greedy': {
        'class': 'GreedyOptimizer',
        'module': 'src.algorithms',
        'init_params': {},
        'optimize_params': {}
    },
    'hill_climbing': {
        'class': 'HillClimbingOptimizer',
        'module': 'src.algorithms',
        'init_params': {},
        'optimize_params': {
            'restart_frequency': 200
        }
    },
    'random_walk': {
        'class': 'RandomWalkOptimizer',
        'module': 'src.algorithms',
        'init_params': {},
        'optimize_params': {}
    },
    'constrained': {
        'class': 'ConstrainedOptimizer',
        'module': 'src.algorithms',
        'init_params': {
            'population_constraint': 0.15
        },
        'optimize_params': {
            'initial_temp': 1000.0,
            'cooling_rate': 0.99,
            'final_temp': 0.01
        }
    }
}

# Objective configurations
OBJECTIVES = {
    'neutral': {
        'description': 'Population balance + proportionality',
        'target_party': None,
        'weights': {
            'population_balance': 1.0,
            'seat_deviation': 1.0,
            'partisan_advantage': 0.0
        }
    },
    'maximize_left_mild': {
        'description': 'Mild left partisan advantage',
        'target_party': 'coalition_left',
        'weights': {
            'population_balance': 0.5,
            'seat_deviation': 0.1,
            'partisan_advantage': 1.0
        }
    },
    'maximize_left_moderate': {
        'description': 'Moderate left partisan advantage',
        'target_party': 'coalition_left',
        'weights': {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': 5.0
        }
    },
    'maximize_left_extreme': {
        'description': 'Extreme left partisan advantage',
        'target_party': 'coalition_left',
        'weights': {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': 50.0
        }
    },
    'maximize_right_mild': {
        'description': 'Mild right partisan advantage',
        'target_party': 'coalition_right',
        'weights': {
            'population_balance': 0.5,
            'seat_deviation': 0.1,
            'partisan_advantage': 1.0
        }
    },
    'maximize_right_moderate': {
        'description': 'Moderate right partisan advantage',
        'target_party': 'coalition_right',
        'weights': {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': 5.0
        }
    },
    'maximize_right_extreme': {
        'description': 'Extreme right partisan advantage',
        'target_party': 'coalition_right',
        'weights': {
            'population_balance': 0.1,
            'seat_deviation': 0.0,
            'partisan_advantage': 50.0
        }
    },
    'balanced_partisan_left': {
        'description': 'Balanced: population balance + moderate left advantage',
        'target_party': 'coalition_left',
        'weights': {
            'population_balance': 1.0,
            'seat_deviation': 0.0,
            'partisan_advantage': 2.0
        }
    },
    'balanced_partisan_right': {
        'description': 'Balanced: population balance + moderate right advantage',
        'target_party': 'coalition_right',
        'weights': {
            'population_balance': 1.0,
            'seat_deviation': 0.0,
            'partisan_advantage': 2.0
        }
    },
    'constrained_left': {
        'description': 'Maximize left with population constraint',
        'target_party': 'coalition_left',
        'weights': {
            'population_balance': 0.0,
            'seat_deviation': 0.0,
            'partisan_advantage': 10.0
        }
    },
    'constrained_right': {
        'description': 'Maximize right with population constraint',
        'target_party': 'coalition_right',
        'weights': {
            'population_balance': 0.0,
            'seat_deviation': 0.0,
            'partisan_advantage': 10.0
        }
    }
}

# Experiment suite for the paper
PAPER_EXPERIMENTS = [
    # Baseline: Neutral optimization with different algorithms
    {
        'name': 'baseline_sa_short',
        'algorithm': 'simulated_annealing',
        'objective': 'neutral',
        'steps': 1000,
        'seed': 42,
        'create_gif': False
    },
    {
        'name': 'baseline_sa_long',
        'algorithm': 'simulated_annealing',
        'objective': 'neutral',
        'steps': 5000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'baseline_greedy',
        'algorithm': 'greedy',
        'objective': 'neutral',
        'steps': 5000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'baseline_hillclimb',
        'algorithm': 'hill_climbing',
        'objective': 'neutral',
        'steps': 5000,
        'seed': 42,
        'create_gif': True
    },

    # Partisan optimization: Simulated annealing with different strengths
    {
        'name': 'partisan_left_mild',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_left_mild',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'partisan_left_moderate',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_left_moderate',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'partisan_left_extreme',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_left_extreme',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'partisan_right_mild',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_right_mild',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'partisan_right_moderate',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_right_moderate',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'partisan_right_extreme',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_right_extreme',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },

    # Multi-objective: Balanced approaches
    {
        'name': 'balanced_left',
        'algorithm': 'simulated_annealing',
        'objective': 'balanced_partisan_left',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'balanced_right',
        'algorithm': 'simulated_annealing',
        'objective': 'balanced_partisan_right',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },

    # Constrained optimization
    {
        'name': 'constrained_left',
        'algorithm': 'constrained',
        'objective': 'constrained_left',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'constrained_right',
        'algorithm': 'constrained',
        'objective': 'constrained_right',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },

    # Algorithm comparison for right-wing optimization
    {
        'name': 'algo_comparison_greedy_right',
        'algorithm': 'greedy',
        'objective': 'maximize_right_extreme',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },
    {
        'name': 'algo_comparison_hillclimb_right',
        'algorithm': 'hill_climbing',
        'objective': 'maximize_right_extreme',
        'steps': 3000,
        'seed': 42,
        'create_gif': True
    },

    # Sensitivity to random seed
    {
        'name': 'seed_sensitivity_1',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_right_extreme',
        'steps': 3000,
        'seed': 123,
        'create_gif': False
    },
    {
        'name': 'seed_sensitivity_2',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_right_extreme',
        'steps': 3000,
        'seed': 456,
        'create_gif': False
    },
    {
        'name': 'seed_sensitivity_3',
        'algorithm': 'simulated_annealing',
        'objective': 'maximize_right_extreme',
        'steps': 3000,
        'seed': 789,
        'create_gif': False
    },
]

# Quick test experiments (for development)
TEST_EXPERIMENTS = [
    {
        'name': 'test_sa',
        'algorithm': 'simulated_annealing',
        'objective': 'neutral',
        'steps': 100,
        'seed': 42,
        'create_gif': False
    },
    {
        'name': 'test_greedy',
        'algorithm': 'greedy',
        'objective': 'neutral',
        'steps': 100,
        'seed': 42,
        'create_gif': False
    },
]
