# Layered Zero Trust Coverage-Gap Simulation

Reproducible simulation for "Beyond Device Trust: A Layered Zero Trust Architecture
Integrating NAC, Segmentation, and Identity-Based Access for ISO/IEC 27001 and TISAX."

## What it does
Compares a coordinated cross-layer Zero Trust decision engine (identity + device + network
weighted equally, each with a hard floor) against an identity-centric baseline, across a
battery of threat scenarios. Demonstrates coverage gaps: threats the coordinated system
isolates that the identity-centric baseline allows.

## Files
- `scores.py`        sub-signal scoring (reasons-first weights, sourced)
- `hybrid_v4.py`     hybrid decision engine (score-based OR criteria/floor)
- `run_scenarios.py` scenario definitions (sub-signal level) + runner
- `make_artifacts.py` produces all CSVs and figures used in the paper
- `SCENARIO_GROUNDING.md` justification for every scenario input
- `SWEEP_FINDINGS.md` sensitivity-sweep results and interpretation

## Reproduce
```
pip install -r requirements.txt
python make_artifacts.py
```
Outputs land in `artifacts/`: results_scenarios.csv, results_sweep.csv, and fig1-3 (png+pdf).

## Parameters
tau = 0.70, floor = 0.40, W_baseline = {identity 0.70, device 0.15, network 0.15},
W_coordinated = {1/3, 1/3, 1/3}. All discussed and swept in the paper (Section 3).
