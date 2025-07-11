#!/usr/bin/env python3
"""
Visualization script for Italian gerrymandering optimization results.

This script creates various plots and visualizations to analyze the optimization results.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import folium
from typing import Optional, Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style for plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class ResultsVisualizer:
    """Class for visualizing gerrymandering optimization results."""
    
    def __init__(self, results_dir: str = "emilia_romagna_results"):
        """
        Initialize the visualizer.
        
        Args:
            results_dir: Directory containing optimization results
        """
        self.results_dir = results_dir
        self.history_df = None
        self.district_stats_df = None
        self.district_map_gdf = None
        
        self._load_results()
    
    def _load_results(self):
        """Load optimization results from files."""
        try:
            # Load optimization history
            history_path = os.path.join(self.results_dir, "optimization_history.csv")
            if os.path.exists(history_path):
                self.history_df = pd.read_csv(history_path)
                logger.info(f"Loaded optimization history with {len(self.history_df)} steps")
            
            # Load district statistics
            stats_path = os.path.join(self.results_dir, "district_statistics.csv")
            if os.path.exists(stats_path):
                self.district_stats_df = pd.read_csv(stats_path)
                logger.info(f"Loaded district statistics for {len(self.district_stats_df)} districts")
            
            # Load district map
            map_path = os.path.join(self.results_dir, "optimized_districts.geojson")
            if os.path.exists(map_path):
                self.district_map_gdf = gpd.read_file(map_path)
                logger.info(f"Loaded district map with {len(self.district_map_gdf)} communes")
                
        except Exception as e:
            logger.error(f"Error loading results: {str(e)}")
    
    def plot_optimization_history(self, save_path: Optional[str] = None):
        """Plot the optimization history showing score progression."""
        if self.history_df is None:
            logger.warning("No optimization history data available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Gerrymandering Optimization History', fontsize=16, fontweight='bold')
        
        # Score progression
        axes[0, 0].plot(self.history_df['steps'], self.history_df['scores'], 'b-', linewidth=2)
        axes[0, 0].set_title('Score Progression')
        axes[0, 0].set_xlabel('Step')
        axes[0, 0].set_ylabel('Score (Lower is Better)')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Temperature progression
        axes[0, 1].plot(self.history_df['steps'], self.history_df['temperatures'], 'r-', linewidth=2)
        axes[0, 1].set_title('Temperature Progression')
        axes[0, 1].set_xlabel('Step')
        axes[0, 1].set_ylabel('Temperature')
        axes[0, 1].set_yscale('log')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Population standard deviation
        axes[1, 0].plot(self.history_df['steps'], self.history_df['population_stds'], 'g-', linewidth=2)
        axes[1, 0].set_title('Population Standard Deviation')
        axes[1, 0].set_xlabel('Step')
        axes[1, 0].set_ylabel('Population Std Dev')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Seat deviation
        axes[1, 1].plot(self.history_df['steps'], self.history_df['seat_deviations'], 'm-', linewidth=2)
        axes[1, 1].set_title('Seat Deviation')
        axes[1, 1].set_xlabel('Step')
        axes[1, 1].set_ylabel('Seat Deviation')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Optimization history plot saved to {save_path}")
        
        plt.show()
    
    def plot_district_statistics(self, save_path: Optional[str] = None):
        """Plot district statistics."""
        if self.district_stats_df is None:
            logger.warning("No district statistics data available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('District Statistics', fontsize=16, fontweight='bold')
        
        # Population distribution
        axes[0, 0].bar(self.district_stats_df['district_id'], self.district_stats_df['population'])
        axes[0, 0].set_title('District Populations')
        axes[0, 0].set_xlabel('District ID')
        axes[0, 0].set_ylabel('Population')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Commune count distribution
        axes[0, 1].bar(self.district_stats_df['district_id'], self.district_stats_df['commune_count'])
        axes[0, 1].set_title('District Commune Counts')
        axes[0, 1].set_xlabel('District ID')
        axes[0, 1].set_ylabel('Number of Communes')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Compactness distribution
        axes[1, 0].bar(self.district_stats_df['district_id'], self.district_stats_df['compactness'])
        axes[1, 0].set_title('District Compactness')
        axes[1, 0].set_xlabel('District ID')
        axes[1, 0].set_ylabel('Compactness Score')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Population vs Commune count scatter
        axes[1, 1].scatter(self.district_stats_df['commune_count'], self.district_stats_df['population'])
        axes[1, 1].set_title('Population vs Commune Count')
        axes[1, 1].set_xlabel('Number of Communes')
        axes[1, 1].set_ylabel('Population')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"District statistics plot saved to {save_path}")
        
        plt.show()
    
    def create_interactive_map(self, save_path: Optional[str] = None):
        """Create an interactive map showing the district boundaries."""
        if self.district_map_gdf is None:
            logger.warning("No district map data available")
            return None
        
        # Calculate center of the map
        bounds = self.district_map_gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=8,
            tiles='OpenStreetMap'
        )
        
        # Add district boundaries
        for idx, row in self.district_map_gdf.iterrows():
            # Create a color based on district ID
            color = plt.cm.Set3(row['district_id'] % 12)
            color_hex = '#{:02x}{:02x}{:02x}'.format(
                int(color[0] * 255), 
                int(color[1] * 255), 
                int(color[2] * 255)
            )
            
            # Add commune to map
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x, color=color_hex: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                },
                tooltip=f"Commune: {row.get('name', 'Unknown')}<br>District: {row['district_id']}"
            ).add_to(m)
        
        if save_path:
            m.save(save_path)
            logger.info(f"Interactive map saved to {save_path}")
        
        return m
    
    def plot_optimization_metrics(self, save_path: Optional[str] = None):
        """Plot key optimization metrics."""
        if self.history_df is None:
            logger.warning("No optimization history data available")
            return
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Key Optimization Metrics', fontsize=16, fontweight='bold')
        
        # Score vs Temperature
        axes[0].scatter(self.history_df['temperatures'], self.history_df['scores'], alpha=0.6)
        axes[0].set_xscale('log')
        axes[0].set_xlabel('Temperature')
        axes[0].set_ylabel('Score')
        axes[0].set_title('Score vs Temperature')
        axes[0].grid(True, alpha=0.3)
        
        # Population balance over time
        axes[1].plot(self.history_df['steps'], self.history_df['population_stds'], 'g-', linewidth=2)
        axes[1].set_xlabel('Step')
        axes[1].set_ylabel('Population Standard Deviation')
        axes[1].set_title('Population Balance Over Time')
        axes[1].grid(True, alpha=0.3)
        
        # Seat deviation over time
        axes[2].plot(self.history_df['steps'], self.history_df['seat_deviations'], 'r-', linewidth=2)
        axes[2].set_xlabel('Step')
        axes[2].set_ylabel('Seat Deviation')
        axes[2].set_title('Seat Deviation Over Time')
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Optimization metrics plot saved to {save_path}")
        
        plt.show()
    
    def generate_summary_report(self, save_path: Optional[str] = None):
        """Generate a comprehensive summary report."""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("ITALIAN GERRYMANDERING OPTIMIZATION REPORT")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        if self.history_df is not None:
            report_lines.append("OPTIMIZATION HISTORY:")
            report_lines.append(f"  Total steps: {len(self.history_df)}")
            report_lines.append(f"  Initial score: {self.history_df['scores'].iloc[0]:.2f}")
            report_lines.append(f"  Final score: {self.history_df['scores'].iloc[-1]:.2f}")
            report_lines.append(f"  Score improvement: {self.history_df['scores'].iloc[0] - self.history_df['scores'].iloc[-1]:.2f}")
            report_lines.append(f"  Initial temperature: {self.history_df['temperatures'].iloc[0]:.2f}")
            report_lines.append(f"  Final temperature: {self.history_df['temperatures'].iloc[-1]:.2f}")
            report_lines.append("")
        
        if self.district_stats_df is not None:
            report_lines.append("DISTRICT STATISTICS:")
            report_lines.append(f"  Number of districts: {len(self.district_stats_df)}")
            report_lines.append(f"  Total population: {self.district_stats_df['population'].sum():,.0f}")
            report_lines.append(f"  Average district population: {self.district_stats_df['population'].mean():,.0f}")
            report_lines.append(f"  Population standard deviation: {self.district_stats_df['population'].std():,.0f}")
            report_lines.append(f"  Population coefficient of variation: {self.district_stats_df['population'].std() / self.district_stats_df['population'].mean():.3f}")
            report_lines.append(f"  Average compactness: {self.district_stats_df['compactness'].mean():.3f}")
            report_lines.append(f"  Total communes: {self.district_stats_df['commune_count'].sum()}")
            report_lines.append("")
            
            # District details
            report_lines.append("DISTRICT DETAILS:")
            for _, row in self.district_stats_df.iterrows():
                report_lines.append(f"  District {row['district_id']}: {row['population']:,.0f} people, {row['commune_count']} communes, compactness {row['compactness']:.3f}")
            report_lines.append("")
        
        if self.history_df is not None:
            report_lines.append("OPTIMIZATION METRICS:")
            final_pop_std = self.history_df['population_stds'].iloc[-1]
            final_seat_dev = self.history_df['seat_deviations'].iloc[-1]
            report_lines.append(f"  Final population standard deviation: {final_pop_std:,.0f}")
            report_lines.append(f"  Final seat deviation: {final_seat_dev}")
            report_lines.append("")
        
        report_lines.append("=" * 60)
        
        report_text = "\n".join(report_lines)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Summary report saved to {save_path}")
        
        print(report_text)
        return report_text
    
    def create_all_visualizations(self, output_dir: str = "visualizations"):
        """Create all visualizations and save them to the output directory."""
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Creating visualizations in {output_dir}")
        
        # Create plots
        self.plot_optimization_history(os.path.join(output_dir, "optimization_history.png"))
        self.plot_district_statistics(os.path.join(output_dir, "district_statistics.png"))
        self.plot_optimization_metrics(os.path.join(output_dir, "optimization_metrics.png"))
        
        # Create interactive map
        self.create_interactive_map(os.path.join(output_dir, "district_map.html"))
        
        # Generate report
        self.generate_summary_report(os.path.join(output_dir, "summary_report.txt"))
        
        logger.info("All visualizations created successfully!")


def analyze_multiple_experiments(experiment_dirs: List[str]):
    """Analyze results from multiple experiments."""
    logger.info(f"Analyzing {len(experiment_dirs)} experiments")
    
    all_results = []
    
    for exp_dir in experiment_dirs:
        if not os.path.exists(exp_dir):
            logger.warning(f"Experiment directory not found: {exp_dir}")
            continue
        
        try:
            # Load history
            history_path = os.path.join(exp_dir, "optimization_history.csv")
            if os.path.exists(history_path):
                history_df = pd.read_csv(history_path)
                final_score = history_df['scores'].iloc[-1]
                final_pop_std = history_df['population_stds'].iloc[-1]
                final_seat_dev = history_df['seat_deviations'].iloc[-1]
                
                all_results.append({
                    'experiment': exp_dir,
                    'final_score': final_score,
                    'final_population_std': final_pop_std,
                    'final_seat_deviation': final_seat_dev,
                    'steps': len(history_df)
                })
        except Exception as e:
            logger.error(f"Error analyzing experiment {exp_dir}: {str(e)}")
    
    if all_results:
        results_df = pd.DataFrame(all_results)
        
        # Create comparison plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Multiple Experiment Comparison', fontsize=16, fontweight='bold')
        
        # Final scores
        axes[0].bar(range(len(results_df)), results_df['final_score'])
        axes[0].set_title('Final Scores')
        axes[0].set_xlabel('Experiment')
        axes[0].set_ylabel('Score')
        axes[0].set_xticks(range(len(results_df)))
        axes[0].set_xticklabels([exp.split('_')[-1] for exp in results_df['experiment']], rotation=45)
        
        # Population standard deviations
        axes[1].bar(range(len(results_df)), results_df['final_population_std'])
        axes[1].set_title('Final Population Standard Deviations')
        axes[1].set_xlabel('Experiment')
        axes[1].set_ylabel('Population Std Dev')
        axes[1].set_xticks(range(len(results_df)))
        axes[1].set_xticklabels([exp.split('_')[-1] for exp in results_df['experiment']], rotation=45)
        
        # Seat deviations
        axes[2].bar(range(len(results_df)), results_df['final_seat_deviation'])
        axes[2].set_title('Final Seat Deviations')
        axes[2].set_xlabel('Experiment')
        axes[2].set_ylabel('Seat Deviation')
        axes[2].set_xticks(range(len(results_df)))
        axes[2].set_xticklabels([exp.split('_')[-1] for exp in results_df['experiment']], rotation=45)
        
        plt.tight_layout()
        plt.savefig("multiple_experiments_comparison.png", dpi=300, bbox_inches='tight')
        plt.show()
        
        # Print summary
        print("\nMultiple Experiment Summary:")
        print(f"Best score: {results_df['final_score'].min():.2f}")
        print(f"Worst score: {results_df['final_score'].max():.2f}")
        print(f"Average score: {results_df['final_score'].mean():.2f}")
        print(f"Score standard deviation: {results_df['final_score'].std():.2f}")
        
        return results_df
    else:
        logger.warning("No valid experiment results found")
        return None


if __name__ == "__main__":
    # Create visualizations for the main experiment
    visualizer = ResultsVisualizer("emilia_romagna_results")
    visualizer.create_all_visualizations()
    
    # Check for multiple experiment directories
    experiment_dirs = [d for d in os.listdir(".") if d.startswith("experiment_run_")]
    if experiment_dirs:
        print(f"\nFound {len(experiment_dirs)} experiment directories")
        response = input("Do you want to analyze multiple experiments? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            analyze_multiple_experiments(experiment_dirs)