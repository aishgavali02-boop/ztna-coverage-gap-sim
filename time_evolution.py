"""
time_evolution.py -- Discrete-time trust evolution (continuous re-evaluation).

Models a SESSION as a sequence of discrete time steps. A signal starts healthy and, under
compromise, DEGRADES over time along a defined trajectory. At every tick the system recomputes
scores and re-decides ALLOW/ISOLATE (NIST continuous-verification tenet). The measured output is
the TICK AT WHICH each system first isolates -- and whether it ever does.

DISCIPLINE (same as the whole project):
  - The degradation trajectory comes from the scenario NARRATIVE, not tuned to a result.
  - Re-eval interval + trajectory shape are representative and SWEPT; results reported as
    "holds across trajectories" or the boundary is stated honestly.
  - Detection tick is a COMPUTED output, never asserted.

This is a discrete-TIME trust-evolution model, NOT the retired SimPy discrete-EVENT latency
engine. No network/PEP timing. Time here = re-evaluation ticks, not milliseconds of enforcement.
"""
import copy
import numpy as np
import scores
import hybrid_v4 as hv


def linear_decay(start, end, n_ticks):
    """Signal moves start->end linearly over n_ticks (inclusive)."""
    return list(np.round(np.linspace(start, end, n_ticks), 4))


def step_decay(start, end, n_ticks, drop_at):
    """Signal holds at start, then drops to end at tick drop_at (sudden compromise)."""
    return [start if t < drop_at else end for t in range(n_ticks)]


def exp_decay(start, end, n_ticks, k=3.0):
    """Signal decays start->end on an exponential-ish curve (fast then slow)."""
    xs = np.linspace(0, 1, n_ticks)
    curve = np.exp(-k * xs)
    curve = (curve - curve.min()) / (curve.max() - curve.min())  # normalize 1->0
    vals = end + (start - end) * curve
    return list(np.round(vals, 4))


def run_session(base_signals, degrading, trajectory):
    """
    base_signals: dict with 'id','dev','net' sub-signal dicts (healthy/steady values).
    degrading: (layer, subsignal) tuple naming the signal that changes over time.
    trajectory: list of values for that sub-signal, one per tick.
    Returns per-tick layer scores + both systems' decisions + first-isolate tick.
    """
    layer, sub = degrading
    ticks = []
    coord_isolate_tick = None
    base_isolate_tick = None

    for t, val in enumerate(trajectory):
        s = copy.deepcopy(base_signals)
        s[layer][sub] = val
        L = {
            "identity": scores.score_identity(**s["id"]),
            "device":   scores.score_device(**s["dev"]),
            "network":  scores.score_network(**s["net"]),
        }
        cd, cc, _ = hv.decide(L, hv.W_COORD, hv.HARD_COORD)
        bd, bc, _ = hv.decide(L, hv.W_BASE, hv.HARD_BASE)
        if cd == "ISOLATE" and coord_isolate_tick is None:
            coord_isolate_tick = t
        if bd == "ISOLATE" and base_isolate_tick is None:
            base_isolate_tick = t
        ticks.append(dict(t=t, degraded_value=val,
                          S_dev=round(L["device"], 4),
                          S_id=round(L["identity"], 4),
                          S_net=round(L["network"], 4),
                          coord=cd, coord_comp=round(cc, 4),
                          baseline=bd, base_comp=round(bc, 4)))
    return ticks, coord_isolate_tick, base_isolate_tick


# --- Scenario B as a TIME-VARYING session -------------------------------------
# Narrative: session authenticates clean, then device posture degrades over the session
# as malware establishes itself. Agent + hw_root stay intact (physical, don't vanish mid-
# session) -- the faithful constraint from the snapshot analysis. Identity + network clean.
# We degrade dev.posture from healthy (0.95) down to cratered (0.05) across the session.
B_BASE = {
    "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
    "dev": dict(agent_present=1, posture=0.95, patch_level=0.6, hw_root_trust=1),
    "net": dict(flow_conformity=0.85, egress_legit=0.85, eastwest_normal=0.85, zone_correct=0.9),
}

