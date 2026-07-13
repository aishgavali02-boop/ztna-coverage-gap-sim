"""
make_artifacts.py  --  ONE clean run that produces every artifact the paper needs.

Outputs (written to ./artifacts/):
  results_scenarios.csv   the scenario battery table (Section 3 core result)
  results_sweep.csv       full sensitivity sweep, long format
  fig1_scenario_scores.(png|pdf)   coordinated vs baseline composite per scenario
  fig2_floor_sweep.(png|pdf)       decision vs floor, per scenario (B_severe boundary)
  fig3_identity_weight_sweep.(png|pdf)  gap robustness across identity-centric weightings

Method discipline (unchanged from the project rules):
  - Nothing is tuned. Weights/tau/floor come from scores.py + hybrid_v4.py as locked.
  - Sweeps vary knobs across DEFINITIONAL ranges and report where results flip.
    We do NOT stop a sweep at a flip point (that would be rigging).
  - Layer scores are computed outputs, never asserted.
"""
import os
import csv
import copy
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import scores
import hybrid_v4 as hv
from run_scenarios import SUB, layer_scores

OUT = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(OUT, exist_ok=True)

SCEN_ORDER = ["Healthy", "A_session_hijack", "B_mild_drift", "B_severe_drift",
              "C_supply_chain", "D_iiot_lateral", "E_identity_compromise"]


def decide_both(L, tau, floor, w_coord, w_base):
    cd, cc, cr = hv.decide(L, w_coord, hv.HARD_COORD, tau=tau, floor=floor)
    bd, bc, br = hv.decide(L, w_base, hv.HARD_BASE, tau=tau, floor=floor)
    if cd != bd:
        result = "COVERAGE_GAP"
    elif cd == "ALLOW":
        result = "agree_allow"
    else:
        result = "both_isolate"
    return cd, cc, bd, bc, result


# ----------------------------------------------------------------------
# 1. SCENARIO TABLE (baseline artifact) -- at locked tau/floor/weights
# ----------------------------------------------------------------------
def write_scenario_table():
    rows = []
    for name in SCEN_ORDER:
        L = layer_scores(SUB[name])
        cd, cc, bd, bc, result = decide_both(
            L, hv.TAU, hv.FLOOR, hv.W_COORD, hv.W_BASE)
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
        w.writeheader()
        w.writerows(rows)
    return rows, path


# ----------------------------------------------------------------------
# 2. SENSITIVITY SWEEPS -- each knob across its DEFINITIONAL range
# ----------------------------------------------------------------------
def sweep_floor(rows_out):
    # Floor is a criteria-based cutoff; definitional range is [0, tau).
    for floor in np.round(np.arange(0.0, hv.TAU, 0.05), 3):
        for name in SCEN_ORDER:
            L = layer_scores(SUB[name])
            cd, cc, bd, bc, result = decide_both(
                L, hv.TAU, float(floor), hv.W_COORD, hv.W_BASE)
            rows_out.append(dict(sweep="floor", knob_value=float(floor),
                                 scenario=name, coord_decision=cd,
                                 baseline_decision=bd, result=result,
                                 coord_composite=round(cc, 4)))


def sweep_tau(rows_out):
    # Threshold; definitional range [0.5, 0.95] (below 0.5 = not zero-trust strict).
    for tau in np.round(np.arange(0.50, 0.96, 0.05), 3):
        for name in SCEN_ORDER:
            L = layer_scores(SUB[name])
            cd, cc, bd, bc, result = decide_both(
                L, float(tau), hv.FLOOR, hv.W_COORD, hv.W_BASE)
            rows_out.append(dict(sweep="tau", knob_value=float(tau),
                                 scenario=name, coord_decision=cd,
                                 baseline_decision=bd, result=result,
                                 coord_composite=round(cc, 4)))


def sweep_identity_weight(rows_out):
    # Baseline identity-centric weight; definitional range [0.50, 0.85].
    # Device/network split the remainder evenly (keeps them soft-but-present).
    for wid in np.round(np.arange(0.50, 0.86, 0.05), 3):
        rem = (1.0 - wid) / 2.0
        w_base = {"identity": float(wid), "device": rem, "network": rem}
        for name in SCEN_ORDER:
            L = layer_scores(SUB[name])
            cd, cc, bd, bc, result = decide_both(
                L, hv.TAU, hv.FLOOR, hv.W_COORD, w_base)
            rows_out.append(dict(sweep="identity_weight", knob_value=float(wid),
                                 scenario=name, coord_decision=cd,
                                 baseline_decision=bd, result=result,
                                 coord_composite=round(cc, 4)))


