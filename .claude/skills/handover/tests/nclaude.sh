#!/bin/bash
# Run a nested non-interactive claude in the CURRENT dir with leica-oracle's token (same idea as ~/.claude/bin/claude-teammate).
here="$PWD"
cd /Users/switchaphon/ghq/github.com/switchaphon/leica-oracle || exit 9
export GPG_TTY=$(tty 2>/dev/null || echo /dev/null)
unset DIRENV_DIR DIRENV_FILE DIRENV_DIFF DIRENV_WATCHES; eval "$(direnv export bash 2>/dev/null)"
export DISCORD_BOT_TOKEN=""
cd "$here" || exit 9
[ -n "$CLAUDE_CODE_OAUTH_TOKEN" ] || { echo "NO TOKEN after direnv" >&2; exit 8; }
exec env -u CLAUDECODE /Users/switchaphon/.local/bin/claude "$@"
