"""
Scenario definitions at sub-signal level, plus the layer-score helper.

Sub-signal inputs are set from each threat narrative -- what the story says is
compromised -- and never chosen to hit a target layer score. Layer scores are
computed by scores.py from those inputs and passed to hybrid_v4.decide().

Every input value is classified in SCENARIO_GROUNDING.md as one of:
  [GIVEN]  the narrative fixes it (a replayed token has already passed MFA)
  [FACT]   a binary fact of the threat, citation-backed (an unmanaged host has
           no enrolled agent and no hardware root of trust)
  [SWEEP]  a magnitude choice, disclosed as representative and varied in the
           sensitivity sweep

Scenario B is split into B_mild and B_severe. Under both severities the device
score stays above the floor (0.733 and 0.603) and both configurations allow
access. This follows directly from the disclosed device weighting: the hardware
root of trust (0.30) and the management agent (0.25) together account for 0.55
of the device score, and neither is removed by a mid-session software-posture
compromise, so degradation of the soft signals alone cannot drive the layer
below the floor. The outcome is reported as a limitation of the approach; the
floor is not lowered and the weights are not changed to produce a detection.
See Section 3.2.3 and Section 4.4 of the paper.
"""
import scores
import hybrid_v4 as hv

# Sub-signal inputs per scenario, justified by the scenario NARRATIVE only.
# Clean signal ~ 0.9-1.0; degraded ~ 0.5-0.7; compromised ~ 0.0-0.3.
SUB = {
    # INPUT GROUNDING: every value is classified [GIVEN] (story forces it) / [FACT] (binary
    # threat fact, cited) / [SWEEP] (magnitude guess, tested by the sensitivity sweep) in
    # SCENARIO_GROUNDING.md. Nothing tuned; layer scores are computed outputs. [SWEEP] values
    # are the ones the sweep varies to establish robustness.
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
