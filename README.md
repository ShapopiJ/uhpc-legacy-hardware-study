# UHPC legacy hardware study — data and code

Supporting data, benchmark source, PBS job scripts, and raw results for the paper
"Maintaining a Productive HPC Cluster on Legacy Hardware: A Case Study in Sustainable
Computing under Constraints" (Shapopi & Backes), covering UHPC, the University of Namibia's
HPC cluster built from repurposed *Ranger* and *Stampede* hardware.

## Contents

- **`OSJitter/`** — OS-jitter measurement (`osjitter`, a vendored copy of
  [gsauthof/osjitter](https://github.com/gsauthof/osjitter), and `fixedwork.c`, a companion
  fixed-FLOP microbenchmark written for this study) and its raw results. Covers both the
  original RDMA-daemon/governor tuning result and the follow-up experiment that isolates the
  two interventions from each other (`RUNBOOK_isolation.md`, `raw/*_condB*`, `raw/*_condC*`).
- **`ThreadPinning/`** — the OpenMP STREAM-Triad benchmark (`stream_triad.c`) and PBS job
  scripts used for the NUMA-locality and thread-pinning-policy results, plus raw CSV results
  and figures. The sweep expressed in the standard OpenMP-4 affinity vocabulary
  (`OMP_PROC_BIND=false`/`close`/`spread`) is in `scripts/job_pinning_spread_close.pbs`, with
  raw data `results/pinning_spread_close_*.csv` and the regenerated `figures/thread_pinning.*`.
- **`GammapyBench/`** — the production-workload benchmark used in the paper: a Gammapy 1.3
  ring-background analysis of 47 Tucanae (416 H.E.S.S. observations, local FITS data only). The
  PBS runner (`scripts/gammapy_bench.pbs`) preloads the dataset into the page cache before the
  timed section so each governor/RDMA condition is measured warm, removing the cold-cache
  confound. `results/` holds the four per-condition job logs and `timing_summary.csv`. The
  repeated, counterbalanced 2×2 campaign (4 reps × 4 conditions) that places a confidence
  interval on the governor effect is driven by `scripts/gammapy_campaign.sh` (with the
  privileged one-time helper `scripts/setup_gammapy_sudo.sh`); its `campaign_*/timing.csv` is
  added once the run completes.
- **`BlasTuning/`** — the ATLAS-vs-OpenBLAS HPL comparison on the *Stampede* rack (the study's
  headline result: 45.8 % → 85.3 % of peak, 1.86×, from a library swap alone). Build script,
  PBS runner, raw HPL output, and `SUMMARY.md` with the full reproduction recipe.
- **`RangerHPL/`** — raw per-node HPL throughput behind the rack-level efficiency figures: the
  24 operational *Ranger* nodes (mean 82.4 GFLOPS, 64.4 % of peak) and the 38 *Stampede* nodes
  (≈149.2 GFLOPS, 43.2 % of peak under system ATLAS). See `RangerHPL/README.md`.
- **`PbsAccounting/`** — anonymised PBS usage extract (`pbs_usage_extract.sh`) and its output
  (`per_year.csv`, `overall.csv`): 42 distinct users over 2019–2026, thousands of jobs/year,
  substantiating the cluster's sustained productivity. Counts only — no usernames or commands.

## License

The vendored `OSJitter/src/osjitter-upstream/` sources retain their original GPLv3+ license
(see `LICENSE` in that directory). Everything else in this repository (the paper-specific
benchmark code, job scripts, and raw results) may be reused for research/reproducibility
purposes with attribution to the paper above.
