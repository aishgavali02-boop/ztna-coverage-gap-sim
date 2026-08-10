"""
make_diagrams.py -- Figures 1, 2 and 3: the conceptual diagrams.

Figure 1  study overview: what is evaluated, how, and what is reported
Figure 2  the four architecture design principles
Figure 3  the four-layer architecture, control plane and data plane

Drawn programmatically so that they regenerate at any resolution and cannot
drift from the parameter values in hybrid_v4.py.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import hybrid_v4 as hv

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
os.makedirs(OUT, exist_ok=True)

NAVY = "#1f3864"; BLUE = "#dce6f5"; GREEN = "#375623"; LGREEN = "#dcecdc"
PURPLE = "#5b3a8e"; LPURPLE = "#e6dcf0"; AMBER = "#bf8f00"; LAMBER = "#fdf0dc"
RED = "#c00000"; LRED = "#f7dede"; GREY = "#666666"; LGREY = "#eeeeee"


def box(ax, x, y, w, h, title, body="", fc="#ffffff", ec=NAVY,
        tc=NAVY, ts=11, bs=8.8, bold=True, bc="#333333"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.5,rounding_size=1.0",
                                fc=fc, ec=ec, lw=1.4))
    if body:
        ax.text(x + w/2, y + h*0.66, title, ha="center", va="center",
                fontsize=ts, color=tc, weight="bold" if bold else "normal")
        ax.text(x + w/2, y + h*0.30, body, ha="center", va="center",
                fontsize=bs, color=bc)
    else:
        ax.text(x + w/2, y + h/2, title, ha="center", va="center",
                fontsize=ts, color=tc, weight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2, color=GREY, ls="-", lw=1.4):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), color=color,
                                 arrowstyle="-|>", mutation_scale=14,
                                 lw=lw, linestyle=ls, shrinkA=3, shrinkB=3))


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=600,
                    bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ------------------------------------------------------------------ FIGURE 1
def figure1():
    fig, ax = plt.subplots(figsize=(13, 7.2))
    ax.set_xlim(0, 130); ax.set_ylim(0, 72); ax.axis("off")

    ax.text(65, 69, "Layered Zero Trust architecture: what is evaluated and what is reported",
            ha="center", fontsize=13, weight="bold", color=NAVY)

    # inputs
    box(ax, 2, 50, 26, 8, "Layer 1  Identity", "authentication, origin,\ncredentials, role",
        fc=BLUE, ec=NAVY, ts=10)
    box(ax, 2, 39, 26, 8, "Layer 2  Device", "hardware root of trust, agent,\nposture, patch level",
        fc=LGREEN, ec=GREEN, tc=GREEN, ts=10)
    box(ax, 2, 28, 26, 8, "Layer 3  Network", "east–west flow, conformity,\negress, zone",
        fc=LPURPLE, ec=PURPLE, tc=PURPLE, ts=10)
    ax.text(15, 24.5, "each scored in [0,1] from named sub-signals",
            ha="center", fontsize=8.5, style="italic", color=GREY)

    # PDP
    box(ax, 34, 32, 24, 23,
        "Layer 4\nPolicy Decision Point",
        f"composite score vs τ = {hv.TAU:.2f}\nper-layer floor at {hv.FLOOR:.2f}",
        fc=NAVY, ec=NAVY, tc="white", ts=11, bs=8.8, bc="#e8eef8")
    for y in (54, 43, 32):
        arrow(ax, 28, y, 34, 43.5)

    # two configurations
    box(ax, 64, 44, 28, 10, "Coordinated",
        "layers weighted equally;\nany layer may deny alone", fc="#ffffff", ec=NAVY, ts=10.5)
    box(ax, 64, 31, 28, 10, "Identity-centric",
        "identity weighted 0.70;\nonly identity may deny", fc="#ffffff", ec=RED, tc=RED, ts=10.5)
    arrow(ax, 58, 46, 64, 49); arrow(ax, 58, 41, 64, 36)
    ax.text(78, 57.5, "same decision mechanism, identical inputs",
            ha="center", fontsize=9, style="italic", color=GREY)

    # evaluation
    box(ax, 98, 44, 30, 10, "Seven scenarios",
        "healthy control, session hijack,\nposture drift ×2, supply chain,\nIIoT lateral, identity compromise",
        fc=LAMBER, ec=AMBER, tc=AMBER, ts=10.5, bs=8)
    box(ax, 98, 31, 30, 10, "Sensitivity analysis",
        "246 single-state and\n50 time-series configurations", fc=LAMBER, ec=AMBER,
        tc=AMBER, ts=10.5, bs=8)
    arrow(ax, 92, 49, 98, 49); arrow(ax, 92, 36, 98, 36)

    # findings
    box(ax, 36, 4, 58, 17, "Reported outcome",
        "three coverage gaps — coordinated isolates, identity-centric allows,\n"
        "each confined to device or network state\n\n"
        "bounded: identity-only compromise favours the identity-centric\n"
        "configuration; compromise confined to soft device signals\n"
        "is caught by neither",
        fc=LGREY, ec=NAVY, ts=11, bs=8.6)
    arrow(ax, 78, 31, 72, 21); arrow(ax, 108, 31, 94, 18)

    box(ax, 98, 6, 30, 11, "Compliance mapping",
        "ISO/IEC 27001:2022\nand TISAX objectives", fc="#ffffff", ec=GREEN,
        tc=GREEN, ts=10.5, bs=8.6)

    box(ax, 2, 5, 30, 15, "Released artefacts",
        "all parameters disclosed\nand swept; source code\nreproduces every result", fc="#ffffff",
        ec=GREY, tc="#333333", ts=10.5, bs=8.6)
    arrow(ax, 36, 12.5, 32, 12.5)
    save(fig, "figure1_study_overview")


# ------------------------------------------------------------------ FIGURE 2
def figure2():
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 110); ax.set_ylim(0, 62); ax.axis("off")
    ax.text(55, 58.5, "Architecture Design Principles", ha="center",
            fontsize=15, weight="bold", color=NAVY)

    box(ax, 40, 24, 30, 14, "Proposed\nZero Trust\nFramework", "", fc=BLUE, ec=NAVY, ts=13)

    box(ax, 2, 42, 34, 11, "1.  Least Privilege Access",
        "context-aware, minimal\nresource authorization", ec=NAVY, ts=10.5)
    box(ax, 74, 42, 34, 11, "2.  Continuous Verification",
        "ongoing authentication and\ntelemetry-based reassessment", ec=NAVY, ts=10.5)
    box(ax, 2, 8, 34, 11, "3.  Multi-Layer Enforcement",
        "identity, endpoint, and\nnetwork controls in parallel", ec=NAVY, ts=10.5)
    box(ax, 74, 8, 34, 11, "4.  Centralized Policy Control",
        "unified control plane and\ndistributed enforcement points", ec=NAVY, ts=10.5)

    arrow(ax, 36, 47, 48, 38, color=NAVY)
    arrow(ax, 74, 47, 62, 38, color=NAVY)
    arrow(ax, 36, 14, 48, 24, color=NAVY)
    arrow(ax, 74, 14, 62, 24, color=NAVY)
    save(fig, "figure2_design_principles")


# ------------------------------------------------------------------ FIGURE 3
def figure3():
    fig, ax = plt.subplots(figsize=(8.6, 11))
    ax.set_xlim(0, 86); ax.set_ylim(0, 110); ax.axis("off")

    box(ax, 8, 96, 70, 9, "CONTROL PLANE", "", fc=BLUE, ec=NAVY, ts=13)

    box(ax, 8, 76, 70, 15, "LAYER 4   Policy Orchestration Layer",
        "Centralized Policy Decision Point (PDP)\n"
        "evaluates identity, device and network state and\n"
        "issues a single access decision to the data plane",
        fc=LPURPLE, ec=PURPLE, tc=PURPLE, ts=11, bs=8.8)

    box(ax, 8, 58, 70, 13, "DATA PLANE",
        "Distributed Policy Enforcement Points (PEPs)\n"
        "apply the decision at each tier",
        fc=LGREEN, ec=GREEN, tc=GREEN, ts=12, bs=8.8)

    box(ax, 8, 38, 21, 15, "LAYER 1", "Identity and\nAccess Context\n(ZTNA)",
        fc=BLUE, ec=NAVY, ts=10, bs=8.6)
    box(ax, 32.5, 38, 21, 15, "LAYER 2", "Device Trust\n(NAC)",
        fc=LGREEN, ec=GREEN, tc=GREEN, ts=10, bs=8.6)
    box(ax, 57, 38, 21, 15, "LAYER 3", "Network\nSegmentation\n(microsegments)",
        fc=LAMBER, ec=AMBER, tc=AMBER, ts=10, bs=8.6)

    box(ax, 8, 20, 70, 11, "Continuous Monitoring and Re-evaluation",
        "telemetry from every layer returns to the PDP;\n"
        "the decision is recomputed at each evaluation point",
        fc=LAMBER, ec=AMBER, tc=AMBER, ts=11, bs=8.8)

    arrow(ax, 43, 96, 43, 91, color=NAVY)
    arrow(ax, 43, 76, 43, 71, color=PURPLE)
    for x in (18.5, 43, 67.5):
        arrow(ax, x, 58, x, 53, color=GREEN)
        arrow(ax, x, 38, x, 31, color=GREY, ls=":")
    ax.add_patch(FancyArrowPatch((78, 25.5), (82, 25.5), color=GREY,
                                 arrowstyle="-", lw=1.3))
    ax.add_patch(FancyArrowPatch((82, 25.5), (82, 100.5), color=GREY,
                                 arrowstyle="-", lw=1.3))
    arrow(ax, 82, 100.5, 78, 100.5, color=GREY)
    ax.text(84.5, 63, "feedback loop", rotation=90, ha="center", va="center",
            fontsize=8.5, style="italic", color=GREY)
    save(fig, "figure3_architecture")


if __name__ == "__main__":
    figure1(); figure2(); figure3()
    print(f"Figures 1, 2 and 3 written to {OUT}")
