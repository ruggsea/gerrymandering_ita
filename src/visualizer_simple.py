"""
Simplified visualization utilities showing only LEFT vs RIGHT (no center).
Districts colored by winner, bars show per-district vote percentages.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, PillowWriter
import geopandas as gpd
import numpy as np
from typing import List, Dict, Optional
import logging


def calculate_district_winners(
    gdf: gpd.GeoDataFrame,
    districts: np.ndarray,
    n_districts: int
) -> Dict[int, str]:
    """
    Calculate which coalition wins each district (LEFT vs RIGHT only).

    Args:
        gdf: GeoDataFrame with voting data
        districts: District assignments
        n_districts: Number of districts

    Returns:
        Dictionary mapping district_id -> 'coalition_left' or 'coalition_right'
    """
    winners = {}
    party_cols = ['coalition_left', 'coalition_right']

    for d in range(n_districts):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]

        # Calculate total votes for each party in this district
        left_votes = district_gdf['coalition_left'].sum()
        right_votes = district_gdf['coalition_right'].sum()

        # Winner is whoever has more votes (ignore center)
        winners[d] = 'coalition_left' if left_votes > right_votes else 'coalition_right'

    return winners


def calculate_district_vote_shares(
    gdf: gpd.GeoDataFrame,
    districts: np.ndarray,
    n_districts: int
) -> Dict[int, Dict[str, float]]:
    """
    Calculate vote share percentages for LEFT and RIGHT in each district.

    Args:
        gdf: GeoDataFrame with voting data
        districts: District assignments
        n_districts: Number of districts

    Returns:
        Dictionary mapping district_id -> {'coalition_left': %, 'coalition_right': %}
    """
    vote_shares = {}

    for d in range(n_districts):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]

        left_votes = district_gdf['coalition_left'].sum()
        right_votes = district_gdf['coalition_right'].sum()
        total_votes = left_votes + right_votes  # Only left + right

        # Convert to percentages
        if total_votes > 0:
            vote_shares[d] = {
                'coalition_left': (left_votes / total_votes) * 100,
                'coalition_right': (right_votes / total_votes) * 100
            }
        else:
            vote_shares[d] = {'coalition_left': 50, 'coalition_right': 50}

    return vote_shares


def plot_state_simple(
    gdf: gpd.GeoDataFrame,
    districts: np.ndarray,
    step: int,
    score: float,
    temperature: float,
    n_districts: int,
    ax1,
    ax2
):
    """
    Plot current state with simplified visualization (LEFT vs RIGHT only):
    - Left: Map colored by WINNER (which coalition wins each district)
    - Right: Bar plot showing vote percentages per district

    Args:
        gdf: GeoDataFrame
        districts: Current district assignments
        step: Current step number
        score: Current score
        temperature: Current temperature
        n_districts: Number of districts
        ax1: Axis for map
        ax2: Axis for bar plot
    """
    # Clear axes
    ax1.clear()
    ax2.clear()

    # Define colors (only left and right)
    party_colors = {
        'coalition_left': '#E74C3C',      # Red
        'coalition_right': '#3498DB'      # Blue
    }

    # Calculate winners for coloring
    winners = calculate_district_winners(gdf, districts, n_districts)

    # Create map colored by winner
    plot_gdf = gdf.copy()
    plot_gdf['district'] = districts

    # Assign winner color to each commune
    def get_commune_color(row):
        district_id = row['district']
        winner = winners.get(district_id, 'coalition_left')
        return party_colors[winner]

    plot_gdf['winner_color'] = plot_gdf.apply(get_commune_color, axis=1)

    # Plot with winner coloring
    plot_gdf.plot(
        color=plot_gdf['winner_color'],
        ax=ax1,
        edgecolor='black',
        linewidth=0.8,
        legend=False
    )

    ax1.set_title(
        f'Step {step} | Score: {score:.1f} | Temp: {temperature:.2f}',
        fontsize=10,
        fontweight='bold'
    )
    ax1.axis('off')

    # Add legend for winners (only left and right)
    legend_patches = [
        mpatches.Patch(color='#E74C3C', label='Left'),
        mpatches.Patch(color='#3498DB', label='Right')
    ]
    ax1.legend(handles=legend_patches, loc='lower left', fontsize=8)

    # Calculate vote shares per district
    vote_shares = calculate_district_vote_shares(gdf, districts, n_districts)

    # Create stacked bar plot (LEFT vs RIGHT only)
    district_ids = sorted(vote_shares.keys())
    x_pos = np.arange(len(district_ids))

    # Stack bars: left on bottom, right on top
    left_heights = [vote_shares[d]['coalition_left'] for d in district_ids]
    right_heights = [vote_shares[d]['coalition_right'] for d in district_ids]

    ax2.bar(
        x_pos,
        left_heights,
        label='Left',
        color='#E74C3C',
        edgecolor='black',
        linewidth=0.5
    )

    ax2.bar(
        x_pos,
        right_heights,
        bottom=left_heights,
        label='Right',
        color='#3498DB',
        edgecolor='black',
        linewidth=0.5
    )

    # Add 50% line (majority threshold for 2-party competition)
    ax2.axhline(50, color='red', linestyle='--', linewidth=2, alpha=0.7, label='50% (Majority)')

    ax2.set_xlabel('District', fontsize=10)
    ax2.set_ylabel('Vote Share (%)', fontsize=10)
    ax2.set_title('Left vs Right Vote Shares by District', fontsize=10, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f'D{d}' for d in district_ids], fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper right', fontsize=7)
    ax2.grid(True, alpha=0.3, axis='y')


def create_animation_simple(
    gdf: gpd.GeoDataFrame,
    history: List[Dict],
    output_path: str,
    fps: int = 2,
    dpi: int = 100
):
    """
    Create animated GIF with simplified visualization (LEFT vs RIGHT only).

    Args:
        gdf: GeoDataFrame with voting data
        history: Optimization history
        output_path: Path to save GIF
        fps: Frames per second
        dpi: Resolution
    """
    logging.info(f"Creating simplified animation with {len(history)} frames")

    n_districts = len(np.unique(history[0]['districts']))

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    plt.tight_layout(pad=3.0)

    def update(frame_idx):
        """Update function for animation."""
        h = history[frame_idx]

        plot_state_simple(
            gdf=gdf,
            districts=h['districts'],
            step=h['step'],
            score=h['score'],
            temperature=h['temperature'],
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
    logging.info(f"Simplified animation saved to {output_path}")

    plt.close(fig)


def plot_final_comparison_simple(
    gdf: gpd.GeoDataFrame,
    initial_districts: np.ndarray,
    final_districts: np.ndarray,
    output_path: str,
    n_districts: int
):
    """
    Create simplified comparison plot of initial vs final districting (LEFT vs RIGHT only).

    Args:
        gdf: GeoDataFrame
        initial_districts: Initial district assignment
        final_districts: Final district assignment
        output_path: Where to save plot
        n_districts: Number of districts
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Initial map (colored by winner)
    plot_state_simple(
        gdf, initial_districts, 0, 0, 0,
        n_districts,
        axes[0, 0], axes[1, 0]
    )
    axes[0, 0].set_title('Initial Districts (by Winner)', fontsize=14, fontweight='bold')
    axes[1, 0].set_title('Initial Vote Shares', fontsize=14, fontweight='bold')

    # Final map (colored by winner)
    plot_state_simple(
        gdf, final_districts, 0, 0, 0,
        n_districts,
        axes[0, 1], axes[1, 1]
    )
    axes[0, 1].set_title('Final Districts (by Winner)', fontsize=14, fontweight='bold')
    axes[1, 1].set_title('Final Vote Shares', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logging.info(f"Simplified comparison plot saved to {output_path}")
    plt.close(fig)
