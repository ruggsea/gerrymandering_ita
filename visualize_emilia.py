"""
Visualize Emilia-Romagna gerrymandering results.
"""
import pickle
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import numpy as np


def load_result(pickle_file: str):
    """Load a gerrymandering result."""
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    return data


def create_district_map(pickle_file: str, output_file: str = None, title: str = None):
    """
    Create a map showing district assignments with winner colors.

    Args:
        pickle_file: Path to result pickle
        output_file: Path to save image (optional)
        title: Map title (optional)
    """
    # Load result
    result = load_result(pickle_file)
    assignment = result['assignment']
    results = result['results']
    municipalities = result['municipalities']

    # Load geometry
    gdf = gpd.read_file('comuni_italiani_trend_liste_2022_2024.geojson')
    emilia_gdf = gdf[gdf['CIRCOSCRIZIONE'] == 'EMILIA-ROMAGNA'].copy()

    # Merge with assignment
    assignment_df = pd.DataFrame({
        'name': municipalities,
        'district': assignment
    })

    emilia_gdf = emilia_gdf.merge(assignment_df, on='name', how='inner')

    # Load vote data to determine district winners
    df = pd.read_csv('politiche_2022_liste_camera_comuni.csv')
    emilia_votes = df[df['CIRCOSCRIZIONE'] == 'EMILIA-ROMAGNA'].copy()

    left_parties = ['PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA',
                    '+EUROPA', 'ALLEANZA VERDI E SINISTRA']
    right_parties = ['FRATELLI D\'ITALIA CON GIORGIA MELONI', 'LEGA PER SALVINI PREMIER',
                     'FORZA ITALIA', 'NOI MODERATI/LUPI - TOTI - BRUGNARO - UDC']
    m5s_parties = ['MOVIMENTO 5 STELLE']

    # Compute district winners
    district_winners = {}
    for d in range(11):
        dist_munis = assignment_df[assignment_df['district'] == d]['name']
        dist_votes = emilia_votes[emilia_votes['name'].isin(dist_munis)]

        left = dist_votes[left_parties].sum().sum()
        right = dist_votes[right_parties].sum().sum()
        m5s = dist_votes[m5s_parties].sum().sum()

        if right > left and right > m5s:
            district_winners[d] = 'right'
        elif left > right and left > m5s:
            district_winners[d] = 'left'
        else:
            district_winners[d] = 'm5s'

    # Map district to winner
    emilia_gdf['winner'] = emilia_gdf['district'].map(district_winners)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # Color map for winners
    color_map = {
        'left': '#E41A1C',    # Red for left (PD color)
        'right': '#377EB8',   # Blue for right
        'm5s': '#FFD700'      # Gold for M5S
    }

    # Plot each district with edge color based on winner
    for district_id in range(11):
        district_data = emilia_gdf[emilia_gdf['district'] == district_id]
        winner = district_winners[district_id]
        color = color_map[winner]

        district_data.plot(
            ax=ax,
            color=color,
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7
        )

        # Add district label
        centroid = district_data.geometry.unary_union.centroid
        ax.text(centroid.x, centroid.y, str(district_id + 1),
                fontsize=12, fontweight='bold',
                ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Create legend
    legend_elements = [
        mpatches.Patch(facecolor=color_map['left'], edgecolor='black', label='LEFT'),
        mpatches.Patch(facecolor=color_map['right'], edgecolor='black', label='RIGHT'),
        mpatches.Patch(facecolor=color_map['m5s'], edgecolor='black', label='M5S')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

    # Set title
    if title is None:
        title = f"Emilia-Romagna: LEFT={results['left_seats']}, RIGHT={results['right_seats']}, M5S={results['m5s_seats']}"
    ax.set_title(title, fontsize=16, fontweight='bold')

    # Remove axes
    ax.set_axis_off()

    # Add metadata
    max_dev = results.get('max_deviation', 0) * 100
    pop_std = results.get('population_std', 0)
    ax.text(0.02, 0.02,
            f"Population: Max deviation {max_dev:.1f}% | Std {pop_std:.0f} voters",
            transform=ax.transAxes,
            fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved map to {output_file}")

    return fig, ax


def main():
    """Generate maps for both results."""
    print("Generating LEFT 4/11 map...")
    create_district_map(
        'emilia_left_4seats_attempt0.pkl',
        'emilia_left_4seats_map.png',
        'Emilia-Romagna Gerrymandered for LEFT (4/11 seats)'
    )

    print("\nGenerating RIGHT 11/11 map...")
    create_district_map(
        'emilia_right_11seats_attempt0.pkl',
        'emilia_right_11seats_map.png',
        'Emilia-Romagna Gerrymandered for RIGHT (11/11 seats)'
    )

    print("\nDone! Check emilia_left_4seats_map.png and emilia_right_11seats_map.png")


if __name__ == '__main__':
    main()
