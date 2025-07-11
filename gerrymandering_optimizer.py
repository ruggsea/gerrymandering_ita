"""
Italian Gerrymandering Optimization Library

A comprehensive library for optimizing Italian voting district boundaries using
simulated annealing to minimize gerrymandering effects.

Author: Research Assistant
Date: 2024
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import logging
import pickle
import json
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import random
import math
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for the gerrymandering optimization algorithm."""
    
    # Simulated annealing parameters
    initial_temperature: float = 1000.0
    cooling_rate: float = 0.99
    min_temperature: float = 0.01
    max_steps: int = 1000
    
    # District parameters
    num_districts: int = 11
    min_district_size: int = 5
    max_district_size: int = 100
    
    # Optimization weights
    population_weight: float = 1.0
    compactness_weight: float = 1.0
    partisan_fairness_weight: float = 1.0
    
    # Constraints
    max_population_deviation: float = 0.1  # 10% deviation allowed
    min_compactness: float = 0.3
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.initial_temperature <= 0:
            raise ValueError("Initial temperature must be positive")
        if not 0 < self.cooling_rate < 1:
            raise ValueError("Cooling rate must be between 0 and 1")
        if self.num_districts <= 0:
            raise ValueError("Number of districts must be positive")


class ItalianVotingData:
    """Handles Italian voting data and geographical information."""
    
    def __init__(self, votes_file: str, geo_file: str, population_file: Optional[str] = None):
        """
        Initialize with voting and geographical data.
        
        Args:
            votes_file: Path to CSV file with voting results
            geo_file: Path to GeoJSON file with geographical boundaries
            population_file: Optional path to population data file
        """
        self.votes_file = votes_file
        self.geo_file = geo_file
        self.population_file = population_file
        
        self.votes_data = None
        self.geo_data = None
        self.population_data = None
        self.combined_data = None
        
        self._load_data()
    
    def _load_data(self):
        """Load and combine all data sources."""
        logger.info("Loading voting data...")
        self.votes_data = pd.read_csv(self.votes_file)
        
        logger.info("Loading geographical data...")
        self.geo_data = gpd.read_file(self.geo_file)
        
        if self.population_file:
            logger.info("Loading population data...")
            self.population_data = pd.read_csv(self.population_file, sep=';')
            self._process_population_data()
        
        self._combine_data()
    
    def _process_population_data(self):
        """Process population data to get total population per commune."""
        if self.population_data is not None:
            # Aggregate population by commune
            self.population_data = self.population_data.groupby('Codice comune')['Totale'].sum().reset_index()
            self.population_data.columns = ['CODICE ISTAT', 'popolazione']
    
    def _combine_data(self):
        """Combine voting and geographical data."""
        # Merge voting data with geographical data
        self.combined_data = self.geo_data.merge(
            self.votes_data, 
            left_on='CODICE ISTAT', 
            right_on='CODICE ISTAT', 
            how='inner'
        )
        
        # Add population data if available
        if self.population_data is not None:
            self.combined_data = self.combined_data.merge(
                self.population_data,
                left_on='CODICE ISTAT',
                right_on='CODICE ISTAT',
                how='left'
            )
        
        # Calculate total votes per commune
        vote_columns = [col for col in self.combined_data.columns 
                       if col not in ['CODICE ISTAT', 'name', 'geometry', 'popolazione', 'CIRCOSCRIZIONE', 'COLLEGIO UNINOMINALE']]
        
        self.combined_data['total_votes'] = self.combined_data[vote_columns].sum(axis=1)
        
        logger.info(f"Combined data contains {len(self.combined_data)} communes")
    
    def get_commune_data(self) -> gpd.GeoDataFrame:
        """Get the combined commune data."""
        return self.combined_data
    
    def get_vote_columns(self) -> List[str]:
        """Get list of political party vote columns."""
        vote_columns = [col for col in self.combined_data.columns 
                       if col not in ['CODICE ISTAT', 'name', 'geometry', 'popolazione', 'CIRCOSCRIZIONE', 'COLLEGIO UNINOMINALE', 'total_votes']]
        return vote_columns


