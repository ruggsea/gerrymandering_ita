"""
Improved visualization utilities showing district winners and vote distributions.
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
    n_districts: int,
    party_cols: List[str]
) -> Dict[int, str]:
    """
    Calculate which party/coalition wins each district.

    Args:
        gdf: GeoDataFrame with voting data
        districts: District assignments
        n_districts: Number of districts
        party_cols: List of party/coalition column names

    Returns:
        Dictionary mapping district_id -> winning_party
    """
    winners = {}

    for d in range(n_districts):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]

        # Calculate total votes for each party in this district
        party_votes = {}
        for party in party_cols:
            if party in district_gdf.columns:
                party_votes[party] = district_gdf[party].sum()

        if party_votes:
            winner = max(party_votes.items(), key=lambda x: x[1])[0]
            winners[d] = winner

    return winners


def calculate_district_vote_shares(
    gdf: gpd.GeoDataFrame,
    districts: np.ndarray,
    n_districts: int,
    party_cols: List[str]
) -> Dict[int, Dict[str, float]]:
    """
    Calculate vote share percentages for each party in each district.

    Args:
        gdf: GeoDataFrame with voting data
        districts: District assignments
        n_districts: Number of districts
        party_cols: List of party/coalition column names

    Returns:
        Dictionary mapping district_id -> {party: vote_share_percentage}
    """
    vote_shares = {}

    for d in range(n_districts):
        mask = districts == d
        district_gdf = gdf.iloc[np.where(mask)[0]]

        party_votes = {}
        total_votes = 0

        for party in party_cols:
            if party in district_gdf.columns:
                votes = district_gdf[party].sum()
                party_votes[party] = votes
                total_votes += votes

        # Convert to percentages
        if total_votes > 0:
            vote_shares[d] = {
                party: (votes / total_votes) * 100
                for party, votes in party_votes.items()
            }
        else:
            vote_shares[d] = {party: 0 for party in party_cols}

    return vote_shares


def plot_state_improved(
    gdf: gpd.GeoDataFrame,
    districts: np.ndarray,
    step: int,
    score: float,
    temperature: float,
    party_cols: List[str],
    party_colors: Dict[str, str],
    n_districts: int,
    ax1,
    ax2
):
    """
    Plot current state with improved visualization:
    - Left: Map colored by WINNER (which coalition wins each district)
    - Right: Bar plot showing vote percentages per district

    Args:
        gdf: GeoDataFrame
        districts: Current district assignments
        step: Current step number
        score: Current score
        temperature: Current temperature
        party_cols: Party columns to track
        party_colors: Colors for each party
        n_districts: Number of districts
        ax1: Axis for map
        ax2: Axis for bar plot
    """
    # Clear axes
    ax1.clear()
    ax2.clear()

    # Calculate winners for coloring
    winners = calculate_district_winners(gdf, districts, n_districts, party_cols)

    # Create map colored by winner
    plot_gdf = gdf.copy()
    plot_gdf['district'] = districts

    # Assign winner color to each commune
    def get_commune_color(row):
        district_id = row['district']
        winner = winners.get(district_id, party_cols[0])
        return party_colors.get(winner, 'gray')

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

    # Add legend for winners
    legend_patches = []
    for party in party_cols:
        patch = mpatches.Patch(
            color=party_colors.get(party, 'gray'),
            label=party.replace('coalition_', '').replace('_', ' ').title()
        )
        legend_patches.append(patch)
    ax1.legend(handles=legend_patches, loc='lower left', fontsize=8)

    # Calculate vote shares per district
    vote_shares = calculate_district_vote_shares(gdf, districts, n_districts, party_cols)

    # Create stacked bar plot
    district_ids = sorted(vote_shares.keys())
    x_pos = np.arange(len(district_ids))

    # Stack bars for each party
    bottoms = np.zeros(len(district_ids))

    for party in party_cols:
        heights = [vote_shares[d].get(party, 0) for d in district_ids]

        ax2.bar(
            x_pos,
            heights,
            bottom=bottoms,
            label=party.replace('coalition_', '').replace('_', ' ').title(),
            color=party_colors.get(party, 'gray'),
            edgecolor='black',
            linewidth=0.5
        )

        bottoms += heights

    # Add 50% line (majority threshold)
    ax2.axhline(50, color='red', linestyle='--', linewidth=2, alpha=0.7, label='50% (Majority)')

    ax2.set_xlabel('District', fontsize=10)
    ax2.set_ylabel('Vote Share (%)', fontsize=10)
    ax2.set_title('Coalition Vote Shares by District', fontsize=10, fontweight='bold')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f'D{d}' for d in district_ids], fontsize=8)
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper right', fontsize=7)
    ax2.grid(True, alpha=0.3, axis='y')


def create_animation_improved(
    gdf: gpd.GeoDataFrame,
    history: List[Dict],
    output_path: str,
    party_cols: List[str] = None,
    party_colors: Dict[str, str] = None,
    fps: int = 2,
    dpi: int = 100
):
    """
    Create animated GIF with improved visualization.

    Args:
        gdf: GeoDataFrame with voting data
        history: Optimization history
        output_path: Path to save GIF
        party_cols: Party columns to track (uses coalitions if None)
        party_colors: Colors for each party
        fps: Frames per second
        dpi: Resolution
    """
    logging.info(f"Creating improved animation with {len(history)} frames")

    # Default to coalitions if no parties specified
    if party_cols is None:
        party_cols = ['coalition_left', 'coalition_right', 'coalition_center']

    if party_colors is None:
        party_colors = {
            'coalition_left': '#E74C3C',
            'coalition_right': '#3498DB',
            'coalition_center': '#F39C12'
        }

    n_districts = len(np.unique(history[0]['districts']))

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    plt.tight_layout(pad=3.0)

    def update(frame_idx):
        """Update function for animation."""
        h = history[frame_idx]

        plot_state_improved(
            gdf=gdf,
            districts=h['districts'],
            step=h['step'],
            score=h['score'],
            temperature=h['temperature'],
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
    logging.info(f"Improved animation saved to {output_path}")

    plt.close(fig)


def plot_final_comparison_improved(
    gdf: gpd.GeoDataFrame,
    initial_districts: np.ndarray,
    final_districts: np.ndarray,
    party_cols: List[str],
    party_colors: Dict[str, str],
    output_path: str,
    n_districts: int
):
    """
    Create improved comparison plot of initial vs final districting.

    Args:
        gdf: GeoDataFrame
        initial_districts: Initial district assignment
        final_districts: Final district assignment
        party_cols: Parties to analyze
        party_colors: Colors for parties
        output_path: Where to save plot
        n_districts: Number of districts
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Initial map (colored by winner)
    plot_state_improved(
        gdf, initial_districts, 0, 0, 0,
        party_cols, party_colors, n_districts,
        axes[0, 0], axes[1, 0]
    )
    axes[0, 0].set_title('Initial Districts (by Winner)', fontsize=14, fontweight='bold')
    axes[1, 0].set_title('Initial Vote Shares', fontsize=14, fontweight='bold')

    # Final map (colored by winner)
    plot_state_improved(
        gdf, final_districts, 0, 0, 0,
        party_cols, party_colors, n_districts,
        axes[0, 1], axes[1, 1]
    )
    axes[0, 1].set_title('Final Districts (by Winner)', fontsize=14, fontweight='bold')
    axes[1, 1].set_title('Final Vote Shares', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    logging.info(f"Improved comparison plot saved to {output_path}")
    plt.close(fig)
