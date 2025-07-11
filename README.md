# Italian Gerrymandering Optimization Library

A comprehensive Python library for optimizing Italian voting district boundaries using simulated annealing to minimize gerrymandering effects. This library is designed for research purposes and provides tools to analyze and optimize electoral district boundaries based on Italian voting data from the 2022 elections.

## Overview

This library implements a simulated annealing algorithm to optimize district boundaries for Italian voting districts, specifically focusing on the Emilia-Romagna region. The optimization aims to:

- **Minimize population imbalance** between districts
- **Maximize compactness** of district shapes
- **Reduce partisan bias** in district allocation
- **Ensure fair representation** in the electoral system

## Features

- **Simulated Annealing Optimization**: Robust optimization algorithm with configurable parameters
- **Italian Voting Data Integration**: Works with real Italian electoral data from 2022
- **Geographical Analysis**: Incorporates geographical boundaries and spatial relationships
- **Comprehensive Metrics**: Population balance, compactness, and partisan fairness measures
- **Visualization Tools**: Interactive maps and detailed analysis plots
- **Research-Ready**: Designed for academic research with detailed logging and export capabilities

## Installation

### Prerequisites

- Python 3.8 or higher
- Required system libraries for GeoPandas (GDAL, GEOS, PROJ)

### Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Key Dependencies

- `numpy`: Numerical computations
- `pandas`: Data manipulation
- `geopandas`: Geographical data processing
- `shapely`: Geometric operations
- `matplotlib` & `seaborn`: Data visualization
- `folium`: Interactive maps
- `scipy` & `scikit-learn`: Scientific computing

## Data Requirements

The library requires the following data files:

1. **Voting Data** (`politiche_2022_raw_votes.csv`): Raw voting results by commune
2. **Geographical Data** (`gerrymandering_base.geojson`): Commune boundaries and metadata
3. **Population Data** (`POSAS_2024_it_Comuni.csv`, optional): Population statistics

## Quick Start

### Basic Usage

```python
from gerrymandering_optimizer import OptimizationConfig, run_optimization_experiment

# Configure optimization parameters
config = OptimizationConfig(
    num_districts=11,
    initial_temperature=1000.0,
    cooling_rate=0.99,
    max_steps=1000
)

# Run optimization
optimizer = run_optimization_experiment(
    votes_file="politiche_2022_raw_votes.csv",
    geo_file="gerrymandering_base.geojson",
    population_file="POSAS_2024_it_Comuni.csv",
    config=config,
    output_dir="results"
)

print(f"Best score achieved: {optimizer.best_score}")
```

### Running Experiments

Use the provided script to run experiments with the exact parameters from the research logs:

```bash
python run_optimization.py
```

This will:
1. Analyze existing experiment results
2. Run a single optimization experiment
3. Optionally run multiple experiments for statistical analysis

### Visualization

Generate comprehensive visualizations of the results:

```bash
python visualize_results.py
```

This creates:
- Optimization history plots
- District statistics visualizations
- Interactive maps
- Summary reports

## Library Components

### Core Classes

#### `OptimizationConfig`
Configuration class for optimization parameters:
- Simulated annealing parameters (temperature, cooling rate)
- District constraints (number, size limits)
- Optimization weights (population, compactness, partisan fairness)

#### `ItalianVotingData`
Handles data loading and preprocessing:
- Loads voting, geographical, and population data
- Combines multiple data sources
- Provides clean interfaces for optimization

#### `DistrictMap`
Represents a district configuration:
- Manages commune-to-district assignments
- Calculates district statistics
- Handles geometric operations

#### `GerrymanderingOptimizer`
Main optimization engine:
- Implements simulated annealing algorithm
- Manages optimization history
- Exports results in multiple formats

### Optimization Algorithm

The library uses **Simulated Annealing** with the following key features:

1. **Initialization**: Random assignment of communes to districts
2. **Neighbor Generation**: Swapping communes between districts
3. **Acceptance Criterion**: Probabilistic acceptance based on temperature
4. **Cooling Schedule**: Exponential temperature reduction
5. **Termination**: Based on minimum temperature or maximum steps

### Scoring Function

The optimization minimizes a weighted combination of:

