#!/usr/bin/env python3
"""
Gerrymandering Optimization Demo
Demonstrates the library's capabilities with real data.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from pathlib import Path
import logging
from fast_gerrymandering import FastGerryOptimizer, GerryConfig, GerrymanderingAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the complete gerrymandering optimization demo."""
    print("=== Fast Gerrymandering Optimization Library Demo ===\n")
    
    # Create output directory
    Path("results").mkdir(exist_ok=True)
    
    # Load and analyze data
    print("1. Loading Italian voting data...")
    gdf = gpd.read_file("comuni_italiani_trend_liste_2022_2024.geojson")
    print(f"   Loaded {len(gdf)} communes")
    
    # Calculate overall vote distribution
    voting_columns = [
        'PARTITO DEMOCRATICO',
        'MOVIMENTO 5 STELLE', 
        'ALLEANZA VERDI E SINISTRA',
        'FRATELLI D\'ITALIA',
        'LEGA SALVINI PREMIER',
        'FORZA ITALIA - NOI MODERATI - PPE'
    ]
    
    center_left_votes = gdf[voting_columns[0]].fillna(0) + gdf[voting_columns[1]].fillna(0) + gdf[voting_columns[2]].fillna(0)
    center_right_votes = gdf[voting_columns[3]].fillna(0) + gdf[voting_columns[4]].fillna(0) + gdf[voting_columns[5]].fillna(0)
    
    total_left = center_left_votes.sum()
    total_right = center_right_votes.sum()
    
    print(f"   Center-left coalition: {total_left:,.0f} votes ({total_left/(total_left+total_right)*100:.1f}%)")
    print(f"   Center-right coalition: {total_right:,.0f} votes ({total_right/(total_left+total_right)*100:.1f}%)")
    
    # Run optimization for center-left advantage
    print("\n2. Running optimization to favor center-left coalition...")
    
    config = GerryConfig(
        temperature=1000,
        cooling_rate=0.99,
        steps=1000,
        partisan_weight=3.0,  # High partisan weight to favor target party
        target_party=0,  # Target center-left
        target_districts=11
    )
    
    optimizer = FastGerryOptimizer("comuni_italiani_trend_liste_2022_2024.geojson", config)
    score, districts, history = optimizer.optimize()
    
    print(f"   Optimization complete!")
    print(f"   Final score: {score:.3f}")
    print(f"   Target party wins: {history['party_wins'][-1]}/{config.target_districts}")
    
    # Analyze results
    print("\n3. Analyzing optimization results...")
    
    # Calculate final district statistics
    final_wins = history['party_wins'][-1]
    win_rate = final_wins / config.target_districts
    
    print(f"   Center-left wins: {final_wins} districts")
    print(f"   Win rate: {win_rate:.1%}")
    
    # Calculate district-by-district results
    print("\n   District-by-district results:")
    for i, district in enumerate(districts):
        total_votes = district['left_votes'] + district['right_votes']
        if total_votes > 0:
            left_share = district['left_votes'] / total_votes
            right_share = district['right_votes'] / total_votes
            winner = "Center-Left" if left_share > right_share else "Center-Right"
            print(f"     District {i+1}: {winner} ({left_share:.1%} vs {right_share:.1%})")
    
    # Create visualization
    print("\n4. Creating optimization visualization...")
    
    analyzer = GerrymanderingAnalyzer(optimizer)
    analyzer.create_simulation_gif(history, "results/gerrymandering_simulation.gif")
    
    print("   GIF saved to results/gerrymandering_simulation.gif")
    
    # Create final district map
    print("\n5. Creating final district map...")
    
    fig, ax = plt.subplots(figsize=(15, 10))
    
    # Plot final districts
    for i, district in enumerate(districts):
        total_votes = district['left_votes'] + district['right_votes']
        if total_votes > 0:
            left_share = district['left_votes'] / total_votes
            right_share = district['right_votes'] / total_votes
            
            if left_share > right_share:
                color = '#ff6b6b'  # Red for center-left
                winner = "Center-Left"
            else:
                color = '#4ecdc4'  # Blue for center-right
                winner = "Center-Right"
        else:
            color = '#gray'
            winner = "Tie"
        
        # Plot district communes
        for commune_idx in district['communes']:
            geom = optimizer.geometries[commune_idx]
            if hasattr(geom, 'exterior'):
                x, y = geom.exterior.xy
                ax.fill(x, y, color=color, alpha=0.7)
                ax.plot(x, y, color='black', linewidth=0.5)
    
    ax.set_aspect('equal')
    ax.set_xlim(optimizer.gdf.bounds.minx.min(), optimizer.gdf.bounds.maxx.max())
    ax.set_ylim(optimizer.gdf.bounds.miny.min(), optimizer.gdf.bounds.maxy.max())
    ax.set_title(f'Optimized Districts - Center-Left Wins: {final_wins}/{config.target_districts}', fontsize=16)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#ff6b6b', alpha=0.7, label='Center-Left Districts'),
        Patch(facecolor='#4ecdc4', alpha=0.7, label='Center-Right Districts')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    plt.savefig("results/final_districts.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   Final district map saved to results/final_districts.png")
    
    # Summary
    print("\n=== Demo Complete ===")
    print(f"Results:")
    print(f"  - Center-left wins: {final_wins}/{config.target_districts} districts ({win_rate:.1%})")
    print(f"  - Optimization score: {score:.3f}")
    print(f"  - Generated files:")
    print(f"    * results/gerrymandering_simulation.gif (optimization animation)")
    print(f"    * results/final_districts.png (final district map)")
    print(f"    * results/parameter_analysis.png (parameter performance)")
    print(f"    * results/sample_vote_distribution.png (vote distribution)")
    
    print(f"\nThe library successfully optimized district boundaries to favor the center-left coalition!")
    print(f"Starting from a random assignment, the algorithm achieved {win_rate:.1%} win rate for the target party.")

if __name__ == "__main__":
    main()