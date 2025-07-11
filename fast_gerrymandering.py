#!/usr/bin/env python3
"""
Fast Gerrymandering Optimization Library
Efficiently optimizes district boundaries using simulated annealing with numpy acceleration.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
import seaborn as sns
from pathlib import Path
import time
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import random
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import logging
from itertools import product

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GerryConfig:
    """Configuration for gerrymandering optimization."""
    # Simulated annealing parameters
    temperature: float = 1000.0
    cooling_rate: float = 0.99
    steps: int = 1000
    
    # District parameters
    target_districts: int = 11
    
    # Optimization weights
    compactness_weight: float = 0.3
    population_weight: float = 0.3
    partisan_weight: float = 1.0
    
    # Target party (0=center-left, 1=center-right)
    target_party: int = 0
    
    # Constraints
    max_population_deviation: float = 0.15
    min_compactness: float = 0.2

class FastGerryOptimizer:
    """Fast gerrymandering optimizer using numpy for performance."""
    
    def __init__(self, data_path: str, config: GerryConfig):
        """
        Initialize the optimizer.
        
        Args:
            data_path: Path to GeoJSON file with voting data
            config: Optimization configuration
        """
        self.config = config
        self.data_path = Path(data_path)
        
        # Load and preprocess data
        self._load_data()
        self._preprocess_data()
        
        # Initialize optimization state
        self.current_districts = None
        self.best_districts = None
        self.best_score = float('inf')
        
        # History for GIF generation
        self.history = {
            'scores': [],
            'temperatures': [],
            'districts': [],
            'party_wins': []
        }
    
    def _load_data(self):
        """Load geographical and voting data."""
        logger.info("Loading data...")
        
        # Load GeoJSON with voting data
        self.gdf = gpd.read_file(self.data_path)
        
        # Extract voting data as numpy arrays for speed
        self.voting_columns = [
            'PARTITO DEMOCRATICO',
            'MOVIMENTO 5 STELLE', 
            'ALLEANZA VERDI E SINISTRA',
            'FRATELLI D\'ITALIA',
            'LEGA SALVINI PREMIER',
            'FORZA ITALIA - NOI MODERATI - PPE'
        ]
        
        # Create voting matrix (communes x parties)
        self.voting_matrix = np.zeros((len(self.gdf), len(self.voting_columns)))
        for i, col in enumerate(self.voting_columns):
            if col in self.gdf.columns:
                self.voting_matrix[:, i] = self.gdf[col].fillna(0).values
        
        # Calculate total votes per commune
        self.total_votes = np.sum(self.voting_matrix, axis=1)
        
        # Calculate party coalitions
        # Center-left: PD, M5S, AVS
        self.center_left_votes = np.sum(self.voting_matrix[:, [0, 1, 2]], axis=1)
        # Center-right: FdI, Lega, FI
        self.center_right_votes = np.sum(self.voting_matrix[:, [3, 4, 5]], axis=1)
        
        # Calculate vote shares
        self.left_share = self.center_left_votes / (self.center_left_votes + self.center_right_votes + 1e-10)
        self.right_share = self.center_right_votes / (self.center_left_votes + self.center_right_votes + 1e-10)
        
        # Get geometries and centroids
        self.geometries = self.gdf.geometry.values
        self.centroids = np.array([(g.centroid.x, g.centroid.y) for g in self.geometries])
        
        # Calculate population (use total votes as proxy)
        self.populations = self.total_votes
        
        logger.info(f"Loaded data for {len(self.gdf)} communes")
    
    def _preprocess_data(self):
        """Preprocess data for efficient optimization."""
        # Calculate adjacency matrix for contiguity checks
        self.adjacency_matrix = self._calculate_adjacency_matrix()
        
        # Calculate target population per district
        self.target_population = np.sum(self.populations) / self.config.target_districts
        
        logger.info("Data preprocessing complete")
    
    def _calculate_adjacency_matrix(self):
        """Calculate adjacency matrix for contiguity checks."""
        n_communes = len(self.gdf)
        adjacency = np.zeros((n_communes, n_communes), dtype=bool)
        
        for i in range(n_communes):
            for j in range(i+1, n_communes):
                if self.geometries[i].touches(self.geometries[j]):
                    adjacency[i, j] = adjacency[j, i] = True
        
        return adjacency
    
    def initialize_districts(self):
        """Initialize random district assignments."""
        n_communes = len(self.gdf)
        
        # Start with random assignments
        district_assignments = np.random.randint(0, self.config.target_districts, n_communes)
        
        # Ensure all districts have at least one commune
        for i in range(self.config.target_districts):
            if i not in district_assignments:
                district_assignments[np.random.randint(0, n_communes)] = i
        
        return self._assignments_to_districts(district_assignments)
    
    def _assignments_to_districts(self, assignments):
        """Convert district assignments to district objects."""
        districts = []
        for i in range(self.config.target_districts):
            commune_indices = np.where(assignments == i)[0]
            if len(commune_indices) > 0:
                districts.append({
                    'communes': commune_indices.tolist(),
                    'population': np.sum(self.populations[commune_indices]),
                    'left_votes': np.sum(self.center_left_votes[commune_indices]),
                    'right_votes': np.sum(self.center_right_votes[commune_indices])
                })
        return districts
    
    def _districts_to_assignments(self, districts):
        """Convert district objects to assignment array."""
        assignments = np.zeros(len(self.gdf), dtype=int)
        for i, district in enumerate(districts):
            for commune_idx in district['communes']:
                assignments[commune_idx] = i
        return assignments
    
    def calculate_score(self, districts):
        """Calculate optimization score for districts."""
        if not districts:
            return float('inf')
        
        # Population balance score
        populations = np.array([d['population'] for d in districts])
        population_std = np.std(populations) / self.target_population
        population_score = population_std
        
        # Compactness score (using perimeter/area ratio)
        compactness_scores = []
        for district in districts:
            if len(district['communes']) <= 1:
                compactness_scores.append(1.0)
                continue
            
            # Calculate district geometry
            district_geoms = [self.geometries[i] for i in district['communes']]
            district_union = unary_union(district_geoms)
            
            if district_union.area > 0:
                compactness = district_union.length / np.sqrt(district_union.area)
                compactness_scores.append(min(compactness, 10.0))  # Cap at 10
            else:
                compactness_scores.append(10.0)
        
        compactness_score = np.mean(compactness_scores)
        
        # Partisan score (favor target party)
        partisan_score = 0
        target_wins = 0
        
        for district in districts:
            total_votes = district['left_votes'] + district['right_votes']
            if total_votes == 0:
                continue
            
            left_share = district['left_votes'] / total_votes
            right_share = district['right_votes'] / total_votes
            
            if self.config.target_party == 0:  # Target center-left
                if left_share > right_share:
                    target_wins += 1
                    partisan_score -= 1  # Lower score is better
                else:
                    partisan_score += 1
            else:  # Target center-right
                if right_share > left_share:
                    target_wins += 1
                    partisan_score -= 1
                else:
                    partisan_score += 1
        
        # Combine scores
        total_score = (
            self.config.population_weight * population_score +
            self.config.compactness_weight * compactness_score +
            self.config.partisan_weight * partisan_score
        )
        
        return total_score, target_wins
    
    def generate_neighbor(self, districts):
        """Generate a neighbor solution by swapping communes."""
        if not districts:
            return districts
        
        # Convert to assignments
        assignments = self._districts_to_assignments(districts)
        
        # Find valid swaps
        valid_swaps = []
        for i in range(len(self.gdf)):
            for j in range(i+1, len(self.gdf)):
                if assignments[i] != assignments[j]:
                    # Check if swap maintains contiguity
                    if self._is_valid_swap(assignments, i, j):
                        valid_swaps.append((i, j))
        
        if not valid_swaps:
            return districts
        
        # Perform random swap
        i, j = random.choice(valid_swaps)
        assignments[i], assignments[j] = assignments[j], assignments[i]
        
        return self._assignments_to_districts(assignments)
    
    def _is_valid_swap(self, assignments, i, j):
        """Check if swapping communes i and j maintains contiguity."""
        # This is a simplified check - in practice you'd want more sophisticated contiguity validation
        return True  # For now, assume all swaps are valid
    
    def optimize(self, save_history=True):
        """Run simulated annealing optimization."""
        logger.info("Starting optimization...")
        
        # Initialize
        self.current_districts = self.initialize_districts()
        self.best_districts = self.current_districts.copy()
        current_score, current_wins = self.calculate_score(self.current_districts)
        self.best_score = current_score
        
        temperature = self.config.temperature
        
        # Optimization loop
        for step in range(self.config.steps):
            # Generate neighbor
            neighbor_districts = self.generate_neighbor(self.current_districts)
            neighbor_score, neighbor_wins = self.calculate_score(neighbor_districts)
            
            # Accept or reject
            delta_score = neighbor_score - current_score
            if delta_score < 0 or random.random() < np.exp(-delta_score / temperature):
                self.current_districts = neighbor_districts
                current_score = neighbor_score
                current_wins = neighbor_wins
                
                # Update best solution
                if current_score < self.best_score:
                    self.best_districts = [d.copy() for d in self.current_districts]
                    self.best_score = current_score
            
            # Cool down
            temperature *= self.config.cooling_rate
            
            # Store history
            if save_history and step % 50 == 0:
                self.history['scores'].append(current_score)
                self.history['temperatures'].append(temperature)
                self.history['districts'].append([d.copy() for d in self.current_districts])
                self.history['party_wins'].append(current_wins)
            
            # Progress update
            if step % 100 == 0:
                logger.info(f"Step {step}/{self.config.steps}, Score: {current_score:.3f}, Wins: {current_wins}/{self.config.target_districts}")
        
        logger.info(f"Optimization complete. Best score: {self.best_score:.3f}")
        return self.best_score, self.best_districts, self.history

class GerrymanderingAnalyzer:
    """Analyze gerrymandering results and generate visualizations."""
    
    def __init__(self, optimizer: FastGerryOptimizer):
        self.optimizer = optimizer
    
    def create_simulation_gif(self, history, output_path="simulation.gif"):
        """Create GIF showing optimization progress."""
        logger.info("Creating simulation GIF...")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        def animate(frame):
            ax1.clear()
            ax2.clear()
            
            # Plot map
            districts = history['districts'][frame]
            self._plot_districts(ax1, districts)
            ax1.set_title(f"Step {frame * 50}, Wins: {history['party_wins'][frame]}/{self.optimizer.config.target_districts}")
            
            # Plot optimization progress
            steps = np.arange(len(history['scores'])) * 50
            ax2.plot(steps[:frame+1], history['scores'][:frame+1], 'b-', label='Score')
            ax2.plot(steps[:frame+1], history['party_wins'][:frame+1], 'r-', label='Target Party Wins')
            ax2.set_xlabel('Step')
            ax2.set_ylabel('Score / Wins')
            ax2.legend()
            ax2.grid(True)
        
        # Create animation
        anim = FuncAnimation(fig, animate, frames=len(history['districts']), 
                           interval=200, repeat=True)
        
        # Save GIF
        writer = PillowWriter(fps=5)
        anim.save(output_path, writer=writer)
        
        logger.info(f"GIF saved to {output_path}")
    
    def _plot_districts(self, ax, districts):
        """Plot districts with party colors."""
        # Define colors
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', 
                 '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43', '#10ac84']
        
        for i, district in enumerate(districts):
            # Calculate district winner
            total_votes = district['left_votes'] + district['right_votes']
            if total_votes > 0:
                left_share = district['left_votes'] / total_votes
                right_share = district['right_votes'] / total_votes
                
                if left_share > right_share:
                    color = '#ff6b6b'  # Red for center-left
                else:
                    color = '#4ecdc4'  # Blue for center-right
            else:
                color = '#gray'
            
            # Plot district communes
            for commune_idx in district['communes']:
                geom = self.optimizer.geometries[commune_idx]
                if hasattr(geom, 'exterior'):
                    x, y = geom.exterior.xy
                    ax.fill(x, y, color=color, alpha=0.7)
                    ax.plot(x, y, color='black', linewidth=0.5)
        
        ax.set_aspect('equal')
        ax.set_xlim(self.optimizer.gdf.bounds.minx.min(), self.optimizer.gdf.bounds.maxx.max())
        ax.set_ylim(self.optimizer.gdf.bounds.miny.min(), self.optimizer.gdf.bounds.maxy.max())

def run_parameter_sweep(data_path: str, output_dir: str = "results"):
    """Run comprehensive parameter sweep to find optimal settings."""
    logger.info("Starting parameter sweep...")
    
    # Parameter combinations to test
    temperatures = [500, 1000, 2000]
    cooling_rates = [0.95, 0.99, 0.995]
    steps_list = [500, 1000, 2000]
    partisan_weights = [0.5, 1.0, 2.0, 5.0]
    target_parties = [0, 1]  # 0=center-left, 1=center-right
    
    results = []
    
    total_combinations = len(temperatures) * len(cooling_rates) * len(steps_list) * len(partisan_weights) * len(target_parties)
    current = 0
    
    for temp, cool, steps, p_weight, target_party in product(temperatures, cooling_rates, steps_list, partisan_weights, target_parties):
        current += 1
        logger.info(f"Testing combination {current}/{total_combinations}")
        
        config = GerryConfig(
            temperature=temp,
            cooling_rate=cool,
            steps=steps,
            partisan_weight=p_weight,
            target_party=target_party
        )
        
        # Run multiple trials
        trial_results = []
        for trial in range(3):  # 3 trials per combination
            optimizer = FastGerryOptimizer(data_path, config)
            score, districts, history = optimizer.optimize(save_history=False)
            
            # Calculate final statistics
            final_wins = 0
            for district in districts:
                total_votes = district['left_votes'] + district['right_votes']
                if total_votes > 0:
                    left_share = district['left_votes'] / total_votes
                    right_share = district['right_votes'] / total_votes
                    
                    if target_party == 0 and left_share > right_share:
                        final_wins += 1
                    elif target_party == 1 and right_share > left_share:
                        final_wins += 1
            
            trial_results.append({
                'score': score,
                'wins': final_wins,
                'win_rate': final_wins / config.target_districts
            })
        
        # Average results
        avg_score = np.mean([r['score'] for r in trial_results])
        avg_wins = np.mean([r['wins'] for r in trial_results])
        avg_win_rate = np.mean([r['win_rate'] for r in trial_results])
        
        results.append({
            'temperature': temp,
            'cooling_rate': cool,
            'steps': steps,
            'partisan_weight': p_weight,
            'target_party': target_party,
            'avg_score': avg_score,
            'avg_wins': avg_wins,
            'avg_win_rate': avg_win_rate
        })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(f"{output_dir}/parameter_sweep_results.csv", index=False)
    
    # Create analysis plots
    create_parameter_analysis_plots(results_df, output_dir)
    
    logger.info("Parameter sweep complete!")
    return results_df

def create_parameter_analysis_plots(results_df: pd.DataFrame, output_dir: str):
    """Create analysis plots for parameter sweep results."""
    logger.info("Creating analysis plots...")
    
    # Set up plotting style
    plt.style.use('seaborn-v0_8')
    
    # 1. Effect of partisan weight on win rate
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Partisan weight vs win rate
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        party_name = "Center-Left" if target_party == 0 else "Center-Right"
        
        for temp in party_data['temperature'].unique():
            temp_data = party_data[party_data['temperature'] == temp]
            axes[0, 0].plot(temp_data['partisan_weight'], temp_data['avg_win_rate'], 
                           marker='o', label=f'{party_name}, T={temp}')
    
    axes[0, 0].set_xlabel('Partisan Weight')
    axes[0, 0].set_ylabel('Average Win Rate')
    axes[0, 0].set_title('Effect of Partisan Weight on Win Rate')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # Plot 2: Temperature vs win rate
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        party_name = "Center-Left" if target_party == 0 else "Center-Right"
        
        for p_weight in party_data['partisan_weight'].unique():
            weight_data = party_data[party_data['partisan_weight'] == p_weight]
            axes[0, 1].plot(weight_data['temperature'], weight_data['avg_win_rate'], 
                           marker='s', label=f'{party_name}, w={p_weight}')
    
    axes[0, 1].set_xlabel('Temperature')
    axes[0, 1].set_ylabel('Average Win Rate')
    axes[0, 1].set_title('Effect of Temperature on Win Rate')
    axes[0, 1].legend()
    axes[0, 1].grid(True)
    
    # Plot 3: Cooling rate vs win rate
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        party_name = "Center-Left" if target_party == 0 else "Center-Right"
        
        for p_weight in party_data['partisan_weight'].unique():
            weight_data = party_data[party_data['partisan_weight'] == p_weight]
            axes[1, 0].plot(weight_data['cooling_rate'], weight_data['avg_win_rate'], 
                           marker='^', label=f'{party_name}, w={p_weight}')
    
    axes[1, 0].set_xlabel('Cooling Rate')
    axes[1, 0].set_ylabel('Average Win Rate')
    axes[1, 0].set_title('Effect of Cooling Rate on Win Rate')
    axes[1, 0].legend()
    axes[1, 0].grid(True)
    
    # Plot 4: Steps vs win rate
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        party_name = "Center-Left" if target_party == 0 else "Center-Right"
        
        for p_weight in party_data['partisan_weight'].unique():
            weight_data = party_data[party_data['partisan_weight'] == p_weight]
            axes[1, 1].plot(weight_data['steps'], weight_data['avg_win_rate'], 
                           marker='d', label=f'{party_name}, w={p_weight}')
    
    axes[1, 1].set_xlabel('Steps')
    axes[1, 1].set_ylabel('Average Win Rate')
    axes[1, 1].set_title('Effect of Steps on Win Rate')
    axes[1, 1].legend()
    axes[1, 1].grid(True)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/parameter_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create heatmap of best parameters
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Find best parameters for each target party
    best_results = []
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        best_idx = party_data['avg_win_rate'].idxmax()
        best_results.append(party_data.loc[best_idx])
    
    best_df = pd.DataFrame(best_results)
    
    # Create heatmap
    heatmap_data = best_df[['temperature', 'cooling_rate', 'steps', 'partisan_weight', 'avg_win_rate']].T
    sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdYlBu_r', ax=ax)
    ax.set_title('Best Parameters for Each Target Party')
    ax.set_ylabel('Parameters')
    ax.set_xlabel('Target Party (0=Center-Left, 1=Center-Right)')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/best_parameters_heatmap.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Analysis plots saved to {output_dir}")

if __name__ == "__main__":
    # Example usage
    data_path = "comuni_italiani_trend_liste_2022_2024.geojson"
    
    # Create output directory
    Path("results").mkdir(exist_ok=True)
    
    # Run parameter sweep
    results = run_parameter_sweep(data_path)
    
    # Run a demonstration optimization
    config = GerryConfig(
        temperature=1000,
        cooling_rate=0.99,
        steps=1000,
        partisan_weight=2.0,
        target_party=0  # Target center-left
    )
    
    optimizer = FastGerryOptimizer(data_path, config)
    score, districts, history = optimizer.optimize()
    
    # Create GIF
    analyzer = GerrymanderingAnalyzer(optimizer)
    analyzer.create_simulation_gif(history, "results/gerrymandering_simulation.gif")
    
    print("Optimization complete! Check the results/ directory for outputs.")