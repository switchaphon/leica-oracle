# Claude Code Rate Limit Bars with Live Countdown

**Date**: 2026-05-01
**Source**: rrr: leica-oracle

## Pattern

Claude Code's statusline JSON includes `rate_limits.five_hour.resets_at` and `rate_limits.seven_day.resets_at` as unix timestamps. These enable live countdown displays instead of static percentages.

## Implementation

```bash
# Convert resets_at to countdown
local diff=$(( reset_ts - $(date +%s) ))
local d=$(( diff / 86400 )) h=$(( (diff % 86400) / 3600 )) m=$(( (diff % 3600) / 60 ))
# Show: "Daily ░░░░░ 9% (⟳ 4h 21m)" or "Weekly █░░░░ 20% (⟳ 4d 23h)"
```

## Also Learned

- ANSI 256-color `\033[38;5;209m` = Anthropic coral — works in Claude Code statusline
- For countdowns > 24h, show days+hours instead of raw hours (119h → 4d 23h)
