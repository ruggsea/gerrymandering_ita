# Gerrymandering in Italy: Computational Analysis

## Research Question

**Is partisan gerrymandering possible in Italy?**

This research investigates whether electoral districts in Italy can be algorithmically manipulated to favor specific political coalitions. Using the Emilia-Romagna region as a case study with 2022 electoral data, we test whether simulated annealing optimization can create district boundaries that significantly alter electoral outcomes.

## Overview

Electoral gerrymandering is the manipulation of electoral district boundaries to favor a particular party or coalition. While extensively studied in systems like the US, its applicability to Italian electoral geography and multi-party system remains unclear.

This project:
1. Implements simulated annealing to optimize district boundaries
2. Tests different optimization objectives (neutral, pro-left, pro-right)
3. Evaluates whether significant partisan advantages can be achieved
4. Visualizes the optimization process and outcomes

## Methodology

### Algorithm: Simulated Annealing
- **Initialization**: Random seed communes grow into districts
- **Proposal**: Randomly reassign communes to neighboring districts
- **Acceptance**: Based on objective function and temperature
- **Cooling**: Gradual temperature reduction

### Objective Function
Combines three weighted components:
- **Population Balance**: Minimize population variance across districts
- **Seat Deviation**: Deviation from proportional representation
- **Partisan Advantage**: Maximize seats for target coalition

### Test Region
- **Emilia-Romagna**: 330 communes, 11 districts
- **Data**: 2022 Italian parliamentary elections
- **Coalitions**: Left (PD, AVS), Right (FdI, Lega, FI), Center (Azione-IV), Populist (M5S)

## Repository Structure

```
gerrymandering_ita/
├── src/
│   ├── gerrymander.py      # Core optimization algorithm
│   ├── data_loader.py      # Data loading utilities
│   └── visualizer.py       # Visualization and GIF generation
├── experiments/            # Experiment configurations
├── results/
│   ├── gifs/              # Animated optimization visualizations
│   ├── data/              # Result data (JSON, pickle)
│   └── logs/              # Execution logs
├── run_experiment.py       # Main experiment runner
├── README.md              # This file
└── requirements.txt       # Python dependencies
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Neutral Optimization (Baseline)
```bash
python run_experiment.py --goal neutral --steps 1000 --create_gif
```

### Run Partisan Experiments

**Moderate left-wing advantage:**
```bash
python run_experiment.py --goal maximize_left --strength moderate --steps 1000 --create_gif
```

**Extreme right-wing advantage:**
```bash
python run_experiment.py --goal maximize_right --strength extreme --steps 2000 --create_gif
```

**Mild partisan advantage:**
```bash
python run_experiment.py --goal maximize_left --strength mild --steps 1000
```

### Full Options
```
--goal              neutral | maximize_left | maximize_right
--strength          mild | moderate | extreme
--n_districts       Number of districts (default: 11)
--steps             Optimization steps (default: 1000)
--initial_temp      Initial temperature (default: 1000.0)
--cooling_rate      Temperature decay (default: 0.99)
--seed              Random seed for reproducibility
--create_gif        Generate animated GIF
--data_dir          Data directory (default: current dir)
--output_dir        Output directory (default: results/)
```

## Output

Each experiment produces:

1. **JSON results** (`results/data/<experiment>.json`):
   - Configuration parameters
   - Optimization history
   - Final district assignments

2. **Pickle file** (`results/data/<experiment>.pkl`):
   - Full GeoDataFrame with geometries
   - Complete optimization history
   - Districts at each step

3. **Comparison plot** (`results/<experiment>_comparison.png`):
   - Initial vs final district maps
   - Initial vs final seat distributions

4. **Animated GIF** (`results/gifs/<experiment>.gif`) [if --create_gif]:
   - Map evolution over time
   - Seat distribution changes
   - Score and temperature tracking

## Example Experiments

### Experiment 1: Neutral Baseline
**Objective**: Create compact, population-balanced districts
```bash
python run_experiment.py --goal neutral --steps 1000 --seed 42 --create_gif
```

### Experiment 2: Moderate Left Advantage
**Objective**: Favor left coalition moderately
```bash
python run_experiment.py --goal maximize_left --strength moderate --steps 1500 --seed 42 --create_gif
```

### Experiment 3: Extreme Right Advantage
**Objective**: Maximize right coalition seats aggressively
```bash
python run_experiment.py --goal maximize_right --strength extreme --steps 2000 --seed 42 --create_gif
```

## Data Sources

- **Electoral Data**: `politiche_2022_liste_camera_comuni.csv`
  - 2022 Italian parliamentary election results by commune
  - Vote shares for all parties

- **Geographic Data**: `gerrymandering_base.geojson`
  - Commune boundaries (MultiPolygon geometries)
  - 7,899 Italian communes

- **Population Data**: `POSAS_2024_it_Comuni.csv`
  - Population demographics by commune

## Key Findings

*(To be filled after running experiments)*

Results will show:
1. Can significant partisan advantages be achieved?
2. How do seat distributions change under different objectives?
3. Trade-offs between compactness, population balance, and partisan gain
4. Feasibility of gerrymandering in Italian multi-party context

## Technical Details

### Optimization Parameters

**Default configuration:**
- Initial temperature: 1000.0
- Final temperature: 0.01
- Cooling rate: 0.99
- Steps: 1000
- Save frequency: Every 10 steps

**Objective weights:**
- Neutral: `{population: 1.0, seats: 1.0, partisan: 0.0}`
- Moderate partisan: `{population: 0.1, seats: 0.0, partisan: 5.0}`
- Extreme partisan: `{population: 0.1, seats: 0.0, partisan: 50.0}`

### Visualization

GIF animations show:
- **Left panel**: District map with color-coded boundaries
- **Right panel**: Seat distribution evolution over time
  - Solid lines: actual seats won
  - Dashed lines: proportional representation baseline

## Future Directions

1. **National-scale analysis**: Expand to all 27 Italian electoral regions
2. **Compactness constraints**: Add geometric compactness measures
3. **Algorithm improvements**: Implement ReCom or other modern methods
4. **Statistical testing**: Compare to ensemble of random districting plans
5. **Multi-objective optimization**: Pareto frontier analysis

## Citation

```bibtex
@software{gerrymandering_italy_2024,
  title={Computational Analysis of Gerrymandering in Italy},
  author={[Your Name]},
  year={2024},
  url={https://github.com/[your-repo]}
}
```

## License

MIT License

## Contact

For questions or collaboration: [Your contact info]

---

**Note**: This is academic research software. Results should be validated and replicated before drawing policy conclusions.
