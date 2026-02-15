#!/usr/bin/env bash
# Local manual sync of docs from source repos.
#
# Usage: bash scripts/sync.sh [source_dir]
#   source_dir defaults to ../../ (relative to scripts/)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SOURCE_DIR="${1:-$(cd "${SCRIPT_DIR}/../../" && pwd)}"

echo "Syncing from: ${SOURCE_DIR}"
echo "Into:         ${REPO_ROOT}"
echo ""

# Repo name -> package directory name
declare -A REPO_TO_PKG=(
    ["wrdata"]="wrdata"
    ["fracTime"]="fractime"
    ["wrtrade"]="wrtrade"
    ["wrchart"]="wrchart"
    ["wrchart-js"]="wrchart-js"
    ["wayyDB"]="wayydb"
)

synced=0
skipped=0

for repo in wrdata fracTime wrtrade wrchart wrchart-js wayyDB; do
    pkg="${REPO_TO_PKG[$repo]}"
    src="${SOURCE_DIR}/${repo}"

    if [ ! -d "$src" ]; then
        echo "SKIP: ${repo} (not found at ${src})"
        ((skipped++))
        continue
    fi

    mkdir -p "${REPO_ROOT}/packages/${pkg}"

    # Copy README.md
    if [ -f "${src}/README.md" ]; then
        cp "${src}/README.md" "${REPO_ROOT}/packages/${pkg}/README.md"
        echo "  OK: ${repo}/README.md -> packages/${pkg}/README.md"
    fi

    # Copy examples/ if it exists
    if [ -d "${src}/examples" ]; then
        mkdir -p "${REPO_ROOT}/packages/${pkg}/examples"
        cp -r "${src}/examples/"* "${REPO_ROOT}/packages/${pkg}/examples/" 2>/dev/null || true
        echo "  OK: ${repo}/examples/ -> packages/${pkg}/examples/"
    fi

    ((synced++))
done

echo ""
echo "--- Post-sync steps ---"

# Extract versions
echo "Extracting versions..."
python3 "${SCRIPT_DIR}/extract-versions.py" "${SOURCE_DIR}"

# Build llms-full.txt
echo ""
echo "Building llms-full.txt..."
bash "${SCRIPT_DIR}/build-llms-full.sh"

echo ""
echo "--- Summary ---"
echo "  Synced:  ${synced}"
echo "  Skipped: ${skipped}"
echo "  Done."
