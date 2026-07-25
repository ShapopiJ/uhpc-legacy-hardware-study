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
  and figures.
- **`ProductionWorkload/`** — the real H.E.S.S. Cen A gamma-ray analysis pipeline (Paris
  Analysis / ROOT, run in Singularity) job scripts, including `bench_slice0_timed.pbs`, a
  non-destructive timed variant used to benchmark the same production analysis under different
  tuning conditions without touching the live results directory.

## License

The vendored `OSJitter/src/osjitter-upstream/` sources retain their original GPLv3+ license
(see `LICENSE` in that directory). Everything else in this repository (the paper-specific
benchmark code, job scripts, and raw results) may be reused for research/reproducibility
purposes with attribution to the paper above.
