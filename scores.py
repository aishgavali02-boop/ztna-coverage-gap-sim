"""
Module 1 - Layer trust scores from named sub-signals.

Each layer score is the weighted sum of four sub-signals and lies in [0,1],
where 1 denotes a fully compliant state and 0 a fully compromised one.

Sub-signal weights were set reasons-first: each weight is defensible from a
source or a stated rationale WITHOUT reference to any scenario outcome. The
ORDERING within each layer is grounded in the cited literature (Hu; Korkuc;
Li; Mishra). The exact MAGNITUDES are disclosed design choices, defended by the
sensitivity sweeps rather than attributed to any external source. The layer
mechanism follows NIST SP 800-207 Sec 3.3.1 (score-based trust algorithm:
per-source values weighted by enterprise configuration, compared to a
threshold).

Weights within each layer sum to 1.0. These values are reported as Table 2 of
the paper.
"""

# --- DEVICE sub-signals ---
# Ordering rationale (reasons-first, no scenario referenced):
#   hw_root_trust (0.30): a hardware root of trust is the hardest device signal
#                         to forge or spoof; Hu treats it as the foundational
#                         device-integrity anchor -> strongest device signal.
#   agent_present (0.25): with no management agent there is no posture
#                         visibility at all; Korkuc frames endpoint enrollment
#                         as the precondition for device trust.
#   posture       (0.25): a real compliance signal, but software-level and
#                         therefore spoofable (Korkuc).
#   patch_level   (0.20): meaningful but slowest-moving and most self-reported
#                         -> weakest device signal.
def score_device(agent_present, posture, patch_level, hw_root_trust):
    return (0.30 * hw_root_trust
            + 0.25 * agent_present
            + 0.25 * posture
            + 0.20 * patch_level)


# --- IDENTITY sub-signals ---
# Ordering rationale (reasons-first, no scenario referenced):
#   mfa                (0.30): front-line authenticator gate; NIST Tenet 6
#                              requires MFA for resource access -> primary
#                              identity assurance.
#   origin_consistency (0.30): NIST Sec 3.3.1 contextual trust algorithms detect
#                              subverted credentials through access patterns
#                              atypical for the subject -> co-top signal for
#                              catching valid-but-stolen credentials.
#   cred_freshness     (0.20): supporting signal; staleness weakens assurance
#                              but does not by itself indicate compromise.
#   role_risk_inv      (0.20): supporting signal; role-appropriateness of the
#                              request.
def score_identity(mfa, cred_freshness, role_risk_inv, origin_consistency):
    return (0.30 * mfa
            + 0.30 * origin_consistency
            + 0.20 * cred_freshness
            + 0.20 * role_risk_inv)


# --- NETWORK sub-signals ---
# Ordering rationale (reasons-first, no scenario referenced):
#   eastwest_normal (0.30): Li centres east-west traffic visibility as the core
#                           signal micro-segmentation exists to provide;
#                           unanalysable east-west traffic raises lateral-attack
#                           success probability. Mishra corroborates lateral
#                           movement as the key network threat -> strongest
#                           network signal.
#   flow_conformity (0.25): overall flow legitimacy against the learned profile
#                           (Li).
#   egress_legit    (0.25): outbound / exfiltration-path legitimacy.
#   zone_correct    (0.20): segmentation and zone placement; supporting
#                           structural signal (Li).
def score_network(flow_conformity, egress_legit, eastwest_normal, zone_correct):
    return (0.30 * eastwest_normal
            + 0.25 * flow_conformity
            + 0.25 * egress_legit
            + 0.20 * zone_correct)
