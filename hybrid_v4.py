"""
Module 3 (v4) - Hybrid decision: baseline vs coordinated.
Design (grounded in NIST 800-207):
  BASELINE = identity-centric ZTNA (Sec 3.1.1 "enhanced identity governance"):
    - identity = HARD (has a floor; identity is the "primary requirement")
    - device/network = SOFT ("may alter the confidence level") -> feed the
      composite via LOW weight, NO floor.
  COORDINATED = full integration:
    - all three = HARD (each has a floor) + composite on top.
Decision (hybrid, NIST Sec 3.3.1 sanctions score-based + criteria-based + combo):
  ISOLATE if EITHER:
    (a) composite weighted score < tau        [score-based]
    (b) any HARD layer < floor                [criteria-based]
  else ALLOW.
Weights + tau + floor are STATIC config (representative values; to be
sensitivity-swept). Scores are DYNAMIC per scenario. ALL VALUES PROVISIONAL.
"""
TAU = 0.7
FLOOR = 0.40   # PROVISIONAL representative value; to be sensitivity-swept
W_COORD = {"identity": 1/3, "device": 1/3, "network": 1/3}   # full integration
W_BASE  = {"identity": 0.70, "device": 0.15, "network": 0.15}  # identity-centric
# Which layers are HARD (floored) in each system:
HARD_COORD = {"identity", "device", "network"}   # all hard
HARD_BASE  = {"identity"}                          # identity hard; dev/net soft
def composite(s, w):
    return w["identity"]*s["identity"] + w["device"]*s["device"] + w["network"]*s["network"]
def decide(s, w, hard_layers, tau=TAU, floor=FLOOR):
    reasons = []
    # (a) score-based
    comp = composite(s, w)
    if comp < tau:
        reasons.append(f"composite {comp:.2f}<tau")
    # (b) criteria-based: only HARD layers have a floor
    for layer in ("identity", "device", "network"):
        if layer in hard_layers and s[layer] < floor:
            reasons.append(f"{layer} {s[layer]:.2f}<floor")
    decision = "ISOLATE" if reasons else "ALLOW"
    return decision, comp, reasons
SCENARIOS = {
    "Healthy":              {"identity":0.96,"device":0.96,"network":0.97},
    "A_session_hijack":     {"identity":0.96,"device":0.11,"network":0.80},
    "B_posture_drift":      {"identity":0.95,"device":0.30,"network":0.85},
    "C_supply_chain":       {"identity":0.94,"device":0.25,"network":0.27},
    "D_iiot_lateral":       {"identity":0.92,"device":0.91,"network":0.27},
    "E_identity_compromise":{"identity":0.35,"device":0.95,"network":0.96},
    "TEST_network_0.30":    {"identity":0.95,"device":0.95,"network":0.30},
}
if __name__ == "__main__":
    print(f"tau={TAU}  floor={FLOOR}")
    print(f"{'scenario':<24}{'COORD':<28}{'BASELINE':<28}")
    print("-"*80)
    for name, s in SCENARIOS.items():
        cd, cc, cr = decide(s, W_COORD, HARD_COORD)
        bd, bc, br = decide(s, W_BASE, HARD_BASE)
        gap = "  <-- COVERAGE GAP" if cd != bd else ""
        cstr = f"{cd}({cc:.2f}) {';'.join(cr) if cr else ''}"
        bstr = f"{bd}({bc:.2f}) {';'.join(br) if br else ''}"
        print(f"{name:<24}{cstr:<28}{bstr:<28}{gap}")
