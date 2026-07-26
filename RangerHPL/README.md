# Per-node HPL data (rack-level figures)

Raw per-node LINPACK/HPL throughput underlying the rack efficiency numbers in the paper.
Each value is a single-node HPL run (`N=58912`, `NB=224`, 2×8 = 16 MPI ranks/node).

## `ranger_pernode_hpl.dat` — Ranger rack (AMD Opteron 8356)

The **24 operational** Ranger nodes (`CN0-00…CN0-11`, `CN1-00…CN1-11`). The rack has 48
physical blade slots but only these 24 are commissioned; this is the data behind the paper's
corrected 24-node rack figures.

- mean = **82.43 GFLOPS**, sample SD = **1.13** (n = 24)
- per-node peak = 16 cores × 2.0 GHz × 4 DP FLOP/cycle = **128 GFLOPS** → efficiency **64.4 %**
- aggregate over 24 nodes = **1.978 TFLOPS** against a 3.07 TFLOPS partition peak (embarrassingly-parallel sum, not a coupled run)

Reproduce the statistics:

```bash
awk 'NR>1{n++; s+=$2; a[n]=$2} END{m=s/n; for(i=1;i<=n;i++) ss+=(a[i]-m)^2;
  printf "n=%d mean=%.3f SD=%.3f eff=%.2f%%\n", n, m, sqrt(ss/(n-1)), 100*m/128}' ranger_pernode_hpl.dat
```

## `stampede_pernode_hpl.dat` — Stampede rack (Intel Xeon E5-2680)

38 Stampede nodes benchmarked with the **system ATLAS** BLAS: mostly ~150.7 GFLOPS with three
low outliers at ~133 GFLOPS; fleet mean ≈ 149.2 GFLOPS = **43.2 %** of the 345.6 GFLOPS peak.
This low ATLAS efficiency is the motivation for the OpenBLAS comparison in `../BlasTuning/`
(which lifts the same node to 85.3 % of peak).

Source directories on the cluster: `…/hpl-2.1/bin/Linux_PII_CBLAS_gm.backup` (Ranger) and
`…/Linux_PII_CBLAS_gm2` (Stampede).
