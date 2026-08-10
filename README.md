# Layered Zero Trust Coverage-Gap Simulation

Reproducible simulation for the paper "Beyond Device Trust: A Layered Zero Trust Architecture Integrating NAC, Segmentation, and Identity-Based Access for ISO/IEC 27001 and TISAX."

## What it does

Compares a coordinated cross-layer Zero Trust decision engine (identity, device and network weighted equally, each with a hard floor) against an identity-centric baseline (identity weighted 0.70, identity floored alone) across seven threat scenarios. Both configurations run on identical inputs, so any difference in outcome is attributable solely to layer weighting and floor placement.

A coverage gap is a scenario in which the coordinated configuration isolates a request that the identity-centric baseline allows. The classification is directional: disagreement alone is not a coverage gap. The opposite case is reported separately as a reverse gap, and does occur -- Scenario E at floor values below 0.30.

## Files

| File | Purpose |
|---|---|
| scores.py | Layer trust scores from named sub-signals (weights = Table 1) |
| hybrid_v4.py | Hybrid decision engine: composite test OR per-layer floor test |
| run_scenarios.py | Scenario definitions at sub-signal level, plus layer_scores() |
| paper_labels.py | Manuscript scenario labels and the greyscale-safe palette |
| make_artifacts.py | Writes results_scenarios.csv and results_sweep.csv |
| time_evolution.py | Time-series model; writes the two time CSVs and Figure 6 |
| make_fig4_fig5.py | Figures 4 and 5 |
| make_fig7_fig8.py | Figures 7 and 8 |
| make_diagrams.py | Figures 1, 2 and 3 (conceptual diagrams) |
| run_all.py | Runs all of the above in order |
| requirements.txt | Python package requirements |
| SCENARIO_GROUNDING.md | Justification for every scenario input |
| SWEEP_FINDINGS.md | Sensitivity-sweep results and interpretation |

## Reproduce

    pip install -r requirements.txt
    python run_all.py

Everything lands in artifacts/. Every dataset and every figure reported in the paper is produced by this one command; none is hand-drawn.

## Parameters

All disclosed, none fitted to an outcome.

    tau   = 0.70   composite decision threshold
    floor = 0.40   per-layer floor
    W_coordinated      = identity 1/3,  device 1/3,  network 1/3   (all three floored)
    W_identity_centric = identity 0.70, device 0.15, network 0.15  (identity floored only)

Sub-signal weights are listed in scores.py with the rationale for each ordering. The orderings are grounded in the cited literature; the magnitudes are design choices, and the sensitivity sweeps in make_artifacts.py establish the ranges over which each reported result holds. Section 3.4 of the paper reports those ranges, including the settings at which results cease to hold.
