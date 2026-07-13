"""
Module 1 - State scores and the decision function f.
Sub-signal weights set REASONS-FIRST in the weighting session (see PROJECT_STATE).
Each weight is defensible from source/rationale WITHOUT reference to any scenario outcome.
Layer ordering + mechanism grounded in NIST 800-207 3.3.1 (score-based TA: per-source
values x enterprise-configured weights vs threshold). Sub-signal ORDERING grounded where
possible ([56] Hu, [7] Korkuc, [9] Li, [10] Mishra); exact VALUES are representative design
choices to be sensitivity-swept. ALL VALUES PROVISIONAL until sweeps prove robustness.
"""
TAU = 0.7

# --- DEVICE sub-signals ---
# Ordering rationale (A), reasons-first, no scenario mentioned:
#   hw_root_trust (0.30): hardware root of trust is hardest to forge/spoof; [56] Hu treats it
#                         as the foundational device-integrity anchor -> strongest device signal.
#   agent_present (0.25): no management agent => no posture visibility at all; [7] Korkuc frames
#                         endpoint enrollment/agent as the precondition for device trust.
#   posture       (0.25): real compliance signal but software-level and spoofable [7].
#   patch_level   (0.20): meaningful but slowest-moving and most self-reported -> weakest.
def score_device(agent_present, posture, patch_level, hw_root_trust):
    return (0.30 * hw_root_trust
            + 0.25 * agent_present
            + 0.25 * posture
            + 0.20 * patch_level)

# --- IDENTITY sub-signals ---
# Ordering rationale, reasons-first, no scenario mentioned:
#   mfa                (0.30): front-line authenticator gate; NIST Tenet 6 mandates MFA for
#                              resource access -> primary identity assurance.
#   origin_consistency (0.30): NIST 3.3.1 contextual TA detects subverted credentials via
#                              access patterns atypical for the subject (origin/time anomaly)
#                              -> co-top signal for catching valid-but-stolen credentials.
#   cred_freshness     (0.20): supporting signal; staleness weakens but does not itself breach.
#   role_risk_inv      (0.20): supporting signal; role-appropriateness of the request.
def score_identity(mfa, cred_freshness, role_risk_inv, origin_consistency):
    return (0.30 * mfa
            + 0.30 * origin_consistency
            + 0.20 * cred_freshness
            + 0.20 * role_risk_inv)

# --- NETWORK sub-signals ---
# Ordering rationale, reasons-first, no scenario mentioned:
#   eastwest_normal (0.30): [9] Li centers east-west/lateral traffic visibility as THE core signal
#                           micro-segmentation exists to provide; unanalyzable east-west traffic
#                           raises lateral-attack success probability. [10] Mishra corroborates
#                           lateral movement as the key network threat -> strongest network signal.
#   flow_conformity (0.25): overall flow legitimacy against learned profile [9].
#   egress_legit    (0.25): outbound/exfil-path legitimacy.
#   zone_correct    (0.20): segmentation/zone placement; supporting structural signal [9].
def score_network(flow_conformity, egress_legit, eastwest_normal, zone_correct):
    return (0.30 * eastwest_normal
            + 0.25 * flow_conformity
            + 0.25 * egress_legit
            + 0.20 * zone_correct)

def f(s_id, s_dev, s_net, tau=TAU):
    failing = []
    if s_id < tau:
        failing.append("identity")
    if s_dev < tau:
        failing.append("device")
    if s_net < tau:
        failing.append("network")
    decision = "ALLOW" if not failing else "ISOLATE"
    return decision, failing

if __name__ == "__main__":
    # Sanity re-run of the locked test cases from PROJECT_STATE (verifies engine still behaves).
    print("Device ordering now: hw_root=0.30, agent=0.25, posture=0.25, patch=0.20")
    print()
    # Healthy
    print("Healthy:", f(
        score_identity(1, 0.95, 0.95, 0.95),
        score_device(1, 0.95, 0.95, 1),
        score_network(0.95, 0.95, 0.95, 0.95)))
    # Identity-context single-layer failure (origin collapses, device+net clean)
    s_id = score_identity(mfa=1, cred_freshness=0.9, role_risk_inv=0.9, origin_consistency=0.0)
    s_dev = score_device(agent_present=1, posture=0.9, patch_level=0.9, hw_root_trust=1)
    s_net = score_network(0.9, 1.0, 1.0, 1.0)
    print(f"Origin-fail: S_id={s_id:.2f} S_dev={s_dev:.2f} S_net={s_net:.2f} -> {f(s_id,s_dev,s_net)}")
