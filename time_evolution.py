"""
time_evolution.py -- Discrete-time trust evolution under continuous re-evaluation.

A session is modelled as a sequence of discrete evaluation points. A signal starts
healthy and, under compromise, degrades along a defined trajectory. At every point the
system recomputes the layer scores and re-applies the decision rule (NIST SP 800-207
continuous-verification tenet). The measured output is the evaluation point at which
each configuration first isolates, and whether it does so at all.

Method discipline:
  - Degradation trajectories come from the scenario narrative, not from a target result.
  - Trajectory depth and shape are representative and swept; results are reported as
    holding across the trajectory space, or the boundary is stated.
  - The first-isolation point is a computed output, never asserted.

Time here denotes discrete re-evaluation points, not elapsed real time. The model
represents no enforcement latency, network delay, or propagation timing.

Outputs (./artifacts/):
    results_time_evolution.csv   per-point scores and decisions (Section 3.3),
                                 for all three time-varying cases
    results_time_sweep.csv       50 sweep runs (Section 3.4.5)
    figure6_time_evolution.(png|pdf)  Figure 6
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

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "artifacts")
N_POINTS = 11


# ---------------------------------------------------------------- trajectories
def linear_decay(start, end, n):
    """Signal moves start -> end linearly over n evaluation points."""
    return list(np.round(np.linspace(start, end, n), 4))


def step_decay(start, end, n, drop_at):
    """Signal holds at start, then drops to end at the given point."""
    return [start if t < drop_at else end for t in range(n)]


def exp_decay(start, end, n, k=3.0):
    """Signal decays start -> end on an exponential curve (fast, then slow)."""
    xs = np.linspace(0, 1, n)
    curve = np.exp(-k * xs)
    curve = (curve - curve.min()) / (curve.max() - curve.min())
    return list(np.round(end + (start - end) * curve, 4))


def make_trajectory(shape, start, end, n=N_POINTS):
    if shape == "linear":
        return linear_decay(start, end, n)
    if shape == "exp":
        return exp_decay(start, end, n)
    if shape.startswith("step"):
        return step_decay(start, end, n, drop_at=int(shape[4:]))
    raise ValueError(f"unknown trajectory shape: {shape}")


# ------------------------------------------------------------------- scenarios
# Device posture drift. The session authenticates cleanly, then device posture
# degrades as malware establishes itself. The management agent and the hardware root
# of trust stay intact -- neither is removed mid-session -- which is the faithful
# constraint. Identity and network remain clean.
DEVICE_DRIFT_BASE = {
    "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
    "dev": dict(agent_present=1, posture=0.95, patch_level=0.6, hw_root_trust=1),
    "net": dict(flow_conformity=0.85, egress_legit=0.85, eastwest_normal=0.85,
                zone_correct=0.9),
}

# Identity drift. A replayed token: multi-factor authentication remains satisfied,
# because the stolen token already passed it. Over the session several identity
# signals degrade together as the adversary's behaviour diverges from the legitimate
# user -- origin consistency, role appropriateness, and credential freshness. Device
# and network remain clean. All three move on the same trajectory because the
# narrative is that the whole identity context diverges at once.
IDENTITY_DRIFT_BASE = {
    "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
    "dev": dict(agent_present=1, posture=0.9, patch_level=0.85, hw_root_trust=1),
    "net": dict(flow_conformity=0.9, egress_legit=0.9, eastwest_normal=0.9,
                zone_correct=0.9),
}

IDENTITY_SIGNALS = [("id", "origin_consistency"),
                    ("id", "role_risk_inv"),
                    ("id", "cred_freshness")]

# Single-signal identity drift. The comparison case for Section 3.3.1: only origin
# consistency degrades, while every other identity sub-signal stays clean. This is
# the identity-layer equivalent of device posture drift -- one soft signal collapsing
# while the rest of the layer holds -- and it is reported as the parallel case there.
SINGLE_SIGNAL_BASE = {
    "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
    "dev": dict(agent_present=1, posture=0.9, patch_level=0.85, hw_root_trust=1),
    "net": dict(flow_conformity=0.9, egress_legit=0.9, eastwest_normal=0.9,
                zone_correct=0.9),
}


# ----------------------------------------------------------------------- engine
def _layer_scores(s):
    return {
        "identity": scores.score_identity(**s["id"]),
        "device": scores.score_device(**s["dev"]),
        "network": scores.score_network(**s["net"]),
    }


def run_session(base, degrading_list, trajectories):
    """Degrade one or more sub-signals, each along its own trajectory, and
    re-decide at every evaluation point.

    Returns (points, coord_first_isolate, baseline_first_isolate); either
    isolation point is None if that configuration never isolates.
    """
    n = len(trajectories[0])
    points, coord_first, base_first = [], None, None
    for t in range(n):
        s = copy.deepcopy(base)
        for (layer, sub), traj in zip(degrading_list, trajectories):
            s[layer][sub] = traj[t]
        L = _layer_scores(s)
        cd, cc, _ = hv.decide(L, hv.W_COORD, hv.HARD_COORD)
        bd, bc, _ = hv.decide(L, hv.W_BASE, hv.HARD_BASE)
        if cd == "ISOLATE" and coord_first is None:
            coord_first = t
        if bd == "ISOLATE" and base_first is None:
            base_first = t
        points.append(dict(t=t,
                           S_id=round(L["identity"], 4),
                           S_dev=round(L["device"], 4),
                           S_net=round(L["network"], 4),
                           coord=cd, coord_comp=round(cc, 4),
                           baseline=bd, base_comp=round(bc, 4)))
    return points, coord_first, base_first


# ------------------------------------------------------------------- artifacts
def write_time_artifacts():
    os.makedirs(OUT, exist_ok=True)

    dev_pts, dev_ci, dev_bi = run_session(
        DEVICE_DRIFT_BASE, [("dev", "posture")],
        [linear_decay(0.95, 0.05, N_POINTS)])

    id_trajs = [linear_decay(0.95, 0.0, N_POINTS),
                linear_decay(0.90, 0.15, N_POINTS),
                linear_decay(0.90, 0.30, N_POINTS)]
    id_pts, id_ci, id_bi = run_session(
        IDENTITY_DRIFT_BASE, IDENTITY_SIGNALS, id_trajs)

    single_pts, single_ci, single_bi = run_session(
        SINGLE_SIGNAL_BASE, [("id", "origin_consistency")],
        [linear_decay(0.95, 0.0, N_POINTS)])

    path_csv = os.path.join(OUT, "results_time_evolution.csv")
    with open(path_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "evaluation_point", "S_id", "S_dev", "S_net",
                    "coord_composite", "coord_decision",
                    "baseline_composite", "baseline_decision"])
        for label, rows in (("device_posture_drift", dev_pts),
                            ("identity_drift", id_pts),
                            ("single_signal_identity_drift", single_pts)):
            for r in rows:
                w.writerow([label, r["t"], r["S_id"], r["S_dev"], r["S_net"],
                            r["coord_comp"], r["coord"],
                            r["base_comp"], r["baseline"]])

    _figure6(dev_pts, id_pts, id_ci, id_bi)
    return dict(csv=path_csv,
                device_coord=dev_ci, device_baseline=dev_bi,
                identity_coord=id_ci, identity_baseline=id_bi,
                single_coord=single_ci, single_baseline=single_bi,
                single_final_S_id=single_pts[-1]["S_id"])


def _figure6(dev_pts, id_pts, id_ci, id_bi):
    """Figure 6.

    Note on reference lines: tau applies to the COMPOSITE score and the floor
    applies to EACH LAYER separately. They are therefore drawn against the
    series each one actually governs -- the floor against the layer score, tau
    against the two composites. Drawing tau against a layer score would imply a
    comparison the decision rule never makes.
    """
    n = len(dev_pts)
    xs = range(n)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 5))

    for ax, pts, layer_key, layer_name, layer_color in (
            (ax1, dev_pts, "S_dev", "Device score", "#1f3864"),
            (ax2, id_pts, "S_id", "Identity score", "#5b3a8e")):
        ax.plot(xs, [r[layer_key] for r in pts], marker="o", ms=4.5, lw=2,
                color=layer_color, label=layer_name)
        ax.plot(xs, [r["coord_comp"] for r in pts], lw=1.4, ls="-",
                color="#8fa9d0", label="Coordinated composite")
        ax.plot(xs, [r["base_comp"] for r in pts], lw=1.4, ls="-",
                color="#e0a0a0", label="Identity-centric composite")
        ax.axhline(hv.FLOOR, ls=":", lw=1.4, color="#c00000")
        ax.text(0.1, hv.FLOOR + 0.02, f"floor = {hv.FLOOR:.2f} (per layer)",
                fontsize=8, color="#c00000")
        ax.axhline(hv.TAU, ls="--", lw=1.2, color="#555555")
        ax.text(0.1, hv.TAU + 0.02, rf"$\tau$ = {hv.TAU:.2f} (composite)",
                fontsize=8, color="#555555")
        ax.set_xlabel("Evaluation point")
        ax.set_ylabel("Score")
        ax.set_ylim(0, 1.05)
        ax.set_xticks(list(xs))
        ax.spines[["top", "right"]].set_visible(False)

    ax1.set_title("Device posture drift", fontsize=11)
    ax1.legend(fontsize=8, loc="lower left", framealpha=0.9)

    # Isolation markers. The two labels are staggered vertically and both anchored
    # to the left of their lines so they cannot collide when the isolation points
    # fall close together on the axis.
    if id_bi is not None:
        ax2.axvline(id_bi, color="#bf8f00", lw=1.6)
        ax2.annotate(f"baseline isolates (point {id_bi})",
                     xy=(id_bi, 0.30), xytext=(id_bi - 0.25, 0.30),
                     fontsize=8, color="#bf8f00", ha="right", va="center")
    if id_ci is not None:
        ax2.axvline(id_ci, color="#1f3864", lw=1.6)
        ax2.annotate(f"coordinated isolates (point {id_ci})",
                     xy=(id_ci, 0.14), xytext=(id_ci - 0.25, 0.14),
                     fontsize=8, color="#1f3864", ha="right", va="center")
    ax2.set_title("Identity drift", fontsize=11)
    ax2.legend(fontsize=8, loc="lower left", framealpha=0.9)

    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"figure6_time_evolution.{ext}"), dpi=600,
                    bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------- sweep
def sweep_time_scenarios():
    """Vary trajectory depth and shape across their definitional ranges.

    Device drift: does 'neither configuration isolates' hold at every depth and
    shape? Identity drift: does the baseline isolate at or before the coordinated
    configuration in every case? The second test is built to detect the opposite
    ordering, which would contradict the explanation given in Section 3.3.2.
    """
    os.makedirs(OUT, exist_ok=True)
    depths = [0.30, 0.20, 0.10, 0.05, 0.0]
    shapes = ["linear", "step3", "step6", "step9", "exp"]
    rows = []

    for depth in depths:
        for shape in shapes:
            traj = make_trajectory(shape, 0.95, depth)
            _, ci, bi = run_session(DEVICE_DRIFT_BASE, [("dev", "posture")], [traj])
            rows.append(dict(scenario="device_posture_drift",
                             depth=depth, shape=shape,
                             coord_isolate_point=ci, baseline_isolate_point=bi,
                             outcome=("neither" if ci is None and bi is None
                                      else f"coord@{ci}/baseline@{bi}")))

    for depth in depths:
        for shape in shapes:
            trajs = [make_trajectory(shape, 0.95, depth),
                     make_trajectory(shape, 0.90, max(0.15, depth)),
                     make_trajectory(shape, 0.90, max(0.30, depth + 0.15))]
            _, ci, bi = run_session(IDENTITY_DRIFT_BASE, IDENTITY_SIGNALS, trajs)
            if ci is None and bi is None:
                verdict = "neither"
            elif bi is not None and (ci is None or bi <= ci):
                verdict = "baseline_first_or_tie"
            else:
                verdict = "COORDINATED_FIRST"
            rows.append(dict(scenario="identity_drift", depth=depth, shape=shape,
                             coord_isolate_point=ci, baseline_isolate_point=bi,
                             outcome=verdict))

    path = os.path.join(OUT, "results_time_sweep.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    dev = [r for r in rows if r["scenario"] == "device_posture_drift"]
    idr = [r for r in rows if r["scenario"] == "identity_drift"]
    print(f"  device drift ({len(dev)} runs): neither isolates in "
          f"{sum(1 for r in dev if r['outcome'] == 'neither')}/{len(dev)}")
    exceptions = [r for r in dev if r["outcome"] != "neither"]
    for r in exceptions:
        print(f"    EXCEPTION depth={r['depth']} shape={r['shape']} -> {r['outcome']}")
    print(f"  identity drift ({len(idr)} runs): baseline first or tie in "
          f"{sum(1 for r in idr if r['outcome'] == 'baseline_first_or_tie')}/{len(idr)}, "
          f"coordinated first in "
          f"{sum(1 for r in idr if r['outcome'] == 'COORDINATED_FIRST')}/{len(idr)}")
    for r in idr:
        if r["outcome"] == "COORDINATED_FIRST":
            print(f"    EXCEPTION depth={r['depth']} shape={r['shape']} "
                  f"-> coordinated isolated first")
    return path


if __name__ == "__main__":
    res = write_time_artifacts()
    print(f"  device drift: coordinated={res['device_coord']} "
          f"baseline={res['device_baseline']} (None = never isolates)")
    print(f"  identity drift: coordinated={res['identity_coord']} "
          f"baseline={res['identity_baseline']}")
    print(f"  single-signal identity drift: coordinated={res['single_coord']} "
          f"baseline={res['single_baseline']} "
          f"(S_id floors at {res['single_final_S_id']})")
    print(f"  -> {res['csv']}")
    sweep_time_scenarios()
    print(f"  -> {os.path.join(OUT, 'results_time_sweep.csv')}")
    print(f"  -> {os.path.join(OUT, 'figure6_time_evolution.png')}")
