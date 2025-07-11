#!/usr/bin/env python3
"""
Create Simulation GIF
Generates an animated GIF showing the evolution of district maps during
simulated annealing optimization, with partisan statistics overlaid.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, PillowWriter
import geopandas as gpd
from shapely.geometry import Polygon, Point
import json
from pathlib import Path
from gerrymandering_optimizer import GerrymanderingOptimizer, Config

class SimulationGIFCreator:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.optimizer = None
        self.geometry_data = None
        self.voting_data = None
        
        # Coalition colors (adjust these to match your color scheme)
        self.coalition_colors = {
            'center-left': '#FF6B6B',  # Red
            'center-right': '#4ECDC4',  # Teal
            'neutral': '#95A5A6'       # Gray
        }
        
    def load_data(self):
        """Load geographical and voting data"""
        print("Loading data...")
        
        # Load geographical data
        geojson_path = self.data_dir / "emilia_romagna_communes.geojson"
        if geojson_path.exists():
            self.geometry_data = gpd.read_file(geojson_path)
        else:
            print(f"Warning: {geojson_path} not found")
            return False
        
        # Load voting data
        csv_path = self.data_dir / "emilia_romagna_voting.csv"
        if csv_path.exists():
            self.voting_data = pd.read_csv(csv_path)
        else:
            print(f"Warning: {csv_path} not found")
            return False
        
        return True
    
    def create_simulation_gif(self, config=None, output_path="simulation.gif", 
                            frame_interval=100, max_frames=50):
        """Create a GIF showing the evolution of districts during optimization"""
        
        if not self.load_data():
            print("Failed to load data. Cannot create GIF.")
            return
        
        # Use default config if none provided
        if config is None:
            config = Config(
                temperature=1000,
                cooling_rate=0.99,
                steps=1000,
                target_districts=11,
                compactness_weight=0.3,
                population_weight=0.3
            )
        
        # Initialize optimizer
        self.optimizer = GerrymanderingOptimizer(self.data_dir, config)
        
        # Run optimization with history tracking
        print("Running optimization with history tracking...")
        final_score, final_districts, history = self.optimizer.optimize_with_history()
        
        # Create frames for GIF
        print("Creating animation frames...")
        frames = self._create_animation_frames(history, frame_interval, max_frames)
        
        # Create the animation
        print("Generating GIF...")
        self._create_animation(frames, output_path)
        
        print(f"GIF saved to {output_path}")
        return output_path
    
    def _create_animation_frames(self, history, frame_interval, max_frames):
        """Create frames for the animation"""
        frames = []
        
        # Sample frames at regular intervals
        step_indices = np.linspace(0, len(history['districts']) - 1, 
                                  min(max_frames, len(history['districts'])), 
                                  dtype=int)
        
        for i, step_idx in enumerate(step_indices):
            districts = history['districts'][step_idx]
            score = history['scores'][step_idx]
            temperature = history['temperatures'][step_idx]
            
            # Create frame
            frame = self._create_frame(districts, score, temperature, step_idx, i)
            frames.append(frame)
            
            if i % 10 == 0:
                print(f"  Created frame {i+1}/{len(step_indices)}")
        
        return frames
    
    def _create_frame(self, districts, score, temperature, step_idx, frame_idx):
        """Create a single frame of the animation"""
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Left subplot: Map
        self._plot_district_map(ax1, districts)
        
        # Right subplot: Statistics
        self._plot_statistics(ax2, districts, score, temperature, step_idx)
        
        # Add title
        fig.suptitle(f'Gerrymandering Optimization - Step {step_idx}', 
                    fontsize=16, fontweight='bold')
        
        return fig
    
    def _plot_district_map(self, ax, districts):
        """Plot the district map"""
        
        # Create a copy of geometry data for coloring
        plot_data = self.geometry_data.copy()
        
        # Assign districts to communes
        commune_to_district = {}
        for i, district in enumerate(districts):
            for commune_id in district['communes']:
                commune_to_district[commune_id] = i
        
        # Color communes based on their district
        colors = []
        for _, row in plot_data.iterrows():
            commune_id = row['id'] if 'id' in row else row.get('ISTAT', row.get('comune_id', 0))
            district_idx = commune_to_district.get(commune_id, -1)
            
            if district_idx >= 0:
                district = districts[district_idx]
                winner = district['winner']
                colors.append(self.coalition_colors.get(winner, self.coalition_colors['neutral']))
            else:
                colors.append(self.coalition_colors['neutral'])
        
        # Plot the map
        plot_data.plot(ax=ax, color=colors, edgecolor='black', linewidth=0.5)
        
        # Add district boundaries (simplified)
        for i, district in enumerate(districts):
            # Get district center for label
            district_communes = [c for c in district['communes'] if c in commune_to_district]
            if district_communes:
                # Find center commune
                center_commune = district_communes[len(district_communes)//2]
                center_row = plot_data[plot_data['id'] == center_commune]
                if not center_row.empty:
                    center = center_row.iloc[0].geometry.centroid
                    ax.annotate(f'D{i+1}', (center.x, center.y), 
                              fontsize=8, ha='center', va='center',
                              bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        ax.set_title('District Map', fontsize=14, fontweight='bold')
        ax.axis('off')
    
    def _plot_statistics(self, ax, districts, score, temperature, step_idx):
        """Plot statistics panel"""
        
        # Calculate statistics
        total_seats = len(districts)
        center_left_seats = sum(1 for d in districts if d['winner'] == 'center-left')
        center_right_seats = sum(1 for d in districts if d['winner'] == 'center-right')
        
        # Population statistics
        populations = [d['total_population'] for d in districts]
        population_std = np.std(populations)
        population_cv = population_std / np.mean(populations)
        
        # Create statistics display
        stats_text = f"""
