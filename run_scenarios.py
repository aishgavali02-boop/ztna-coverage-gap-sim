"""
Run the four real scenarios (A-D) + E through scores.py -> hybrid_v4 decision.
Scenario sub-signal inputs are set FROM THE NARRATIVE (what is compromised), NOT
to hit a target layer score. Layer scores are COMPUTED by scores.py, then fed to
the hybrid decide(). This is the first run with reasons-first sub-signal weights.
OBSERVE the output; do NOT tune weights to it.

SCENARIO B RESOLUTION (locked):
  B split into B_mild + B_severe. Both compute device ABOVE floor (0.73 / 0.60) and
  both ALLOW under coordinated -> neither is a coverage gap. This is NOT tuned; it is
  a consequence of the reasons-first device weights: hw_root_trust(0.30)+agent(0.25)=0.55
  are hard-to-forge and stay intact under posture drift, so posture collapse alone cannot
  drag device below the floor.
  DECISION: Option 1 -- report B_severe as an HONEST LIMITATION, not a defect, and do NOT
  lower the floor or reweight to force a gap (that would be tuning-to-outcome).
    - CLASS limitation (citable): signal-based access control cannot catch a threat that
      stays clean on its heavily-weighted/evaluated signals. Cite NIST SP 800-207 Sec 5.3
      (valid attacker / insider operating within authorized purview). VERIFIED verbatim.
    - SPECIFIC manifestation (disclosed, NOT cited): device=0.60 while posture~0.05 follows
      directly from the Sec 2.4.1 weighting. Disclose as a consequence of disclosed params
      (satisfies McIntosh disclosed-parameter bar); there is nothing external to cite for it.
  SYED [2] DROPPED for this point: full paper read (incl. Sec VIII Discussion) -- Syed does
  NOT state the within-pattern limitation. Do not cite Syed here. NIST 5.3 stands alone.
  This blind spot is the same class as the locked Sec 4.4 scope note.
"""
import scores
import hybrid_v4 as hv

# Sub-signal inputs per scenario, justified by the scenario NARRATIVE only.
# Clean signal ~ 0.9-1.0; degraded ~ 0.5-0.7; compromised ~ 0.0-0.3.
SUB = {
    # INPUT GROUNDING: every value is classified [GIVEN] (story forces it) / [FACT] (binary
    # threat fact, cited) / [SWEEP] (magnitude guess, tested by Step-2 sweep) in
    # SCENARIO_GROUNDING.md. Nothing tuned; layer scores are computed outputs. [SWEEP] values
    # are the ones the sweep must vary to prove robustness.
    # A: session hijack via token exfil. Identity looks valid (token replayed) EXCEPT origin;
    #    device is the compromised layer (exfil host: no agent, bad posture, no hw root).
    "A_session_hijack": {
        "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.5),
        "dev": dict(agent_present=0, posture=0.2, patch_level=0.3, hw_root_trust=0),
        "net": dict(flow_conformity=0.85, egress_legit=0.8, eastwest_normal=0.85, zone_correct=0.9),
    },
    # B_mild: routine post-auth posture drift. Patch slips behind, one posture check fails.
    #    Agent stays enrolled; hw root of trust intact (physical, does not vanish mid-session).
    #    Identity + network clean. Represents the common gray-zone drift.
    "B_mild_drift": {
        "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
        "dev": dict(agent_present=1, posture=0.45, patch_level=0.35, hw_root_trust=1),
        "net": dict(flow_conformity=0.85, egress_legit=0.85, eastwest_normal=0.85, zone_correct=0.9),
    },
    # B_severe: active-compromise drift. EDR reports active malware mid-session -> posture
    #    CRATERS (~0.05) and patch bad. BUT agent still enrolled (1) and hw root intact (1) --
    #    those do not physically disappear mid-session. This is the faithful severe case:
    #    does the coordinated floor catch a genuine active compromise when the hard-to-forge
    #    signals are (correctly) still up? Report whatever falls out; do NOT nudge to clear floor.
    "B_severe_drift": {
        "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.95),
        "dev": dict(agent_present=1, posture=0.05, patch_level=0.2, hw_root_trust=1),
        "net": dict(flow_conformity=0.85, egress_legit=0.85, eastwest_normal=0.85, zone_correct=0.9),
    },
    # C: supply-chain compromise, edge/agentless device. Device synthetic + noisy (no agent,
    #    no hw root, weak posture); network also anomalous (unexpected east-west + egress).
    "C_supply_chain": {
        "id":  dict(mfa=1, cred_freshness=0.85, role_risk_inv=0.9, origin_consistency=0.9),
        "dev": dict(agent_present=0, posture=0.3, patch_level=0.4, hw_root_trust=0),
        "net": dict(flow_conformity=0.35, egress_legit=0.3, eastwest_normal=0.25, zone_correct=0.4),
    },
    # D: compromised legacy IIoT / OT lateral movement. Identity + device look ok; NETWORK is
    #    the compromised layer (abnormal east-west, wrong zone, illegit egress).
    "D_iiot_lateral": {
        "id":  dict(mfa=1, cred_freshness=0.9, role_risk_inv=0.85, origin_consistency=0.9),
        "dev": dict(agent_present=1, posture=0.85, patch_level=0.8, hw_root_trust=1),
        "net": dict(flow_conformity=0.3, egress_legit=0.35, eastwest_normal=0.2, zone_correct=0.3),
    },
    # E: identity-layer compromise (impossible-travel / anomalous origin + failed MFA context).
    #    Device + network clean. Both systems should catch this (identity hard for both).
    "E_identity_compromise": {
        "id":  dict(mfa=0, cred_freshness=0.6, role_risk_inv=0.7, origin_consistency=0.0),
        "dev": dict(agent_present=1, posture=0.9, patch_level=0.9, hw_root_trust=1),
        "net": dict(flow_conformity=0.9, egress_legit=0.9, eastwest_normal=0.9, zone_correct=0.9),
    },
    "Healthy": {
        "id":  dict(mfa=1, cred_freshness=0.95, role_risk_inv=0.95, origin_consistency=0.95),
        "dev": dict(agent_present=1, posture=0.95, patch_level=0.95, hw_root_trust=1),
        "net": dict(flow_conformity=0.95, egress_legit=0.95, eastwest_normal=0.95, zone_correct=0.95),
    },
}

def layer_scores(s):
    return {
        "identity": scores.score_identity(**s["id"]),
        "device":   scores.score_device(**s["dev"]),
        "network":  scores.score_network(**s["net"]),
    }

print(f"tau={hv.TAU}  floor={hv.FLOOR}")
print(f"{'scenario':<22}{'S_id':>6}{'S_dev':>7}{'S_net':>7}  | {'COORD':<26}{'BASELINE':<26} gap?")
print("-"*104)
for name, s in SUB.items():
    L = layer_scores(s)
    cd, cc, cr = hv.decide(L, hv.W_COORD, hv.HARD_COORD)
    bd, bc, br = hv.decide(L, hv.W_BASE,  hv.HARD_BASE)
    gap = "COVERAGE GAP" if cd != bd else ("agree" if cd=="ALLOW" else "both ISOLATE")
    cstr = f"{cd}({cc:.2f})"
    bstr = f"{bd}({bc:.2f})"
    print(f"{name:<22}{L['identity']:>6.2f}{L['device']:>7.2f}{L['network']:>7.2f}  | {cstr:<26}{bstr:<26}{gap}")
