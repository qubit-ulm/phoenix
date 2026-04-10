#!/usr/bin/env bash

set -euo pipefail

OS_NAME="$(uname -s)"

echo "==> PHOENIX suggested toolchains and optional packages"
echo
echo "PHOENIX can generate code without every native tool installed, but wrappers,"
echo "support libraries, and complete makefiles benefit from having the toolchain"
echo "available locally."
echo

case "${OS_NAME}" in
    Linux)
        cat <<'EOF'
Suggested package groups on Debian/Ubuntu-like systems:
  - build-essential
  - gfortran
  - python3-dev
  - pkg-config
  - opencl-headers
  - ocl-icd-opencl-dev
  - nvidia-cuda-toolkit    (if you use CUDA locally)

Suggested package groups on Fedora-like systems:
  - gcc gcc-c++ gcc-gfortran
  - python3-devel
  - make
  - opencl-headers
  - ocl-icd-devel
  - cuda-toolkit           (if you use CUDA locally)
EOF
        ;;
    Darwin)
        cat <<'EOF'
Suggested package groups on macOS:
  - Xcode Command Line Tools
  - gcc                    (Homebrew, for gfortran and friends)
  - pkg-config

CUDA and OpenCL support depend strongly on the local machine and installed SDKs.
EOF
        ;;
    *)
        cat <<'EOF'
Suggested tools:
  - a C compiler
  - a Fortran compiler
  - make
  - pkg-config
  - optional OpenCL/CUDA SDKs for those backends
EOF
        ;;
esac

echo
echo "Suggested optional Python extras:"
echo "  - pip install -e '.[test]'"
echo "  - pip install -e '.[docs]'"
echo "  - pip install -e '.[opencl]'"
echo "  - pip install -e '.[cuda-cupy]'"
echo "  - pip install -e '.[cuda-pycuda]'"
