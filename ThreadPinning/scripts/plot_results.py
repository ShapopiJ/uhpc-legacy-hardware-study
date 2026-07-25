#!/usr/bin/env python3
"""Plot NUMA-locality and thread-pinning STREAM-Triad results.
Reads CSVs from ../results, writes PNG+PDF figures to ../figures.
Run locally: python3 plot_results.py
"""
import csv
import glob
import os
import statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
FIGURES = os.path.join(HERE, "..", "figures")
os.makedirs(FIGURES, exist_ok=True)

# validated categorical slots (see dataviz skill palette.md)
BLUE = "#2a78d6"
GREEN = "#008300"
RED = "#e34948"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- figure 1
def plot_numa_locality():
    path = sorted(glob.glob(os.path.join(RESULTS, "numa_locality_*.csv")))[-1]
    rows = load_csv(path)
    by_mode = defaultdict(list)
    for r in rows:
        by_mode[r["mode"]].append(float(r["bandwidth_GBps"]))

    modes = ["local", "remote"]
    means = [st.mean(by_mode[m]) for m in modes]
    stds = [st.stdev(by_mode[m]) for m in modes]
    colors = [BLUE, RED]
    labels = ["Local\n(CPU node 0, mem node 0)", "Remote\n(CPU node 0, mem node 1)"]

    fig, ax = plt.subplots(figsize=(5.0, 4.2))
    x = range(len(modes))
    bars = ax.bar(x, means, yerr=stds, capsize=5, color=colors, width=0.55,
                   edgecolor="none", zorder=3,
                   error_kw={"ecolor": MUTED, "elinewidth": 1.2})

    for xi, m, s in zip(x, means, stds):
        ax.text(xi, m + s + 0.35, f"{m:.1f} GB/s", ha="center", va="bottom",
                fontsize=10, color=INK, fontweight="bold")

    penalty = (means[0] - means[1]) / means[0] * 100
    # ax.text(0.5, 0.94, f"remote access costs {penalty:.0f}% bandwidth",
            #  transform=ax.transAxes, ha="center", va="top", fontsize=10,
            #  color=MUTED, style="italic")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("STREAM-Triad bandwidth (GB/s)")
    ax.set_ylim(0, max(means) * 1.25)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIGURES, f"numa_locality.{ext}"), dpi=200)
    plt.close(fig)
    print(f"wrote numa_locality.png/pdf  (n={len(rows)//2} reps/mode, source={os.path.basename(path)})")


# ---------------------------------------------------------------- figure 2
def plot_thread_pinning():
    sweep_path = sorted(glob.glob(os.path.join(RESULTS, "thread_pinning_2*.csv")))[-1]
    sa_path = sorted(glob.glob(os.path.join(RESULTS, "thread_pinning_socketaware_*.csv")))
    rows = load_csv(sweep_path)
    if sa_path:
        rows += load_csv(sa_path[-1])

    data = defaultdict(lambda: defaultdict(list))  # mode -> threads -> [bw]
    for r in rows:
        data[r["mode"]][int(r["threads"])].append(float(r["bandwidth_GBps"]))

    series = [
        ("unpinned", "Unpinned (PBS default)", BLUE, "o"),
        ("pinned", "Pinned, core-packed\n(OMP_PLACES=cores)", RED, "s"),
        ("pinned_socketaware", "Pinned, socket-aware\n(OMP_PLACES=sockets)", GREEN, "^"),
    ]

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    all_threads = sorted({t for m in data.values() for t in m})

    for key, label, color, marker in series:
        if key not in data:
            continue
        threads = sorted(data[key].keys())
        means = [st.mean(data[key][t]) for t in threads]
        stds = [st.stdev(data[key][t]) if len(data[key][t]) > 1 else 0 for t in threads]
        ax.errorbar(threads, means, yerr=stds, label=label, color=color,
                    marker=marker, markersize=6, linewidth=1.8, capsize=4,
                    zorder=3)

    ax.set_xscale("log", base=2)
    ax.set_xticks(all_threads)
    ax.set_xticklabels([str(t) for t in all_threads])
    ax.set_xlabel("OpenMP threads")
    ax.set_ylabel("STREAM-Triad bandwidth (GB/s)")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False, loc="lower right", fontsize=9)

    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIGURES, f"thread_pinning.{ext}"), dpi=200)
    plt.close(fig)
    print(f"wrote thread_pinning.png/pdf  (sources={os.path.basename(sweep_path)}"
          + (f", {os.path.basename(sa_path[-1])}" if sa_path else "") + ")")


if __name__ == "__main__":
    plot_numa_locality()
    plot_thread_pinning()
