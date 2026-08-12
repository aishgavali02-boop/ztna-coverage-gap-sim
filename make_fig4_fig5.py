"""
make_fig4_fig5.py -- Figure 4 (hybrid decision rule) and Figure 5 (composite
scores and decisions by scenario).

Figure 4 is a schematic of the decision rule defined in hybrid_v4.py. Its
parameter values are read from that module rather than typed, so the diagram
cannot drift from the engine.

Figure 5 is computed: every bar height and every decision comes from
run_scenarios.py -> scores.py -> hybrid_v4.py. Nothing is asserted.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from decimal import Decimal, ROUND_HALF_UP

import hybrid_v4 as hv
from run_scenarios import SUB, layer_scores
from paper_labels import SCEN_ORDER, PAPER_LABEL, COORD_COLOR, BASE_COLOR

def _fmt3(v):
    return str(Decimal(str(v)).quantize(Decimal("1.000"), rounding=ROUND_HALF_UP))


OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)


def _save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=600,
                    bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------
# FIGURE 4 -- hybrid decision rule schematic
# ----------------------------------------------------------------------
def figure5():
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.set_xlim(0, 100); ax.set_ylim(0, 52); ax.axis("off")

    def box(x, y, w, h, text, fc, ec, tc="black", fs=9.5, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.6,rounding_size=1.2",
                                    fc=fc, ec=ec, lw=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, weight=weight)

    def arrow(x1, y1, x2, y2, color="#555555", label=None, lx=0, ly=0):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), color=color,
                                     arrowstyle="-|>", mutation_scale=13,
                                     lw=1.2, shrinkA=2, shrinkB=2))
        if label:
            ax.text(lx, ly, label, fontsize=8.5, color=color, ha="center")

    # inputs
    box(1, 34, 20, 9, "Layer 1: Identity\n$S_{id}$", "#dce6f5", "#1f3864")
    box(1, 22, 20, 9, "Layer 2: Device\n$S_{dev}$", "#dcecdc", "#375623")
    box(1, 10, 20, 9, "Layer 3: Network\n$S_{net}$", "#e6dcf0", "#5b3a8e")
    ax.text(11, 6.5, "layer scores in [0,1]", fontsize=8.5,
            style="italic", ha="center", color="#555555")

    # PDP
    box(30, 20, 16, 13, "Layer 4\nPDP", "#1f3864", "#1f3864",
        tc="white", fs=11, weight="bold")
    for y in (38.5, 26.5, 14.5):
        arrow(21, y, 30, 26.5)

    # tests
    box(53, 31, 27, 11,
        f"Test 1: per-layer floor\nany floored layer < {hv.FLOOR:.2f} ?",
        "#fdf0dc", "#bf8f00")
    box(53, 11, 27, 11,
        "Test 2: composite\n"
        r"$w_{id}S_{id} + w_{dev}S_{dev} + w_{net}S_{net} < \tau$ ?",
        "#fdf0dc", "#bf8f00")
    arrow(46, 28, 53, 36.5)
    arrow(46, 25, 53, 16.5)
    arrow(66.5, 31, 66.5, 22, color="#375623", label="no", lx=68.5, ly=26)

    # outcomes
    box(85, 31, 14, 11, "ISOLATE", "#f7dede", "#c00000",
        tc="#c00000", fs=11, weight="bold")
    box(85, 11, 14, 11, "ALLOW", "#dcecdc", "#375623",
        tc="#375623", fs=11, weight="bold")
    arrow(80, 36.5, 85, 36.5, color="#c00000", label="yes", lx=82.5, ly=38.2)
    arrow(80, 16.5, 85, 34, color="#c00000", label="yes", lx=82.5, ly=19.5)
    arrow(80, 14.5, 85, 16.5, color="#375623", label="no", lx=82.5, ly=12.3)

    ax.text(0, 49.5,
            "Hybrid decision rule: composite score test combined with "
            "per-layer floor test", fontsize=12, weight="bold", ha="left")
    ax.text(0, 46,
            rf"$\tau$ = {hv.TAU:.2f} applied to the composite;   "
            rf"floor = {hv.FLOOR:.2f} applied to each floored layer",
            fontsize=9.5, ha="left", color="#444444")
    ax.text(50, 2.5,
            "The request is isolated if either test is true; access is allowed "
            "only if both are false.",
            fontsize=9, style="italic", ha="center", color="#444444")
    _save(fig, "figure4_decision_rule")


# ----------------------------------------------------------------------
# FIGURE 5 -- computed composite scores and decisions
# ----------------------------------------------------------------------
def figure6():
    rows = []
    for name in SCEN_ORDER:
        L = layer_scores(SUB[name])
        cd, cc, bd, bc, cls = hv.decide_both(L)
        rows.append((name, cd, cc, bd, bc, cls))

    x = np.arange(len(rows))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11.5, 6))

    for i, (name, cd, cc, bd, bc, cls) in enumerate(rows):
        for off, dec, val, col in ((-w/2, cd, cc, COORD_COLOR),
                                   (+w/2, bd, bc, BASE_COLOR)):
            solid = (dec == "ISOLATE")
            ax.bar(i + off, val, w, color=col, edgecolor=col, linewidth=1.1,
                   alpha=1.0 if solid else 0.32)
            ax.text(i + off, val + 0.015, _fmt3(val), ha="center",
                    va="bottom", fontsize=8.2)
            ax.text(i + off, 0.022, "ISO" if solid else "ALW", ha="center",
                    va="bottom", fontsize=7.8, weight="bold",
                    color="white" if solid else "#333333")

    ax.axhline(hv.TAU, ls="--", lw=1.3, color="black")
    ax.text(len(rows) - 0.42, hv.TAU + 0.012, rf"$\tau$ = {hv.TAU:.2f}",
            fontsize=9.5, ha="right")

    # annotate the computed coverage gaps; positions are derived, not typed
    for i, (name, cd, cc, bd, bc, cls) in enumerate(rows):
        if cls == "COVERAGE_GAP":
            ax.annotate("", xy=(i - w/2, cc + 0.03), xytext=(i + w/2, bc + 0.03),
                        arrowprops=dict(arrowstyle="<->", color="#8c4a00", lw=1.2))
            ax.text(i, max(cc, bc) + 0.075, "coverage gap", ha="center",
                    fontsize=8.6, weight="bold", color="#8c4a00")
        elif cls == "agree_allow" and name.startswith("B_severe"):
            ax.text(i, max(cc, bc) + 0.055,
                    "limitation:\nneither isolates", ha="center", fontsize=8.2,
                    style="italic", color="#555555")

    ax.set_xticks(x)
    ax.set_xticklabels([PAPER_LABEL[n] for n, *_ in rows], fontsize=9)
    ax.set_ylabel("Composite score")
    ax.set_ylim(0, 1.16)
    ax.set_title("Composite scores and decisions by scenario "
                 "(ISO = isolate, ALW = allow; solid fill = isolate)",
                 fontsize=11.5)
    ax.legend(handles=[
        plt.Rectangle((0, 0), 1, 1, fc=COORD_COLOR, label="Coordinated"),
        plt.Rectangle((0, 0), 1, 1, fc=BASE_COLOR,
                      label="Identity-centric baseline")],
        loc="upper right", fontsize=9.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    _save(fig, "figure5_scenario_outcomes")


if __name__ == "__main__":
    figure5()
    figure6()
    print(f"Figures 4 and 5 written to {OUT}")
