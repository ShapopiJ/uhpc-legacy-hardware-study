#!/bin/bash
# Build OpenBLAS (Sandy Bridge target) + HPL 2.3 against it on the uhpc
# manager node, for the ATLAS-vs-OpenBLAS HPL comparison on the Stampede rack.
# Runs entirely in ~/blas-study ; installs nothing system-wide.
set -euo pipefail

BASE="$HOME/blas-study"
OB_VER="0.3.26"
HPL_VER="2.3"
NPROC=$(nproc)

mkdir -p "$BASE"
cd "$BASE"

echo "=== [$(date)] toolchain ==="
gcc --version | head -1
# OpenMPI 3.1.2 (gnu8)
module load gnu8 openmpi3 2>/dev/null || true
which mpicc gcc gfortran

# ---------------------------------------------------------------- OpenBLAS
if [ ! -f "$BASE/opt/openblas/lib/libopenblas.a" ]; then
  echo "=== [$(date)] fetching OpenBLAS $OB_VER ==="
  if [ ! -f "OpenBLAS-$OB_VER.tar.gz" ]; then
    curl -fsSL -o "OpenBLAS-$OB_VER.tar.gz" \
      "https://github.com/OpenMathLib/OpenBLAS/releases/download/v$OB_VER/OpenBLAS-$OB_VER.tar.gz"
  fi
  rm -rf "OpenBLAS-$OB_VER"
  tar xf "OpenBLAS-$OB_VER.tar.gz"
  cd "OpenBLAS-$OB_VER"
  echo "=== [$(date)] building OpenBLAS (TARGET=SANDYBRIDGE, sequential) ==="
  # Sequential BLAS: HPL gets its parallelism from 16 MPI ranks/node (matches
  # the paper's "16 processes per node" and a clean ATLAS-serial comparison).
  make -j"$NPROC" TARGET=SANDYBRIDGE USE_OPENMP=0 USE_THREAD=0 NO_AFFINITY=1 \
       CC=gcc FC=gfortran > "$BASE/openblas_build.log" 2>&1
  make PREFIX="$BASE/opt/openblas" install >> "$BASE/openblas_build.log" 2>&1
  cd "$BASE"
  echo "=== OpenBLAS installed ==="
else
  echo "=== OpenBLAS already built, skipping ==="
fi

# ---------------------------------------------------------------- HPL
cd "$BASE"
if [ ! -f "hpl-$HPL_VER.tar.gz" ]; then
  echo "=== [$(date)] fetching HPL $HPL_VER ==="
  curl -fsSL -o "hpl-$HPL_VER.tar.gz" "https://www.netlib.org/benchmark/hpl/hpl-$HPL_VER.tar.gz"
fi
rm -rf "hpl-$HPL_VER"
tar xf "hpl-$HPL_VER.tar.gz"
cd "hpl-$HPL_VER"

ARCH="SANDYBRIDGE_OB"
MPIDIR=$(dirname "$(dirname "$(which mpicc)")")
cat > "Make.$ARCH" <<EOF
SHELL        = /bin/sh
CD           = cd
CP           = cp
LN_S         = ln -f -s
MKDIR        = mkdir -p
RM           = /bin/rm -f
TOUCH        = touch
ARCH         = $ARCH
TOPdir       = $BASE/hpl-$HPL_VER
INCdir       = \$(TOPdir)/include
BINdir       = \$(TOPdir)/bin/\$(ARCH)
LIBdir       = \$(TOPdir)/lib/\$(ARCH)
HPLlib       = \$(LIBdir)/libhpl.a
MPdir        = $MPIDIR
MPinc        = -I\$(MPdir)/include
MPlib        = -L\$(MPdir)/lib -lmpi
LAdir        = $BASE/opt/openblas
LAinc        = -I\$(LAdir)/include
LAlib        = \$(LAdir)/lib/libopenblas.a
F2CDEFS      = -DAdd__ -DF77_INTEGER=int -DStringSunStyle
HPL_INCLUDES = -I\$(INCdir) -I\$(INCdir)/\$(ARCH) \$(LAinc) \$(MPinc)
HPL_LIBS     = \$(HPLlib) \$(LAlib) \$(MPlib) -lm -lpthread -lgfortran
HPL_OPTS     = -DHPL_CALL_CBLAS
HPL_DEFS     = \$(F2CDEFS) \$(HPL_OPTS) \$(HPL_INCLUDES)
CC           = mpicc
CCNOOPT      = \$(HPL_DEFS)
CCFLAGS      = \$(HPL_DEFS) -fomit-frame-pointer -O3 -funroll-loops -W -Wall -fopenmp
LINKER       = mpicc
LINKFLAGS    = \$(CCFLAGS) -fopenmp
ARCHIVER     = ar
ARFLAGS      = r
RANLIB       = echo
EOF

echo "=== [$(date)] building HPL against OpenBLAS ==="
make arch="$ARCH" > "$BASE/hpl_build.log" 2>&1
ls -la "bin/$ARCH/xhpl" && echo "=== xhpl (OpenBLAS) built OK ==="
echo "=== [$(date)] DONE.  xhpl at: $BASE/hpl-$HPL_VER/bin/$ARCH/xhpl ==="
