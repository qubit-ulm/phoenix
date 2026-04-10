#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DUMP_DIR="${ROOT_DIR}/dmp"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=1
fi

mkdir -p "${DUMP_DIR}"

unique_target() {
    local target="$1"
    if [[ ! -e "${target}" ]]; then
        printf '%s\n' "${target}"
        return
    fi

    local dir base stem ext counter candidate
    dir="$(dirname "${target}")"
    base="$(basename "${target}")"
    stem="${base}"
    ext=""

    if [[ "${base}" == *.* ]]; then
        stem="${base%.*}"
        ext=".${base##*.}"
    fi

    counter=1
    while true; do
        candidate="${dir}/${stem}_${counter}${ext}"
        if [[ ! -e "${candidate}" ]]; then
            printf '%s\n' "${candidate}"
            return
        fi
        counter=$((counter + 1))
    done
}

move_path() {
    local source="$1"
    [[ -e "${source}" ]] || return 0

    local rel target
    rel="${source#${ROOT_DIR}/}"
    target="$(unique_target "${DUMP_DIR}/${rel}")"

    printf '%s -> %s\n' "${rel}" "${target#${ROOT_DIR}/}"
    if [[ "${DRY_RUN}" -eq 1 ]]; then
        return 0
    fi

    mkdir -p "$(dirname "${target}")"
    mv "${source}" "${target}"
}

for rel in \
    ".idea" \
    ".pytest_cache" \
    ".venv" \
    "venv" \
    "phoenix_build" \
    "doc/_build"
do
    move_path "${ROOT_DIR}/${rel}"
done

while IFS= read -r -d '' directory; do
    move_path "${directory}"
done < <(
    find "${ROOT_DIR}" \
        \( \
            -path "${ROOT_DIR}/.git" -o \
            -path "${DUMP_DIR}" -o \
            -path "${ROOT_DIR}/.idea" -o \
            -path "${ROOT_DIR}/.pytest_cache" -o \
            -path "${ROOT_DIR}/.venv" -o \
            -path "${ROOT_DIR}/venv" -o \
            -path "${ROOT_DIR}/phoenix_build" -o \
            -path "${ROOT_DIR}/doc/_build" \
        \) -prune -o \
        -type d \( -name "__pycache__" -o -name "generated_*" \) -print0
)

for rel in \
    "doc/cbuilder.log" \
    "doc/fortranbuilder.log"
do
    move_path "${ROOT_DIR}/${rel}"
done

while IFS= read -r -d '' file; do
    move_path "${file}"
done < <(
    find "${ROOT_DIR}" \
        \( \
            -path "${ROOT_DIR}/.git" -o \
            -path "${DUMP_DIR}" -o \
            -path "${ROOT_DIR}/.idea" -o \
            -path "${ROOT_DIR}/.pytest_cache" -o \
            -path "${ROOT_DIR}/.venv" -o \
            -path "${ROOT_DIR}/venv" -o \
            -path "${ROOT_DIR}/phoenix_build" -o \
            -path "${ROOT_DIR}/doc/_build" \
        \) -prune -o \
        -type f -name "*.pyc" -print0
)

while IFS= read -r -d '' file; do
    move_path "${file}"
done < <(
    find "${ROOT_DIR}/demo" "${ROOT_DIR}/tutorials" \
        -type f \
        \( -name "*.gif" -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.svg" -o -name "*.pdf" \) \
        -print0 2>/dev/null
)
