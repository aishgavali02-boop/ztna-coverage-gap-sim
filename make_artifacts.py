"""
make_artifacts.py -- writes the two single-state result datasets used by the
paper: the scenario table (Table 4) and the full sensitivity sweep (Section 3.4).

Method discipline:
  - Nothing is tuned. Weights, tau and floor come from hybrid_v4.py as locked.
  - Sweeps run to the definitional limits of each parameter and report where
    outcomes flip. A sweep is never stopped at a flip point.
  - Layer scores are computed by scores.py from sub-signal inputs; they are
    never asserted.
  - Classification is directional (hybrid_v4.classify_pair): a coverage gap
    requires the coordinated configuration to isolate while the baseline allows.

Outputs (./artifacts/): results_scenarios.csv, results_sweep.csv
"""
import os
import csv
import copy
import numpy as np

import hybrid_v4 as hv
from run_scenarios import SUB, layer_scores
from paper_labels import SCEN_ORDER

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)


def write_scenario_table():
    rows = []
    for name in SCEN_ORDER:
        L = layer_scores(SUB[name])
        cd, cc, bd, bc, result = hv.decide_both(L)
        rows.append({
            "scenario": name,
            "S_identity": round(L["identity"], 4),
            "S_device": round(L["device"], 4),
            "S_network": round(L["network"], 4),
            "coord_decision": cd, "coord_composite": round(cc, 4),
            "baseline_decision": bd, "baseline_composite": round(bc, 4),
            "result": result,
        })
    path = os.path.join(OUT, "results_scenarios.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return rows, path


def _record(rows_out, sweep, knob, name, cd, cc, bd, bc, result):
    rows_out.append(dict(sweep=sweep, knob_value=float(knob), scenario=name,
                         coord_decision=cd, baseline_decision=bd,
                         result=result, coord_composite=round(cc, 4),
                         baseline_composite=round(bc, 4)))


def sweep_floor(rows_out):
    """Floor is a per-layer cutoff; definitional range is [0, tau)."""
    for floor in np.round(np.arange(0.0, hv.TAU, 0.05), 3):
        for name in SCEN_ORDER:
            L = layer_scores(SUB[name])
            cd, cc, bd, bc, res = hv.decide_both(L, floor=float(floor))
            _record(rows_out, "floor", floor, name, cd, cc, bd, bc, res)


def sweep_tau(rows_out):
    """Composite threshold; definitional range [0.50, 0.95]."""
    for tau in np.round(np.arange(0.50, 0.96, 0.05), 3):
        for name in SCEN_ORDER:
            L = layer_scores(SUB[name])
            cd, cc, bd, bc, res = hv.decide_both(L, tau=float(tau))
            _record(rows_out, "tau", tau, name, cd, cc, bd, bc, res)


def sweep_identity_weight(rows_out):
    """Baseline identity weight [0.50, 0.85]; device and network split the
    remainder evenly, keeping them soft but present."""
    for wid in np.round(np.arange(0.50, 0.86, 0.05), 3):
        rem = (1.0 - wid) / 2.0
        w_base = {"identity": float(wid), "device": rem, "network": rem}
        for name in SCEN_ORDER:
            L = layer_scores(SUB[name])
            cd, cc, bd, bc, res = hv.decide_both(L, w_base=w_base)
            _record(rows_out, "identity_weight", wid, name, cd, cc, bd, bc, res)


def sweep_soft_posture(rows_out):
    """Sub-signal magnitude: vary compromised device posture across [0.0, 0.5]
    in the two scenarios whose device signal is soft-degraded, to show the A gap
    and the B_severe limitation are not artifacts of the chosen magnitude."""
    for posture in np.round(np.arange(0.0, 0.51, 0.05), 3):
        for name in ("A_session_hijack", "B_severe_drift"):
            s = copy.deepcopy(SUB[name])
            s["dev"]["posture"] = float(posture)
            L = layer_scores(s)
            cd, cc, bd, bc, res = hv.decide_both(L)
            _record(rows_out, "soft_posture", posture, name, cd, cc, bd, bc, res)


def write_sweeps():
    rows = []
    sweep_floor(rows); sweep_tau(rows)
    sweep_identity_weight(rows); sweep_soft_posture(rows)
    path = os.path.join(OUT, "results_sweep.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    return rows, path


def main():
    scen_rows, p1 = write_scenario_table()
    for r in scen_rows:
        print(f"  {r['scenario']:<22} coord={r['coord_decision']:<8}"
              f"base={r['baseline_decision']:<8}{r['result']}")
    print(f"  -> {p1}")
    sweep_rows, p2 = write_sweeps()
    print(f"  {len(sweep_rows)} sweep rows -> {p2}")


if __name__ == "__main__":
    main()
