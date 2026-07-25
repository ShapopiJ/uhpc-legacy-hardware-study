/* fixedwork.c -- companion to osjitter: times a fixed, known amount of FP
 * work over repeated trials so jitter shows up as trial-to-trial variance,
 * convertible directly into FLOPs lost. Not part of upstream osjitter.
 *
 * Usage: ./fixedwork [cpu=0] [trials=100]
 * Output: CSV "trial,ns" to stdout (read by ../src/plot_jitter.py); a
 * diagnostic sink value to stderr. */

#define _GNU_SOURCE             // needed before sched.h for cpu_set_t/CPU_SET/sched_setaffinity
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>

#define ITERS 200000000UL      // kernel() does 2 FLOPs/iter -> 4e8 FLOPs/call, fixed and known
                                // sized so one trial ~450ms on Xeon E5-2680: long enough that a
                                // ~1ms OS tick is a measurable fraction, short enough that 60
                                // trials finish in ~30s

static double kernel(double x) {
    for (unsigned long i = 0; i < ITERS; ++i) {
        x = x * 1.0000000001 + 1e-12;  // serial dependency: compiler can't reorder/vectorize this,
                                        // so timing variance is external jitter, not codegen noise
    }
    return x;                          // multiplier ~1, addend ~0: keeps x from overflow/decay
                                        // over 2e8 iterations
}

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);              // MONOTONIC: immune to NTP jumps, unlike REALTIME
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

int main(int argc, char **argv) {
    int cpu = 0;                        // default core 0
    int trials = 100;                   // default trial count
    if (argc > 1) cpu = atoi(argv[1]);
    if (argc > 2) trials = atoi(argv[2]);

    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(cpu, &set);                                // pin to `cpu` so this run is comparable to
                                                        // osjitter's per-core stats on the same core,
                                                        // and so scheduler migration doesn't masquerade
                                                        // as jitter
    if (sched_setaffinity(0, sizeof(set), &set) != 0) {
        perror("sched_setaffinity");
        return 1;                                      // fail loudly rather than silently measure
                                                        // the wrong core
    }

    volatile double sink = 0.0;    // volatile: stops the optimizer from proving kernel() is dead
                                    // code and deleting the loop

    printf("trial,ns\n");          // header row; plot_jitter.py skips it via next(r)

    for (int t = 0; t < trials; ++t) {
        uint64_t start = now_ns();
        sink = kernel(sink + (double)t);   // feed sink+t in: stops the compiler merging/hoisting
                                            // identical-looking trials into one call
        uint64_t end = now_ns();           // time only kernel(), not the printf below

        printf("%d,%llu\n", t, (unsigned long long)(end - start));  // ns precision: post-tuning
                                                                     // stddevs are ~0.1-0.2ms
    }

    fprintf(stderr, "sink=%g\n", sink);  // stderr, not stdout, so it never lands in the CSV;
                                          // belt-and-braces use of sink against dead-code elimination
    return 0;
}