# --- Scenario F: identity/origin drift mid-session (the POSITIVE time-varying case) ----------
# Narrative: session authenticates clean (MFA passed). The token is then replayed from an
# increasingly anomalous origin -- attacker requests diverge from the user's established pattern
# over the session. origin_consistency degrades tick by tick; MFA stays satisfied (token already
# passed); device + network clean. Identity is hard-floored in BOTH systems, so this tests WHEN
# each system reacts as the identity signal decays. Trajectory from narrative, not tuned.
F_BASE = {
    "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
    "dev": dict(agent_present=1, posture=0.9, patch_level=0.85, hw_root_trust=1),
    "net": dict(flow_conformity=0.9, egress_legit=0.9, eastwest_normal=0.9, zone_correct=0.9),
}


# --- Scenario G: MULTI-signal identity drift (realistic session hijack over time) ------------
# Narrative: token replayed by attacker. Over the session, MULTIPLE identity signals degrade
# together as the attacker's behavior diverges from the legitimate user: origin_consistency
# falls (different location/network), role_risk_inv falls (accessing things off the user's normal
# role), cred_freshness falls (session context ages/desyncs). MFA stays satisfied -- the stolen
# token already passed it; that is the whole point of a hijack. Device + network clean.
# All three degrading signals move together on the SAME trajectory because the narrative says the
# attacker's whole identity context diverges at once -- NOT tuned to cross a threshold.
G_BASE = {
    "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
    "dev": dict(agent_present=1, posture=0.9, patch_level=0.85, hw_root_trust=1),
    "net": dict(flow_conformity=0.9, egress_legit=0.9, eastwest_normal=0.9, zone_correct=0.9),
}


def run_multi(base, degrading_list, trajectories):
    """Like run_session but degrades several sub-signals, each on its own trajectory."""
    n = len(trajectories[0])
    ticks = []
    coord_isolate_tick = None
    base_isolate_tick = None
    for t in range(n):
        s = copy.deepcopy(base)
        for (layer, sub), traj in zip(degrading_list, trajectories):
            s[layer][sub] = traj[t]
        L = {
            "identity": scores.score_identity(**s["id"]),
            "device":   scores.score_device(**s["dev"]),
            "network":  scores.score_network(**s["net"]),
        }
        cd, cc, _ = hv.decide(L, hv.W_COORD, hv.HARD_COORD)
        bd, bc, _ = hv.decide(L, hv.W_BASE, hv.HARD_BASE)
        if cd == "ISOLATE" and coord_isolate_tick is None:
            coord_isolate_tick = t
        if bd == "ISOLATE" and base_isolate_tick is None:
            base_isolate_tick = t
        ticks.append(dict(t=t, S_id=round(L["identity"], 4), S_dev=round(L["device"], 4),
                          S_net=round(L["network"], 4), coord=cd, coord_comp=round(cc, 4),
                          baseline=bd, base_comp=round(bc, 4)))
    return ticks, coord_isolate_tick, base_isolate_tick


def run_scenario_G(N=11):
    print("=== Scenario G: multi-signal identity drift (origin+role+cred degrade together) ===")
    for name, endpts in [("linear", None), ("step@6", 6)]:
        if endpts is None:
            trajs = [linear_decay(0.95, 0.0, N),   # origin
                     linear_decay(0.90, 0.15, N),  # role_risk_inv
                     linear_decay(0.90, 0.30, N)]  # cred_freshness
        else:
            trajs = [step_decay(0.95, 0.0, N, endpts),
                     step_decay(0.90, 0.15, N, endpts),
                     step_decay(0.90, 0.30, N, endpts)]
        degrading = [("id", "origin_consistency"), ("id", "role_risk_inv"), ("id", "cred_freshness")]
        ticks, ci, bi = run_multi(G_BASE, degrading, trajs)
        print(f"  --- {name} ---")
        print(f"  {'t':>2} {'S_id':>6} {'coord':>8} {'baseline':>9}")
        for row in ticks:
            print(f"  {row['t']:>2} {row['S_id']:>6} {row['coord']:>8} {row['baseline']:>9}")
        print(f"    coord first ISOLATE tick={ci}  baseline first ISOLATE tick={bi}\n")


