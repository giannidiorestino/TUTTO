#!/bin/bash
# Pull the latest tutto.bib from this repo into another project directory.
#
# Usage:
#   ./sync-tutto-bib.sh /path/to/other/project
#
# Always fetches the current main branch from GitHub first, so the copy
# is up to date even if this local clone is stale.

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 /path/to/target/project" >&2
  exit 1
fi

target="$1"
script_path="${BASH_SOURCE[0]}"
while [ -L "$script_path" ]; do
  link_target="$(readlink "$script_path")"
  case "$link_target" in
    /*) script_path="$link_target" ;;
    *) script_path="$(dirname "$script_path")/$link_target" ;;
  esac
done
repo_dir="$(cd "$(dirname "$script_path")" && pwd)"

if [ ! -d "$target" ]; then
  echo "Target directory does not exist: $target" >&2
  exit 1
fi

git -C "$repo_dir" fetch origin main
git -C "$repo_dir" checkout origin/main -- tutto.bib

{
  echo "% Synced from TUTTO (github.com/giannidiorestino/TUTTO) on $(date +%Y-%m-%d)"
  cat "$repo_dir/tutto.bib"
} > "$target/tutto.bib"
echo "Copied tutto.bib into $target (dated $(date +%Y-%m-%d))"
