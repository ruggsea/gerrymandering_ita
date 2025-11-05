# Methodology: Computational Analysis of Gerrymandering in Italy

## Research Question

**Can electoral districts in Italy be algorithmically manipulated to create partisan advantage?**

This study investigates the feasibility of gerrymandering in the Italian electoral system using the Emilia-Romagna region as a case study with data from the 2022 parliamentary elections.

---

## 1. Study Design

### 1.1 Geographic Scope
- **Region**: Emilia-Romagna
- **Communes**: 330 municipalities
- **Target Districts**: 11 electoral districts
- **Electoral System**: Mixed-member proportional (focus on single-member plurality component)

### 1.2 Political Landscape
We aggregate parties into three coalitions:

| Coalition | Parties | Ideology |
|-----------|---------|----------|
| **Left** | PD (Partito Democratico), AVS (Alleanza Verdi e Sinistra) | Center-left, progressive |
| **Right** | FdI (Fratelli d'Italia), Lega, Forza Italia | Center-right, conservative |
| **Center** | Azione-Italia Viva, Calenda | Centrist, liberal |

**Baseline 2022 Results (Proportional)**:
- Left: 4.46 seats (40.6%)
- Right: 5.38 seats (48.9%)
- Center: 1.16 seats (10.5%)

---

## 2. Optimization Algorithms

We compare four optimization approaches:

### 2.1 Simulated Annealing (Primary)
**Rationale**: Well-established metaheuristic for combinatorial optimization with proven effectiveness in redistricting problems.

**Algorithm**:
```
Initialize: Random district assignment
For t = 1 to T:
    1. Propose: Move random commune to neighboring district
    2. Evaluate: Compute objective function score
    3. Accept with probability:
       - If Δscore < 0: accept (improvement)
       - Else: accept with P = exp(-Δscore / temperature)
    4. Cool: temperature ← temperature × cooling_rate
```

**Parameters**:
- Initial temperature: 1000.0
- Cooling rate: 0.99
- Final temperature: 0.01
- Steps: 500-5000 (varying)

**Advantages**:
- Escapes local optima via probabilistic acceptance
- Proven convergence properties
- Widely used in redistricting literature

### 2.2 Greedy Optimization
**Rationale**: Baseline comparison to assess benefit of stochastic exploration.

**Algorithm**:
```
Initialize: Random district assignment
For t = 1 to T:
    1. Propose: Move random commune to neighboring district
    2. Evaluate: Compute objective function score
    3. Accept only if Δscore < 0 (strict improvement)
```

**Advantages**:
- Simple, deterministic
- Fast convergence
- No hyperparameters

**Limitations**:
- Prone to local optima
- No exploration mechanism

### 2.3 Hill Climbing with Random Restarts
**Rationale**: Combines greedy local search with restart mechanism to overcome local optima.

**Algorithm**:
```
For restart = 1 to R:
    Initialize: Random district assignment
    While not stuck:
        1. Propose: Move random commune to neighboring district
        2. Accept only if improvement
        3. If stuck for 50 iterations: restart
```

**Parameters**:
- Restart frequency: Every 200 steps or when stuck
- Stuck threshold: 50 consecutive rejections

**Advantages**:
- Better than pure greedy
- No temperature tuning needed

### 2.4 Constrained Optimization (Two-Phase)
**Rationale**: Maximize partisan gain subject to population balance constraint.

**Algorithm**:
```
Phase 1 (steps 0-100): Achieve feasibility
    - Prioritize solutions satisfying population constraint
    - Use simulated annealing to explore

Phase 2 (remaining steps): Optimize partisan gain
    - Only accept feasible solutions
    - Maximize seats for target coalition
```

**Constraint**:
- Population std deviation ≤ 15% of mean

**Advantages**:
- Realistic constraint modeling
- Separates feasibility from optimization
- Produces legally viable districts

---

## 3. Objective Functions

### 3.1 General Form

```
Score = w₁ × PopulationBalance + w₂ × SeatDeviation + w₃ × PartisanAdvantage
```

Where:
- **PopulationBalance**: Standard deviation of district populations (minimize)
- **SeatDeviation**: |Actual seats - Proportional seats| (minimize)
- **PartisanAdvantage**: -(Seats won by target party) (minimize to maximize seats)

### 3.2 Objective Variants

| Objective | w₁ (Pop) | w₂ (Seat) | w₃ (Partisan) | Description |
|-----------|----------|-----------|---------------|-------------|
| **Neutral** | 1.0 | 1.0 | 0.0 | Fair districts |
| **Mild Partisan** | 0.5 | 0.1 | 1.0 | Slight partisan tilt |
| **Moderate Partisan** | 0.1 | 0.0 | 5.0 | Strong partisan tilt |
| **Extreme Partisan** | 0.1 | 0.0 | 50.0 | Maximum partisan gain |
| **Balanced** | 1.0 | 0.0 | 2.0 | Population + partisan |
| **Constrained** | 0.0 | 0.0 | 10.0 | Pure partisan (with constraint) |

### 3.3 Metrics Computation

**Population Balance**:
```python
district_pops = [sum(population in district d) for d in districts]
score_pop = std(district_pops)
```

**Seat Deviation**:
```python
proportional_seats = (party_votes / total_votes) × n_districts
actual_seats = count(districts where party wins plurality)
score_seat = |actual_seats - proportional_seats|
```

**Partisan Advantage**:
```python
seats_won = count(districts where target_party wins plurality)
score_partisan = -seats_won  # Negative because we minimize
```

---

## 4. Experimental Design

### 4.1 Baseline Experiments
**Purpose**: Establish neutral optimization performance and algorithm comparison.

| Experiment | Algorithm | Steps | Objective |
|------------|-----------|-------|-----------|
| baseline_sa_short | Simulated Annealing | 1000 | Neutral |
| baseline_sa_long | Simulated Annealing | 5000 | Neutral |
| baseline_greedy | Greedy | 5000 | Neutral |
| baseline_hillclimb | Hill Climbing | 5000 | Neutral |

**Expected Outcomes**:
- Balanced population districts
- Near-proportional seat allocation
- Algorithm performance ranking

### 4.2 Partisan Optimization Experiments
**Purpose**: Test gerrymandering feasibility with varying intensity.

**Left Coalition**:
- partisan_left_mild (w=1.0, steps=3000)
- partisan_left_moderate (w=5.0, steps=3000)
- partisan_left_extreme (w=50.0, steps=3000)

**Right Coalition**:
- partisan_right_mild (w=1.0, steps=3000)
- partisan_right_moderate (w=5.0, steps=3000)
- partisan_right_extreme (w=50.0, steps=3000)

**Expected Outcomes**:
- Seat distributions diverging from proportional
- Trade-off between population balance and partisan gain
- Asymmetric gerrymandering potential (left vs right)

### 4.3 Multi-Objective Experiments
**Purpose**: Explore trade-offs between competing objectives.

| Experiment | Approach | Description |
|------------|----------|-------------|
| balanced_left | Weighted sum (1:0:2) | Moderate left + balance |
| balanced_right | Weighted sum (1:0:2) | Moderate right + balance |
| constrained_left | Two-phase | Max left with pop constraint |
| constrained_right | Two-phase | Max right with pop constraint |

**Expected Outcomes**:
- Pareto-optimal solutions
- Achievable partisan gain under realistic constraints
- Comparison of multi-objective strategies

### 4.4 Algorithm Comparison
**Purpose**: Evaluate relative algorithm performance on identical objective.

| Experiment | Algorithm | Objective | Steps |
|------------|-----------|-----------|-------|
| partisan_right_extreme | SA | Max Right | 3000 |
| algo_comparison_greedy_right | Greedy | Max Right | 3000 |
| algo_comparison_hillclimb_right | Hill Climb | Max Right | 3000 |

**Metrics**:
- Final score achieved
- Convergence rate
- Computational time
- Solution quality

### 4.5 Sensitivity Analysis
**Purpose**: Test robustness to random initialization.

| Experiment | Seed | Objective |
|------------|------|-----------|
| partisan_right_extreme | 42 | Max Right |
| seed_sensitivity_1 | 123 | Max Right |
| seed_sensitivity_2 | 456 | Max Right |
| seed_sensitivity_3 | 789 | Max Right |

**Analysis**:
- Mean and variance of seat distributions
- Convergence consistency
- Algorithm stability

---

## 5. Evaluation Metrics

### 5.1 Primary Metrics

**Seat Advantage**:
```
Advantage = Actual Seats - Proportional Seats
```
- Primary measure of gerrymandering success
- Positive = benefiting coalition gains seats
- Negative = coalition loses seats

**Population Imbalance**:
```
Imbalance = std(district_populations) / mean(district_populations)
```
- Measures fairness of district sizes
- Lower = more balanced
- Constraint: typically ≤15%

**Compactness** (future work):
- Polsby-Popper ratio
- Reock score
- Geometric regularity

### 5.2 Secondary Metrics

**Convergence Rate**:
- Steps to reach 95% of final score
- Measures algorithm efficiency

**Stability**:
- Variance across random seeds
- Robustness to initialization

**Wasted Votes**:
- Votes not contributing to seat wins
- Efficiency gap calculation

---

## 6. Implementation Details

### 6.1 Geographic Constraints

**Adjacency Graph**:
- Built using Shapely `.touches()` on commune geometries
- Ensures contiguity: all communes in district must be connected

**Proposal Mechanism**:
```python
def propose_move(districts):
    1. Select random commune c
    2. Find neighboring communes of c
    3. Get districts D_neighbors of those neighbors
    4. Move c to random district in D_neighbors
```

**Contiguity Enforcement**:
- Implicit through adjacency-based proposals
- Guarantees connected districts by construction

### 6.2 Data Sources

**Electoral Data** (`politiche_2022_liste_camera_comuni.csv`):
- Official Ministry of Interior election results
- 2022 parliamentary elections
- Vote shares by party and commune

**Geographic Data** (`gerrymandering_base.geojson`):
- ISTAT commune boundaries
- MultiPolygon geometries
- CRS: WGS84 (EPSG:4326)

**Population Data** (`POSAS_2024_it_Comuni.csv`):
- ISTAT population statistics
- Used as proxy via 2022 voter turnout

### 6.3 Computational Environment

- **Language**: Python 3.10+
- **Key Libraries**:
  - GeoPandas 0.14+ (spatial operations)
  - NumPy 1.24+ (numerical computation)
  - Matplotlib 3.7+ (visualization)
  - Shapely 2.0+ (geometry operations)

- **Hardware**:
  - Standard desktop CPU
  - ~8GB RAM required
  - Runtime: 1-30 minutes per experiment

---

## 7. Validation and Reproducibility

### 7.1 Reproducibility Measures

**Random Seeds**:
- All experiments use fixed seeds
- Default seed: 42
- Sensitivity analysis with seeds: 42, 123, 456, 789

**Data Versioning**:
- Fixed 2022 election data
- SHA-256 hash of input files documented

**Code Versioning**:
- Git repository with tagged releases
- Requirements.txt for dependency management

### 7.2 Validation Checks

**Sanity Checks**:
- All communes assigned to exactly one district
- All districts contain ≥1 commune
- Total population preserved

**Geometric Validation**:
- District geometries are valid (no self-intersections)
- Contiguity verified via graph connectivity

**Electoral Validation**:
- Seat counts sum to 11
- Vote totals match input data

---

## 8. Analysis Plan

### 8.1 Comparative Analysis

**Algorithm Performance**:
- Compare final scores across algorithms
- Convergence plots (score vs iteration)
- Runtime comparison

**Objective Trade-offs**:
- Pareto frontier: partisan gain vs population balance
- Scatter plots of competing objectives
- Identify dominated solutions

**Partisan Asymmetry**:
- Compare left vs right gerrymandering potential
- Analyze geographic distribution of party support
- Identify structural advantages

### 8.2 Visualizations

**Maps**:
- Initial vs final district boundaries
- Color-coded by party dominance
- Population density overlays

**Time Series**:
- Seat distribution evolution (GIF animations)
- Score convergence plots
- Temperature schedules

**Summary Plots**:
- Bar charts: seat distributions across experiments
- Heatmaps: objective weights vs outcomes
- Box plots: sensitivity analysis results

### 8.3 Statistical Tests

**Significance Testing**:
- t-tests: seat advantage vs proportional baseline
- ANOVA: algorithm performance comparison
- Chi-square: seat distribution goodness-of-fit

**Effect Sizes**:
- Cohen's d for seat advantage magnitude
- Correlation: objective weights vs seat gains

---

## 9. Limitations

### 9.1 Methodological Limitations

1. **Single Region**: Results specific to Emilia-Romagna; may not generalize to all Italy
2. **Static Voting**: Assumes 2022 voting patterns persist (ignores voter mobility)
3. **Simplified Model**: Ignores multi-member districts, preferential voting
4. **No Constraints**: Real redistricting has legal/administrative constraints

### 9.2 Computational Limitations

1. **Local Optima**: No guarantee of global optimum (NP-hard problem)
2. **Proposal Mechanism**: Simple random moves; more sophisticated operators possible
3. **Single Objective Function**: Weighted sum may miss Pareto-optimal solutions

### 9.3 Data Limitations

1. **Population Proxy**: Using votes as population estimate (excludes non-voters)
2. **Geometry Simplification**: Commune boundaries may have minor inaccuracies
3. **Temporal Mismatch**: 2022 electoral data vs 2024 population data

---

## 10. Future Extensions

### 10.1 Methodological Extensions

- **National-scale analysis**: All 27 Italian electoral regions
- **Advanced algorithms**: ReCom, GerryChain, Markov Chain Monte Carlo
- **Compactness constraints**: Enforce geometric regularity
- **Legal constraints**: Respect provincial/regional boundaries

### 10.2 Analysis Extensions

- **Ensemble methods**: Generate distributions of valid plans
- **Statistical gerrymandering detection**: Outlier analysis vs neutral ensemble
- **Multi-party analysis**: Beyond left/right binary
- **Temporal robustness**: Test across 2018, 2022 elections

### 10.3 Practical Extensions

- **Interactive tool**: Web interface for exploring scenarios
- **Policy recommendations**: Identify reform options
- **Transparency**: Public audit of official districts

---

## 11. Ethical Considerations

This research is conducted for **academic purposes** to:
1. Understand vulnerabilities in electoral systems
2. Inform democratic reform and transparency
3. Develop detection methods for gerrymandering

**Ethical Guidelines**:
- Results are publicly available for transparency
- Methods disclosed to enable independent verification
- Recommendations focus on fairness and electoral integrity
- No advocacy for implementing partisan gerrymanders

**Dual-Use Acknowledgment**:
While these techniques could theoretically be used for manipulation, we believe:
1. Transparency about vulnerabilities improves democratic resilience
2. Detection methods require understanding attack vectors
3. Informed public discourse requires quantitative analysis

---

## References

*To be added: Citations for redistricting algorithms, Italian electoral law, gerrymandering literature*

---

**Document Version**: 1.0
**Last Updated**: 2024-11-05
**Authors**: [To be filled]