OPTIMIZATION STATISTICS

Step: {step_idx}
Temperature: {temperature:.1f}
Score: {score:.3f}

SEAT DISTRIBUTION
Center-Left: {center_left_seats} seats ({center_left_seats/total_seats*100:.1f}%)
Center-Right: {center_right_seats} seats ({center_right_seats/total_seats*100:.1f}%)

POPULATION BALANCE
Mean Population: {np.mean(populations):,.0f}
Std Deviation: {population_std:,.0f}
Coefficient of Variation: {population_cv:.3f}

DISTRICT DETAILS
"""
        
        # Add district details
        for i, district in enumerate(districts):
            winner = district['winner']
            pop = district['total_population']
            stats_text += f"D{i+1}: {winner} ({pop:,.0f} pop)\n"
        
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
        
        # Add seat distribution pie chart
        if total_seats > 0:
            ax_pie = ax.inset_axes([0.6, 0.6, 0.35, 0.35])
            sizes = [center_left_seats, center_right_seats]
            labels = ['Center-Left', 'Center-Right']
            colors_pie = [self.coalition_colors['center-left'], self.coalition_colors['center-right']]
            
            if sum(sizes) > 0:
                ax_pie.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%')
                ax_pie.set_title('Seat Distribution')
        
        ax.set_title('Statistics', fontsize=14, fontweight='bold')
        ax.axis('off')
    
    def _create_animation(self, frames, output_path):
        """Create the GIF animation"""
        
        # Use the first frame to get figure properties
        fig = frames[0]
        
        # Create animation
        def animate(frame_idx):
            # Clear the figure
            fig.clear()
            
            # Get the frame
            frame_fig = frames[frame_idx]
            
            # Copy the frame content
            for i, ax in enumerate(frame_fig.axes):
                if i < len(fig.axes):
                    # Copy the content
                    for artist in ax.get_children():
                        if hasattr(artist, 'get_geometry'):
                            # This is a geometry object, copy it
                            pass
                        # Add other artists as needed
            
            return fig.axes
        
        # Create animation
        anim = FuncAnimation(fig, animate, frames=len(frames), 
                           interval=500, blit=False, repeat=True)
        
        # Save as GIF
        writer = PillowWriter(fps=2)
        anim.save(output_path, writer=writer)
        
        # Close all figures to free memory
        for frame in frames:
            plt.close(frame)
        plt.close(fig)
    
    def create_comparison_gif(self, configs, output_path="comparison.gif"):
        """Create a GIF comparing different optimization strategies"""
        
        if not self.load_data():
            print("Failed to load data. Cannot create comparison GIF.")
            return
        
        frames = []
        
        for i, config in enumerate(configs):
            print(f"Running optimization {i+1}/{len(configs)}...")
            
            # Run optimization
            optimizer = GerrymanderingOptimizer(self.data_dir, config)
            final_score, final_districts, history = optimizer.optimize()
            
            # Create frame
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # Plot map
            self._plot_district_map(ax1, final_districts)
            
            # Plot statistics
            self._plot_statistics(ax2, final_districts, final_score, 0, 0)
            
            # Add title
            config_name = f"Config {i+1}: T={config.temperature}, CR={config.cooling_rate}"
            fig.suptitle(config_name, fontsize=16, fontweight='bold')
            
            frames.append(fig)
        
        # Create animation
        fig = frames[0]
        
        def animate(frame_idx):
            return frames[frame_idx].axes
        
        anim = FuncAnimation(fig, animate, frames=len(frames), 
                           interval=2000, blit=False, repeat=True)
        
        # Save as GIF
        writer = PillowWriter(fps=1)
        anim.save(output_path, writer=writer)
        
        # Close figures
        for frame in frames:
            plt.close(frame)
        plt.close(fig)
        
        print(f"Comparison GIF saved to {output_path}")

def main():
    """Create simulation GIFs"""
    print("Creating Simulation GIFs")
    print("=" * 40)
    
    # Initialize GIF creator
    gif_creator = SimulationGIFCreator()
    
    # Create single simulation GIF
    print("Creating single simulation GIF...")
    gif_creator.create_simulation_gif(
        config=Config(
            temperature=1000,
            cooling_rate=0.99,
            steps=1000,
            target_districts=11,
            compactness_weight=0.3,
            population_weight=0.3
        ),
        output_path="simulation_evolution.gif",
        max_frames=30
    )
    
    # Create comparison GIF with different strategies
    print("\nCreating comparison GIF...")
    configs = [
        Config(temperature=500, cooling_rate=0.95, steps=500, target_districts=11),
        Config(temperature=1000, cooling_rate=0.99, steps=1000, target_districts=11),
        Config(temperature=2000, cooling_rate=0.995, steps=2000, target_districts=11),
    ]
    
    gif_creator.create_comparison_gif(configs, "strategy_comparison.gif")
    
    print("\nGIF creation complete!")

if __name__ == "__main__":
    main()