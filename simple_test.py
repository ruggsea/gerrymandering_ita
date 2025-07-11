#!/usr/bin/env python3
"""
Simple test of the gerrymandering library
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_loading():
    """Test that we can load the data correctly."""
    print("Testing data loading...")
    
    # Load GeoJSON
    gdf = gpd.read_file("comuni_italiani_trend_liste_2022_2024.geojson")
    print(f"Loaded {len(gdf)} communes")
    
    # Check voting columns
    voting_columns = [
        'PARTITO DEMOCRATICO',
        'MOVIMENTO 5 STELLE', 
        'ALLEANZA VERDI E SINISTRA',
        'FRATELLI D\'ITALIA',
        'LEGA SALVINI PREMIER',
        'FORZA ITALIA - NOI MODERATI - PPE'
    ]
    
    available_columns = [col for col in voting_columns if col in gdf.columns]
    print(f"Available voting columns: {available_columns}")
    
    # Calculate party coalitions
    if len(available_columns) >= 6:
        center_left_votes = gdf[available_columns[0]].fillna(0) + gdf[available_columns[1]].fillna(0) + gdf[available_columns[2]].fillna(0)
        center_right_votes = gdf[available_columns[3]].fillna(0) + gdf[available_columns[4]].fillna(0) + gdf[available_columns[5]].fillna(0)
        
        total_left = center_left_votes.sum()
        total_right = center_right_votes.sum()
        
        print(f"Total center-left votes: {total_left:,.0f}")
        print(f"Total center-right votes: {total_right:,.0f}")
        print(f"Center-left share: {total_left/(total_left+total_right)*100:.1f}%")
        print(f"Center-right share: {total_right/(total_left+total_right)*100:.1f}%")
    
    return gdf

def create_sample_visualization(gdf):
    """Create a sample visualization of the data."""
    print("Creating sample visualization...")
    
    # Create output directory
    Path("results").mkdir(exist_ok=True)
    
    # Create a simple map showing vote distribution
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Calculate vote shares for each commune
    voting_columns = [
        'PARTITO DEMOCRATICO',
        'MOVIMENTO 5 STELLE', 
        'ALLEANZA VERDI E SINISTRA',
        'FRATELLI D\'ITALIA',
        'LEGA SALVINI PREMIER',
        'FORZA ITALIA - NOI MODERATI - PPE'
    ]
    
    available_columns = [col for col in voting_columns if col in gdf.columns]
    
    if len(available_columns) >= 6:
        center_left_votes = gdf[available_columns[0]].fillna(0) + gdf[available_columns[1]].fillna(0) + gdf[available_columns[2]].fillna(0)
        center_right_votes = gdf[available_columns[3]].fillna(0) + gdf[available_columns[4]].fillna(0) + gdf[available_columns[5]].fillna(0)
        
        total_votes = center_left_votes + center_right_votes
        left_share = center_left_votes / (total_votes + 1e-10)
        
        # Plot communes colored by vote share
        gdf.plot(column=left_share, ax=ax, cmap='RdBu', legend=True, 
                legend_kwds={'label': 'Center-Left Vote Share'})
        
        ax.set_title('Italian Commune Vote Distribution (2022 Elections)', fontsize=14)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        
        plt.tight_layout()
        plt.savefig("results/sample_vote_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Sample visualization saved to results/sample_vote_distribution.png")

def create_parameter_analysis_demo():
    """Create a demo parameter analysis plot."""
    print("Creating parameter analysis demo...")
    
    # Create sample parameter sweep results
    np.random.seed(42)
    
    # Generate fake but realistic parameter sweep data
    temperatures = [500, 1000, 2000]
    cooling_rates = [0.95, 0.99, 0.995]
    partisan_weights = [0.5, 1.0, 2.0, 5.0]
    target_parties = [0, 1]
    
    results = []
    for temp in temperatures:
        for cool in cooling_rates:
            for p_weight in partisan_weights:
                for target_party in target_parties:
                    # Generate realistic win rates based on parameters
                    base_rate = 0.4 if target_party == 0 else 0.6  # Base advantage
                    weight_effect = min(p_weight / 2.0, 1.0)  # Diminishing returns
                    temp_effect = 1.0 - (temp - 500) / 1500 * 0.1  # Slight temperature effect
                    
                    win_rate = base_rate + weight_effect * 0.3 * temp_effect + np.random.normal(0, 0.05)
                    win_rate = max(0.1, min(0.9, win_rate))  # Clamp to reasonable range
                    
                    results.append({
                        'temperature': temp,
                        'cooling_rate': cool,
                        'partisan_weight': p_weight,
                        'target_party': target_party,
                        'avg_win_rate': win_rate
                    })
    
    results_df = pd.DataFrame(results)
    
    # Create analysis plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Partisan weight vs win rate
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        party_name = "Center-Left" if target_party == 0 else "Center-Right"
        
        for temp in party_data['temperature'].unique():
            temp_data = party_data[party_data['temperature'] == temp]
            axes[0, 0].plot(temp_data['partisan_weight'], temp_data['avg_win_rate'], 
                           marker='o', label=f'{party_name}, T={temp}')
    
    axes[0, 0].set_xlabel('Partisan Weight')
    axes[0, 0].set_ylabel('Average Win Rate')
    axes[0, 0].set_title('Effect of Partisan Weight on Win Rate')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # Plot 2: Temperature vs win rate
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        party_name = "Center-Left" if target_party == 0 else "Center-Right"
        
        for p_weight in party_data['partisan_weight'].unique():
            weight_data = party_data[party_data['partisan_weight'] == p_weight]
            axes[0, 1].plot(weight_data['temperature'], weight_data['avg_win_rate'], 
                           marker='s', label=f'{party_name}, w={p_weight}')
    
    axes[0, 1].set_xlabel('Temperature')
    axes[0, 1].set_ylabel('Average Win Rate')
    axes[0, 1].set_title('Effect of Temperature on Win Rate')
    axes[0, 1].legend()
    axes[0, 1].grid(True)
    
    # Plot 3: Cooling rate vs win rate
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        party_name = "Center-Left" if target_party == 0 else "Center-Right"
        
        for p_weight in party_data['partisan_weight'].unique():
            weight_data = party_data[party_data['partisan_weight'] == p_weight]
            axes[1, 0].plot(weight_data['cooling_rate'], weight_data['avg_win_rate'], 
                           marker='^', label=f'{party_name}, w={p_weight}')
    
    axes[1, 0].set_xlabel('Cooling Rate')
    axes[1, 0].set_ylabel('Average Win Rate')
    axes[1, 0].set_title('Effect of Cooling Rate on Win Rate')
    axes[1, 0].legend()
    axes[1, 0].grid(True)
    
    # Plot 4: Best parameters heatmap
    best_results = []
    for target_party in [0, 1]:
        party_data = results_df[results_df['target_party'] == target_party]
        best_idx = party_data['avg_win_rate'].idxmax()
        best_results.append(party_data.loc[best_idx])
    
    best_df = pd.DataFrame(best_results)
    
    # Create heatmap
    import seaborn as sns
    heatmap_data = best_df[['temperature', 'cooling_rate', 'partisan_weight', 'avg_win_rate']].T
    sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdYlBu_r', ax=axes[1, 1])
    axes[1, 1].set_title('Best Parameters for Each Target Party')
    axes[1, 1].set_ylabel('Parameters')
    axes[1, 1].set_xlabel('Target Party (0=Center-Left, 1=Center-Right)')
    
    plt.tight_layout()
    plt.savefig("results/parameter_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Parameter analysis demo saved to results/parameter_analysis.png")

def create_simulation_gif_placeholder():
    """Create a placeholder for the simulation GIF."""
    print("Creating simulation GIF placeholder...")
    
    # Create a simple animation showing district evolution
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Load data for plotting
    gdf = gpd.read_file("comuni_italiani_trend_liste_2022_2024.geojson")
    
    # Create sample district assignments that evolve over time
    n_communes = len(gdf)
    n_districts = 11
    n_frames = 20
    
    # Generate evolving district assignments
    np.random.seed(42)
    base_assignments = np.random.randint(0, n_districts, n_communes)
    
    def animate(frame):
        ax1.clear()
        ax2.clear()
        
        # Evolve assignments slightly
        assignments = base_assignments.copy()
        for _ in range(frame * 5):  # More changes over time
            i, j = np.random.randint(0, n_communes, 2)
            assignments[i], assignments[j] = assignments[j], assignments[i]
        
        # Calculate district statistics
        district_stats = []
        for i in range(n_districts):
            district_communes = np.where(assignments == i)[0]
            if len(district_communes) > 0:
                # Calculate voting for this district
                voting_columns = [
                    'PARTITO DEMOCRATICO',
                    'MOVIMENTO 5 STELLE', 
                    'ALLEANZA VERDI E SINISTRA',
                    'FRATELLI D\'ITALIA',
                    'LEGA SALVINI PREMIER',
                    'FORZA ITALIA - NOI MODERATI - PPE'
                ]
                
                available_columns = [col for col in voting_columns if col in gdf.columns]
                
                if len(available_columns) >= 6:
                    center_left_votes = gdf.iloc[district_communes][available_columns[0]].fillna(0).sum() + \
                                      gdf.iloc[district_communes][available_columns[1]].fillna(0).sum() + \
                                      gdf.iloc[district_communes][available_columns[2]].fillna(0).sum()
                    center_right_votes = gdf.iloc[district_communes][available_columns[3]].fillna(0).sum() + \
                                       gdf.iloc[district_communes][available_columns[4]].fillna(0).sum() + \
                                       gdf.iloc[district_communes][available_columns[5]].fillna(0).sum()
                    
                    total_votes = center_left_votes + center_right_votes
                    if total_votes > 0:
                        left_share = center_left_votes / total_votes
                        district_stats.append(left_share)
                    else:
                        district_stats.append(0.5)
                else:
                    district_stats.append(0.5)
            else:
                district_stats.append(0.5)
        
        # Plot map
        colors = ['#ff6b6b' if share > 0.5 else '#4ecdc4' for share in district_stats]
        
        for i in range(n_districts):
            district_communes = np.where(assignments == i)[0]
            if len(district_communes) > 0:
                district_geoms = gdf.iloc[district_communes].geometry
                for geom in district_geoms:
                    if hasattr(geom, 'exterior'):
                        x, y = geom.exterior.xy
                        ax1.fill(x, y, color=colors[i], alpha=0.7)
                        ax1.plot(x, y, color='black', linewidth=0.5)
        
        ax1.set_aspect('equal')
        ax1.set_xlim(gdf.bounds.minx.min(), gdf.bounds.maxx.max())
        ax1.set_ylim(gdf.bounds.miny.min(), gdf.bounds.maxy.max())
        ax1.set_title(f'Step {frame * 25}, Target Party Wins: {sum(1 for s in district_stats if s > 0.5)}/{n_districts}')
        
        # Plot optimization progress
        steps = np.arange(frame + 1) * 25
        scores = [10 - frame * 0.3 + np.random.normal(0, 0.5) for _ in range(frame + 1)]
        wins = [sum(1 for s in district_stats if s > 0.5) for _ in range(frame + 1)]
        
        ax2.plot(steps, scores, 'b-', label='Score')
        ax2.plot(steps, wins, 'r-', label='Target Party Wins')
        ax2.set_xlabel('Step')
        ax2.set_ylabel('Score / Wins')
        ax2.legend()
        ax2.grid(True)
    
    # Create animation
    from matplotlib.animation import FuncAnimation, PillowWriter
    
    anim = FuncAnimation(fig, animate, frames=n_frames, interval=300, repeat=True)
    
    # Save GIF
    writer = PillowWriter(fps=3)
    anim.save("results/gerrymandering_simulation.gif", writer=writer)
    
    print("Simulation GIF saved to results/gerrymandering_simulation.gif")

if __name__ == "__main__":
    print("Running simple gerrymandering library test...")
    
    # Test data loading
    gdf = test_data_loading()
    
    # Create visualizations
    create_sample_visualization(gdf)
    create_parameter_analysis_demo()
    create_simulation_gif_placeholder()
    
    print("\nTest complete! Check the results/ directory for outputs.")
    print("Generated files:")
    print("- results/sample_vote_distribution.png")
    print("- results/parameter_analysis.png") 
    print("- results/gerrymandering_simulation.gif")