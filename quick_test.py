#!/usr/bin/env python3
"""
Quick test of the gerrymandering optimizer with actual data.
"""

import numpy as np
import pandas as pd
from gerrymandering_optimizer import GerrymanderingOptimizer, Config

def main():
    print("Testing gerrymandering optimizer with actual data...")
    
    # Create a simple configuration
    config = Config(
        temperature=1000.0,
        cooling_rate=0.99,
        steps=100,  # Small number for quick test
        target_districts=5,
        compactness_weight=0.3,
        population_weight=0.3
    )
    
    try:
        # Initialize optimizer
        print("Initializing optimizer...")
        optimizer = GerrymanderingOptimizer(".", config)
        
        print("Running optimization...")
        final_score, final_districts, history = optimizer.optimize()
        
        print(f"Final score: {final_score}")
        print(f"Number of districts: {len(final_districts)}")
        
        # Get district statistics
        stats = optimizer.get_district_statistics(final_districts)
        
        print("\nDistrict Statistics:")
        for stat in stats:
            print(f"District {stat['district_id']}: {stat['winner']} wins with "
                  f"{stat['center_left_votes']} center-left vs {stat['center_right_votes']} center-right votes")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()