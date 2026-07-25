#!/bin/bash
# Compile the STREAM-Triad benchmark. Run on the cluster login/compute node.
# Default system gcc (8.2.0, /opt/ohpc/pub/compiler/gcc/8.2.0) already supports -fopenmp.
set -e
gcc -O2 -fopenmp -o stream_triad stream_triad.c
echo "built: $(pwd)/stream_triad"
