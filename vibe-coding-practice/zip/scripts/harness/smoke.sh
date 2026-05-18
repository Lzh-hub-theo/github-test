#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

cd "$root_dir"

if command -v python3 >/dev/null 2>&1; then
  python3 -m py_compile server.py
  echo "Python syntax check passed"
fi

if [ -f "$root_dir/requirements.txt" ]; then
  echo "Dependencies: $(cat requirements.txt | wc -l) packages"
fi

echo "Smoke check complete"