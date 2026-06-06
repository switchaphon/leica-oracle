#!/usr/bin/env bash
# maw team — Full Lifecycle Demo
# Run: bash ψ/lab/maw-team-demo.sh
set -euo pipefail

TEAM="demo-$(date +%s | tail -c 5)"
echo "════════════════════════════════════════════════════"
echo "  maw team lifecycle: $TEAM"
echo "════════════════════════════════════════════════════"

echo ""
echo "▸ CREATE"
maw team create "$TEAM" --description "lifecycle demo"

echo ""
echo "▸ SPAWN 3 agents"
maw team spawn "$TEAM" scout --prompt "Find all TODO comments in the repo"
maw team spawn "$TEAM" analyst --prompt "Read CLAUDE.md and assess oracle identity"
maw team spawn "$TEAM" writer --prompt "Write a one-line summary of this oracle"

echo ""
echo "▸ ADD TASKS"
maw team add "Find TODOs" --team "$TEAM" --assign scout
maw team add "Assess identity" --team "$TEAM" --assign analyst
maw team add "Write summary" --team "$TEAM" --assign writer

echo ""
echo "▸ TASKS"
maw team tasks "$TEAM"

echo ""
echo "▸ COMPLETE ALL"
maw team done 1 --team "$TEAM"
maw team done 2 --team "$TEAM"
maw team done 3 --team "$TEAM"

echo ""
echo "▸ STATUS"
maw team status "$TEAM"

echo ""
echo "▸ SHUTDOWN --merge --force"
maw team shutdown "$TEAM" --merge --force

echo ""
echo "▸ VAULT CHECK"
echo "  manifest:"
ls ψ/memory/mailbox/teams/"$TEAM"/ 2>/dev/null || echo "  (no vault — already cleaned)"
echo "  agent mailboxes:"
for agent in scout analyst writer; do
  if [ -d "ψ/memory/mailbox/$agent" ]; then
    echo "    ψ/memory/mailbox/$agent/ ✓"
  fi
done

echo ""
echo "▸ RESUME (reincarnation)"
maw team resume "$TEAM" 2>/dev/null || echo "  (resume skipped — vault may be gone)"

echo ""
echo "▸ DELETE"
maw team delete "$TEAM" 2>/dev/null || echo "  (already clean)"

echo ""
echo "════════════════════════════════════════════════════"
echo "  ✓ $TEAM — full cycle complete"
echo "════════════════════════════════════════════════════"
