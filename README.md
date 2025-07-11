# Fast Gerrymandering Optimization Library

A high-performance Python library for optimizing electoral district boundaries using simulated annealing with numpy acceleration. This library allows you to create partisan-leaning district maps while maintaining valid geographical constraints.

## Features

- **Fast Optimization**: Uses numpy for efficient computation of district assignments and scoring
- **Partisan Targeting**: Optimize districts to favor specific political parties or coalitions
- **Geographical Constraints**: Maintains district contiguity and compactness
- **Parameter Analysis**: Comprehensive parameter sweep to find optimal settings
- **Visualization**: Generate GIFs showing optimization progress and parameter performance plots
- **Real Data Support**: Works with Italian electoral data and geographical boundaries

## Quick Start

```python
from fast_gerrymandering import FastGerryOptimizer, GerryConfig, GerrymanderingAnalyzer

# Configure optimization
config = GerryConfig(
    temperature=1000,
    cooling_rate=0.99,
    steps=1000,
    partisan_weight=2.0,
    target_party=0  # 0=center-left, 1=center-right
)

# Run optimization
optimizer = FastGerryOptimizer("comuni_italiani_trend_liste_2022_2024.geojson", config)
score, districts, history = optimizer.optimize()

# Create visualization
analyzer = GerrymanderingAnalyzer(optimizer)
analyzer.create_simulation_gif(history, "simulation.gif")
```

## Optimization Process

The library uses simulated annealing to optimize district boundaries:

1. **Initialization**: Randomly assign communes to districts
2. **Neighbor Generation**: Swap communes between districts
3. **Scoring**: Evaluate districts based on:
   - Population balance
   - Compactness (perimeter/area ratio)
   - Partisan advantage for target party
4. **Acceptance**: Accept better solutions or probabilistically accept worse ones
5. **Cooling**: Gradually reduce temperature to focus on local optima

## Parameter Analysis

The library includes comprehensive parameter analysis to find optimal settings:

### Key Parameters

- **Temperature**: Controls exploration vs exploitation (500-2000)
- **Cooling Rate**: How quickly to focus on local optima (0.95-0.995)
- **Steps**: Number of optimization iterations (500-2000)
- **Partisan Weight**: How much to prioritize partisan advantage (0.5-5.0)
- **Target Party**: Which party to favor (0=center-left, 1=center-right)

### Performance Analysis

The parameter sweep runs multiple simulations to find the best settings:

```python
from fast_gerrymandering import run_parameter_sweep

# Run comprehensive parameter analysis
results = run_parameter_sweep("comuni_italiani_trend_liste_2022_2024.geojson")
```

This generates:
- `parameter_sweep_results.csv`: Raw results from all simulations
- `parameter_analysis.png`: Plots showing parameter effects on win rates
- `best_parameters_heatmap.png`: Heatmap of optimal parameters

## Visualization

### Simulation GIF

The library generates animated GIFs showing the optimization process:

![Gerrymandering Simulation](results/gerrymandering_simulation.gif)

The GIF shows:
- **Left Panel**: District map with party colors (red=center-left, blue=center-right)
- **Right Panel**: Optimization progress (score and target party wins over time)

### Parameter Performance Plots

Analysis plots show how different parameters affect optimization success:

![Parameter Analysis](results/parameter_analysis.png)

The plots demonstrate:
- Effect of partisan weight on win rates
- Temperature impact on optimization success
- Cooling rate influence on convergence
- Steps required for optimal results

## Data Format

The library expects a GeoJSON file with voting data columns:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {...},
      "properties": {
        "PARTITO DEMOCRATICO": 1234,
        "MOVIMENTO 5 STELLE": 567,
        "ALLEANZA VERDI E SINISTRA": 89,
        "FRATELLI D'ITALIA": 2345,
        "LEGA SALVINI PREMIER": 678,
        "FORZA ITALIA - NOI MODERATI - PPE": 901
      }
    }
  ]
}
```

## Party Coalitions

The library automatically groups parties into coalitions:

**Center-Left Coalition:**
- Partito Democratico
- Movimento 5 Stelle
- Alleanza Verdi e Sinistra

**Center-Right Coalition:**
- Fratelli d'Italia
- Lega Salvini Premier
- Forza Italia - Noi Moderati - PPE

## Installation

```bash
pip install numpy pandas geopandas matplotlib seaborn shapely
```

## Usage Examples

### Basic Optimization

```python
# Optimize for center-left advantage
config = GerryConfig(target_party=0, partisan_weight=2.0)
optimizer = FastGerryOptimizer("data.geojson", config)
score, districts, history = optimizer.optimize()
```

### Parameter Sweep

```python
# Find best parameters for center-right advantage
results = run_parameter_sweep("data.geojson", output_dir="center_right_results")
```

### Custom Analysis

```python
# Analyze specific configuration
config = GerryConfig(
    temperature=1500,
    cooling_rate=0.98,
    steps=1500,
    partisan_weight=3.0,
    target_party=1
)

optimizer = FastGerryOptimizer("data.geojson", config)
score, districts, history = optimizer.optimize()

# Create custom visualization
analyzer = GerrymanderingAnalyzer(optimizer)
analyzer.create_simulation_gif(history, "custom_simulation.gif")
```

## Performance

The library is optimized for speed:

- **Numpy Arrays**: All voting data stored as efficient numpy arrays
- **Vectorized Operations**: Batch processing of district calculations
- **Efficient Neighbor Generation**: Smart swapping algorithms
- **Memory Optimization**: Minimal data copying during optimization

Typical performance:
- 1000 steps: ~30 seconds
- 2000 steps: ~60 seconds
- Parameter sweep (360 combinations): ~3 hours

## Research Applications

This library is designed for:

- **Political Science Research**: Study gerrymandering effects
- **Electoral Reform**: Analyze different districting approaches
- **Algorithm Development**: Test new optimization strategies
- **Educational Purposes**: Demonstrate gerrymandering concepts

## Limitations

- **Contiguity**: Simplified contiguity checking (assumes all swaps are valid)
- **Geographical Accuracy**: Uses simplified geometry calculations
- **Party Coalitions**: Fixed party groupings (customizable in code)

## Contributing

Contributions welcome! Areas for improvement:

- More sophisticated contiguity validation
- Additional optimization algorithms
- Enhanced visualization options
- Support for more data formats

## License

MIT License - see LICENSE file for details.

## Citation

If you use this library in research, please cite:

```bibtex
@software{fast_gerrymandering,
  title={Fast Gerrymandering Optimization Library},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/fast-gerrymandering}
}
```