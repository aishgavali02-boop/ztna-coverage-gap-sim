"""
run_all.py -- single-command reproduction of every computed artifact in the
paper.

    python run_all.py

Writes to ./artifacts/:
    results_scenarios.csv          Table 4
    results_sweep.csv              Section 3.4 sensitivity sweeps (246 rows)
    results_time_evolution.csv     Section 3.3 time series
    results_time_sweep.csv         Section 3.4.5 time-series sweep
    figure1_study_overview         Figure 1
    figure2_design_principles      Figure 2
    figure3_architecture           Figure 3
    figure4_decision_rule          Figure 4
    figure5_scenario_outcomes      Figure 5
    figure6_time_evolution         Figure 6
    figure7_floor_sweep            Figure 7
    figure8_identity_weight_sweep  Figure 8

Every figure in the paper is generated here; none is hand-drawn. Output
filenames match the figure numbers used in the manuscript.
"""
import runpy
import sys

STEPS = [
    ("Scenario table and sensitivity sweeps", "make_artifacts.py"),
    ("Time-series evolution and time sweep", "time_evolution.py"),
    ("Figures 4 and 5", "make_fig4_fig5.py"),
    ("Figures 7 and 8", "make_fig7_fig8.py"),
    ("Figures 1, 2 and 3 (conceptual diagrams)", "make_diagrams.py"),
]

if __name__ == "__main__":
    for label, script in STEPS:
        print(f"\n=== {label}  ({script}) ===")
        try:
            runpy.run_path(script, run_name="__main__")
        except FileNotFoundError:
            print(f"  SKIPPED: {script} not found", file=sys.stderr)
    print("\nAll artifacts written to ./artifacts/")
