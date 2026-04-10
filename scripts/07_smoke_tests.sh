#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
CONFIG_BIN="${CONFIG_BIN:-${ROOT_DIR}/bin/phoenix-config}"
TEST_BACKEND="${PHOENIX_TEST_BACKEND:-python}"
RUN_PYTEST="${RUN_PYTEST:-1}"

echo "==> PHOENIX smoke tests"
echo

if [[ -x "${CONFIG_BIN}" ]]; then
    echo "-- backend smoke test via phoenix-config (${TEST_BACKEND})"
    "${CONFIG_BIN}" --test "${TEST_BACKEND}" || true
    echo
fi

if [[ "${RUN_PYTEST}" == "1" ]]; then
    echo "-- focused pytest smoke tests"
    "${PYTHON_BIN}" -m pytest -q \
        tests/test_logger.py \
        tests/test_build_logging.py \
        tests/test_atomic_region_generation.py \
        tests/test_omp_resource_generation.py
fi
