/*
 * fixedwork.c
 * ===========
 *
 * PURPOSE
 * -------
 * osjitter (see ../osjitter-upstream/osjitter.c) measures OS jitter directly:
 * it busy-polls the CPU's Time Stamp Counter (TSC) and reports raw counts and
 * durations of "interruptions" -- moments where something else (an
 * interrupt, a context switch, a scheduler event) stole CPU time away from
 * the polling loop. That is a hardware/kernel-level view of jitter.
 *
 * What it does NOT tell you is how that jitter affects something you
 * actually care about: a real, fixed piece of computation. Two systems could
 * report similar osjitter numbers but differ in how much those interruptions
 * actually perturb an application's wall-clock time, depending on where in
 * the instruction stream the interruptions land and how the CPU's frequency
 * scaling reacts.
 *
 * fixedwork.c closes that gap. It runs an EXACT, KNOWN amount of floating-
 * point work (a fixed iteration count of a simple kernel -- so we know
 * precisely how many FLOPs it performs), repeats that same fixed workload
 * many times back-to-back, and times each repetition ("trial") separately.
 * If the underlying system were perfectly jitter-free, every trial would
 * take identically the same wall-clock time (modulo microarchitectural
 * noise like cache warm-up on the very first trial). Any variation between
 * trials is real evidence of jitter reaching the application level -- and
 * because we know the FLOP count per trial, we can convert that variation
 * directly into "FLOPs of work the node failed to get done" (see
 * ../SUMMARY.md, "Contextualizing the impact").
 *
 * This file is original code written for this experiment. It is NOT part of
 * the upstream osjitter project (osjitter-upstream/) -- it is a companion
 * benchmark, used alongside osjitter, not instead of it.
 *
 * USAGE
 * -----
 *   ./fixedwork [cpu] [trials]
 *
 *   cpu     -- which logical CPU core to pin this process to (default: 0).
 *              Should match (or be a representative sample of) the cores
 *              osjitter was run against, so the two tools describe the same
 *              hardware under the same conditions.
 *   trials  -- how many repetitions of the fixed workload to run and time
 *              (default: 100; the jitter experiment used 60 to roughly
 *              match osjitter's own 60-second measurement window).
 *
 * OUTPUT
 * ------
 * A CSV to stdout with one row per trial: `trial,ns` (trial index, wall
 * time of that trial in nanoseconds). This is the exact format
 * ../src/plot_jitter.py expects to find in ../raw/<node>_fixedwork_<phase>.csv.
 * A diagnostic line (see SINK, below) is printed to stderr and is not part
 * of the CSV.
 */

/* _GNU_SOURCE must be defined before any system headers are included. It
 * unlocks glibc's non-POSIX extensions -- specifically here, the
 * cpu_set_t type and the CPU_ZERO/CPU_SET macros used below for pinning
 * this process to one core. Without it, sched.h would only expose the
 * portable POSIX subset, which does not include CPU affinity control. */
#define _GNU_SOURCE
#include <sched.h>      /* cpu_set_t, CPU_ZERO, CPU_SET, sched_setaffinity */
#include <stdio.h>      /* printf, fprintf, perror */
#include <stdlib.h>     /* atoi */
#include <stdint.h>     /* uint64_t -- a fixed-width integer for the nanosecond timestamps */
#include <time.h>       /* clock_gettime, struct timespec, CLOCK_MONOTONIC */
#include <unistd.h>     /* pulled in for POSIX declarations used transitively by sched.h */

/* Number of loop iterations in the fixed workload. This is the "known
 * quantity" the whole experiment is built on: kernel() below performs
 * exactly 2 floating-point operations per iteration (one multiply, one
 * add), so each call to kernel() does EXACTLY
 *
 *     ITERS * 2 = 200,000,000 * 2 = 4x10^8 FLOPs
 *
 * every single time, regardless of how long it takes. That fixed FLOP
 * count is what lets us convert "trial took longer than usual" into
 * "the node effectively achieved fewer FLOPs/second during that trial" in
 * SUMMARY.md. The specific value (2x10^8 iterations) was chosen so a
 * single trial takes roughly ~450ms on the target Xeon E5-2680 cores --
 * long enough that a single OS-tick's worth of jitter (~1ms, see the
 * paper's discussion of the kernel's HZ=1000 timer) is a small, measurable
 * fraction of the trial, but short enough that 60 back-to-back trials
 * finish in about half a minute.
 */
