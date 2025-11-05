"""
Core gerrymandering algorithm using simulated annealing.
"""
import numpy as np
import geopandas as gpd
import logging
from typing import Dict, List, Tuple, Optional, Callable
import copy
from src.contiguity import is_valid_move, validate_all_districts_contiguous


class GerrymanderOptimizer:
    """Simulated annealing optimizer for electoral district redistricting."""

    def __init__(
        self,
        gdf: gpd.GeoDataFrame,
        n_districts: int,
        target_party: str = None,
        objective_weights: Dict[str, float] = None,
        random_seed: int = None
    ):
        """
        Initialize the optimizer.

        Args:
            gdf: GeoDataFrame with commune geometries and voting data
            n_districts: Number of districts to create
            target_party: Party to favor (None for neutral optimization)
            objective_weights: Weights for different optimization criteria
                - 'population_balance': Weight for population equality
                - 'seat_deviation': Weight for seat proportionality
                - 'partisan_advantage': Weight for partisan advantage
            random_seed: Random seed for reproducibility
        """
        self.gdf = gdf.copy()
        self.n_districts = n_districts
        self.target_party = target_party
        self.random_seed = random_seed

        if random_seed is not None:
            np.random.seed(random_seed)

        # Default weights
        self.weights = {
            'population_balance': 1.0,
            'seat_deviation': 1.0,
            'partisan_advantage': 0.0
        }
        if objective_weights:
            self.weights.update(objective_weights)

        # Build adjacency graph
        self._build_adjacency()

        # Store population data
        if 'population' not in self.gdf.columns:
            logging.warning("No population column found, using uniform weights")
            self.gdf['population'] = 1

        self.history = []

    def _build_adjacency(self):
        """Build adjacency graph of communes."""
        logging.info("Building adjacency graph")
        self.neighbors = {}

        for idx, row in self.gdf.iterrows():
            touching = self.gdf[self.gdf.geometry.touches(row.geometry)].index.tolist()
            self.neighbors[idx] = touching

    def initialize_districts(self) -> np.ndarray:
        """
        Initialize districts by selecting random seed communes and
        assigning others to nearest seed.

        Returns:
            Array of district assignments for each commune
        """
        logging.info(f"Initializing the map")
        logging.info(f"Selecting {self.n_districts} random communes to start the districts")

        # Select random seed communes
        seeds = np.random.choice(
            self.gdf.index,
            size=self.n_districts,
            replace=False
        )

        # Initialize assignments
        districts = np.full(len(self.gdf), -1, dtype=int)
        for i, seed in enumerate(seeds):
            districts[self.gdf.index.get_loc(seed)] = i

        # Assign remaining communes to nearest district seed
        logging.info("Assigning the remaining communes to districts")
        unassigned = [i for i in range(len(self.gdf)) if districts[i] == -1]

        assigned_count = 0
        while unassigned:
            for idx in unassigned[:]:
                commune_geom = self.gdf.iloc[idx].geometry

                # Find nearest assigned commune
                min_dist = float('inf')
                nearest_district = -1

                for assigned_idx in range(len(self.gdf)):
                    if districts[assigned_idx] != -1:
                        dist = commune_geom.distance(self.gdf.iloc[assigned_idx].geometry)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_district = districts[assigned_idx]

                if nearest_district != -1:
                    districts[idx] = nearest_district
                    unassigned.remove(idx)
                    assigned_count += 1

                    if assigned_count % 50 == 0:
                        logging.info(f"Assigned {assigned_count} communes")

        logging.info(f"Finished assigning communes to districts, assigned {len(self.gdf)} communes out of {len(self.gdf)} communes")

        for d in range(self.n_districts):
            count = np.sum(districts == d)
            logging.info(f"District {d} has {count} communes")

        # Validate all districts are contiguous
        is_valid, non_contiguous = validate_all_districts_contiguous(
            districts, self.n_districts, self.neighbors
        )

        if not is_valid:
            logging.warning(f"Initial districts not contiguous: {non_contiguous}")
            logging.warning("This should be rare with nearest-neighbor initialization")
        else:
            logging.info("✓ All initial districts are contiguous")

        logging.info("Finished initializing the map")
        return districts

    def compute_score(
        self,
        districts: np.ndarray,
        return_components: bool = False
    ) -> float:
        """
        Compute objective function score for a district assignment.
        Lower is better.

        Args:
            districts: Array of district assignments
            return_components: If True, return dict of score components

        Returns:
            Total score (or dict of components)
        """
        # Population balance: standard deviation of district populations
        district_pops = []
        for d in range(self.n_districts):
            mask = districts == d
            pop = self.gdf.iloc[np.where(mask)[0]]['population'].sum()
            district_pops.append(pop)

        pop_std = np.std(district_pops)

        # Seat deviation: difference between proportional and actual seats
        seat_dev = 0
        if self.target_party and self.target_party in self.gdf.columns:
            # Calculate what seats each party would win
            party_votes_total = self.gdf[self.target_party].sum()
            total_votes = self.gdf.select_dtypes(include=[np.number]).filter(
                regex='^[A-Z]'
            ).sum(axis=0).sum()

            proportional_seats = (party_votes_total / total_votes) * self.n_districts

            # Count actual seats won (plurality in each district)
            actual_seats = 0
            for d in range(self.n_districts):
                mask = districts == d
                district_votes = self.gdf.iloc[np.where(mask)[0]][self.target_party].sum()

                # Check if target party wins this district
                district_total = 0
                for col in self.gdf.select_dtypes(include=[np.number]).filter(regex='^[A-Z]').columns:
                    other_votes = self.gdf.iloc[np.where(mask)[0]][col].sum()
                    if other_votes > district_votes:
                        break
                else:
                    actual_seats += 1

            seat_dev = abs(actual_seats - proportional_seats)

        # Partisan advantage: maximize (or minimize) seats for target party
        partisan_score = 0
        if self.target_party and self.weights['partisan_advantage'] != 0:
            actual_seats = 0
            for d in range(self.n_districts):
                mask = districts == d
                district_votes = self.gdf.iloc[np.where(mask)[0]][self.target_party].sum()

                # Find max votes for any party in this district
                max_votes = 0
                for col in self.gdf.select_dtypes(include=[np.number]).filter(regex='^[A-Z]').columns:
                    other_votes = self.gdf.iloc[np.where(mask)[0]][col].sum()
                    max_votes = max(max_votes, other_votes)

                if district_votes >= max_votes:
                    actual_seats += 1

            # Negative because we want to maximize seats
            partisan_score = -actual_seats if self.weights['partisan_advantage'] > 0 else actual_seats

        components = {
            'population_std': pop_std,
            'seat_deviation': seat_dev,
            'partisan_advantage': partisan_score
        }

        if return_components:
            return components

        # Combine scores with weights
        total_score = (
            self.weights['population_balance'] * pop_std +
            self.weights['seat_deviation'] * seat_dev +
            self.weights['partisan_advantage'] * abs(partisan_score)
        )

        return total_score

    def propose_move(self, districts: np.ndarray) -> Tuple[np.ndarray, int, int, int]:
        """
        Propose a new district assignment by moving one commune to a neighboring district.
        Only accepts moves that preserve contiguity of both districts.

        Returns:
            new_districts, commune_idx, old_district, new_district
        """
        # Try up to 100 times to find a valid contiguous move
        for attempt in range(100):
            new_districts = districts.copy()

            # Select random commune
            commune_idx = np.random.randint(len(self.gdf))
            old_district = districts[commune_idx]
            commune_map_idx = self.gdf.index[commune_idx]

            # Find neighboring districts
            neighbors = self.neighbors[commune_map_idx]
            if not neighbors:
                continue

            neighbor_districts = set()
            for neighbor_idx in neighbors:
                neighbor_loc = self.gdf.index.get_loc(neighbor_idx)
                neighbor_districts.add(districts[neighbor_loc])

            neighbor_districts.discard(old_district)

            if not neighbor_districts:
                continue

            # Move to random neighboring district
            new_district = np.random.choice(list(neighbor_districts))
            new_districts[commune_idx] = new_district

            # Check if move preserves contiguity
            if is_valid_move(new_districts, commune_idx, old_district,
                           new_district, self.neighbors, commune_map_idx):
                return new_districts, commune_idx, old_district, new_district

        # If no valid move found after 100 attempts, return unchanged
        return districts, commune_idx, old_district, old_district

    def optimize(
        self,
        initial_temp: float = 1000.0,
        final_temp: float = 0.01,
        cooling_rate: float = 0.99,
        steps: int = 1000,
        save_frequency: int = 50
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Run simulated annealing optimization.

        Args:
            initial_temp: Starting temperature
            final_temp: Ending temperature
            cooling_rate: Temperature decay rate
            steps: Number of optimization steps
            save_frequency: How often to save state to history

        Returns:
            best_districts, history
        """
        # Initialize
        current_districts = self.initialize_districts()
        current_score = self.compute_score(current_districts)

        best_districts = current_districts.copy()
        best_score = current_score

        temperature = initial_temp

        logging.info(f"Generated a map with {self.n_districts} districts, starting the simulation")
        logging.info(f"Step 0, current temperature: {temperature}, current score: {current_score}")

        # Track history
        self.history = []

        for step in range(steps):
            # Propose move
            new_districts, _, old_d, new_d = self.propose_move(current_districts)

            if old_d == new_d:
                continue

            # Evaluate
            new_score = self.compute_score(new_districts)
            delta = new_score - current_score

            # Accept or reject
            if delta < 0 or np.random.random() < np.exp(-delta / temperature):
                current_districts = new_districts
                current_score = new_score

                if current_score < best_score:
                    best_districts = current_districts.copy()
                    best_score = current_score

            # Cool down
            temperature *= cooling_rate

            # Log progress
            if step % save_frequency == 0:
                components = self.compute_score(current_districts, return_components=True)
                logging.info(
                    f"Step {step}, current temperature: {temperature}, current score: {current_score}"
                )
                logging.info(
                    f"Seat deviation: {components['seat_deviation']:.0f}, "
                    f"population std: {components['population_std']:.2f}"
                )

                # Save to history
                self.history.append({
                    'step': step,
                    'temperature': temperature,
                    'score': current_score,
                    'districts': current_districts.copy(),
                    **components
                })

            if temperature < final_temp:
                break

        logging.info(f"Optimization complete. Best score: {best_score}")
        return best_districts, self.history
