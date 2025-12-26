"""
Emilia-Romagna gerrymandering with VALID, CONTIGUOUS districts.
Core business: Fast simulations with geographic constraints.
"""
import pandas as pd
import geopandas as gpd
import numpy as np
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque
import pickle


class EmiliaGerrymander:
    """Gerrymandering for Emilia-Romagna with contiguity constraints."""

    def __init__(self):
        """Load Emilia-Romagna data with geometry."""
        print("Loading Emilia-Romagna data...")

        # Load votes from CSV
        df = pd.read_csv('politiche_2022_liste_camera_comuni.csv')
        self.df = df[df['CIRCOSCRIZIONE'] == 'EMILIA-ROMAGNA'].copy()

        # Load geometry from GeoJSON
        gdf = gpd.read_file('comuni_italiani_trend_liste_2022_2024.geojson')
        self.gdf = gdf[gdf['CIRCOSCRIZIONE'] == 'EMILIA-ROMAGNA'].copy()

        # Merge on municipality name (keep as GeoDataFrame)
        gdf_subset = self.gdf[['name', 'geometry']]
        self.data = gdf_subset.merge(
            self.df,
            on='name',
            how='inner'
        )

        # Set the geometry column (merge may rename it to geometry_x)
        if 'geometry_x' in self.data.columns:
            self.data = self.data.set_geometry('geometry_x')
        elif 'geometry' not in self.data.columns and isinstance(self.data, gpd.GeoDataFrame):
            # Find the geometry column
            geom_cols = [c for c in self.data.columns if self.data[c].dtype == 'geometry']
            if geom_cols:
                self.data = self.data.set_geometry(geom_cols[0])

        # Define coalitions
        self.left_parties = [
            'PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA',
            '+EUROPA', 'ALLEANZA VERDI E SINISTRA'
        ]
        self.right_parties = [
            'FRATELLI D\'ITALIA CON GIORGIA MELONI',
            'LEGA PER SALVINI PREMIER',
            'FORZA ITALIA',
            'NOI MODERATI/LUPI - TOTI - BRUGNARO - UDC'
        ]
        self.m5s_parties = ['MOVIMENTO 5 STELLE']

        # Calculate votes per municipality
        self.municipalities = list(self.data['name'])
        self.left_votes = np.array([
            self.data.iloc[i][self.left_parties].sum()
            for i in range(len(self.data))
        ])
        self.right_votes = np.array([
            self.data.iloc[i][self.right_parties].sum()
            for i in range(len(self.data))
        ])
        self.m5s_votes = np.array([
            self.data.iloc[i][self.m5s_parties].sum()
            for i in range(len(self.data))
        ])

        self.n_municipalities = len(self.municipalities)
        self.n_districts = 11

        # Build adjacency graph from geometry
        print("Building adjacency graph...")
        self.adjacency = self._build_adjacency()

        print(f"\nLoaded {self.n_municipalities} municipalities")
        print(f"Target: {self.n_districts} districts")
        print(f"LEFT={self.left_votes.sum():,.0f} RIGHT={self.right_votes.sum():,.0f} M5S={self.m5s_votes.sum():,.0f}")
        print(f"Adjacency: avg {np.mean([len(v) for v in self.adjacency.values()]):.1f} neighbors/municipality")

    def _build_adjacency(self) -> Dict[int, Set[int]]:
        """Build adjacency graph: which municipalities touch each other."""
        adjacency = defaultdict(set)

        # Use .geometry attribute instead of column access
        geometries = list(self.data.geometry)

        for i in range(self.n_municipalities):
            for j in range(i + 1, self.n_municipalities):
                # Check if geometries touch or intersect
                if geometries[i].touches(geometries[j]) or geometries[i].intersects(geometries[j]):
                    adjacency[i].add(j)
                    adjacency[j].add(i)

        return adjacency

    def is_contiguous(self, assignment: np.ndarray, district: int) -> bool:
        """Check if a district is geographically contiguous."""
        municipalities = np.where(assignment == district)[0]

        if len(municipalities) == 0:
            return True
        if len(municipalities) == 1:
            return True

        # BFS to check connectivity
        visited = set()
        queue = deque([municipalities[0]])
        visited.add(municipalities[0])

        while queue:
            current = queue.popleft()
            for neighbor in self.adjacency[current]:
                if neighbor not in visited and assignment[neighbor] == district:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(municipalities)

    def all_districts_contiguous(self, assignment: np.ndarray) -> bool:
        """Check if ALL districts are contiguous."""
        for d in range(self.n_districts):
            if not self.is_contiguous(assignment, d):
                return False
        return True

    def compute_utility(self, assignment: np.ndarray, target: str = 'right') -> Tuple[int, Dict]:
        """Compute utility = seats won by target."""
        district_left = np.zeros(self.n_districts)
        district_right = np.zeros(self.n_districts)
        district_m5s = np.zeros(self.n_districts)

        np.add.at(district_left, assignment, self.left_votes)
        np.add.at(district_right, assignment, self.right_votes)
        np.add.at(district_m5s, assignment, self.m5s_votes)

        right_wins = (district_right > district_left) & (district_right > district_m5s)
        left_wins = (district_left > district_right) & (district_left > district_m5s)

        results = {
            'left_seats': int(left_wins.sum()),
            'right_seats': int(right_wins.sum()),
            'm5s_seats': int((~right_wins & ~left_wins).sum())
        }

        if target == 'right':
            utility = results['right_seats']
        elif target == 'left':
            utility = results['left_seats']
        else:
            utility = results['m5s_seats']

        return utility, results

    def initialize_contiguous(self, seed: int = None) -> np.ndarray:
        """Initialize with contiguous districts using region growing."""
        if seed is not None:
            np.random.seed(seed)

        assignment = np.full(self.n_municipalities, -1)
        unassigned = set(range(self.n_municipalities))

        # Random seeds for each district
        seeds = np.random.choice(list(unassigned), self.n_districts, replace=False)

        for d, seed_muni in enumerate(seeds):
            assignment[seed_muni] = d
            unassigned.remove(seed_muni)

        # Grow districts from seeds
        while unassigned:
            # For each district, find unassigned neighbors
            grown = False
            for d in range(self.n_districts):
                district_munis = np.where(assignment == d)[0]

                # Find unassigned neighbors
                candidates = set()
                for muni in district_munis:
                    for neighbor in self.adjacency[muni]:
                        if neighbor in unassigned:
                            candidates.add(neighbor)

                if candidates:
                    # Pick random candidate
                    new_muni = np.random.choice(list(candidates))
                    assignment[new_muni] = d
                    unassigned.remove(new_muni)
                    grown = True
                    break

            if not grown:
                # Stuck - assign remaining to nearest district
                for muni in list(unassigned):
                    # Find any neighbor's district
                    for neighbor in self.adjacency[muni]:
                        if assignment[neighbor] != -1:
                            assignment[muni] = assignment[neighbor]
                            break
                    if assignment[muni] != -1:
                        unassigned.remove(muni)

        return assignment

    def optimize_contiguous(self, initial_assignment: np.ndarray, target: str,
                           n_iterations: int = 10000, verbose: bool = True) -> Tuple[np.ndarray, int, Dict]:
        """
        Optimize with contiguity constraint.

        Strategy: Only swap municipalities between districts if:
        1. Both districts remain contiguous after swap
        2. Utility improves
        """
        current = initial_assignment.copy()
        current_utility, current_results = self.compute_utility(current, target)

        best = current.copy()
        best_utility = current_utility
        best_results = current_results

        improvements = 0
        attempts = 0

        for iteration in range(n_iterations):
            # Try swapping a municipality to a neighboring district
            muni = np.random.randint(0, self.n_municipalities)
            old_district = current[muni]

            # Find neighboring districts (districts of adjacent municipalities)
            neighbor_districts = set()
            for neighbor in self.adjacency[muni]:
                if current[neighbor] != old_district:
                    neighbor_districts.add(current[neighbor])

            if not neighbor_districts:
                continue

            new_district = np.random.choice(list(neighbor_districts))

            # Try swap
            current[muni] = new_district
            attempts += 1

            # Check contiguity
            if self.is_contiguous(current, old_district) and self.is_contiguous(current, new_district):
                # Valid swap - evaluate utility
                new_utility, new_results = self.compute_utility(current, target)

                if new_utility > best_utility:
                    best = current.copy()
                    best_utility = new_utility
                    best_results = new_results
                    improvements += 1

                    if verbose and improvements % 5 == 0:
                        print(f"  Iter {iteration}: {best_utility} seats (LEFT={best_results['left_seats']}, RIGHT={best_results['right_seats']})")
                elif new_utility < current_utility:
                    # Revert
                    current[muni] = old_district
                else:
                    # Accept same utility for exploration
                    current_utility = new_utility
                    current_results = new_results
            else:
                # Invalid - revert
                current[muni] = old_district

        if verbose:
            print(f"Optimization: {improvements} improvements from {attempts} valid attempts")

        return best, best_utility, best_results

    def run_simulation(self, target: str, n_iterations: int = 10000,
                      seed: int = None, verbose: bool = True) -> Tuple[np.ndarray, Dict]:
        """Run simulation with contiguous districts."""
        if verbose:
            print(f"\n{'='*60}")
            print(f"EMILIA-ROMAGNA: Maximize {target.upper()} seats")
            print(f"{'='*60}")

        # Initialize with contiguous districts
        assignment = self.initialize_contiguous(seed)

        # Verify contiguity
        if not self.all_districts_contiguous(assignment):
            raise ValueError("Initialization failed to create contiguous districts")

        initial_utility, initial_results = self.compute_utility(assignment, target)

        if verbose:
            print(f"Initial: LEFT={initial_results['left_seats']} RIGHT={initial_results['right_seats']} M5S={initial_results['m5s_seats']}")

        # Optimize
        best, best_utility, best_results = self.optimize_contiguous(
            assignment, target, n_iterations, verbose
        )

        # Final verification
        if not self.all_districts_contiguous(best):
            raise ValueError("Optimization broke contiguity!")

        if verbose:
            print(f"Final: LEFT={best_results['left_seats']} RIGHT={best_results['right_seats']} M5S={best_results['m5s_seats']}")
            print(f"✓ All districts contiguous and valid")

        return best, best_results

    def sweep_until_goal(self, target: str, goal_seats: int, max_attempts: int = 50,
                        n_iterations: int = 10000):
        """Run until goal achieved."""
        print(f"\n{'='*70}")
        print(f"GOAL: {target.upper()} wins {goal_seats}+ seats (IRL: LEFT=1, RIGHT=10)")
        print(f"{'='*70}")

        for attempt in range(max_attempts):
            print(f"\nAttempt {attempt + 1}/{max_attempts}")

            assignment, results = self.run_simulation(
                target, n_iterations, seed=attempt, verbose=False
            )

            achieved = results[f'{target}_seats']
            print(f"  Result: LEFT={results['left_seats']} RIGHT={results['right_seats']} M5S={results['m5s_seats']}")
            print(f"  {target.upper()}: {achieved}/{goal_seats}")

            if achieved >= goal_seats:
                print(f"\n🎯 GOAL ACHIEVED! {target.upper()} won {achieved} seats with VALID districts!")

                output = f"emilia_{target}_{achieved}seats_attempt{attempt}.pkl"
                with open(output, 'wb') as f:
                    pickle.dump({
                        'assignment': assignment,
                        'results': results,
                        'municipalities': self.municipalities
                    }, f)
                print(f"Saved: {output}")

                return assignment, results

        print(f"\n❌ Goal not achieved after {max_attempts} attempts")
        return None, None


def main():
    sim = EmiliaGerrymander()

    print("\n" + "="*70)
    print("IRL 2022: LEFT=1 (Bologna), RIGHT=10")
    print("="*70)

    # Try to maximize right-wing
    print("\n\n" + "#"*70)
    print("# GOAL: RIGHT wins all 11 seats")
    print("#"*70)
    sim.sweep_until_goal('right', 11, max_attempts=20, n_iterations=50000)

    # Try to maximize left-wing
    print("\n\n" + "#"*70)
    print("# GOAL: LEFT wins 2+ seats (one more than IRL)")
    print("#"*70)
    sim.sweep_until_goal('left', 2, max_attempts=20, n_iterations=50000)


if __name__ == '__main__':
    main()