def run_all_demo():
    N = 11
    print(f"tau={hv.TAU} floor={hv.FLOOR}\n")

    print("=== Scenario B: device posture drift (0.95 -> 0.05) ===")
    for name, traj in [
        ("linear", linear_decay(0.95, 0.05, N)),
        ("step@6", step_decay(0.95, 0.05, N, drop_at=6)),
        ("exp",    exp_decay(0.95, 0.05, N)),
    ]:
        ticks, ci, bi = run_session(B_BASE, ("dev", "posture"), traj)
        print(f"  {name:8} coord first ISOLATE tick={ci}  baseline first ISOLATE tick={bi}")

    print("\n=== Scenario F: identity origin drift (0.95 -> 0.0) ===")
    for name, traj in [
        ("linear", linear_decay(0.95, 0.0, N)),
        ("step@6", step_decay(0.95, 0.0, N, drop_at=6)),
        ("exp",    exp_decay(0.95, 0.0, N)),
    ]:
        ticks, ci, bi = run_session(F_BASE, ("id", "origin_consistency"), traj)
        print(f"  --- {name} ---")
        print(f"  {'t':>2} {'origin':>7} {'S_id':>6} {'coord':>8} {'baseline':>9}")
        for row in ticks:
            print(f"  {row['t']:>2} {row['degraded_value']:>7} {row['S_id']:>6} "
                  f"{row['coord']:>8} {row['baseline']:>9}")
        print(f"    coord first ISOLATE tick={ci}  baseline first ISOLATE tick={bi}\n")


# --- Artifact output: save B + G time-series to CSV + a figure ------------------------------
def write_time_artifacts(outdir):
    import csv, os
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(outdir, exist_ok=True)
    N = 11

    # B: device posture drift (linear) -- the honest MISS
    b_ticks, b_ci, b_bi = run_session(B_BASE, ("dev", "posture"),
                                      linear_decay(0.95, 0.05, N))
    # G: multi-signal identity drift (linear) -- the two-sided result
    g_trajs = [linear_decay(0.95, 0.0, N), linear_decay(0.90, 0.15, N),
               linear_decay(0.90, 0.30, N)]
    g_degrading = [("id", "origin_consistency"), ("id", "role_risk_inv"),
                   ("id", "cred_freshness")]
    g_ticks, g_ci, g_bi = run_multi(G_BASE, g_degrading, g_trajs)

    # CSV
    path_csv = os.path.join(outdir, "results_time_evolution.csv")
    with open(path_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "tick", "S_id", "S_dev", "S_net",
                    "coord_decision", "baseline_decision"])
        for r in b_ticks:
            w.writerow(["B_device_posture_drift", r["t"], r["S_id"], r["S_dev"],
                        r["S_net"], r["coord"], r["baseline"]])
        for r in g_ticks:
            w.writerow(["G_identity_multisignal_drift", r["t"], r["S_id"], r["S_dev"],
                        r["S_net"], r["coord"], r["baseline"]])

    # Figure: the degrading layer score over ticks, with tau + floor + isolate markers
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    b_dev = [r["S_dev"] for r in b_ticks]
    ax1.plot(range(N), b_dev, marker="o", label="S_device")
    ax1.axhline(hv.TAU, ls="--", color="black", lw=1, label=f"tau={hv.TAU}")
    ax1.axhline(hv.FLOOR, ls=":", color="red", lw=1, label=f"floor={hv.FLOOR}")
    ax1.set_title("B: device posture drift\n(neither system isolates \u2014 class limitation over time)")
    ax1.set_xlabel("re-evaluation tick"); ax1.set_ylabel("layer score"); ax1.set_ylim(0, 1)
    ax1.legend(fontsize=8)

    g_id = [r["S_id"] for r in g_ticks]
    ax2.plot(range(N), g_id, marker="o", color="tab:purple", label="S_identity")
    ax2.axhline(hv.TAU, ls="--", color="black", lw=1, label=f"tau={hv.TAU}")
    ax2.axhline(hv.FLOOR, ls=":", color="red", lw=1, label=f"floor={hv.FLOOR}")
    if g_bi is not None:
        ax2.axvline(g_bi, color="tab:orange", lw=1.5, label=f"baseline isolates (t={g_bi})")
    if g_ci is not None:
        ax2.axvline(g_ci, color="tab:blue", lw=1.5, label=f"coordinated isolates (t={g_ci})")
    ax2.set_title("G: identity multi-signal drift\n(baseline isolates FIRST \u2014 identity is its strength)")
    ax2.set_xlabel("re-evaluation tick"); ax2.set_ylabel("layer score"); ax2.set_ylim(0, 1)
    ax2.legend(fontsize=8)

    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(outdir, f"fig4_time_evolution.{ext}"), dpi=200)
    plt.close(fig)

    return dict(csv=path_csv, B_coord_isolate=b_ci, B_base_isolate=b_bi,
                G_coord_isolate=g_ci, G_base_isolate=g_bi)