1. **Population Balance**: Standard deviation of district populations
2. **Compactness**: Area-to-perimeter ratio (isoperimetric quotient)
3. **Partisan Fairness**: Measures of electoral bias (extensible)

## Research Context

### Italian Electoral System

The Italian electoral system uses a mixed system with:
- Single-member districts for some seats
- Proportional representation for others
- Regional variations in district allocation

### Emilia-Romagna Region

The experiments focus on Emilia-Romagna, which has:
- 11 electoral districts
- ~330 communes
- Diverse political landscape
- Significant population variations

### Gerrymandering Concerns

The optimization addresses:
- **Population malapportionment**: Unequal district sizes
- **Geographic gerrymandering**: Irregular district shapes
- **Partisan bias**: Favoring specific political parties

## Experiment Parameters

Based on the analysis of existing experiment logs, the library uses these parameters:

```
Region: Emilia-Romagna
Districts: 11
Initial Temperature: 1000.0
Cooling Rate: 0.99
Min Temperature: 0.01
Max Steps: 1000
Population Weight: 1.0
Compactness Weight: 1.0
Partisan Fairness Weight: 1.0
```

## Output Files

The library generates several output files:

### Optimization Results
- `optimized_districts.geojson`: District boundaries with assignments
- `optimization_history.csv`: Step-by-step optimization progress
- `district_statistics.csv`: Final district statistics

### Visualizations
- `optimization_history.png`: Score and temperature progression
- `district_statistics.png`: District population and compactness
- `district_map.html`: Interactive map of districts
- `summary_report.txt`: Comprehensive analysis report

## Advanced Usage

### Custom Optimization

```python
from gerrymandering_optimizer import ItalianVotingData, GerrymanderingOptimizer, OptimizationConfig

# Load data
voting_data = ItalianVotingData(
    votes_file="politiche_2022_raw_votes.csv",
    geo_file="gerrymandering_base.geojson",
    population_file="POSAS_2024_it_Comuni.csv"
)

# Custom configuration
config = OptimizationConfig(
    num_districts=15,
    initial_temperature=500.0,
    cooling_rate=0.95,
    population_weight=2.0,
    compactness_weight=0.5
)

# Create optimizer
optimizer = GerrymanderingOptimizer(voting_data, config)

# Run optimization
best_map = optimizer.optimize(save_path="custom_result.pkl")

# Export results
optimizer.export_results("custom_results")
```

### Multiple Experiments

```python
from run_optimization import run_multiple_experiments

# Run 10 experiments with different random seeds
results = run_multiple_experiments(num_runs=10)

# Analyze results
for result in results:
    print(f"Run {result['run']}: Score {result['best_score']:.2f}")
```

## Performance Considerations

### Computational Requirements
- **Memory**: ~2-4GB for Emilia-Romagna region
- **Time**: 10-30 minutes per experiment (1000 steps)
- **Storage**: ~100MB per experiment

### Optimization Tips
- Reduce `max_steps` for faster experiments
- Adjust `cooling_rate` for different convergence behavior
- Modify weights to focus on specific objectives

## Research Applications

This library is designed for:

1. **Academic Research**: Electoral system analysis
2. **Policy Analysis**: Redistricting impact assessment
3. **Comparative Studies**: Different optimization approaches
4. **Educational Purposes**: Understanding gerrymandering

## Contributing

This library is designed for research purposes. Contributions are welcome for:

- Additional optimization algorithms
- Enhanced visualization tools
- Support for other Italian regions
- Improved partisan fairness metrics

## License

This project is designed for research and educational purposes. Please ensure compliance with data usage agreements and research ethics guidelines.

## Citation

If you use this library in your research, please cite:

```
Italian Gerrymandering Optimization Library (2024)
A simulated annealing approach to electoral district optimization
Research Assistant, Cursor AI
```

## Support

For questions or issues:
1. Check the documentation and examples
2. Review the log files for debugging information
3. Ensure all data files are properly formatted
4. Verify system dependencies are installed

## Future Enhancements

Planned improvements include:
- Support for multiple Italian regions
- Advanced partisan fairness metrics
- Machine learning-based optimization
- Real-time visualization during optimization
- Integration with electoral simulation tools