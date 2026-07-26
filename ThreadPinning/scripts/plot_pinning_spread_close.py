#!/usr/bin/env python3
"""Regenerate thread_pinning figure with the standard OMP_PROC_BIND close/spread
sweep (unpinned / close / spread). Writes images/thread_pinning.{pdf,png}."""
import csv, glob, os, statistics as st
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/Users/jshapopi/Library/CloudStorage/OneDrive-Unam/Projects/cluster/OldEquipmentPaper"
RESULTS = os.path.join(ROOT, "ThreadPinning", "results")
IMAGES = os.path.join(ROOT, "images")

BLUE="#2a78d6"; GREEN="#008300"; RED="#e34948"; INK="#0b0b0b"; MUTED="#898781"; GRID="#e1e0d9"
plt.rcParams.update({"font.family":"sans-serif","font.size":11,"axes.edgecolor":MUTED,
    "axes.labelcolor":INK,"text.color":INK,"xtick.color":INK,"ytick.color":INK,
    "axes.grid":True,"grid.color":GRID,"grid.linewidth":0.8,"axes.axisbelow":True,
    "figure.facecolor":"white","axes.facecolor":"white"})

path = sorted(glob.glob(os.path.join(RESULTS, "pinning_spread_close_*.csv")))[-1]
rows = list(csv.DictReader(open(path)))
data = defaultdict(lambda: defaultdict(list))
for r in rows:
    data[r["mode"]][int(r["threads"])].append(float(r["bandwidth_GBps"]))

series = [
    ("unpinned", "Unpinned (OMP_PROC_BIND=false)", BLUE, "o"),
    ("close",    "close (OMP_PROC_BIND=close)",    RED,  "s"),
    ("spread",   "spread (OMP_PROC_BIND=spread)",  GREEN,"^"),
]
fig, ax = plt.subplots(figsize=(6.4, 4.6))
all_threads = sorted({t for m in data.values() for t in m})
for key,label,color,marker in series:
    threads = sorted(data[key].keys())
    means=[st.mean(data[key][t]) for t in threads]
    stds=[st.stdev(data[key][t]) if len(data[key][t])>1 else 0 for t in threads]
    ax.errorbar(threads, means, yerr=stds, label=label, color=color,
                marker=marker, markersize=6, linewidth=1.8, capsize=4, zorder=3)
ax.set_xscale("log", base=2)
ax.set_xticks(all_threads); ax.set_xticklabels([str(t) for t in all_threads])
ax.set_xlabel("OpenMP threads"); ax.set_ylabel("STREAM-Triad bandwidth (GB/s)")
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.legend(frameon=False, loc="lower right", fontsize=9)
fig.tight_layout()
for ext in ("pdf","png"):
    fig.savefig(os.path.join(IMAGES, f"thread_pinning.{ext}"), dpi=200)
print("wrote images/thread_pinning.pdf/png from", os.path.basename(path))
