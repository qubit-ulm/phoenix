#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
PIP_EXTRAS="${PIP_EXTRAS:-}"
INSTALL_TEST_DEPS="${INSTALL_TEST_DEPS:-1}"

echo "==> PHOENIX package installation"
echo
echo "Installing from : ${ROOT_DIR}"
echo "Python command  : ${PYTHON_BIN}"

if [[ -n "${PIP_EXTRAS}" ]]; then
    echo "Extras          : ${PIP_EXTRAS}"
    "${PYTHON_BIN}" -m pip install -e "${ROOT_DIR}[${PIP_EXTRAS}]"
else
    "${PYTHON_BIN}" -m pip install -e "${ROOT_DIR}"
fi

if [[ "${INSTALL_TEST_DEPS}" == "1" ]]; then
    echo
    echo "Installing the baseline requirements file as well."
    "${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/requirements.txt"
fi

echo
echo "Installation stage finished."
