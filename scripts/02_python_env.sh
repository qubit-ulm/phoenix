#!/usr/bin/env bash

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "==> PHOENIX Python environment check"
echo

"${PYTHON_BIN}" - <<'PY'
import os
import site
import sys

print(f"Executable      : {sys.executable}")
print(f"Prefix          : {sys.prefix}")
print(f"Base prefix     : {sys.base_prefix}")
print(f"Venv active     : {sys.prefix != sys.base_prefix}")
print("Site packages   :")
for path in site.getsitepackages():
    print(f"  - {path}")
user_site = site.getusersitepackages()
print(f"User site       : {user_site}")
print(f"VIRTUAL_ENV     : {os.environ.get('VIRTUAL_ENV', '<unset>')}")
PY

echo
echo "Recommendation:"
echo "  Use the interpreter from the virtual environment where PHOENIX should live."
echo "  Override it explicitly if needed, for example:"
echo "    make install PYTHON_BIN=/path/to/python"
