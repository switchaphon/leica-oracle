# maw engine config: silent fallback to claude

**Date**: 2026-06-26
**Source**: rrr --deep: leica-oracle
**Tags**: maw, omx, engine, config, gotcha, critical

## Lesson

`maw team up` resolves engine names via `engineCommand()` in `team-liveness.ts:185-188`:
```typescript
const key = opts.resume ? `${engine}-resume` : engine;
return config.commands?.[key] ?? config.commands?.default ?? key;
```

If `engine: omx` is in the charter but `omx` is NOT in `config.commands`, it silently falls back to `config.commands.default` which is `"claude"`. No warning. No error. The team spawns, tmux windows open, everything looks right — but it's Claude burning tokens, not omx running free.

## Config location

`~/.config/maw/maw.config.json` — NOT `~/.maw/`

## Required commands mapping

```json
"commands": {
  "default": "claude",
  "omx": "omx --yolo --direct",
  "omx-resume": "omx --yolo --direct resume --last"
}
```

## Verification

After adding the mapping, always test the full chain:
1. Write charter with `engine: omx`
2. `maw team up` 
3. `maw peek` the spawned coder
4. Confirm engine shows gpt-5.5, NOT Claude

"Binary installed" ≠ "config routes to it" ≠ "maw team up launches it"
