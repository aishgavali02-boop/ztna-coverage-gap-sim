"""
Module 3 - Hybrid decision engine: identity-centric baseline vs coordinated.

Design (grounded in NIST SP 800-207):
  BASELINE = identity-centric ZTNA (Sec 3.1.1 "enhanced identity governance"):
    - identity = HARD (floored; identity is the primary requirement)
    - device/network = SOFT ("may alter the confidence level") -> feed the
      composite via LOW weight, NO floor.
  COORDINATED = full integration:
    - all three = HARD (each floored) + composite on top.

Decision rule (hybrid; NIST Sec 3.3.1 sanctions score-based, criteria-based,
and combinations of the two):
  ISOLATE if EITHER
    (a) composite weighted score < tau      [score-based]
    (b) any floored layer < floor           [criteria-based]
  else ALLOW.

Weights, tau and floor are disclosed design parameters, not literature values.
Their robustness is established by the sensitivity sweeps in make_artifacts.py
and reported in Section 3.4 of the paper. Layer scores are computed outputs of
scores.py, never asserted.
"""

TAU = 0.70
FLOOR = 0.40

W_COORD = {"identity": 1/3, "device": 1/3, "network": 1/3}     # full integration
W_BASE = {"identity": 0.70, "device": 0.15, "network": 0.15}   # identity-centric

# Which layers are floored in each configuration:
HARD_COORD = {"identity", "device", "network"}   # all three floored
HARD_BASE = {"identity"}                         # identity only


def composite(s, w):
    """Weighted sum of the three layer scores."""
    return (w["identity"] * s["identity"]
            + w["device"] * s["device"]
            + w["network"] * s["network"])


def decide(s, w, hard_layers, tau=TAU, floor=FLOOR):
    """Return (decision, composite, reasons) for one configuration."""
    reasons = []
    comp = composite(s, w)
    if comp < tau:                                   # (a) score-based test
        reasons.append(f"composite {comp:.2f}<tau")
    for layer in ("identity", "device", "network"):  # (b) criteria-based test
        if layer in hard_layers and s[layer] < floor:
            reasons.append(f"{layer} {s[layer]:.2f}<floor")
    return ("ISOLATE" if reasons else "ALLOW"), comp, reasons


def classify_pair(coord_decision, baseline_decision):
    """Classify the relationship between the two configurations' decisions.

    A COVERAGE GAP is defined in the paper as the coordinated configuration
    isolating a request that the identity-centric baseline allows. The test is
    therefore DIRECTIONAL: disagreement alone is not sufficient. The opposite
    case (coordinated allows, baseline isolates) does occur -- Scenario E at
    floor values below 0.30 -- and is reported separately as REVERSE_GAP.
    """
    if coord_decision == "ISOLATE" and baseline_decision == "ALLOW":
        return "COVERAGE_GAP"
    if coord_decision == "ALLOW" and baseline_decision == "ISOLATE":
        return "REVERSE_GAP"
    if coord_decision == "ALLOW":
        return "agree_allow"
    return "both_isolate"


def decide_both(layer_scores, tau=TAU, floor=FLOOR, w_coord=None, w_base=None):
    """Evaluate one input under both configurations.

    Returns (coord_decision, coord_composite, baseline_decision,
             baseline_composite, classification).
    """
    w_coord = W_COORD if w_coord is None else w_coord
    w_base = W_BASE if w_base is None else w_base
    cd, cc, _ = decide(layer_scores, w_coord, HARD_COORD, tau=tau, floor=floor)
    bd, bc, _ = decide(layer_scores, w_base, HARD_BASE, tau=tau, floor=floor)
    return cd, cc, bd, bc, classify_pair(cd, bd)
