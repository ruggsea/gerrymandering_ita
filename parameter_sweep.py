#!/usr/bin/env python3
"""
Parameter Sweep for Gerrymandering Optimization
Runs multiple simulations with different parameters to find optimal settings
for favoring minority parties while maintaining valid districts.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product
import time
import json
from pathlib import Path
from gerrymandering_optimizer import GerrymanderingOptimizer, Config

class ParameterSweep:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.results = []
        
    def run_sweep(self, n_runs_per_config=5):
        """Run parameter sweep with multiple configurations"""
        
        # Parameter ranges to test
        param_configs = {
            'temperature': [500, 1000, 1500, 2000],
            'cooling_rate': [0.95, 0.97, 0.99, 0.995],
            'steps': [500, 1000, 2000, 3000],
            'target_districts': [8, 9, 10, 11],  # Different district counts
            'compactness_weight': [0.1, 0.3, 0.5, 0.7],  # Balance between partisan and compactness
            'population_weight': [0.1, 0.3, 0.5, 0.7]   # Population balance weight
        }
        
        # Generate all combinations
        param_names = list(param_configs.keys())
        param_values = list(param_configs.values())
        
        total_configs = np.prod([len(vals) for vals in param_values])
        total_runs = total_configs * n_runs_per_config
        
        print(f"Running {total_runs} simulations across {total_configs} parameter configurations...")
        
        run_count = 0
        
        for param_combo in product(*param_values):
            config_dict = dict(zip(param_names, param_combo))
            
            print(f"\nTesting config {run_count//n_runs_per_config + 1}/{total_configs}: {config_dict}")
            
            for run in range(n_runs_per_config):
                run_count += 1
                print(f"  Run {run + 1}/{n_runs_per_config}")
                
                try:
                    result = self._run_single_simulation(config_dict, run)
                    self.results.append(result)
                except Exception as e:
                    print(f"    Error in run {run + 1}: {e}")
                    continue
                    
                if run_count % 10 == 0:
                    print(f"Progress: {run_count}/{total_runs} ({run_count/total_runs*100:.1f}%)")
        
        return self.results
    
    def _run_single_simulation(self, config_dict, run_id):
        """Run a single simulation with given parameters"""
        
        # Create configuration
        config = Config(
            temperature=config_dict['temperature'],
            cooling_rate=config_dict['cooling_rate'],
            steps=config_dict['steps'],
            target_districts=config_dict['target_districts'],
            compactness_weight=config_dict['compactness_weight'],
            population_weight=config_dict['population_weight']
        )
        
        # Initialize optimizer with data directory
        optimizer = GerrymanderingOptimizer(".", config)
        
        # Run optimization
        start_time = time.time()
        final_score, final_districts, history = optimizer.optimize()
        end_time = time.time()
        
        # Analyze results
        analysis = self._analyze_results(final_districts, optimizer)
        
        return {
            'run_id': run_id,
            'config': config_dict,
            'final_score': final_score,
            'execution_time': end_time - start_time,
            'analysis': analysis,
            'history': history
        }
    
    def _analyze_results(self, districts, optimizer):
        """Analyze the results of a simulation"""
        
        # Get district statistics
        district_stats = optimizer.get_district_statistics(districts)
        
        # Calculate partisan metrics
        total_seats = len(districts)
        center_left_seats = sum(1 for d in districts if d['winner'] == 'center-left')
        center_right_seats = sum(1 for d in districts if d['winner'] == 'center-right')
        
        # Calculate efficiency metrics
        minority_win_rate = min(center_left_seats, center_right_seats) / total_seats
        majority_win_rate = max(center_left_seats, center_right_seats) / total_seats
        
        # Population balance
        populations = [d['total_population'] for d in districts]
        population_std = np.std(populations)
        population_cv = population_std / np.mean(populations)  # Coefficient of variation
        
        # Compactness (simplified - could be enhanced)
        compactness_scores = [d.get('compactness', 0) for d in districts]
        avg_compactness = np.mean(compactness_scores)
        
        return {
            'total_seats': total_seats,
            'center_left_seats': center_left_seats,
            'center_right_seats': center_right_seats,
            'minority_win_rate': minority_win_rate,
            'majority_win_rate': majority_win_rate,
            'population_std': population_std,
            'population_cv': population_cv,
            'avg_compactness': avg_compactness,
            'district_stats': district_stats
        }
    
    def save_results(self, filename="parameter_sweep_results.json"):
        """Save results to JSON file"""
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = []
        for result in self.results:
            serializable_result = result.copy()
            if 'history' in serializable_result:
                # Convert history arrays to lists
                serializable_result['history'] = {
                    'scores': serializable_result['history']['scores'].tolist(),
                    'temperatures': serializable_result['history']['temperatures'].tolist()
                }
            serializable_results.append(serializable_result)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Results saved to {filename}")
    
    def create_analysis_plots(self, save_dir="plots"):
        """Create comprehensive analysis plots"""
        
        if not self.results:
            print("No results to plot. Run sweep first.")
            return
        
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)
        
        # Convert to DataFrame for easier analysis
        df = self._results_to_dataframe()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # 1. Parameter Impact on Minority Win Rate
        self._plot_parameter_impact(df, save_dir)
        
        # 2. Best Configurations
        self._plot_best_configurations(df, save_dir)
        
        # 3. Trade-offs between metrics
        self._plot_tradeoffs(df, save_dir)
        
        # 4. Convergence analysis
        self._plot_convergence(save_dir)
        
        print(f"Plots saved to {save_dir}")
    
    def _results_to_dataframe(self):
        """Convert results to pandas DataFrame"""
        rows = []
        for result in self.results:
            row = {
                'run_id': result['run_id'],
                'execution_time': result['execution_time'],
                'final_score': result['final_score'],
                **result['config'],
                **result['analysis']
            }
            rows.append(row)
        return pd.DataFrame(rows)
    
    def _plot_parameter_impact(self, df, save_dir):
        """Plot impact of each parameter on minority win rate"""
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.ravel()
        
        params = ['temperature', 'cooling_rate', 'steps', 'target_districts', 
                 'compactness_weight', 'population_weight']
        
        for i, param in enumerate(params):
            ax = axes[i]
            
            # Group by parameter value and calculate mean minority win rate
            grouped = df.groupby(param)['minority_win_rate'].agg(['mean', 'std']).reset_index()
            
            ax.errorbar(grouped[param], grouped['mean'], yerr=grouped['std'], 
                       marker='o', capsize=5, capthick=2, linewidth=2)
            ax.set_xlabel(param.replace('_', ' ').title())
            ax.set_ylabel('Minority Win Rate')
            ax.set_title(f'Impact of {param.replace("_", " ").title()}')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_dir / 'parameter_impact.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_best_configurations(self, df, save_dir):
        """Plot best configurations for different objectives"""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Best for minority win rate
        best_minority = df.nlargest(10, 'minority_win_rate')
        axes[0,0].barh(range(len(best_minority)), best_minority['minority_win_rate'])
        axes[0,0].set_yticks(range(len(best_minority)))
        axes[0,0].set_yticklabels([f"T:{r['temperature']}, CR:{r['cooling_rate']:.3f}" 
                                  for _, r in best_minority.iterrows()])
        axes[0,0].set_xlabel('Minority Win Rate')
        axes[0,0].set_title('Top 10 Configurations for Minority Win Rate')
        
        # Best for population balance
        best_population = df.nsmallest(10, 'population_cv')
        axes[0,1].barh(range(len(best_population)), best_population['population_cv'])
        axes[0,1].set_yticks(range(len(best_population)))
        axes[0,1].set_yticklabels([f"T:{r['temperature']}, CR:{r['cooling_rate']:.3f}" 
                                  for _, r in best_population.iterrows()])
        axes[0,1].set_xlabel('Population Coefficient of Variation')
        axes[0,1].set_title('Top 10 Configurations for Population Balance')
        
        # Best for compactness
        best_compactness = df.nlargest(10, 'avg_compactness')
        axes[1,0].barh(range(len(best_compactness)), best_compactness['avg_compactness'])
        axes[1,0].set_yticks(range(len(best_compactness)))
        axes[1,0].set_yticklabels([f"T:{r['temperature']}, CR:{r['cooling_rate']:.3f}" 
                                  for _, r in best_compactness.iterrows()])
        axes[1,0].set_xlabel('Average Compactness')
        axes[1,0].set_title('Top 10 Configurations for Compactness')
        
        # Best overall score
        best_score = df.nsmallest(10, 'final_score')
        axes[1,1].barh(range(len(best_score)), best_score['final_score'])
        axes[1,1].set_yticks(range(len(best_score)))
        axes[1,1].set_yticklabels([f"T:{r['temperature']}, CR:{r['cooling_rate']:.3f}" 
                                  for _, r in best_score.iterrows()])
        axes[1,1].set_xlabel('Final Score (Lower is Better)')
        axes[1,1].set_title('Top 10 Configurations by Overall Score')
        
        plt.tight_layout()
        plt.savefig(save_dir / 'best_configurations.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_tradeoffs(self, df, save_dir):
        """Plot trade-offs between different metrics"""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # Minority win rate vs population balance
        scatter = axes[0,0].scatter(df['minority_win_rate'], df['population_cv'], 
                                   c=df['final_score'], cmap='viridis', alpha=0.6)
        axes[0,0].set_xlabel('Minority Win Rate')
        axes[0,0].set_ylabel('Population CV')
        axes[0,0].set_title('Trade-off: Minority Win Rate vs Population Balance')
        plt.colorbar(scatter, ax=axes[0,0], label='Final Score')
        
        # Minority win rate vs compactness
        scatter = axes[0,1].scatter(df['minority_win_rate'], df['avg_compactness'], 
                                   c=df['final_score'], cmap='viridis', alpha=0.6)
        axes[0,1].set_xlabel('Minority Win Rate')
        axes[0,1].set_ylabel('Average Compactness')
        axes[0,1].set_title('Trade-off: Minority Win Rate vs Compactness')
        plt.colorbar(scatter, ax=axes[0,1], label='Final Score')
        
        # Population balance vs compactness
        scatter = axes[1,0].scatter(df['population_cv'], df['avg_compactness'], 
                                   c=df['minority_win_rate'], cmap='viridis', alpha=0.6)
        axes[1,0].set_xlabel('Population CV')
        axes[1,0].set_ylabel('Average Compactness')
        axes[1,0].set_title('Trade-off: Population Balance vs Compactness')
        plt.colorbar(scatter, ax=axes[1,0], label='Minority Win Rate')
        
        # Temperature vs cooling rate heatmap
        pivot = df.pivot_table(values='minority_win_rate', 
                              index='temperature', columns='cooling_rate', aggfunc='mean')
        sns.heatmap(pivot, annot=True, fmt='.3f', ax=axes[1,1], cmap='viridis')
        axes[1,1].set_title('Minority Win Rate by Temperature and Cooling Rate')
        
        plt.tight_layout()
        plt.savefig(save_dir / 'tradeoffs.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_convergence(self, save_dir):
        """Plot convergence patterns for different parameter sets"""
        
        # Sample a few different configurations
        sample_results = []
        for result in self.results:
            if len(sample_results) < 6:  # Show 6 different configs
                config_key = f"T{result['config']['temperature']}_CR{result['config']['cooling_rate']}"
                if not any(r['config_key'] == config_key for r in sample_results):
                    result['config_key'] = config_key
                    sample_results.append(result)
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.ravel()
        
        for i, result in enumerate(sample_results):
            ax = axes[i]
            history = result['history']
            
            ax.plot(history['scores'], label='Score', linewidth=2)
            ax.set_xlabel('Step')
            ax.set_ylabel('Score')
            ax.set_title(f"Convergence: {result['config_key']}\n"
                        f"Final Score: {result['final_score']:.3f}")
            ax.grid(True, alpha=0.3)
            ax.legend()
        
        plt.tight_layout()
        plt.savefig(save_dir / 'convergence.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Run the parameter sweep"""
    print("Starting Parameter Sweep for Gerrymandering Optimization")
    print("=" * 60)
    
    # Initialize sweep
    sweep = ParameterSweep()
    
    # Run sweep (reduce n_runs_per_config for faster testing)
    results = sweep.run_sweep(n_runs_per_config=3)
    
    # Save results
    sweep.save_results()
    
    # Create analysis plots
    sweep.create_analysis_plots()
    
    # Print summary
    df = sweep._results_to_dataframe()
    print("\n" + "=" * 60)
    print("PARAMETER SWEEP SUMMARY")
    print("=" * 60)
    print(f"Total simulations run: {len(results)}")
    print(f"Best minority win rate: {df['minority_win_rate'].max():.3f}")
    print(f"Average minority win rate: {df['minority_win_rate'].mean():.3f}")
    print(f"Best configuration for minority win rate:")
    best_config = df.loc[df['minority_win_rate'].idxmax()]
    for param, value in best_config.items():
        if param in ['temperature', 'cooling_rate', 'steps', 'target_districts', 
                    'compactness_weight', 'population_weight']:
            print(f"  {param}: {value}")

if __name__ == "__main__":
    main()