#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

echo "==> PHOENIX system check"
echo
echo "Repository root : ${ROOT_DIR}"
echo "Shell           : ${SHELL:-unknown}"
echo "Python command  : ${PYTHON_BIN}"
echo

if command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    echo "Python version:"
    "${PYTHON_BIN}" --version
else
    echo "Python interpreter '${PYTHON_BIN}' was not found."
    exit 1
fi

echo
echo "Detected toolchains and helper binaries:"
for tool in gcc clang gfortran nvcc make cmake git pkg-config f2py; do
    if command -v "${tool}" >/dev/null 2>&1; then
        printf '  [ok] %s -> %s\n' "${tool}" "$(command -v "${tool}")"
    else
        printf '  [--] %s not found\n' "${tool}"
    fi
done

echo
echo "Detected optional Python modules:"
"${PYTHON_BIN}" - <<'PY'
import importlib.util

for module in ("numpy", "pyopencl", "cupy", "pycuda", "sphinx", "pytest"):
    found = importlib.util.find_spec(module) is not None
    tag = "ok" if found else "--"
    print(f"  [{tag}] {module}")
PY
