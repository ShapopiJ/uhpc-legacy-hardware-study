#!/bin/bash
# Autonomous Gammapy 2x2 repeat campaign (16 runs = 4 reps x 4 conditions),
# counterbalanced order. For each run: set the condition on sp0-00 via the
# passwordless helper, submit the real Gammapy PBS job, wait, record wall time.
# Launch once under nohup on the uhpc login node; runs ~22h unattended.
set -u
BENCH=/home/jshapopi/Projects/GammapyBench
STAMP=$(date +%Y%m%d_%H%M%S)
CAMP=$BENCH/campaign_$STAMP
mkdir -p "$CAMP"
LOG=$CAMP/campaign.log
SUMMARY=$CAMP/timing.csv
echo "run,round,condition,job_id,governor,rdma,bench_seconds,python_exit" > "$SUMMARY"

# 4 rounds, each a permutation of A B C D (counterbalances order & carryover)
ORDER=(A B C D  B D A C  C A D B  D C B A)

log(){ echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

log "campaign start: 16 runs, output $CAMP"
run=0
for idx in "${!ORDER[@]}"; do
  COND=${ORDER[$idx]}
  round=$(( idx/4 + 1 ))
  run=$((run+1))
  log "run $run/16 (round $round) condition $COND"

  # --- set condition on sp0-00 ---
  SET=$(ssh -o ConnectTimeout=15 sp0-00 "sudo -n /usr/local/sbin/gammapy_setcond $COND" 2>&1)
  log "  setcond: $SET"
  sleep 3

  # --- submit + wait ---
  JID=$(cd "$BENCH" && qsub -v COND=$COND gammapy_bench.pbs 2>>"$LOG")
  JID=${JID%%.*}
  if [ -z "$JID" ]; then log "  ERROR: qsub failed, skipping"; continue; fi
  log "  submitted job $JID; waiting..."
  while qstat "$JID" >/dev/null 2>&1; do sleep 60; done

  # --- collect timing from job output ---
  OUT=$(ls -t "$BENCH"/GPY_bench.o${JID}* 2>/dev/null | head -1)
  if [ -z "$OUT" ] || [ ! -f "$OUT" ]; then log "  ERROR: no output file for $JID"; continue; fi
  # epoch is the LAST field of the BENCH_START/END lines ("BENCH_START <iso> <epoch>")
  SECS=$(awk '/^BENCH_START/{s=$NF} /^BENCH_END/{e=$NF} END{ if(s&&e) printf "%.1f", e-s }' "$OUT")
  GOV=$(awk -F'[= ]' '/^governor=/{print $2; exit}' "$OUT")
  RDMA=$(awk -F'[= ]' '/rdma-ndd=/{for(i=1;i<=NF;i++) if($i ~ /rdma-ndd/){print $(i+1); exit}}' "$OUT")
  PYRC=$(awk -F'=' '/^python_exit=/{print $2; exit}' "$OUT")
  log "  DONE $COND: ${SECS}s (governor=$GOV rdma=$RDMA python_exit=$PYRC)"
  echo "$run,$round,$COND,$JID,$GOV,$RDMA,$SECS,$PYRC" >> "$SUMMARY"
done

log "campaign complete. Summary:"
cat "$SUMMARY" | tee -a "$LOG"
# quick governor-effect readout
awk -F, 'NR>1{g[$5]+=$7; n[$5]++} END{for(k in g) printf "  %s mean = %.1f s (n=%d)\n", k, g[k]/n[k], n[k]}' "$SUMMARY" | tee -a "$LOG"
