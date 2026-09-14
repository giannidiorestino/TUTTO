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
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$target" ]; then
  echo "Target directory does not exist: $target" >&2
  exit 1
fi

git -C "$repo_dir" fetch origin main
git -C "$repo_dir" checkout origin/main -- tutto.bib

cp "$repo_dir/tutto.bib" "$target/tutto.bib"
echo "Copied tutto.bib into $target"
