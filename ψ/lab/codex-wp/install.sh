#!/usr/bin/env bash
# Install codex-wp into ~/.claude/bin as a real copy, not a symlink: a branch switch in this repo
# must not make the wrapper disappear for every oracle on this machine.
# Runs the unit tests first and refuses to install if they fail. Keeps a timestamped backup of any
# previous install (nothing is deleted).
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
dest="$HOME/.claude/bin/codex-wp"

( cd "$here" && python3 -m unittest -q test_codex_wp ) || { echo "unit tests failed: not installing" >&2; exit 1; }

mkdir -p "$HOME/.claude/bin"
if [ -e "$dest" ]; then
  cp -p "$dest" "$dest.bak-$(date +%Y%m%d-%H%M%S)"
fi
cp "$here/codex_wp.py" "$dest"
chmod +x "$dest"
echo "installed: $dest ($("$dest" --version))"
echo "next: $dest check      (cheap, no model call)"
echo "      $dest selftest   (one real Codex call, about 150k tokens)"
