# Gammapy 2×2 repeat campaign — result

Replicated, counterbalanced campaign: **4 repeats × 4 conditions = 16 timed runs** in
randomised block order, on `sp0-00`, real Gammapy 1.3 ring-background analysis of 47 Tuc
(416 H.E.S.S. observations, warm page cache). Data: `results/campaign_timing.csv`; driver:
`scripts/gammapy_campaign.sh`; analysis: `scripts/gammapy_campaign_analyze.py`.

## Conditions

| Cond | governor | rdma-ndd |
|---|---|---|
| A | ondemand | active |
| B | ondemand | inactive |
| C | performance | active |
| D | performance | inactive |

## Result (bench seconds; all 16 runs `python_exit=0`, identical science)

| Group | n | mean ± SD (s) |
|---|---|---|
| **ondemand** (A+B) | 8 | 5094 ± 118 |
| **performance** (C+D) | 8 | 5019 ± 98 |

- **Governor effect:** performance faster by **75 s = 1.5 %**. Welch two-sample **t = 1.4**,
  **95 % CI [−0.8 %, +3.8 %]** — spans zero, so **not statistically significant**.
- **RDMA effect:** −0.7 %, t = 0.6 — null, consistent with the OS-jitter microbenchmark.
- Overall: mean 5057 s, SD 111 s (min 4924, max 5343).

## Interpretation

The single-run pilot (`results/timing_summary.csv`) suggested a 4.3 % governor effect;
replication shows that was inflated by run-to-run noise. On this mixed I/O-, memory- and
compute-bound pipeline the governor's throughput benefit is small and within measurement
noise. This does **not** contradict the OS-jitter result — the governor's large, unambiguous
effect is on run-to-run *variance* / tail latency of a tight floating-point loop (40–70×), not
on the mean throughput of a real, I/O-interleaved analysis.

## Reproduce

```bash
# one-time (root, on sp0-00): install the passwordless condition helper
ssh sp0-00 'sudo bash ~/Projects/GammapyBench/scripts/setup_gammapy_sudo.sh'
# launch the autonomous campaign (~22 h)
cd ~/Projects/GammapyBench
nohup bash scripts/gammapy_campaign.sh > ~/gammapy_campaign.driver.log 2>&1 &
# analyse
cd campaign_*/ && python3 gammapy_campaign_analyze.py
```

> Note: the driver's per-run timing parse originally read the wrong field of the
> `BENCH_START/END` markers (fixed here to `$NF`, the epoch). The published
> `campaign_timing.csv` was recovered directly from the per-job `GPY_bench.o*` outputs.
