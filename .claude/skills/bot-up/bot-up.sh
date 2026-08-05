#!/bin/bash
# bot-up — bring an oracle's Discord bot up in its own tmux window.
#
# Why this exists: the manual path is three tmux commands, and `send-keys`
# silently only TYPES unless you pass the literal word `Enter` as a separate
# argument. Two half-sent commands concatenate on one input line and run as
# garbage. This script always sends Enter, and verifies before and after.
#
# Usage:
#   bot-up.sh <oracle> [session] [--no-bypass] [--force]
#   bot-up.sh leica
#   bot-up.sh pops-vet 04-pops-vet
#
set -euo pipefail

BASE=/Users/switchaphon/ghq/github.com/switchaphon

ORACLE=""; SESSION=""; BYPASS=1; FORCE=0
for a in "$@"; do
  case "$a" in
    --no-bypass) BYPASS=0 ;;
    --force)     FORCE=1 ;;
    -*)          echo "unknown flag: $a" >&2; exit 2 ;;
    *)           if [ -z "$ORACLE" ]; then ORACLE="$a"; else SESSION="$a"; fi ;;
  esac
done
[ -n "$ORACLE" ] || { echo "usage: bot-up.sh <oracle> [session] [--no-bypass] [--force]" >&2; exit 2; }

REPO="$BASE/${ORACLE}-oracle"
WIN="${ORACLE}-discord"

# ── preflight ───────────────────────────────────────────────────────────────
[ -d "$REPO" ] || { echo "✗ no such repo: $REPO" >&2; exit 1; }

if ! pass show "discord/$ORACLE" >/dev/null 2>&1; then
  echo "✗ no 'pass show discord/$ORACLE' entry." >&2
  echo "  That bot application may have been deleted (pops-atlas, rpro-ent-atlas)." >&2
  exit 1
fi

grep -q 'DISCORD_BOT_TOKEN' "$REPO/.envrc" 2>/dev/null || {
  echo "✗ $REPO/.envrc has no DISCORD_BOT_TOKEN line." >&2; exit 1; }

(cd "$REPO" && direnv export bash >/dev/null 2>&1) || {
  echo "✗ direnv is not allowed for $REPO — run: direnv allow" >&2; exit 1; }

# ── pick the session ────────────────────────────────────────────────────────
if [ -z "$SESSION" ]; then
  SESSION=$(tmux ls -F '#{session_name}' 2>/dev/null | grep -E "(^|-)${ORACLE}\$" | head -1 || true)
fi
if [ -z "$SESSION" ]; then
  SESSION="$ORACLE"
  tmux new-session -d -s "$SESSION" -c "$REPO"
  echo "· created session $SESSION"
fi

# ── refuse to double-launch ─────────────────────────────────────────────────
if tmux list-windows -t "$SESSION" -F '#{window_name}' 2>/dev/null | grep -qx "$WIN"; then
  if [ "$FORCE" -eq 1 ]; then
    tmux kill-window -t "$SESSION:$WIN"; echo "· killed existing $WIN (--force)"
  else
    echo "✗ $SESSION:$WIN already exists. Two bots on one token double-reply." >&2
    echo "  Re-run with --force to replace it." >&2
    exit 1
  fi
fi

# ── create the window ───────────────────────────────────────────────────────
# No command is passed: tmux then starts an INTERACTIVE shell, which is the only
# way the direnv hook in ~/.zshrc fires. Passing a command runs it under `sh -c`
# where direnv never loads and no token reaches Claude.
tmux new-window -d -t "$SESSION" -n "$WIN" -c "$REPO"
echo "· created window $SESSION:$WIN"

send() { tmux send-keys -t "$SESSION:$WIN" "$1" Enter; }   # Enter is never optional

# wait_for <extended-regex> <seconds>
# The pattern MUST NOT match the command being typed — send-keys echoes it into
# the pane, so a loose substring matches instantly and you end up waiting on the
# echo instead of the result. Anchor it, or match text only the output produces.
wait_for() {
  local pat="$1" n="${2:-20}"
  for _ in $(seq 1 "$n"); do
    if tmux capture-pane -p -t "$SESSION:$WIN" 2>/dev/null | grep -qE "$pat"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

# ── verify direnv actually populated the pane, BEFORE launching ─────────────
tmux send-keys -t "$SESSION:$WIN" C-u          # clear any residue on the line
send 'printf "BOTUP %s %s %s\n" "${#DISCORD_BOT_TOKEN}" "${#CLAUDE_CODE_OAUTH_TOKEN}" "$CLAUDE_TOKEN_NAME"'

# '^BOTUP [0-9]' — anchored and requires a digit, so it cannot match the echoed
# `printf "BOTUP %s ...` command line.
if ! wait_for '^BOTUP [0-9]' 15; then
  echo "✗ no response from the pane — shell may not have started." >&2
  tmux capture-pane -p -t "$SESSION:$WIN" | grep -vE '^\s*$' | tail -6 >&2
  exit 1
fi
LINE=$(tmux capture-pane -p -t "$SESSION:$WIN" | grep -E '^BOTUP [0-9]' | tail -1 || true)
read -r _ DLEN CLEN TNAME <<<"$LINE"

# Lengths and a name only — never the values.
echo "· direnv: discord=$DLEN claude=$CLEN token=$TNAME"

[ "${DLEN:-0}" -gt 0 ] || { echo "✗ DISCORD_BOT_TOKEN empty — direnv did not load. Run: direnv allow" >&2; exit 1; }
[ "${CLEN:-0}" -gt 0 ] || { echo "✗ CLAUDE_CODE_OAUTH_TOKEN empty — per-repo token separation would break." >&2; exit 1; }
[ "$DLEN" -eq 72 ] || echo "⚠ discord token is $DLEN chars, expected 72 — possible truncated paste."

# ── launch ──────────────────────────────────────────────────────────────────
CMD='claude --channels plugin:discord@claude-plugins-official'
[ "$BYPASS" -eq 1 ] && CMD="$CMD --dangerously-skip-permissions"

tmux send-keys -t "$SESSION:$WIN" C-u
send "$CMD"
echo "· launched: $CMD"

# Match the banner's own words, not the channel name — the name appears in the
# command line we just echoed, so it would match instantly and prove nothing.
if wait_for 'inject directly' 30; then
  echo "✓ channel attached in $SESSION:$WIN"
else
  echo "⚠ no channel banner after 30s. Last lines:" >&2
  tmux capture-pane -p -t "$SESSION:$WIN" | grep -vE '^\s*$' | tail -8 >&2
  exit 1
fi

cat <<EOF

Loaded ≠ accepted. The steps above prove the token reached Claude; only Discord
can prove it is still valid — a rotated token looks identical until the
handshake. Tag @${ORACLE} in Discord and wait for a reply.
EOF