if __name__ == "__main__":
    run_all_demo()
    run_scenario_G()


# --- SWEEP the time scenarios (depth, rate, shape) ------------------------------------------
# Discipline: vary across DEFINITIONAL ranges, report where results hold/flip, never stop at a
# convenient point. For G the load-bearing question: does baseline isolate at <= coordinated's
# tick across all trajectories? For B: does "neither isolates" hold across all depths?
def sweep_time_scenarios():
    import csv, os
    rows = []
    N = 11
    depths = [0.30, 0.20, 0.10, 0.05, 0.0]        # how far the signal ultimately falls
    shapes = ["linear", "step3", "step6", "step9", "exp"]

    def make(shape, start, end):
        if shape == "linear": return linear_decay(start, end, N)
        if shape == "exp":    return exp_decay(start, end, N)
        if shape.startswith("step"):
            return step_decay(start, end, N, drop_at=int(shape[4:]))

    # --- B: device posture drift. Sweep depth + shape. ---
    for depth in depths:
        for shape in shapes:
            traj = make(shape, 0.95, depth)
            _, ci, bi = run_session(B_BASE, ("dev", "posture"), traj)
            rows.append(dict(scenario="B_device_posture", knob=f"depth={depth},shape={shape}",
                             coord_isolate_tick=ci, baseline_isolate_tick=bi,
                             outcome=("neither" if ci is None and bi is None
                                      else f"coord@{ci}/base@{bi}")))

    # --- G: identity multi-signal drift. Sweep depth (of origin) + shape.
    # role_risk and cred degrade proportionally to origin's depth (same narrative, scaled). ---
    for depth in depths:
        for shape in shapes:
            o = make(shape, 0.95, depth)
            r = make(shape, 0.90, max(0.15, depth))     # role ends slightly higher
            c = make(shape, 0.90, max(0.30, depth + 0.15))  # cred ends higher still
            degrading = [("id", "origin_consistency"), ("id", "role_risk_inv"),
                         ("id", "cred_freshness")]
            _, ci, bi = run_multi(G_BASE, degrading, [o, r, c])
            # the load-bearing check: baseline isolates no later than coordinated?
            if ci is None and bi is None:
                verdict = "neither"
            elif bi is not None and (ci is None or bi <= ci):
                verdict = "baseline_first_or_tie"   # the expected structural result
            else:
                verdict = "COORD_FIRST"             # would contradict the structural claim
            rows.append(dict(scenario="G_identity_multisig", knob=f"depth={depth},shape={shape}",
                             coord_isolate_tick=ci, baseline_isolate_tick=bi, outcome=verdict))

    path = os.path.join("artifacts", "results_time_sweep.csv")
    os.makedirs("artifacts", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # summarize
    b = [r for r in rows if r["scenario"] == "B_device_posture"]
    g = [r for r in rows if r["scenario"] == "G_identity_multisig"]
    b_neither = sum(1 for r in b if r["outcome"] == "neither")
    g_base_first = sum(1 for r in g if r["outcome"] == "baseline_first_or_tie")
    g_coord_first = sum(1 for r in g if r["outcome"] == "COORD_FIRST")
    g_neither = sum(1 for r in g if r["outcome"] == "neither")
    print(f"B sweep ({len(b)} runs): 'neither isolates' in {b_neither}/{len(b)}")
    b_caught = [r for r in b if r["outcome"] != "neither"]
    if b_caught:
        print("  B EXCEPTIONS (something caught it):")
        for r in b_caught: print("   ", r["knob"], "->", r["outcome"])
    print(f"G sweep ({len(g)} runs): baseline_first_or_tie={g_base_first}, "
          f"coord_first={g_coord_first}, neither={g_neither}")
    if g_coord_first:
        print("  G EXCEPTIONS (coordinated caught FIRST -- would break the claim):")
        for r in g:
            if r["outcome"] == "COORD_FIRST": print("   ", r["knob"], "->", r)
    return path

if __name__ == "__main__":
    pass
