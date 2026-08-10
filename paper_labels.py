"""
Shared presentation constants: the scenario labels and the greyscale-safe
palette used by every figure in the paper. Kept in one place so that the
figures cannot drift apart from each other or from the manuscript.
"""

SCEN_ORDER = ["Healthy", "A_session_hijack", "B_mild_drift", "B_severe_drift",
              "C_supply_chain", "D_iiot_lateral", "E_identity_compromise"]

# Manuscript labels. Code names are never printed in a figure.
PAPER_LABEL = {
    "Healthy":               "Healthy\n(control)",
    "A_session_hijack":      "A: Session\nhijack",
    "B_mild_drift":          "B (mild):\nPosture drift",
    "B_severe_drift":        "B (severe):\nPosture drift",
    "C_supply_chain":        "C: Supply\nchain",
    "D_iiot_lateral":        "D: IIoT\nlateral",
    "E_identity_compromise": "E: Identity\ncompromise",
}

FLAT_LABEL = {k: v.replace("\n", " ") for k, v in PAPER_LABEL.items()}

# Categorical palette. Chosen to survive greyscale printing: the four
# categories differ in lightness, not only in hue.
CAT_COLOR = {
    "COVERAGE_GAP": "#1f3864",   # darkest  - coordinated isolates, baseline allows
    "REVERSE_GAP":  "#8c6d31",   # dark     - coordinated allows, baseline isolates
    "both_isolate": "#8fa9d0",   # mid      - both isolate
    "agree_allow":  "#e8e8e8",   # lightest - both allow
}

CAT_LABEL = {
    "COVERAGE_GAP": "Coverage gap",
    "REVERSE_GAP":  "Reverse gap",
    "both_isolate": "Both isolate",
    "agree_allow":  "Both allow",
}

COORD_COLOR = "#1f3864"
BASE_COLOR = "#c00000"
