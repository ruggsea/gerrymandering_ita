"""
Additional optimization algorithms for gerrymandering.
"""
import numpy as np
import geopandas as gpd
import logging
from typing import Dict, List, Tuple
from src.gerrymander import GerrymanderOptimizer


class GreedyOptimizer(GerrymanderOptimizer):
    """Greedy algorithm - always accept improving moves."""

    def optimize(
        self,
        initial_temp: float = None,
        final_temp: float = None,
        cooling_rate: float = None,
        steps: int = 1000,
        save_frequency: int = 50
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Run greedy optimization (always accept improvements).
        Temperature parameters are ignored.
        """
        current_districts = self.initialize_districts()
        current_score = self.compute_score(current_districts)

        best_districts = current_districts.copy()
        best_score = current_score

        logging.info(f"Generated a map with {self.n_districts} districts, starting greedy optimization")
        logging.info(f"Step 0, current score: {current_score}")

        self.history = []
        improvements = 0

        for step in range(steps):
            new_districts, _, old_d, new_d = self.propose_move(current_districts)

            if old_d == new_d:
                continue

            new_score = self.compute_score(new_districts)

            # Greedy: only accept if better
            if new_score < current_score:
                current_districts = new_districts
                current_score = new_score
                improvements += 1

                if current_score < best_score:
                    best_districts = current_districts.copy()
                    best_score = current_score

            if step % save_frequency == 0:
                components = self.compute_score(current_districts, return_components=True)
                logging.info(
                    f"Step {step}, current score: {current_score}, improvements: {improvements}"
                )
                logging.info(
                    f"Seat deviation: {components['seat_deviation']:.0f}, "
                    f"population std: {components['population_std']:.2f}"
                )

                self.history.append({
                    'step': step,
                    'temperature': 0.0,
                    'score': current_score,
                    'districts': current_districts.copy(),
                    **components
                })

        logging.info(f"Greedy optimization complete. Best score: {best_score}, Total improvements: {improvements}")
        return best_districts, self.history


class HillClimbingOptimizer(GerrymanderOptimizer):
    """Hill climbing with random restarts."""

    def optimize(
        self,
        initial_temp: float = None,
        final_temp: float = None,
        cooling_rate: float = None,
        steps: int = 1000,
        save_frequency: int = 50,
        restart_frequency: int = 200
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Run hill climbing with random restarts.
        """
        best_districts = None
        best_score = float('inf')

        logging.info(f"Starting hill climbing with restarts every {restart_frequency} steps")

        self.history = []
        restarts = 0

        for restart in range(0, steps, restart_frequency):
            # Random restart
            current_districts = self.initialize_districts()
            current_score = self.compute_score(current_districts)
            restarts += 1

            logging.info(f"Restart {restarts}, initial score: {current_score}")

            improvements = 0
            stuck_count = 0

            for step in range(restart, min(restart + restart_frequency, steps)):
                new_districts, _, old_d, new_d = self.propose_move(current_districts)

                if old_d == new_d:
                    continue

                new_score = self.compute_score(new_districts)

                if new_score < current_score:
                    current_districts = new_districts
                    current_score = new_score
                    improvements += 1
                    stuck_count = 0

                    if current_score < best_score:
                        best_districts = current_districts.copy()
                        best_score = current_score
                else:
                    stuck_count += 1

                # Early restart if stuck
                if stuck_count > 50:
                    logging.info(f"Step {step}, stuck for 50 iterations, restarting early")
                    break

                if step % save_frequency == 0:
                    components = self.compute_score(current_districts, return_components=True)
                    logging.info(
                        f"Step {step}, current score: {current_score}"
                    )
                    logging.info(
                        f"Seat deviation: {components['seat_deviation']:.0f}, "
                        f"population std: {components['population_std']:.2f}"
                    )

                    self.history.append({
                        'step': step,
                        'temperature': 0.0,
                        'score': current_score,
                        'districts': current_districts.copy(),
                        **components
                    })

        logging.info(f"Hill climbing complete. Best score: {best_score}, Restarts: {restarts}")
        return best_districts, self.history


class RandomWalkOptimizer(GerrymanderOptimizer):
    """Random walk baseline - accept all moves."""

    def optimize(
        self,
        initial_temp: float = None,
        final_temp: float = None,
        cooling_rate: float = None,
        steps: int = 1000,
        save_frequency: int = 50
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Random walk - accept all proposed moves.
        """
        current_districts = self.initialize_districts()
        current_score = self.compute_score(current_districts)

        best_districts = current_districts.copy()
        best_score = current_score

        logging.info(f"Generated a map with {self.n_districts} districts, starting random walk")
        logging.info(f"Step 0, current score: {current_score}")

        self.history = []

        for step in range(steps):
            new_districts, _, old_d, new_d = self.propose_move(current_districts)

            if old_d == new_d:
                continue

            # Random walk: always accept
            current_districts = new_districts
            current_score = self.compute_score(current_districts)

            if current_score < best_score:
                best_districts = current_districts.copy()
                best_score = current_score

            if step % save_frequency == 0:
                components = self.compute_score(current_districts, return_components=True)
                logging.info(
                    f"Step {step}, current score: {current_score}"
                )
                logging.info(
                    f"Seat deviation: {components['seat_deviation']:.0f}, "
                    f"population std: {components['population_std']:.2f}"
                )

                self.history.append({
                    'step': step,
                    'temperature': 0.0,
                    'score': current_score,
                    'districts': current_districts.copy(),
                    **components
                })

        logging.info(f"Random walk complete. Best score: {best_score}")
        return best_districts, self.history


class ConstrainedOptimizer(GerrymanderOptimizer):
    """
    Constrained optimization: maximize partisan gain subject to population constraint.
    Uses two-phase approach: first satisfy constraint, then optimize partisan.
    """

    def __init__(self, *args, population_constraint: float = 0.15, **kwargs):
        """
        Args:
            population_constraint: Maximum allowed population std deviation (as fraction of mean)
        """
        super().__init__(*args, **kwargs)
        self.population_constraint = population_constraint

    def is_feasible(self, districts: np.ndarray) -> bool:
        """Check if district assignment satisfies population constraint."""
        district_pops = []
        for d in range(self.n_districts):
            mask = districts == d
            pop = self.gdf.iloc[np.where(mask)[0]]['population'].sum()
            district_pops.append(pop)

        mean_pop = np.mean(district_pops)
        std_pop = np.std(district_pops)

        return (std_pop / mean_pop) <= self.population_constraint

    def optimize(
        self,
        initial_temp: float = 1000.0,
        final_temp: float = 0.01,
        cooling_rate: float = 0.99,
        steps: int = 1000,
        save_frequency: int = 50
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        Two-phase optimization:
        Phase 1: Achieve population constraint
        Phase 2: Maximize partisan gain while maintaining constraint
        """
        current_districts = self.initialize_districts()
        current_score = self.compute_score(current_districts)

        best_districts = current_districts.copy()
        best_score = current_score

        temperature = initial_temp
        phase = 1

        logging.info(f"Generated a map with {self.n_districts} districts")
        logging.info(f"Starting constrained optimization (population constraint: {self.population_constraint:.1%})")
        logging.info(f"Phase 1: Achieving population balance")

        self.history = []

        for step in range(steps):
            new_districts, _, old_d, new_d = self.propose_move(current_districts)

            if old_d == new_d:
                continue

            new_score = self.compute_score(new_districts)
            new_feasible = self.is_feasible(new_districts)
            current_feasible = self.is_feasible(current_districts)

            # Phase transition
            if phase == 1 and current_feasible and step > 100:
                phase = 2
                logging.info(f"Phase 2: Maximizing partisan gain (step {step})")

            # Acceptance criteria
            accept = False

            if phase == 1:
                # Phase 1: Prioritize feasibility, then score
                if new_feasible and not current_feasible:
                    accept = True
                elif new_feasible and current_feasible and new_score < current_score:
                    accept = True
                elif not new_feasible and not current_feasible:
                    delta = new_score - current_score
                    if delta < 0 or np.random.random() < np.exp(-delta / temperature):
                        accept = True
            else:
                # Phase 2: Only accept feasible solutions
                if new_feasible:
                    delta = new_score - current_score
                    if delta < 0 or np.random.random() < np.exp(-delta / temperature):
                        accept = True

            if accept:
                current_districts = new_districts
                current_score = new_score

                if current_score < best_score and self.is_feasible(current_districts):
                    best_districts = current_districts.copy()
                    best_score = current_score

            temperature *= cooling_rate

            if step % save_frequency == 0:
                components = self.compute_score(current_districts, return_components=True)
                feasible_str = "✓ feasible" if self.is_feasible(current_districts) else "✗ infeasible"

                logging.info(
                    f"Step {step}, phase {phase}, temp: {temperature:.2f}, score: {current_score:.1f} ({feasible_str})"
                )
                logging.info(
                    f"Seat deviation: {components['seat_deviation']:.0f}, "
                    f"population std: {components['population_std']:.2f}"
                )

                self.history.append({
                    'step': step,
                    'temperature': temperature,
                    'score': current_score,
                    'districts': current_districts.copy(),
                    'phase': phase,
                    'feasible': self.is_feasible(current_districts),
                    **components
                })

            if temperature < final_temp:
                break

        logging.info(f"Constrained optimization complete. Best score: {best_score}")
        return best_districts, self.history
