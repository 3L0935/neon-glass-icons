#!/usr/bin/env bash
# Build the public theme and pack it for a release / the KDE Store: dist/NeonGlass-<version>.tar.gz
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="${1:-$(date +%Y.%m.%d)}"
tmp="$(mktemp -d)"
python3 -I "$ROOT/tools/build.py" --public --out "$tmp/NeonGlass"
mkdir -p "$ROOT/dist"
tar -C "$tmp" -czf "$ROOT/dist/NeonGlass-$version.tar.gz" NeonGlass
rm -rf "$tmp"
ls -la "$ROOT/dist/NeonGlass-$version.tar.gz"
