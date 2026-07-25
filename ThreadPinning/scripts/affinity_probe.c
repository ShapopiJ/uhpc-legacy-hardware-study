/* Prints which physical CPU each OpenMP thread actually lands on. */
#define _GNU_SOURCE
#include <stdio.h>
#include <sched.h>
#include <omp.h>

int main(void) {
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        int cpu = sched_getcpu();
        #pragma omp critical
        printf("thread=%d cpu=%d\n", tid, cpu);
    }
    return 0;
}
