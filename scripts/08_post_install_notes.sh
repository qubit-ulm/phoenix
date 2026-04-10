#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> PHOENIX post-install notes"
echo
echo "Recommended next steps:"
echo "  1. Read the nutshell tutorials:"
echo "       tutorials/00a_in_a_nutshell_keymaps.py"
echo "       tutorials/00b_in_a_nutshell_instructions.py"
echo "       tutorials/00c_in_a_nutshell_first_library.py"
echo "       tutorials/00d_in_a_nutshell_mapapply_library.py"
echo
echo "  2. Inspect backend configuration status:"
echo "       ${ROOT_DIR}/bin/phoenix-config --status"
echo
echo "  3. Try a pure-Python tutorial first:"
echo "       python tutorials/04_python_backend.py"
echo
echo "  4. Build the documentation when you want the full written guide:"
echo "       make doc"