#define ITERS 200000000UL

/* kernel() is the fixed unit of work that gets timed.
 *
 * Why this specific computation and not, say, a matrix multiply or a
 * library FLOPS benchmark:
 *
 *   1. SERIAL DATA DEPENDENCY: each iteration's result (x) feeds directly
 *      into the next iteration's computation. The compiler cannot
 *      reorder, parallelize, or vectorize these multiply-adds across
 *      iterations (there is nothing independent to vectorize -- iteration
 *      i+1 literally cannot start its multiply until iteration i's add has
 *      produced a value). This makes the per-iteration cost of the loop
 *      very stable and reproducible: any variation we observe in the
 *      timing is overwhelmingly likely to be caused by external
 *      interruptions (the thing we're trying to measure), not by the
 *      compiler/CPU choosing a different execution strategy from run to
 *      run.
 *
 *   2. FIXED, COUNTABLE FLOP COST: exactly one floating-point multiply
 *      (`x * 1.0000000001`) and one floating-point add (`+ 1e-12`) happen
 *      per loop iteration -- no branches, no data-dependent control flow,
 *      nothing that could make the iteration count vs. FLOP count
 *      relationship fuzzy.
 *
 *   3. THE MULTIPLIER IS DELIBERATELY CLOSE TO 1.0 (and the addend close
 *      to 0.0): this keeps x from overflowing to infinity or decaying to
 *      zero over 2x10^8 iterations, so the loop keeps doing genuine,
 *      well-defined floating-point work for its entire duration instead
 *      of degenerating into operations on inf/nan/subnormal values partway
 *      through (which can have different -- and inconsistent -- CPU
 *      timing characteristics).
 *
 * The `static` keyword just gives this function internal linkage (it's
 * only called from within this translation unit); it has no bearing on
 * the timing methodology.
 */
static double kernel(double x) {
    for (unsigned long i = 0; i < ITERS; ++i) {
        x = x * 1.0000000001 + 1e-12;
    }
    return x;
}

/* now_ns() returns the current time as a single 64-bit nanosecond count.
 *
 * CLOCK_MONOTONIC (rather than CLOCK_REALTIME) is used deliberately: it is
 * guaranteed by POSIX to never jump backwards or be adjusted by NTP
 * time-sync corrections. A wall-clock (CLOCK_REALTIME) reading could, in
 * principle, jump during a trial due to an NTP correction landing at just
 * the wrong moment, which would corrupt a timing measurement and could
 * even show up as a fake "jitter" event that had nothing to do with the
 * OS-noise sources this experiment is actually studying. CLOCK_MONOTONIC
 * sidesteps that entirely -- it only ever moves forward, at a steady rate,
 * driven by the same underlying timer hardware/TSC that osjitter itself
 * relies on.
 *
 * struct timespec gives seconds and nanoseconds separately; the two are
 * combined here into one uint64_t nanosecond count purely because it is
 * simpler to do arithmetic (end - start) on a single integer than on two
 * separate struct fields.
 */
