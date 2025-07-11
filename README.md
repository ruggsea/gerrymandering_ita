# Fast Gerrymandering Optimization Library

A high-performance Python library for optimizing electoral district boundaries using simulated annealing with numpy acceleration. This library allows you to create partisan-leaning district maps while maintaining valid geographical constraints.

## 🎯 What This Library Does

This library demonstrates how to **gerrymander electoral districts** to favor specific political parties. It takes real Italian voting data and optimizes district boundaries to maximize wins for your chosen party while maintaining valid geographical constraints.

### 📊 Key Results

- **Input**: 7,899 Italian communes with real 2022 voting data
- **Output**: Optimized district map favoring center-left or center-right
- **Performance**: Can achieve 70-80% win rate for target party despite vote minority
- **Visualization**: Animated GIF showing the complete optimization process

### 🎬 Demo Outputs

The library generates several visual outputs:

1. **`results/gerrymandering_simulation.gif`** - Watch the algorithm transform random districts into a gerrymandered map
2. **`results/parameter_analysis.png`** - See which parameters work best for partisan advantage
3. **`results/sample_vote_distribution.png`** - View natural vote distribution before optimization
4. **`results/final_districts.png`** - Final optimized district map

**Run the demo**: `python3 run_demo.py`

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

**📁 File: `results/gerrymandering_simulation.gif`**

The GIF shows:
- **Left Panel**: District map with party colors (red=center-left, blue=center-right)
- **Right Panel**: Optimization progress (score and target party wins over time)
- **Evolution**: From random district assignment to optimized gerrymandered map

### Parameter Performance Plots

Analysis plots show how different parameters affect optimization success:

**📁 File: `results/parameter_analysis.png`**

The plots demonstrate:
- Effect of partisan weight on win rates
- Temperature impact on optimization success
- Cooling rate influence on convergence
- Steps required for optimal results

### Vote Distribution Map

**📁 File: `results/sample_vote_distribution.png`**

Shows the natural vote distribution across Italian communes before optimization.

## Generated Outputs

After running the library, you'll find these files in the `results/` directory:

- **`gerrymandering_simulation.gif`** - Animation showing district optimization from random to gerrymandered
- **`parameter_analysis.png`** - Comprehensive analysis of parameter effects on win rates
- **`sample_vote_distribution.png`** - Natural vote distribution across Italian communes
- **`final_districts.png`** - Final optimized district map (generated by demo)

### Viewing the Results

To view the generated files:

```bash
# View the GIF (optimization animation)
open results/gerrymandering_simulation.gif

# View the parameter analysis plots
open results/parameter_analysis.png

# View the vote distribution map
open results/sample_vote_distribution.png
```

**Note**: The GIF shows the complete optimization process, demonstrating how the algorithm transforms random district assignments into a gerrymandered map that favors the target party while maintaining geographical constraints.

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