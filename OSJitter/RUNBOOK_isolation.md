# Runbook: isolating the RDMA-daemon vs. governor confound

Reproduces the Section 3.5 (`sec:jitter-isolation`) experiment: same `osjitter -t 60` and
`fixedwork <cpu> 60` measurements as the original test in `SUMMARY.md`, on the same two nodes
(`sp0-00`, `sp1-00`), but with the two interventions toggled independently instead of together.

Current live state (confirmed 2026-07-24): both nodes are governor=`performance`,
`rdma-ndd`=inactive — i.e. Condition D (both tuned). Condition A (both untuned) is already
recorded in `raw/*_baseline.txt` / `raw/*_fixedwork_pre.csv`. **Only Conditions B and C are new.**

Both nodes are currently idle and unallocated in PBS (checked 2026-07-24 18:20 SAST) — safe to run now.

## What you need to do (requires root on sp0-00 and sp1-00)

Run each block below, then tell me you've done it — I'll immediately run the measurement
commands over SSH as `jshapopi` (no root needed for the measurement itself) and save the results.

### Step 1 — Condition B: RDMA stopped, governor back to `ondemand`

On **both** sp0-00 and sp1-00 as root:
```sh
# rdma-ndd is already stopped from the original tuning; only the governor needs to change
for c in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo ondemand > "$c"; done
systemctl status rdma-ndd --no-pager   # confirm still inactive
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor   # confirm "ondemand"
```
Tell me when done — I'll run:
```sh
ssh sp0-00 '~/osjitter-build/osjitter -t 60' > raw/sp0-00_condB.txt
ssh sp0-00 '~/osjitter-build/fixedwork 0 60' > raw/sp0-00_fixedwork_condB.csv
ssh sp1-00 '~/osjitter-build/osjitter -t 60' > raw/sp1-00_condB.txt
ssh sp1-00 '~/osjitter-build/fixedwork 0 60' > raw/sp1-00_fixedwork_condB.csv
```

### Step 2 — Condition C: governor back to `performance`, RDMA daemon started

On **both** nodes as root:
```sh
for c in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > "$c"; done
systemctl start rdma-ndd
systemctl status rdma-ndd --no-pager   # confirm active
```
Tell me when done — I'll run the same four commands as Step 1 with `_condC` in place of `_condB`.

### Step 3 — restore the real tuned state (Condition D, i.e. put the cluster back the way it was)

On **both** nodes as root:
```sh
systemctl stop rdma-ndd
for c in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > "$c"; done
systemctl status rdma-ndd --no-pager
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```
This returns the nodes to their current production configuration. **Do not skip this step** —
Conditions B and C are deliberately worse than the cluster's normal tuned state and should not
be left in place.

## After both conditions are collected

I'll extend `src/plot_jitter.py` to plot all four conditions (or add a small results table if a
4-way version of Figure `fig:jitter-impact` gets too busy) and fill in the
"[Results for B and C: pending...]" placeholder in Section 3.5 of `Main.tex` with the actual
involuntary-context-switch and fixedwork-stddev numbers, attributing the improvement between the
two interventions.
