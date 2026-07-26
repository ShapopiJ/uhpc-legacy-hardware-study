# BLAS tuning — ATLAS vs OpenBLAS HPL (Stampede rack)

Paired single-node HPL comparison isolating the effect of the BLAS library. Same node
(`SP1-00`), same problem (`N=58912`, `NB=224`), governor `performance`; **only the linked
BLAS library differs**.

## Result

| Library | Config | GFLOPS | % of peak | Solve time |
|---|---|---|---|---|
| System ATLAS (`/usr/lib64/atlas`) | 8 MPI ranks × 2 threads (threaded `libtatlas`) | 158.2 | 45.8 % | 862 s |
| OpenBLAS 0.3.26 (`TARGET=SANDYBRIDGE`) | 16 MPI ranks × 1 thread (sequential) | 294.9 | 85.3 % | 462 s |

**1.86× speed-up** from a zero-cost, reversible library change. Per-node theoretical peak
= 16 cores × 2.7 GHz × 8 DP FLOP/cycle (AVX) = **345.6 GFLOPS**; efficiency = GFLOPS / 345.6.
Raw HPL output in `results/atlas.out` and `results/openblas.out` (the `WR...` line, field 7,
is the GFLOPS figure).

## Reproduce

1. **Build** (on the manager node `uhpc` — the diskless compute nodes have no headers; the
   manager shares the Sandy-Bridge ISA family):

   ```bash
   bash scripts/build_openblas_hpl.sh      # OpenBLAS 0.3.26 + HPL 2.3, installs to ~/blas-study
   ```

   Key flags: `make TARGET=SANDYBRIDGE USE_OPENMP=0 USE_THREAD=0 NO_AFFINITY=1` (a sequential,
   Sandy-Bridge-tuned OpenBLAS), then HPL 2.3 linked against the static `libopenblas.a` with
   `-DHPL_CALL_CBLAS`, `mpicc`, `-O3 -funroll-loops -fopenmp`.

2. **Run** the paired benchmark (pins to `SP1-00`):

   ```bash
   cd ~/blas-study && qsub scripts/hpl_blas_compare.pbs
   ```

   ATLAS uses the facility's existing `xhpl.backup` (threaded `libtatlas`, 8 ranks × 2 threads);
   OpenBLAS uses the freshly-built sequential `xhpl` (16 single-threaded ranks). Both fill all
   16 cores — each library in its standard full-node configuration.

3. **Read**: `grep '^WR' results/atlas.out results/openblas.out | tail`.

`HPL.dat.template` is the shared HPL input (the runner writes per-library copies with the
appropriate P×Q grid: 2×4 for ATLAS's 8 ranks, 2×8 for OpenBLAS's 16 ranks).
