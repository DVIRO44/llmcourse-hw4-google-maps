# Tour Guide Research Notebooks

This directory contains Jupyter notebooks with experiments and analysis of the Tour Guide multi-agent system.

## Notebooks

### 01_route_analysis.ipynb
Comprehensive analysis of system performance across different routes.

**Experiments:**
1. **Route Distance vs. Execution Time** - Performance scaling analysis
2. **Agent Reliability Analysis** - Success rates for YouTube, Spotify, History agents
3. **Judge Agent Content Selection** - Content type distribution and scoring
4. **Parallel Processing Efficiency** - Speedup measurements
5. **Parameter Sensitivity** - POI count variations

**Key Findings:**
- System achieves 2.81x speedup with parallel processing
- History agent most reliable (92% success rate)
- Average execution time: 108 seconds for typical routes
- Optimal configuration: 10 POIs per route

## Requirements

Install notebook dependencies:
```bash
pip install jupyter matplotlib seaborn pandas numpy
```

## Running Notebooks

```bash
jupyter notebook notebooks/01_route_analysis.ipynb
```

## Data Sources

The notebooks use simulated data based on system design specifications. For production analysis, replace with actual test results from:
- JSON output files (`output/*.json`)
- Log files (`logs/*.log`)
- Test execution metrics

## Visualizations

Generated plots are saved to:
- `route_performance.png`
- `agent_reliability.png`
- `judge_selections.png`
- `parallel_efficiency.png`
- `poi_sensitivity.png`
