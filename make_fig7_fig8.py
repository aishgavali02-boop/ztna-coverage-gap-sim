"""
make_fig7_fig8.py -- Figure 7 (floor sweep) and Figure 8 (baseline
identity-weight sweep).

Both figures are drawn from results_sweep.csv, which make_artifacts.py writes.
Classification uses hybrid_v4.classify_pair(), which is DIRECTIONAL: a coverage
gap requires the coordinated configuration to isolate while the identity-centric
baseline allows. The opposite case is shown separately as a reverse gap; it
occurs for Scenario E at floor values below 0.30, where the coordinated
composite (0.705) is above tau and the identity score no longer breaches so low
a floor, while the baseline composite (0.460) is below tau.
"""
import os
import csv
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory
import numpy as np

import hybrid_v4 as hv
from paper_labels import SCEN_ORDER, FLAT_LABEL, CAT_COLOR, CAT_LABEL

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "artifacts")
os.makedirs(OUT, exist_ok=True)

CAT_ORDER = ["COVERAGE_GAP", "REVERSE_GAP", "both_isolate", "agree_allow"]


def load(sweep_name):
    path = os.path.join(OUT, "results_sweep.csv")
    if not os.path.exists(path):
        raise SystemExit("results_sweep.csv not found. Run make_artifacts.py first.")
    data = defaultdict(dict)
    with open(path) as f:
        for r in csv.DictReader(f):
            if r["sweep"] == sweep_name:
                data[r["scenario"]][float(r["knob_value"])] = r["result"]
    return data


def band_figure(sweep_name, xlabel, operating_point, title, fname):
    data = load(sweep_name)
    scens = [s for s in SCEN_ORDER if s in data]
    knobs = sorted(next(iter(data.values())).keys())
    step = (knobs[1] - knobs[0]) if len(knobs) > 1 else 0.05

    fig, ax = plt.subplots(figsize=(11, 6.2))
    for row, s in enumerate(scens):
        for k in knobs:
            cat = data[s][k]
            ax.barh(row, step, left=k - step / 2,
                    color=CAT_COLOR.get(cat, "#ffffff"),
                    edgecolor="none", height=0.86)
        ax.barh(row, knobs[-1] - knobs[0] + step, left=knobs[0] - step / 2,
                color="none", edgecolor="#666666", lw=0.7, height=0.86)

    ax.axvline(operating_point, ls="--", lw=1.6, color="#c00000")
    # Anchor the label in axes coordinates vertically and data coordinates
    # horizontally, so it sits clear above the plot whatever the y-axis
    # direction or the number of scenario rows.
    trans = blended_transform_factory(ax.transData, ax.transAxes)
    ax.text(operating_point, 1.015, f"operating point ({operating_point:g})",
            transform=trans, color="#c00000", fontsize=9.5,
            ha="center", va="bottom", weight="bold")

    ax.set_yticks(range(len(scens)))
    ax.set_yticklabels([FLAT_LABEL[s] for s in scens], fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_xlim(knobs[0] - step / 2, knobs[-1] + step / 2)
    ax.set_xticks(knobs)
    ax.set_xticklabels([f"{k:g}" for k in knobs], fontsize=8.5)
    ax.set_title(title, fontsize=11.5, pad=26)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    present = [c for c in CAT_ORDER
               if any(c in data[s].values() for s in scens)]
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, fc=CAT_COLOR[c],
                                     ec="#666666", lw=0.7, label=CAT_LABEL[c])
                       for c in present],
              loc="upper center", bbox_to_anchor=(0.5, -0.13),
              ncol=len(present), frameon=False, fontsize=9.5)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{fname}.{ext}"), dpi=600,
                    bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    band_figure("floor", "Floor value", hv.FLOOR,
                "Decision outcome by scenario across floor values",
                "figure7_floor_sweep")
    band_figure("identity_weight", "Baseline identity weight", 0.70,
                "Decision outcome by scenario across baseline identity weights",
                "figure8_identity_weight_sweep")
    print(f"Figures 7 and 8 written to {OUT}")