static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int main(int argc, char **argv) {
    /* Defaults: pin to core 0, run 100 trials. Both are overridable from
     * the command line (see the USAGE block at the top of this file) so
     * the same binary can be pointed at whichever core/trial-count a given
     * measurement run needs, without recompiling. */
    int cpu = 0;
    int trials = 100;
    if (argc > 1) cpu = atoi(argv[1]);
    if (argc > 2) trials = atoi(argv[2]);

    /* Pin this process to a single logical CPU core for the entire run.
     *
     * This matters for two reasons:
     *
     *   1. It makes the measurement directly comparable to osjitter, which
     *      also measures jitter on a per-core basis (one polling thread
     *      pinned per core) -- we want fixedwork's per-trial timing on a
     *      given core to be describing the SAME core osjitter reported
     *      jitter statistics for.
     *
     *   2. Without pinning, the Linux scheduler could migrate this process
     *      between cores mid-run. A migration itself costs time (cache and
     *      TLB reload on the new core) and would show up in our
     *      measurements as "jitter" that is really just scheduler-induced
     *      migration overhead, conflating two different effects we want to
     *      keep separate.
     *
     * cpu_set_t is a bitmask type representing a set of CPU cores.
     * CPU_ZERO clears it (starts from "no cores selected"), CPU_SET(cpu,
     * &set) turns on the bit for the one core we want, and
     * sched_setaffinity(0, ...) applies that mask to the CURRENT process
     * (the first argument, pid=0, means "this process" rather than some
     * other process by PID). If the kernel refuses (e.g. an invalid core
     * number), we fail loudly and exit rather than silently measuring the
     * wrong core.
     */
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);
    if (sched_setaffinity(0, sizeof(set), &set) != 0) {
        perror("sched_setaffinity");
        return 1;
    }

    /* sink accumulates kernel()'s return value across trials, and is
     * declared `volatile` for one specific reason: to stop the compiler's
     * optimizer from proving that the entire kernel() computation is
     * "dead code" (a value that is computed but never used for anything
     * observable) and deleting the loop entirely. `volatile` forces the
     * compiler to treat every read and write of `sink` as an observable
     * side effect it must actually perform, so the 2x10^8-iteration loop
     * inside kernel() cannot be optimized away no matter how aggressively
     * the compiler is told to optimize (this file is built with -O3, see
     * ../src -- actually the parent build script -- for the exact flags).
     *
     * Threading sink's value INTO the next trial (`sink + (double)t`
     * below) serves a second purpose beyond just "give kernel() an input":
     * it also prevents the compiler from noticing that all 60 trials
     * compute the same thing and hoisting/merging them into one call --
     * each trial starts from a different, previously-computed value, so
     * each call to kernel() is a genuinely distinct piece of work from the
     * compiler's point of view, forcing all 60 trials to actually execute.
     */
    volatile double sink = 0.0;

    /* CSV header. plot_jitter.py (../src/plot_jitter.py) reads this file
     * with Python's csv module and skips this header row via next(r). */
    printf("trial,ns\n");

    for (int t = 0; t < trials; ++t) {
        /* Time ONLY the call to kernel() -- not the printf below, and not
         * loop-control overhead outside the timed region -- so that what
         * we measure is as close as possible to "how long did the fixed
         * unit of work take," with nothing else attributable to the
         * benchmark harness itself mixed into the number. */
        uint64_t start = now_ns();
        sink = kernel(sink + (double)t);
        uint64_t end = now_ns();

        /* One CSV row per trial: the trial index and its wall-clock
         * duration in nanoseconds. Nanosecond resolution (rather than,
         * say, milliseconds) is used so that small jitter-induced
         * differences between trials -- which can be well under a
         * millisecond, see the ~0.1-0.2ms post-tuning standard deviations
         * in SUMMARY.md -- are preserved with plenty of precision instead
         * of being rounded away. %llu is used because `end - start` is
         * cast to `unsigned long long` for portable printf formatting
         * across platforms where uint64_t may or may not be exactly
         * `unsigned long`.
         */
        printf("%d,%llu\n", t, (unsigned long long)(end - start));
    }

    /* Print the final accumulated value to stderr (deliberately NOT
     * stdout, so it never contaminates the CSV data stream that
     * plot_jitter.py parses). This serves as a second, belt-and-braces
     * defense against dead-code elimination: even if some future compiler
     * became smart enough to see through the `volatile` trick above, this
     * final read-and-print of sink is an unambiguous, unavoidable use of
     * the computed result that no optimizer can reason its way around.
     * The actual numeric value of sink is not meaningful and is not used
     * anywhere in the analysis -- only its existence as a "used" value
     * matters.
     */
    fprintf(stderr, "sink=%g\n", sink);
    return 0;
}
