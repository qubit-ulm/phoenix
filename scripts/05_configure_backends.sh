#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_BIN="${CONFIG_BIN:-${ROOT_DIR}/bin/phoenix-config}"
CONFIG_INIT_BIN="${CONFIG_INIT_BIN:-${ROOT_DIR}/bin/phoenix-config-init}"
CONFIG_MODE="${CONFIG_MODE:-interactive}"

echo "==> PHOENIX backend configuration"
echo

if [[ ! -x "${CONFIG_BIN}" ]]; then
    echo "Configuration frontend not found at ${CONFIG_BIN}"
    exit 1
fi

echo "Current backend status:"
"${CONFIG_BIN}" --status || true
echo

case "${CONFIG_MODE}" in
    interactive)
        if [[ -t 0 && -x "${CONFIG_INIT_BIN}" ]]; then
            echo "Launching guided backend initialization."
            echo
            "${CONFIG_INIT_BIN}"
        else
            echo "Interactive initialization skipped because there is no TTY or"
            echo "the init frontend is unavailable."
            echo "Run manually later with:"
            echo "  ${CONFIG_INIT_BIN}"
        fi
        ;;
    status)
        echo "CONFIG_MODE=status selected. Showing status only."
        ;;
    *)
        echo "Unknown CONFIG_MODE='${CONFIG_MODE}'. Supported: interactive, status"
        exit 1
        ;;
esac
