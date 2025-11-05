"""
Contiguity checking utilities for district optimization.
"""
import numpy as np
import networkx as nx
from typing import Dict, Set


def check_district_contiguity(
    districts: np.ndarray,
    district_id: int,
    neighbors: Dict[int, list]
) -> bool:
    """
    Check if a district is contiguous (all communes connected).

    Args:
        districts: Array of district assignments
        district_id: District to check
        neighbors: Adjacency dict {commune_idx: [neighbor_indices]}

    Returns:
        True if district is contiguous, False otherwise
    """
    # Get all communes in this district
    district_communes = np.where(districts == district_id)[0]

    if len(district_communes) == 0:
        return False
    if len(district_communes) == 1:
        return True

    # Build graph of communes in this district
    G = nx.Graph()
    G.add_nodes_from(district_communes)

    for commune_idx in district_communes:
        for neighbor_idx in neighbors.get(commune_idx, []):
            neighbor_loc = np.where(np.array(list(neighbors.keys())) == neighbor_idx)[0]
            if len(neighbor_loc) > 0:
                neighbor_loc = neighbor_loc[0]
                if districts[neighbor_loc] == district_id:
                    G.add_edge(commune_idx, neighbor_loc)

    # Check if graph is connected
    return nx.is_connected(G)


def is_valid_move(
    districts: np.ndarray,
    commune_idx: int,
    old_district: int,
    new_district: int,
    neighbors: Dict[int, list],
    commune_map_idx: int
) -> bool:
    """
    Check if moving a commune preserves contiguity.

    Args:
        districts: Current district assignments
        commune_idx: Position in districts array
        old_district: Current district of commune
        new_district: Target district
        neighbors: Adjacency dict
        commune_map_idx: Original index in GeoDataFrame

    Returns:
        True if move preserves contiguity of both districts
    """
    # Check 1: Commune must border the new district
    commune_neighbors = neighbors.get(commune_map_idx, [])
    new_district_has_neighbor = False

    for neighbor_idx in commune_neighbors:
        # Find neighbor's position in districts array
        neighbor_locs = np.where(np.array(list(neighbors.keys())) == neighbor_idx)[0]
        if len(neighbor_locs) > 0:
            neighbor_loc = neighbor_locs[0]
            if districts[neighbor_loc] == new_district:
                new_district_has_neighbor = True
                break

    if not new_district_has_neighbor:
        return False

    # Check 2: Removing commune doesn't fragment old district
    # (only check if old district has more than 1 commune)
    old_district_size = np.sum(districts == old_district)
    if old_district_size <= 1:
        return True  # Can't fragment a single-commune district

    # Simulate the move
    test_districts = districts.copy()
    test_districts[commune_idx] = new_district

    # Check if old district remains contiguous
    return check_district_contiguity(test_districts, old_district, neighbors)


def validate_all_districts_contiguous(
    districts: np.ndarray,
    n_districts: int,
    neighbors: Dict[int, list]
) -> tuple[bool, list]:
    """
    Validate that all districts are contiguous.

    Args:
        districts: District assignments
        n_districts: Total number of districts
        neighbors: Adjacency dict

    Returns:
        (all_contiguous, list_of_non_contiguous_districts)
    """
    non_contiguous = []

    for d in range(n_districts):
        if not check_district_contiguity(districts, d, neighbors):
            non_contiguous.append(d)

    return len(non_contiguous) == 0, non_contiguous
