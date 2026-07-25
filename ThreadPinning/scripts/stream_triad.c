/* Minimal OpenMP STREAM-Triad benchmark: a[i] = b[i] + scalar*c[i]
 * Arrays are sized well beyond L3 cache so the timing reflects main-memory
 * bandwidth, not cache reuse. Prints one number to stdout: GB/s of the
 * fastest of `iters` triad passes (standard STREAM methodology: report the
 * best timing to strip out one-off OS jitter, while still submitting many
 * independent job repeats to capture scheduler/placement variance).
 *
 * Usage: stream_triad <N_elements_per_array> <iters>
 */
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

int main(int argc, char **argv) {
    long N = (argc > 1) ? atol(argv[1]) : 200000000L;   /* ~1.6GB/array */
    int iters = (argc > 2) ? atoi(argv[2]) : 5;

    double *a = malloc((size_t)N * sizeof(double));
    double *b = malloc((size_t)N * sizeof(double));
    double *c = malloc((size_t)N * sizeof(double));
    if (!a || !b || !c) { fprintf(stderr, "alloc failed\n"); return 1; }

    /* first-touch initialization: each thread inits the region it will
     * later operate on, so memory pages land on the NUMA node local to
     * the thread that touches them first. */
    #pragma omp parallel for schedule(static)
    for (long i = 0; i < N; i++) { a[i] = 1.0; b[i] = 2.0; c[i] = 0.0; }

    const double scalar = 3.0;
    double best_time = 1e30;

    for (int it = 0; it < iters; it++) {
        double t0 = omp_get_wtime();
        #pragma omp parallel for schedule(static)
        for (long i = 0; i < N; i++) {
            a[i] = b[i] + scalar * c[i];
        }
        double dt = omp_get_wtime() - t0;
        if (dt < best_time) best_time = dt;
    }

    double bytes = 3.0 * (double)N * sizeof(double); /* 2 reads + 1 write */
    double gbps = bytes / best_time / 1.0e9;
    printf("%.6f\n", gbps);
    return 0;
}