class DistrictMap:
    """Represents a district map with communes assigned to districts."""
    
    def __init__(self, commune_data: gpd.GeoDataFrame, num_districts: int):
        """
        Initialize district map.
        
        Args:
            commune_data: GeoDataFrame with commune data
            num_districts: Number of districts to create
        """
        self.commune_data = commune_data.copy()
        self.num_districts = num_districts
        self.district_assignments = {}
        self.district_geometries = {}
        self.district_stats = {}
        
        self._initialize_districts()
    
    def _initialize_districts(self):
        """Initialize districts with random commune assignments."""
        logger.info(f"Selecting {self.num_districts} random communes to start the districts")
        
        # Select random seed communes for each district
        seed_communes = random.sample(list(self.commune_data.index), self.num_districts)
        
        # Initialize district assignments
        for i, seed_idx in enumerate(seed_communes):
            self.district_assignments[seed_idx] = i
        
        logger.info("Assigning the remaining communes to districts")
        
        # Assign remaining communes to nearest district
        unassigned = [idx for idx in self.commune_data.index if idx not in seed_communes]
        
        for i, commune_idx in enumerate(unassigned):
            if i % 50 == 0:
                logger.info(f"Assigned {i} communes")
            
            # Find nearest district
            commune_geom = self.commune_data.loc[commune_idx, 'geometry']
            min_distance = float('inf')
            best_district = 0
            
            for district_id in range(self.num_districts):
                district_communes = [idx for idx, dist in self.district_assignments.items() if dist == district_id]
                if district_communes:
                    district_geom = unary_union([self.commune_data.loc[idx, 'geometry'] for idx in district_communes])
                    distance = commune_geom.distance(district_geom)
                    if distance < min_distance:
                        min_distance = distance
                        best_district = district_id
            
            self.district_assignments[commune_idx] = best_district
        
        logger.info(f"Finished assigning communes to districts, assigned {len(self.district_assignments)} communes out of {len(self.commune_data)} communes")
        
        # Log district sizes
        for district_id in range(self.num_districts):
            district_communes = [idx for idx, dist in self.district_assignments.items() if dist == district_id]
            logger.info(f"District {district_id} has {len(district_communes)} communes")
        
        self._update_district_geometries()
        self._calculate_district_stats()
    
    def _update_district_geometries(self):
        """Update district geometries based on current assignments."""
        for district_id in range(self.num_districts):
            district_communes = [idx for idx, dist in self.district_assignments.items() if dist == district_id]
            if district_communes:
                geometries = [self.commune_data.loc[idx, 'geometry'] for idx in district_communes]
                self.district_geometries[district_id] = unary_union(geometries)
    
    def _calculate_district_stats(self):
        """Calculate statistics for each district."""
        for district_id in range(self.num_districts):
            district_communes = [idx for idx, dist in self.district_assignments.items() if dist == district_id]
            
            if district_communes:
                district_data = self.commune_data.loc[district_communes]
                
                # Population statistics
                if 'popolazione' in district_data.columns:
                    population = district_data['popolazione'].sum()
                    population_std = district_data['popolazione'].std()
                else:
                    population = len(district_communes)  # Use commune count as proxy
                    population_std = 0
                
                # Voting statistics
                vote_columns = [col for col in district_data.columns 
                              if col not in ['CODICE ISTAT', 'name', 'geometry', 'popolazione', 'CIRCOSCRIZIONE', 'COLLEGIO UNINOMINALE', 'total_votes']]
                
                vote_totals = {}
                for col in vote_columns:
                    vote_totals[col] = district_data[col].sum()
                
                # Compactness (using area/perimeter ratio)
                if district_id in self.district_geometries:
                    area = self.district_geometries[district_id].area
                    perimeter = self.district_geometries[district_id].length
                    compactness = (4 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
                else:
                    compactness = 0
                
                self.district_stats[district_id] = {
                    'population': population,
                    'population_std': population_std,
                    'commune_count': len(district_communes),
                    'vote_totals': vote_totals,
                    'compactness': compactness,
                    'communes': district_communes
                }
    
    def get_district_communes(self, district_id: int) -> List[int]:
        """Get list of commune indices for a district."""
        return [idx for idx, dist in self.district_assignments.items() if dist == district_id]
    
    def get_commune_district(self, commune_idx: int) -> int:
        """Get district ID for a commune."""
        return self.district_assignments.get(commune_idx, -1)
    
    def swap_communes(self, commune1: int, commune2: int) -> bool:
        """
        Swap two communes between districts.
        
        Args:
            commune1: Index of first commune
            commune2: Index of second commune
            
        Returns:
            True if swap was successful, False otherwise
        """
        if commune1 not in self.district_assignments or commune2 not in self.district_assignments:
            return False
        
        # Perform swap
        district1 = self.district_assignments[commune1]
        district2 = self.district_assignments[commune2]
        
        self.district_assignments[commune1] = district2
        self.district_assignments[commune2] = district1
        
        # Update geometries and stats
        self._update_district_geometries()
        self._calculate_district_stats()
        
        return True
    
    def get_score(self, config: OptimizationConfig) -> float:
        """
        Calculate the overall score for this district map.
        
        Args:
            config: Optimization configuration
            
        Returns:
            Overall score (lower is better)
        """
        # Population balance score
        populations = [stats['population'] for stats in self.district_stats.values()]
        population_mean = np.mean(populations)
        population_std = np.std(populations)
        population_score = population_std / population_mean if population_mean > 0 else float('inf')
        
        # Compactness score
        compactness_scores = [stats['compactness'] for stats in self.district_stats.values()]
        avg_compactness = np.mean(compactness_scores)
        compactness_score = 1.0 - avg_compactness  # Invert so lower is better
        
        # Partisan fairness score (simplified)
        # This could be enhanced with more sophisticated partisan fairness metrics
        partisan_score = 0.0
        
        total_score = (config.population_weight * population_score + 
                      config.compactness_weight * compactness_score +
                      config.partisan_fairness_weight * partisan_score)
        
        return total_score


class GerrymanderingOptimizer:
    """Main class for optimizing district boundaries using simulated annealing."""
    
    def __init__(self, voting_data: ItalianVotingData, config: OptimizationConfig):
        """
        Initialize the optimizer.
        
        Args:
            voting_data: Italian voting data
            config: Optimization configuration
        """
        self.voting_data = voting_data
        self.config = config
        self.current_map = None
        self.best_map = None
        self.best_score = float('inf')
        
        self.history = {
            'scores': [],
            'temperatures': [],
            'steps': [],
            'population_stds': [],
            'seat_deviations': []
        }
    
    def initialize_map(self) -> DistrictMap:
        """Initialize a new district map."""
        commune_data = self.voting_data.get_commune_data()
        return DistrictMap(commune_data, self.config.num_districts)
    
    def get_neighbor_solution(self, current_map: DistrictMap) -> DistrictMap:
        """
        Generate a neighbor solution by swapping two communes.
        
        Args:
            current_map: Current district map
            
        Returns:
            New district map with swapped communes
        """
        # Create a copy of the current map
        new_map = DistrictMap(self.voting_data.get_commune_data(), self.config.num_districts)
        new_map.district_assignments = current_map.district_assignments.copy()
        new_map._update_district_geometries()
        new_map._calculate_district_stats()
        
        # Select two random communes from different districts
        commune_indices = list(current_map.district_assignments.keys())
        commune1 = random.choice(commune_indices)
        district1 = current_map.get_commune_district(commune1)
        
        # Find a commune from a different district
        other_communes = [idx for idx in commune_indices 
                         if current_map.get_commune_district(idx) != district1]
        
        if other_communes:
            commune2 = random.choice(other_communes)
            new_map.swap_communes(commune1, commune2)
        
        return new_map
    
    def calculate_seat_deviation(self, district_map: DistrictMap) -> int:
        """
        Calculate seat deviation (simplified metric).
        
        Args:
            district_map: District map to evaluate
            
        Returns:
            Seat deviation score
        """
        # This is a simplified metric - in practice, you'd calculate actual seat allocation
        populations = [stats['population'] for stats in district_map.district_stats.values()]
        population_mean = np.mean(populations)
        
        deviations = [abs(pop - population_mean) / population_mean for pop in populations]
        return sum(1 for dev in deviations if dev > self.config.max_population_deviation)
    
    def optimize(self, save_path: Optional[str] = None) -> DistrictMap:
        """
        Run the simulated annealing optimization.
        
        Args:
            save_path: Optional path to save the best solution
            
        Returns:
            Best district map found
        """
        logger.info("Initializing the map")
        self.current_map = self.initialize_map()
        self.best_map = self.current_map
        self.best_score = self.current_map.get_score(self.config)
        
        temperature = self.config.initial_temperature
        step = 0
        
        logger.info(f"Generated a map with {self.config.num_districts} districts, starting the simulation")
        
        while temperature > self.config.min_temperature and step < self.config.max_steps:
            # Generate neighbor solution
            neighbor_map = self.get_neighbor_solution(self.current_map)
            neighbor_score = neighbor_map.get_score(self.config)
            
            # Calculate acceptance probability
            delta_score = neighbor_score - self.current_map.get_score(self.config)
            acceptance_prob = math.exp(-delta_score / temperature) if temperature > 0 else 0
            
            # Accept or reject the neighbor
            if delta_score < 0 or random.random() < acceptance_prob:
                self.current_map = neighbor_map
                current_score = neighbor_score
            else:
                current_score = self.current_map.get_score(self.config)
            
            # Update best solution
            if current_score < self.best_score:
                self.best_map = self.current_map
                self.best_score = current_score
            
            # Log progress
            if step % 50 == 0:
                seat_deviation = self.calculate_seat_deviation(self.current_map)
                population_std = np.std([stats['population'] for stats in self.current_map.district_stats.values()])
                
                logger.info(f"Step {step}, current temperature: {temperature}, current score: {current_score}")
                logger.info(f"Seat deviation: {seat_deviation}, population std: {population_std}")
                
                # Store history
                self.history['scores'].append(current_score)
                self.history['temperatures'].append(temperature)
                self.history['steps'].append(step)
                self.history['population_stds'].append(population_std)
                self.history['seat_deviations'].append(seat_deviation)
            
            # Cool down
            temperature *= self.config.cooling_rate
            step += 1
        
        # Save best solution if path provided
        if save_path:
            self.save_solution(save_path)
        
        return self.best_map
    
    def save_solution(self, path: str):
        """Save the best solution to a file."""
        solution_data = {
            'best_map': self.best_map,
            'best_score': self.best_score,
            'config': self.config,
            'history': self.history,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(path, 'wb') as f:
            pickle.dump(solution_data, f)
        
        logger.info(f"Solution saved to {path}")
    
    def load_solution(self, path: str):
        """Load a solution from a file."""
        with open(path, 'rb') as f:
            solution_data = pickle.load(f)
        
        self.best_map = solution_data['best_map']
        self.best_score = solution_data['best_score']
        self.config = solution_data['config']
        self.history = solution_data['history']
        
        logger.info(f"Solution loaded from {path}")
    
    def export_results(self, output_dir: str):
        """
        Export optimization results to various formats.
        
        Args:
            output_dir: Directory to save results
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Export district map as GeoJSON
        if self.best_map:
            district_gdf = self.voting_data.get_commune_data().copy()
            district_gdf['district_id'] = district_gdf.index.map(self.best_map.district_assignments)
            district_gdf.to_file(os.path.join(output_dir, 'optimized_districts.geojson'), driver='GeoJSON')
        
        # Export optimization history
        history_df = pd.DataFrame(self.history)
        history_df.to_csv(os.path.join(output_dir, 'optimization_history.csv'), index=False)
        
        # Export district statistics
        if self.best_map:
            stats_data = []
            for district_id, stats in self.best_map.district_stats.items():
                stats_data.append({
                    'district_id': district_id,
                    'population': stats['population'],
                    'commune_count': stats['commune_count'],
                    'compactness': stats['compactness']
                })
            
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_csv(os.path.join(output_dir, 'district_statistics.csv'), index=False)
        
        logger.info(f"Results exported to {output_dir}")


def run_optimization_experiment(
    votes_file: str,
    geo_file: str,
    population_file: Optional[str] = None,
    config: Optional[OptimizationConfig] = None,
    output_dir: str = "results"
) -> GerrymanderingOptimizer:
    """
    Run a complete gerrymandering optimization experiment.
    
    Args:
        votes_file: Path to voting data CSV
        geo_file: Path to geographical data GeoJSON
        population_file: Optional path to population data
        config: Optimization configuration
        output_dir: Directory to save results
        
    Returns:
        Optimizer with results
    """
    if config is None:
        config = OptimizationConfig()
    
    # Load data
    voting_data = ItalianVotingData(votes_file, geo_file, population_file)
    
    # Create optimizer
    optimizer = GerrymanderingOptimizer(voting_data, config)
    
    # Run optimization
    best_map = optimizer.optimize()
    
    # Export results
    optimizer.export_results(output_dir)
    
    return optimizer


if __name__ == "__main__":
    # Example usage
    config = OptimizationConfig(
        num_districts=11,
        initial_temperature=1000.0,
        cooling_rate=0.99,
        max_steps=1000
    )
    
    optimizer = run_optimization_experiment(
        votes_file="politiche_2022_raw_votes.csv",
        geo_file="gerrymandering_base.geojson",
        population_file="POSAS_2024_it_Comuni.csv",
        config=config,
        output_dir="optimization_results"
    )
    
    print(f"Best score achieved: {optimizer.best_score}")
    print(f"Optimization completed successfully!")