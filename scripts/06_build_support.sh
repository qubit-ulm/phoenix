#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_BIN="${CONFIG_BIN:-${ROOT_DIR}/bin/phoenix-config}"
BACKENDS="${PHOENIX_BUILD_BACKENDS:-c fortran cuda opencl}"

echo "==> PHOENIX backend support build"
echo

if [[ ! -x "${CONFIG_BIN}" ]]; then
    echo "Configuration frontend not found at ${CONFIG_BIN}"
    exit 1
fi

for backend in ${BACKENDS}; do
    echo "-- building support for ${backend}"
    if "${CONFIG_BIN}" --build "${backend}"; then
        echo "   done"
    else
        echo "   skipped or failed; inspect the configuration and toolchain for ${backend}"
    fi
    echo
done
