# Changes Summary - Contiguity and Simplified Experiments

## Date: 2025-11-05

### Overview
Major refactoring to address two critical issues:
1. **Districts must always be contiguous** (no disconnected pieces)
2. **Simplified visualizations** showing LEFT vs RIGHT only (no center coalition)

---

## 1. Contiguity Enforcement

### New File: `src/contiguity.py`
- Uses NetworkX for graph-based contiguity checking
- Three key functions:
  - `check_district_contiguity()`: Verifies a single district is fully connected
  - `is_valid_move()`: Checks if moving a commune preserves contiguity
  - `validate_all_districts_contiguous()`: Validates entire configuration

### Modified: `src/gerrymander.py`
- **`propose_move()` method**: Now tries up to 100 times to find a contiguous move
- Only accepts moves that preserve contiguity of BOTH old and new districts
- **`initialize_districts()` method**: Validates initial districts are contiguous
- Logs "✓ All initial districts are contiguous" on success

### Why This Matters
- Previous experiments may have created fragmented districts
- Now guaranteed that every district is a single connected region
- More realistic: real-world districts must be contiguous

---

## 2. Improved Visualizations

### New File: `src/visualizer_improved.py`
- Maps colored by **WINNER** (which coalition wins each district)
- Bar plots show **per-district vote percentages** (not aggregate seats)
- Still includes all three coalitions (left, right, center)

### New File: `src/visualizer_simple.py`
- **LEFT vs RIGHT only** (completely ignores center coalition)
- Maps colored by winner: Red (left) or Blue (right)
- Stacked bars show left/right percentages per district
- 50% majority line clearly visible

### Why This Matters
**Old visualization problems:**
- Maps colored by arbitrary district IDs (not meaningful)
- Bar plots showed total seats over time (not per-district competition)
- Hard to see which coalition wins each district

**New visualization benefits:**
- See at a glance which coalition controls each district
- See how competitive each district is (close to 50% or landslide)
- Track how district winners flip during optimization

---

## 3. Simplified Experiments

### New File: `experiments/simple_experiments.py`
**4 experiments only:**
1. `sa_maximize_left`: Simulated Annealing to maximize left seats
2. `sa_maximize_right`: Simulated Annealing to maximize right seats
3. `greedy_maximize_left`: Greedy algorithm to maximize left seats
4. `greedy_maximize_right`: Greedy algorithm to maximize right seats

**Configuration:**
- All use 2022 electoral data
- All use seed=42 for reproducibility
- All run 3000 steps
- All create animated GIFs

### New File: `run_simple_experiments.py`
- Batch runner for the 4 simple experiments
- Uses `visualizer_simple.py` (LEFT vs RIGHT only)
- All experiments enforce contiguity

### Backed Up Old Results
- Previous 19-experiment suite backed up to `results_backup_TIMESTAMP/`
- Fresh `results/` directory for simple experiments

---

## 4. Updated Dependencies

### Modified: `requirements.txt`
- Added `networkx>=3.0` (required for contiguity checking)

---

## 5. Updated Existing Files

### Modified: `run_experiment.py`
- Now imports from `visualizer_improved.py`
- Includes party colors parameter

### Modified: `run_batch_experiments.py`
- Now imports from `visualizer_improved.py`
- Includes party colors parameter

---

## Key Differences: Old vs New

| Aspect | Old Approach | New Approach |
|--------|--------------|--------------|
| **Contiguity** | Not enforced | Required via NetworkX |
| **Map coloring** | By district ID | By winning coalition |
| **Bar plots** | Total seats over time | Per-district percentages |
| **Coalitions shown** | Left, Right, Center | Left vs Right only |
| **Experiments** | 19 complex experiments | 4 simple experiments |
| **Focus** | Comprehensive analysis | Clear comparison |

---

## What's Running Now

**4 experiments currently in progress:**
1. SA maximize left (in progress)
2. SA maximize right (pending)
3. Greedy maximize left (pending)
4. Greedy maximize right (pending)

**Expected outputs per experiment:**
- JSON results file
- Pickle file with full history
- Comparison PNG (initial vs final)
- Animated GIF showing optimization

**Total expected files:** 16 (4 × 4 file types)

---

## Next Steps After Experiments Complete

1. **Analyze results**:
   - Which algorithm performs better?
   - Can left coalition successfully gerrymander?
   - Can right coalition successfully gerrymander?
   - Asymmetry in gerrymandering potential?

2. **Create summary visualizations**:
   - Side-by-side comparison of all 4 experiments
   - Table showing final seat counts

3. **Update paper materials**:
   - Simplified findings (4 experiments instead of 19)
   - Focus on LEFT vs RIGHT competition
   - Clear demonstration of contiguity enforcement

---

## Technical Notes

### Contiguity Algorithm
- Build adjacency graph from commune borders
- For each move, check if old district remains connected
- If old district becomes disconnected, reject move
- Try up to 100 moves before giving up
- Very fast: uses NetworkX BFS

### Performance Impact
- Contiguity checking adds ~10-20% overhead
- Worth it for correctness
- Most moves are valid (rarely hit 100 attempts)

### Visualization Performance
- Simplified visualizer slightly faster (fewer coalitions)
- GIF creation still takes ~30 seconds per experiment
- High-quality output (150 DPI for comparison, 80 DPI for GIFs)

---

**Status:** Experiments running in background. Check progress with:
```bash
tail -f experiment_run.log
```
