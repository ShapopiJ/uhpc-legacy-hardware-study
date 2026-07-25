#!/usr/bin/env python3
"""Render the pre/post fixedwork jitter comparison charts.

Reads the 60-trial fixedwork CSVs from ../raw/ (relative to this file) and
writes two outputs into the OSJitter/ directory:

  jitter_impact.png        -- titled dashboard version (used in SUMMARY.md / Notion)
  jitter_impact_paper.pdf  -- untitled, larger-font vector version (used in Main.tex)

Requires: matplotlib (tested with 3.5.3). Run with:

    python3 plot_jitter.py
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec

SCRIPT_DIR = Path(__file__).resolve().parent
OSJITTER_DIR = SCRIPT_DIR.parent
RAW_DIR = OSJITTER_DIR / "raw"

NODES = ["sp0-00", "sp1-00"]

COLOR_PRE = "#2a78d6"   # categorical slot 1, blue -- pre-tuning
COLOR_POST = "#008300"  # categorical slot 2, green -- post-tuning


def load(node, phase):
    path = RAW_DIR / f"{node}_fixedwork_{phase}.csv"
    xs, ys = [], []
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            xs.append(int(row[0]))
            ys.append(int(row[1]) / 1e6)  # ns -> ms
    return xs, ys


def render(out_path, *, titled: bool):
    """Build the two-panel, broken-axis pre/post comparison figure.

    titled=True  -> in-figure title/subtitle, muted dashboard palette, PNG (docs/Notion).
    titled=False -> no in-figure text (caption carries it in the paper), pure
                    black/white ink, larger fonts sized for the paper's
                    \\textwidth, vector PDF (Main.tex).
    """
    if titled:
        surface, grid = "#fcfcfb", "#e1e0d9"
        ink_primary, ink_muted, baseline = "#0b0b0b", "#898781", "#c3c2b7"
        tick_fs, axlabel_fs, nodelabel_fs, legend_fs = 8.5, 9.5, 11.5, 9.5
        fig_w, fig_h = 11, 6.2
        top = 0.84
    else:
        surface, grid = "#ffffff", "#d8d8d3"
        ink_primary, ink_muted, baseline = "#000000", "#5a5a5a", "#6b6b6b"
        # Sized to match the paper's \textwidth (495pt ~ 6.85in) so no
        # further LaTeX scaling is needed -- these font sizes are chosen for
        # readability at that final printed size, not for on-screen viewing.
        tick_fs, axlabel_fs, nodelabel_fs, legend_fs = 11, 13, 15, 13
        fig_w, fig_h = 6.85, 4.6
        top = 0.80

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=surface)

    if titled:
        fig.suptitle(
            "Fixed single-core workload: 60 trials, pre- vs post-tuning",
            fontsize=13, color=ink_primary, fontweight="bold", x=0.02, ha="left",
        )
        fig.text(
            0.02, 0.93,
            "Stopping rdma-ndd + CPU governor ondemand → performance on sp0-00 / sp1-00",
            fontsize=9.5, color="#52514e", ha="left",
        )

    outer = gridspec.GridSpec(1, 2, figure=fig, left=0.11, right=0.99, top=top, bottom=0.13, wspace=0.10)

    for col, node in enumerate(NODES):
        inner = gridspec.GridSpecFromSubplotSpec(
            2, 1, subplot_spec=outer[col], height_ratios=[1, 3], hspace=0.06
        )
        ax_top = fig.add_subplot(inner[0])
        ax_bot = fig.add_subplot(inner[1], sharex=ax_top)

        xpre, ypre = load(node, "pre")
        xpost, ypost = load(node, "post")

        for ax in (ax_top, ax_bot):
            ax.set_facecolor(surface)
            ax.plot(xpre, ypre, color=COLOR_PRE, linewidth=1.5, linestyle="-",
                     marker="^", markersize=4.6, markevery=(1 if titled else 5),
                     label="Pre-tuning", zorder=3, clip_on=True)
            ax.plot(xpost, ypost, color=COLOR_POST, linewidth=1.5, linestyle="--",
                     marker="o", markersize=4.0, markevery=(1 if titled else 5),
                     label="Post-tuning", zorder=4, clip_on=True)
            ax.grid(True, axis="y", color=grid, linewidth=0.8, zorder=0)
            ax.grid(False, axis="x")
            ax.tick_params(axis="both", colors=ink_muted, labelsize=tick_fs, length=0)

        # top: full range (shows the outlier spike)
        top_max = max(max(ypre), max(ypost))
        ax_top.set_ylim(505, top_max * 1.01)
        ax_top.spines["bottom"].set_visible(False)
        ax_top.tick_params(labelbottom=False)
        ax_top.set_yticks([510, 520] if top_max > 515 else [510])
        for spine in ["top", "right", "left"]:
            ax_top.spines[spine].set_visible(False)

        # bottom: zoomed baseline detail
        ax_bot.set_ylim(457.4, 459.6)
        for spine in ["top", "right", "left"]:
            ax_bot.spines[spine].set_visible(False)
        ax_bot.spines["bottom"].set_color(baseline)
        ax_bot.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
        ax_bot.set_xlabel("Trial", fontsize=axlabel_fs, color=(ink_muted if titled else ink_primary))

        # break marks
        d = 0.010 if titled else 0.012
        kwargs = dict(transform=ax_top.transAxes, color=ink_muted, clip_on=False, linewidth=1)
        ax_top.plot((-d, +d), (-d * 3, +d * 3), **kwargs)
        kwargs.update(transform=ax_bot.transAxes)
        ax_bot.plot((-d, +d), (1 - d, 1 + d), **kwargs)

        ax_top.set_title(node, fontsize=nodelabel_fs, color=ink_primary, fontweight="bold", loc="left", pad=8)

        if col == 0:
            ax_bot.set_ylabel("Trial wall time (ms)", fontsize=axlabel_fs, color=(ink_muted if titled else ink_primary))
        else:
            ax_bot.tick_params(labelleft=True)

    handles = [
        plt.Line2D([0], [0], color=COLOR_PRE, marker="^", markersize=6, linewidth=1.5, linestyle="-", label="Pre-tuning"),
        plt.Line2D([0], [0], color=COLOR_POST, marker="o", markersize=5.5, linewidth=1.5, linestyle="--", label="Post-tuning"),
    ]
    if titled:
        fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.965),
                   frameon=False, fontsize=legend_fs, labelcolor=ink_primary, ncol=2,
                   handlelength=1.6, columnspacing=1.2)
        fig.savefig(out_path, dpi=200, facecolor=surface)
    else:
        fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.55, 0.99),
                   frameon=False, fontsize=legend_fs, labelcolor=ink_primary, ncol=2,
                   handlelength=2.2, columnspacing=1.5)
        fig.savefig(out_path, facecolor=surface)

    plt.close(fig)
    print("wrote", out_path)


if __name__ == "__main__":
    render(OSJITTER_DIR / "jitter_impact.png", titled=True)
    render(OSJITTER_DIR / "jitter_impact_paper.pdf", titled=False)
