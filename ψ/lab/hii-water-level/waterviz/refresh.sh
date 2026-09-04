#!/bin/bash
# refresh.sh - keep the SQLite store and the built page current.
#
#   refresh.sh live   one request, all 154 current readings   (every 15 min)
#   refresh.sh full   154 requests, backfills the 10-min series (nightly)
#
# Source cadence is 10 min for สสน. stations and 1 h for ชป., so polling faster
# than 15 min buys nothing. The nightly full run is what closes the gaps the
# live poll skips.
#
# NOTE: this refreshes the database and the local waterviz.html only.
# Publishing the page to claude.ai is a manual step - see README.
set -euo pipefail

PY=/opt/homebrew/bin/python3
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="$HOME/hii-data"
DB="$DATA/waterviz.db"
SNAP="$DATA/snapshot.json"
LOG="$DATA/refresh.log"
MODE="${1:-live}"

mkdir -p "$DATA"
exec >>"$LOG" 2>&1

# One run at a time. A nightly full backfill takes minutes; without this the
# 15-minute live poll would start on top of it and both would fight the db.
# mkdir is atomic on every POSIX filesystem - macOS has no flock(1).
LOCK="$DATA/.refresh.lock"
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -f "$LOCK/pid" ] && kill -0 "$(cat "$LOCK/pid" 2>/dev/null)" 2>/dev/null; then
    echo "===== $(date '+%F %T %z')  mode=$MODE  SKIPPED, pid $(cat "$LOCK/pid") still running"
    exit 0
  fi
  echo "===== $(date '+%F %T %z')  clearing a stale lock"
  rm -rf "$LOCK"; mkdir "$LOCK"
fi
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT INT TERM

echo "===== $(date '+%F %T %z')  mode=$MODE"

if [ "$MODE" = "full" ]; then
  "$PY" "$DIR/ingest.py" --db "$DB" --days 30 --delay 0.35 \
        --export "$SNAP" --export-days 30 --points 360
else
  "$PY" "$DIR/ingest.py" --db "$DB" --skip-backfill \
        --export "$SNAP" --export-days 30 --points 360
fi

"$PY" "$DIR/build.py" "$SNAP"
echo "rows: $("$PY" -c "import sqlite3,sys;print(f'{sqlite3.connect(sys.argv[1]).execute(\"SELECT COUNT(*) FROM reading\").fetchone()[0]:,}')" "$DB")"
echo "done $(date '+%T')"