def sweep_soft_posture(rows_out):
    # A [SWEEP] sub-signal magnitude: vary compromised-device posture across [0.0, 0.5]
    # in A and B_severe (the scenarios whose device signal is soft-degraded) to show the
    # A gap and the B_severe limitation are not artifacts of the exact posture guess.
    targets = ["A_session_hijack", "B_severe_drift"]
    for posture in np.round(np.arange(0.0, 0.51, 0.05), 3):
        for name in targets:
            s = copy.deepcopy(SUB[name])
            s["dev"]["posture"] = float(posture)
            L = layer_scores(s)
            cd, cc, bd, bc, result = decide_both(
                L, hv.TAU, hv.FLOOR, hv.W_COORD, hv.W_BASE)
            rows_out.append(dict(sweep="soft_posture", knob_value=float(posture),
                                 scenario=name, coord_decision=cd,
                                 baseline_decision=bd, result=result,
                                 coord_composite=round(cc, 4)))


def write_sweeps():
    rows = []
    sweep_floor(rows)
    sweep_tau(rows)
    sweep_identity_weight(rows)
    sweep_soft_posture(rows)
    path = os.path.join(OUT, "results_sweep.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows, path


# ----------------------------------------------------------------------
# 3. FIGURES
# ----------------------------------------------------------------------
def fig_scenario_scores(rows):
    names = [r["scenario"] for r in rows]
    coord = [r["coord_composite"] for r in rows]
    base = [r["baseline_composite"] for r in rows]
    x = np.arange(len(names))
    w = 0.38
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w/2, coord, w, label="Coordinated")
    ax.bar(x + w/2, base, w, label="Baseline (identity-centric)")
    ax.axhline(hv.TAU, ls="--", lw=1, color="black", label=f"tau = {hv.TAU}")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=30, ha="right")
    ax.set_ylabel("Composite trust score")
    ax.set_title("Composite score by scenario: coordinated vs identity-centric baseline")
    ax.legend()
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig1_scenario_scores.{ext}"), dpi=200)
    plt.close(fig)


def _decision_grid(sweep_rows, sweep_name):
    knobs = sorted({r["knob_value"] for r in sweep_rows if r["sweep"] == sweep_name})
    scens = [s for s in SCEN_ORDER if any(
        r["sweep"] == sweep_name and r["scenario"] == s for r in sweep_rows)]
    grid = np.zeros((len(scens), len(knobs)))
    for i, s in enumerate(scens):
        for j, k in enumerate(knobs):
            match = [r for r in sweep_rows if r["sweep"] == sweep_name
                     and r["scenario"] == s and r["knob_value"] == k]
            grid[i, j] = 1.0 if match and match[0]["result"] == "COVERAGE_GAP" else (
                0.5 if match and match[0]["result"] == "both_isolate" else 0.0)
    return scens, knobs, grid


def fig_sweep_heat(sweep_rows, sweep_name, xlabel, fname, mark=None):
    scens, knobs, grid = _decision_grid(sweep_rows, sweep_name)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    im = ax.imshow(grid, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1,
                   extent=[min(knobs), max(knobs), len(scens)-0.5, -0.5])
    ax.set_yticks(range(len(scens)))
    ax.set_yticklabels(scens)
    ax.set_xlabel(xlabel)
    ax.set_title(f"Decision outcome vs {xlabel}  (green = coverage gap, "
                 f"yellow = both isolate, red = agree/allow)")
    if mark is not None:
        ax.axvline(mark, ls="--", lw=1.5, color="black")
    fig.colorbar(im, ax=ax, ticks=[0, 0.5, 1],
                 label="0 agree  .5 both-isolate  1 gap")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{fname}.{ext}"), dpi=200)
    plt.close(fig)


# ----------------------------------------------------------------------
def main():
    print("Writing scenario table ...")
    scen_rows, p1 = write_scenario_table()
    for r in scen_rows:
        print(f"  {r['scenario']:<22} coord={r['coord_decision']:<8}"
              f"base={r['baseline_decision']:<8}{r['result']}")
    print(f"  -> {p1}")

    print("Running sweeps ...")
    sweep_rows, p2 = write_sweeps()
    print(f"  {len(sweep_rows)} sweep rows -> {p2}")

    print("Making figures ...")
    fig_scenario_scores(scen_rows)
    fig_sweep_heat(sweep_rows, "floor", "floor",
                   "fig2_floor_sweep", mark=hv.FLOOR)
    fig_sweep_heat(sweep_rows, "identity_weight", "baseline identity weight",
                   "fig3_identity_weight_sweep", mark=0.70)
    print(f"  figures -> {OUT}/fig1..fig3 (png+pdf)")
    print("DONE.")


if __name__ == "__main__":
    main()
