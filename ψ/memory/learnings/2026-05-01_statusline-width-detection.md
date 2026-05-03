# Claude Code Statusline: Terminal Width Detection

**Date**: 2026-05-01
**Source**: rrr --deep: leica-oracle
**Confidence**: High (verified empirically)

## The Problem

Claude Code runs the statusline command as a subprocess with no real TTY. Standard width detection methods fail:

| Method | Returns | Why |
|--------|---------|-----|
| `tput cols` | 80 | Default, no TTY attached |
| `$COLUMNS` | 0 (or unset) | Claude Code sets it to 0 |
| `stty size` (no redirect) | empty | No stdin terminal |

## The Solution

```bash
# Priority: explicit override → real TTY → tmux → safe fallback
if [ -n "$COLUMNS" ] && [ "$COLUMNS" -gt 0 ]; then
  COLS=$COLUMNS
else
  COLS=$(stty size </dev/tty 2>/dev/null | awk '{print $2}')
  [ -z "$COLS" ] || [ "$COLS" -le 0 ] && COLS=$(tmux display-message -p '#{pane_width}' 2>/dev/null)
  [ -z "$COLS" ] || [ "$COLS" -le 0 ] && COLS=120
fi
```

## tmux Session Group Constraint

When the same session is viewed from two clients (e.g., MacBook half-screen + external monitor), tmux constrains the window to the **smallest** client's width. This means:
- Both screens see 95 cols even if the external monitor has 200+
- Adaptive statusline cannot serve different layouts to different clients
- The medium layout (70-140 cols) is the correct default for multi-client sessions

## Fleet Config Schema

Three fields make an Oracle visible in the statusline:
```json
{
  "project_path": "/absolute/path/to/project/repo",
  "icon": "🌊",
  "short_name": "nrsim"
}
```
Missing `project_path` → silently skipped. This is the contract between maw fleet configs and the statusline.
