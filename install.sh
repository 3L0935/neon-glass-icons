#!/usr/bin/env bash
# Build NeonGlass and install it for the current user (a link, so a rebuild updates it).
#   ./install.sh [folder color]   cyan | violet | pink | mint | lagoon | dusk | aurora (default: lagoon)
#   ./install.sh --apply          also switch Plasma to it
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
color=lagoon; apply=0
for arg in "$@"; do case "$arg" in --apply) apply=1;; *) color="$arg";; esac; done
python3 -I "$ROOT/tools/build.py" --folders "$color"
mkdir -p "$HOME/.local/share/icons"
ln -sfn "$ROOT/NeonGlass" "$HOME/.local/share/icons/NeonGlass"
rm -f "$HOME/.cache/icon-cache.kcache"
if [ "$apply" = 1 ]; then
  /usr/lib/plasma-changeicons NeonGlass
  echo "applied; restart Plasma to refresh every panel: systemctl --user restart plasma-plasmashell"
fi
echo "back to the previous theme: /usr/lib/plasma-changeicons Tela-circle-synth"
