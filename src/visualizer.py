"""
Visualization utilities for gerrymandering experiments.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, PillowWriter
import geopandas as gpd
import numpy as np
from typing import List, Dict, Optional
import logging


def calculate_seat_distribution(
    gdf: gpd.GeoDataFrame,
    districts: np.ndarray,
    n_districts: int,
    party_cols: List[str]
) -> Dict[str, int]:
    """
    Calculate how many seats each party wins.

    Args:
        gdf: GeoDataFrame with voting data
        districts: District assignments
        n_districts: Number of districts
        party_cols: List of party column names to analyze

    Returns:
        Dictionary mapping party names to seat counts
    """
    seats = {party: 0 for party in party_cols}

    for d in range(n_districts):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]

        # Find which party gets most votes in this district
        party_votes = {}
        for party in party_cols:
            if party in district_gdf.columns:
                party_votes[party] = district_gdf[party].sum()

        if party_votes:
            winner = max(party_votes.items(), key=lambda x: x[1])[0]
            seats[winner] += 1

    return seats


def plot_state(
    gdf: gpd.GeoDataFrame,
    districts: np.ndarray,
    step: int,
    score: float,
    temperature: float,
    seat_history: List[Dict],
    party_cols: List[str],
    party_colors: Dict[str, str],
    n_districts: int,
    ax1,
    ax2
):
    """
    Plot current state: map on left, seat evolution on right.

    Args:
        gdf: GeoDataFrame
        districts: Current district assignments
        step: Current step number
        score: Current score
        temperature: Current temperature
        seat_history: History of seat distributions
        party_cols: Party columns to track
        party_colors: Colors for each party
        n_districts: Number of districts
        ax1: Axis for map
        ax2: Axis for seat plot
    """
    # Clear axes
    ax1.clear()
    ax2.clear()

    # Plot map
    plot_gdf = gdf.copy()
    plot_gdf['district'] = districts

    plot_gdf.plot(
        column='district',
        ax=ax1,
        cmap='tab20',
        edgecolor='black',
        linewidth=0.5,
        legend=False
    )

    ax1.set_title(
        f'Step {step} | Score: {score:.1f} | Temp: {temperature:.2f}',
        fontsize=10,
        fontweight='bold'
    )
    ax1.axis('off')

    # Plot seat evolution
    if seat_history:
        steps = [h['step'] for h in seat_history]

        for party in party_cols:
            seats = [h['seats'].get(party, 0) for h in seat_history]
            ax2.plot(
                steps,
                seats,
                label=party,
                color=party_colors.get(party, 'gray'),
                linewidth=2,
                marker='o',
                markersize=3
            )

        ax2.set_xlabel('Step', fontsize=10)
        ax2.set_ylabel('Seats Won', fontsize=10)
        ax2.set_title('Seat Distribution Evolution', fontsize=10, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=7)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, n_districts + 1)

        # Add proportional representation line
        if party_cols:
            proportional_seats = {}
            for party in party_cols:
                if party in gdf.columns:
                    total_votes = gdf[party].sum()
                    all_votes = sum(gdf[p].sum() for p in party_cols if p in gdf.columns)
                    proportional_seats[party] = (total_votes / all_votes) * n_districts

            for party, prop_seats in proportional_seats.items():
                ax2.axhline(
                    prop_seats,
                    color=party_colors.get(party, 'gray'),
                    linestyle='--',
                    alpha=0.5,
                    linewidth=1
                )


def create_animation(
    gdf: gpd.GeoDataFrame,
    history: List[Dict],
    output_path: str,
    party_cols: List[str] = None,
    party_colors: Dict[str, str] = None,
    fps: int = 2,
    dpi: int = 100
):
    """
    Create animated GIF showing optimization progress.

    Args:
        gdf: GeoDataFrame with voting data
        history: Optimization history from GerrymanderOptimizer
        output_path: Path to save GIF
        party_cols: Party columns to track (uses coalitions if None)
        party_colors: Colors for each party
        fps: Frames per second
        dpi: Resolution
    """
    logging.info(f"Creating animation with {len(history)} frames")

    # Default to coalitions if no parties specified
    if party_cols is None:
        party_cols = ['coalition_left', 'coalition_right', 'coalition_center']

    if party_colors is None:
        party_colors = {
            'coalition_left': '#E74C3C',
            'coalition_right': '#3498DB',
            'coalition_center': '#F39C12',
            "FRATELLI D'ITALIA CON GIORGIA MELONI": '#1a1a6e',
            "PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA": '#e74c3c',
            "MOVIMENTO 5 STELLE": '#f1c40f',
            "LEGA PER SALVINI PREMIER": '#2ecc71'
        }

    n_districts = len(np.unique(history[0]['districts']))

    # Calculate seat distribution for each step
    seat_history = []
    for h in history:
        seats = calculate_seat_distribution(
            gdf,
            h['districts'],
            n_districts,
            party_cols
        )
        seat_history.append({
            'step': h['step'],
            'seats': seats
        })

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    plt.tight_layout(pad=3.0)

    def update(frame_idx):
        """Update function for animation."""
        h = history[frame_idx]

        plot_state(
            gdf=gdf,
            districts=h['districts'],
            step=h['step'],
            score=h['score'],
            temperature=h['temperature'],
            seat_history=seat_history[:frame_idx + 1],
            party_cols=party_cols,
            party_colors=party_colors,
            n_districts=n_districts,
            ax1=ax1,
            ax2=ax2
        )

    # Create animation
    anim = FuncAnimation(
        fig,
        update,
        frames=len(history),
        interval=1000 / fps,
        repeat=True
    )

    # Save
    writer = PillowWriter(fps=fps)
    anim.save(output_path, writer=writer, dpi=dpi)
    logging.info(f"Animation saved to {output_path}")

    plt.close(fig)


def plot_final_comparison(
    gdf: gpd.GeoDataFrame,
    initial_districts: np.ndarray,
    final_districts: np.ndarray,
    party_cols: List[str],
    output_path: str,
    n_districts: int
):
    """
    Create comparison plot of initial vs final districting.

    Args:
        gdf: GeoDataFrame
        initial_districts: Initial district assignment
        final_districts: Final district assignment
        party_cols: Parties to analyze
        output_path: Where to save plot
        n_districts: Number of districts
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Initial map
    plot_gdf = gdf.copy()
    plot_gdf['district'] = initial_districts
    plot_gdf.plot(
        column='district',
        ax=axes[0, 0],
        cmap='tab20',
        edgecolor='black',
        linewidth=0.5,
        legend=False
    )
    axes[0, 0].set_title('Initial Districts', fontsize=14, fontweight='bold')
    axes[0, 0].axis('off')

    # Final map
    plot_gdf['district'] = final_districts
    plot_gdf.plot(
        column='district',
        ax=axes[0, 1],
        cmap='tab20',
        edgecolor='black',
        linewidth=0.5,
        legend=False
    )
    axes[0, 1].set_title('Final Districts', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')

    # Initial seats
    initial_seats = calculate_seat_distribution(gdf, initial_districts, n_districts, party_cols)
    axes[1, 0].bar(range(len(party_cols)), [initial_seats.get(p, 0) for p in party_cols])
    axes[1, 0].set_xticks(range(len(party_cols)))
    axes[1, 0].set_xticklabels([p.replace('coalition_', '').replace('_', ' ').title() for p in party_cols], rotation=45, ha='right')
    axes[1, 0].set_ylabel('Seats')
    axes[1, 0].set_title('Initial Seat Distribution', fontsize=14, fontweight='bold')
    axes[1, 0].set_ylim(0, n_districts)
    axes[1, 0].grid(True, alpha=0.3)

    # Final seats
    final_seats = calculate_seat_distribution(gdf, final_districts, n_districts, party_cols)
    axes[1, 1].bar(range(len(party_cols)), [final_seats.get(p, 0) for p in party_cols])
    axes[1, 1].set_xticks(range(len(party_cols)))
    axes[1, 1].set_xticklabels([p.replace('coalition_', '').replace('_', ' ').title() for p in party_cols], rotation=45, ha='right')
    axes[1, 1].set_ylabel('Seats')
    axes[1, 1].set_title('Final Seat Distribution', fontsize=14, fontweight='bold')
    axes[1, 1].set_ylim(0, n_districts)
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    logging.info(f"Comparison plot saved to {output_path}")
