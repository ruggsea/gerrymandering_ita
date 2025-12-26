"""
Clean gerrymandering simulator focused on speed and results.
Core business: run many simulations fast with good heuristics.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import pickle
from pathlib import Path


class GerrymanderSimulator:
    """Fast gerrymandering simulation engine."""

    def __init__(self, data_file: str = 'politiche_2022_liste_camera_comuni.csv'):
        """Load and prepare voting data."""
        # Load data
        df = pd.read_csv(data_file)

        # Define coalitions
        self.left_parties = [
            'PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA',
            '+EUROPA',
            'ALLEANZA VERDI E SINISTRA',
            'IMPEGNO CIVICO LUIGI DI MAIO - CENTRO DEMOCRATICO'
        ]
        self.right_parties = [
            'FRATELLI D\'ITALIA CON GIORGIA MELONI',
            'LEGA PER SALVINI PREMIER',
            'FORZA ITALIA',
            'NOI MODERATI/LUPI - TOTI - BRUGNARO - UDC'
        ]
        self.m5s_parties = ['MOVIMENTO 5 STELLE']

        # Calculate votes per municipality
        self.municipalities = []
        self.left_votes = []
        self.right_votes = []
        self.m5s_votes = []

        for idx, row in df.iterrows():
            left = sum(row[p] if pd.notna(row[p]) else 0 for p in self.left_parties)
            right = sum(row[p] if pd.notna(row[p]) else 0 for p in self.right_parties)
            m5s = sum(row[p] if pd.notna(row[p]) else 0 for p in self.m5s_parties)

            self.municipalities.append(row['name'])
            self.left_votes.append(left)
            self.right_votes.append(right)
            self.m5s_votes.append(m5s)

        # Convert to numpy for speed
        self.left_votes = np.array(self.left_votes)
        self.right_votes = np.array(self.right_votes)
        self.m5s_votes = np.array(self.m5s_votes)
        self.total_votes = self.left_votes + self.right_votes + self.m5s_votes

        self.n_municipalities = len(self.municipalities)
        self.n_districts = 139

        print(f"Loaded {self.n_municipalities} municipalities")
        print(f"Target: {self.n_districts} districts")
        print(f"Total votes: LEFT={self.left_votes.sum():,.0f} RIGHT={self.right_votes.sum():,.0f} M5S={self.m5s_votes.sum():,.0f}")

    def compute_utility(self, assignment: np.ndarray, target: str = 'right',
                       return_details: bool = False) -> Tuple[int, Dict]:
        """
        Compute utility = number of seats won by target coalition.

        This is the key metric for gerrymandering:
        - We want to maximize seats for our target
        - Pack opponent votes into few districts
        - Crack our votes efficiently across many districts

        Returns: (utility_value, detailed_results)
        """
        # Vectorized computation for speed
        district_left = np.zeros(self.n_districts)
        district_right = np.zeros(self.n_districts)
        district_m5s = np.zeros(self.n_districts)

        # Accumulate votes by district (vectorized)
        np.add.at(district_left, assignment, self.left_votes)
        np.add.at(district_right, assignment, self.right_votes)
        np.add.at(district_m5s, assignment, self.m5s_votes)

        # Determine winners (vectorized)
        right_wins = (district_right > district_left) & (district_right > district_m5s)
        left_wins = (district_left > district_right) & (district_left > district_m5s)
        m5s_wins = ~right_wins & ~left_wins

        right_seats = right_wins.sum()
        left_seats = left_wins.sum()
        m5s_seats = m5s_wins.sum()

        # Utility is seats won by target
        if target == 'right':
            utility = int(right_seats)
        elif target == 'left':
            utility = int(left_seats)
        else:
            utility = int(m5s_seats)

        if return_details:
            results = {
                'left_seats': int(left_seats),
                'right_seats': int(right_seats),
                'm5s_seats': int(m5s_seats),
                'district_results': []
            }

            for d in range(self.n_districts):
                if right_wins[d]:
                    winner = 'right'
                elif left_wins[d]:
                    winner = 'left'
                else:
                    winner = 'm5s'

                results['district_results'].append({
                    'district': d,
                    'left': district_left[d],
                    'right': district_right[d],
                    'm5s': district_m5s[d],
                    'winner': winner,
                    'n_munis': (assignment == d).sum()
                })

            return utility, results
        else:
            # Minimal results for speed
            results = {
                'left_seats': int(left_seats),
                'right_seats': int(right_seats),
                'm5s_seats': int(m5s_seats)
            }
            return utility, results

    def random_assignment(self, seed: int = None) -> np.ndarray:
        """Create random district assignment."""
        if seed is not None:
            np.random.seed(seed)

        # Ensure each district gets at least some municipalities
        assignment = np.random.randint(0, self.n_districts, self.n_municipalities)
        return assignment

    def balanced_random_assignment(self, seed: int = None) -> np.ndarray:
        """Create balanced random assignment (each district gets similar number of municipalities)."""
        if seed is not None:
            np.random.seed(seed)

        munis_per_district = self.n_municipalities // self.n_districts
        assignment = np.repeat(np.arange(self.n_districts), munis_per_district)

        # Handle remainder
        remainder = self.n_municipalities - len(assignment)
        if remainder > 0:
            assignment = np.concatenate([assignment, np.random.randint(0, self.n_districts, remainder)])

        # Shuffle
        np.random.shuffle(assignment)
        return assignment

    def strategic_pack_assignment(self, target: str, seed: int = None) -> np.ndarray:
        """
        Create strategic packing assignment for minority coalition.

        Strategy:
        1. Identify municipalities where target coalition is strongest (relative to total)
        2. Pack opponent's votes into a few high-vote districts
        3. Spread target's votes across many districts efficiently
        """
        if seed is not None:
            np.random.seed(seed)

        # Calculate vote shares for each municipality
        if target == 'left':
            target_votes = self.left_votes
            opponent_votes = self.right_votes + self.m5s_votes
        else:
            target_votes = self.right_votes
            opponent_votes = self.left_votes + self.m5s_votes

        # Get relative strength (target share)
        total = target_votes + opponent_votes + 1  # Avoid division by zero
        target_share = target_votes / total

        # Sort municipalities by target share (descending)
        sorted_indices = np.argsort(-target_share)

        # Create assignment
        assignment = np.zeros(self.n_municipalities, dtype=int)
        munis_per_district = self.n_municipalities // self.n_districts

        # Distribute sorted municipalities across districts
        # This naturally packs opponents into some districts and spreads target across others
        for i, muni_idx in enumerate(sorted_indices):
            district = i // munis_per_district
            if district >= self.n_districts:
                district = self.n_districts - 1
            assignment[muni_idx] = district

        return assignment

    def optimize_greedy(self, initial_assignment: np.ndarray, target: str,
                       n_iterations: int = 10000, verbose: bool = True) -> Tuple[np.ndarray, int, Dict]:
        """
        Optimize assignment using greedy local search with random swaps.

        Simple but effective:
        1. Try random swaps of municipalities between districts
        2. Accept if utility improves
        3. Repeat many times
        """
        current_assignment = initial_assignment.copy()
        current_utility, current_results = self.compute_utility(current_assignment, target)

        best_assignment = current_assignment.copy()
        best_utility = current_utility
        best_results = current_results

        improvements = 0

        for iteration in range(n_iterations):
            # Try random swap
            muni_idx = np.random.randint(0, self.n_municipalities)
            new_district = np.random.randint(0, self.n_districts)

            # Make swap
            old_district = current_assignment[muni_idx]
            if old_district == new_district:
                continue

            current_assignment[muni_idx] = new_district

            # Evaluate
            new_utility, new_results = self.compute_utility(current_assignment, target)

            # Accept if improves
            if new_utility > best_utility:
                best_assignment = current_assignment.copy()
                best_utility = new_utility
                best_results = new_results
                improvements += 1

                if verbose and improvements % 10 == 0:
                    print(f"  Iter {iteration}: New best = {best_utility} seats for {target.upper()}")
            elif new_utility < current_utility:
                # Revert if worse
                current_assignment[muni_idx] = old_district
            else:
                # Accept if same (exploration)
                current_utility = new_utility
                current_results = new_results

        if verbose:
            print(f"Optimization complete: {improvements} improvements found")

        return best_assignment, best_utility, best_results

    def optimize_simulated_annealing(self, initial_assignment: np.ndarray, target: str,
                                    n_iterations: int = 50000, temp_init: float = 20.0,
                                    temp_final: float = 0.001, verbose: bool = True) -> Tuple[np.ndarray, int, Dict]:
        """
        Optimize using simulated annealing to escape local optima.

        Accepts worse moves with probability exp(-delta/T) where:
        - delta = utility loss
        - T = temperature (decreases over time)

        This is crucial for minority coalitions that need to escape local optima.
        """
        current_assignment = initial_assignment.copy()
        current_utility, current_results = self.compute_utility(current_assignment, target)

        best_assignment = current_assignment.copy()
        best_utility = current_utility
        best_results = current_results

        improvements = 0
        accepts = 0

        for iteration in range(n_iterations):
            # Cooling schedule: exponential decay
            progress = iteration / n_iterations
            temp = temp_init * ((temp_final / temp_init) ** progress)

            # Try random swap
            muni_idx = np.random.randint(0, self.n_municipalities)
            new_district = np.random.randint(0, self.n_districts)

            # Make swap
            old_district = current_assignment[muni_idx]
            if old_district == new_district:
                continue

            current_assignment[muni_idx] = new_district

            # Evaluate
            new_utility, new_results = self.compute_utility(current_assignment, target)

            # Compute utility change
            delta = new_utility - current_utility

            # Accept if improves OR with probability based on temperature
            if delta > 0:
                # Improvement
                current_utility = new_utility
                current_results = new_results
                accepts += 1

                if new_utility > best_utility:
                    best_assignment = current_assignment.copy()
                    best_utility = new_utility
                    best_results = new_results
                    improvements += 1

                    if verbose and improvements % 5 == 0:
                        print(f"  Iter {iteration}: New best = {best_utility} seats (temp={temp:.3f})")
            elif np.random.random() < np.exp(delta / temp):
                # Accept worse move for exploration
                current_utility = new_utility
                current_results = new_results
                accepts += 1
            else:
                # Reject
                current_assignment[muni_idx] = old_district

        if verbose:
            print(f"Annealing complete: {improvements} improvements, {accepts} total accepts")

        return best_assignment, best_utility, best_results

    def run_simulation(self, target: str, n_iterations: int = 10000,
                      seed: int = None, verbose: bool = True, use_annealing: bool = False) -> Tuple[np.ndarray, Dict]:
        """
        Run complete simulation:
        1. Initialize assignment (strategic for minority, random for majority)
        2. Optimize for target coalition
        3. Return best result
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"SIMULATION: Maximize {target.upper()} seats")
            print(f"{'='*60}")

        # Initialize with strategic packing for minority coalition
        if target == 'left':
            assignment = self.strategic_pack_assignment(target, seed)
            if verbose:
                print("Using strategic packing initialization for minority coalition")
        else:
            assignment = self.balanced_random_assignment(seed)

        initial_utility, initial_results = self.compute_utility(assignment, target)

        if verbose:
            print(f"Initial: LEFT={initial_results['left_seats']} RIGHT={initial_results['right_seats']} M5S={initial_results['m5s_seats']}")

        # Optimize: use simulated annealing for better exploration
        if use_annealing or target == 'left':
            best_assignment, best_utility, best_results = self.optimize_simulated_annealing(
                assignment, target, n_iterations, verbose=verbose
            )
        else:
            best_assignment, best_utility, best_results = self.optimize_greedy(
                assignment, target, n_iterations, verbose
            )

        if verbose:
            print(f"\nFinal: LEFT={best_results['left_seats']} RIGHT={best_results['right_seats']} M5S={best_results['m5s_seats']}")
            print(f"Target ({target.upper()}) achieved: {best_utility} seats")

        # Get detailed results for final output
        _, final_results = self.compute_utility(best_assignment, target, return_details=True)
        return best_assignment, final_results

    def sweep_until_goal(self, target: str, goal_seats: int, max_attempts: int = 100,
                        n_iterations: int = 10000, verbose: bool = True):
        """
        Run simulations until we achieve goal.

        Args:
            target: 'left' or 'right'
            goal_seats: number of seats to achieve
            max_attempts: maximum simulation attempts
            n_iterations: iterations per simulation
        """
        print(f"\n{'='*70}")
        print(f"GOAL: Achieve {goal_seats} seats for {target.upper()}")
        print(f"{'='*70}")

        for attempt in range(max_attempts):
            print(f"\nAttempt {attempt + 1}/{max_attempts}")

            assignment, results = self.run_simulation(
                target,
                n_iterations=n_iterations,
                seed=attempt,
                verbose=False
            )

            if target == 'right':
                achieved = results['right_seats']
            else:
                achieved = results['left_seats']

            print(f"  Result: LEFT={results['left_seats']} RIGHT={results['right_seats']} M5S={results['m5s_seats']}")
            print(f"  {target.upper()} seats: {achieved}/{goal_seats}")

            if achieved >= goal_seats:
                print(f"\n🎯 GOAL ACHIEVED! {target.upper()} won {achieved} seats!")

                # Save result
                output_file = f"gerrymander_{target}_{achieved}seats_attempt{attempt}.pkl"
                self.save_result(output_file, assignment, results)
                print(f"Saved to: {output_file}")

                return assignment, results

        print(f"\n❌ Goal not achieved after {max_attempts} attempts")
        return None, None

    def save_result(self, filename: str, assignment: np.ndarray, results: Dict):
        """Save simulation result."""
        data = {
            'assignment': assignment,
            'results': results,
            'municipalities': self.municipalities
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)


def main():
    """Main entry point."""
    sim = GerrymanderSimulator()

    print("\n" + "="*70)
    print("IRL 2022 RESULTS")
    print("="*70)
    print("LEFT: 7 seats")
    print("RIGHT: 126 seats")
    print("M5S: 6 seats")
    print("TOTAL: 139 seats")

    # Goal 1: Right wins 138 seats (all but one)
    print("\n\n" + "#"*70)
    print("# GOAL 1: Right-wing wins 138/139 seats (all but one)")
    print("#"*70)
    sim.sweep_until_goal('right', 138, max_attempts=10, n_iterations=10000)

    # Goal 2: Left wins 8+ seats (one more than IRL)
    print("\n\n" + "#"*70)
    print("# GOAL 2: Left-wing wins 8+ seats (one more than IRL)")
    print("#"*70)
    # Use more iterations for left since it needs simulated annealing
    sim.sweep_until_goal('left', 8, max_attempts=50, n_iterations=200000)


if __name__ == '__main__':
    main()
