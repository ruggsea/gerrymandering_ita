#!/usr/bin/env python3
"""
Test script for the Italian Gerrymandering Optimization Library.

This script tests the basic functionality of the library components.
"""

import os
import sys
import logging
from gerrymandering_optimizer import (
    OptimizationConfig, 
    ItalianVotingData, 
    DistrictMap, 
    GerrymanderingOptimizer
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_loading():
    """Test data loading functionality."""
    logger.info("Testing data loading...")
    
    try:
        # Check if required files exist
        required_files = [
            "politiche_2022_raw_votes.csv",
            "gerrymandering_base.geojson"
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                logger.error(f"Required file not found: {file_path}")
                return False
        
        # Test data loading
        voting_data = ItalianVotingData(
            votes_file="politiche_2022_raw_votes.csv",
            geo_file="gerrymandering_base.geojson",
            population_file="POSAS_2024_it_Comuni.csv" if os.path.exists("POSAS_2024_it_Comuni.csv") else None
        )
        
        commune_data = voting_data.get_commune_data()
        logger.info(f"Successfully loaded data for {len(commune_data)} communes")
        
        # Check data structure
        expected_columns = ['CODICE ISTAT', 'geometry']
        for col in expected_columns:
            if col not in commune_data.columns:
                logger.error(f"Missing expected column: {col}")
                return False
        
        logger.info("Data loading test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Data loading test failed: {str(e)}")
        return False


def test_configuration():
    """Test configuration validation."""
    logger.info("Testing configuration...")
    
    try:
        # Test valid configuration
        config = OptimizationConfig(
            num_districts=11,
            initial_temperature=1000.0,
            cooling_rate=0.99,
            max_steps=1000
        )
        logger.info("Valid configuration created successfully")
        
        # Test invalid configurations
        try:
            invalid_config = OptimizationConfig(initial_temperature=-1)
            logger.error("Should have raised ValueError for negative temperature")
            return False
        except ValueError:
            logger.info("Correctly caught invalid temperature")
        
        try:
            invalid_config = OptimizationConfig(cooling_rate=1.5)
            logger.error("Should have raised ValueError for cooling rate > 1")
            return False
        except ValueError:
            logger.info("Correctly caught invalid cooling rate")
        
        logger.info("Configuration test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Configuration test failed: {str(e)}")
        return False


def test_district_map():
    """Test district map functionality."""
    logger.info("Testing district map...")
    
    try:
        # Load data
        voting_data = ItalianVotingData(
            votes_file="politiche_2022_raw_votes.csv",
            geo_file="gerrymandering_base.geojson"
        )
        
        commune_data = voting_data.get_commune_data()
        
        # Create district map
        district_map = DistrictMap(commune_data, num_districts=5)
        
        # Check district assignments
        total_communes = len(district_map.district_assignments)
        expected_communes = len(commune_data)
        
        if total_communes != expected_communes:
            logger.error(f"Expected {expected_communes} communes, got {total_communes}")
            return False
        
        # Check district statistics
        if len(district_map.district_stats) != 5:
            logger.error(f"Expected 5 districts, got {len(district_map.district_stats)}")
            return False
        
        # Test commune swapping
        commune_indices = list(district_map.district_assignments.keys())
        if len(commune_indices) >= 2:
            commune1, commune2 = commune_indices[0], commune_indices[1]
            district1_before = district_map.get_commune_district(commune1)
            district2_before = district_map.get_commune_district(commune2)
            
            success = district_map.swap_communes(commune1, commune2)
            
            if success:
                district1_after = district_map.get_commune_district(commune1)
                district2_after = district_map.get_commune_district(commune2)
                
                if district1_after == district2_before and district2_after == district1_before:
                    logger.info("Commune swapping test passed!")
                else:
                    logger.error("Commune swapping failed")
                    return False
            else:
                logger.error("Commune swapping returned False")
                return False
        
        logger.info("District map test passed!")
        return True
        
    except Exception as e:
        logger.error(f"District map test failed: {str(e)}")
        return False


def test_optimizer():
    """Test optimizer functionality."""
    logger.info("Testing optimizer...")
    
    try:
        # Load data
        voting_data = ItalianVotingData(
            votes_file="politiche_2022_raw_votes.csv",
            geo_file="gerrymandering_base.geojson"
        )
        
        # Create configuration
        config = OptimizationConfig(
            num_districts=3,  # Small number for testing
            initial_temperature=100.0,
            cooling_rate=0.9,
            max_steps=10  # Small number for testing
        )
        
        # Create optimizer
        optimizer = GerrymanderingOptimizer(voting_data, config)
        
        # Test initialization
        initial_map = optimizer.initialize_map()
        if initial_map is None:
            logger.error("Failed to initialize map")
            return False
        
        # Test neighbor generation
        neighbor_map = optimizer.get_neighbor_solution(initial_map)
        if neighbor_map is None:
            logger.error("Failed to generate neighbor solution")
            return False
        
        # Test scoring
        initial_score = initial_map.get_score(config)
        neighbor_score = neighbor_map.get_score(config)
        
        logger.info(f"Initial score: {initial_score}")
        logger.info(f"Neighbor score: {neighbor_score}")
        
        # Test short optimization run
        logger.info("Running short optimization test...")
        best_map = optimizer.optimize()
        
        if best_map is None:
            logger.error("Optimization failed")
            return False
        
        logger.info(f"Best score achieved: {optimizer.best_score}")
        
        logger.info("Optimizer test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Optimizer test failed: {str(e)}")
        return False


def test_export_functionality():
    """Test export functionality."""
    logger.info("Testing export functionality...")
    
    try:
        # Load data and run short optimization
        voting_data = ItalianVotingData(
            votes_file="politiche_2022_raw_votes.csv",
            geo_file="gerrymandering_base.geojson"
        )
        
        config = OptimizationConfig(
            num_districts=3,
            initial_temperature=100.0,
            cooling_rate=0.9,
            max_steps=5
        )
        
        optimizer = GerrymanderingOptimizer(voting_data, config)
        optimizer.optimize()
        
        # Test export
        test_output_dir = "test_output"
        optimizer.export_results(test_output_dir)
        
        # Check if files were created
        expected_files = [
            "optimized_districts.geojson",
            "optimization_history.csv",
            "district_statistics.csv"
        ]
        
        for filename in expected_files:
            filepath = os.path.join(test_output_dir, filename)
            if os.path.exists(filepath):
                logger.info(f"Export file created: {filename}")
            else:
                logger.warning(f"Export file missing: {filename}")
        
        # Clean up test directory
        import shutil
        if os.path.exists(test_output_dir):
            shutil.rmtree(test_output_dir)
        
        logger.info("Export functionality test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Export functionality test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all tests."""
    logger.info("=" * 50)
    logger.info("RUNNING ITALIAN GERRYMANDERING LIBRARY TESTS")
    logger.info("=" * 50)
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Configuration", test_configuration),
        ("District Map", test_district_map),
        ("Optimizer", test_optimizer),
        ("Export Functionality", test_export_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name} test...")
        try:
            if test_func():
                logger.info(f"✓ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test FAILED with exception: {str(e)}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"TEST SUMMARY: {passed}/{total} tests passed")
    logger.info("=" * 50)
    
    if passed == total:
        logger.info("🎉 All tests passed! The library is ready to use.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)