# Maw Fleet Config Contract

**Date**: 2026-05-01
**Source**: rrr --deep: leica-oracle

## Schema

Every Project PM Oracle should have a fleet config at `~/.config/maw/fleet/<name>.json` with these fields:

```json
{
  "name": "pops-clinic",
  "icon": "🏥",
  "short_name": "pops",
  "project_path": "/absolute/path/to/project/repo",
  "windows": [{ "name": "pops-clinic-oracle", "repo": "switchaphon/pops-clinic-oracle" }],
  "sync_peers": ["leica"],
  "budded_from": "leica",
  "budded_at": "2026-04-28T16:06:57.780Z"
}
```

## Required for tooling

- `project_path` — absolute path to the actual project repo (not the Oracle repo)
- `icon` — emoji for display in statusline/tooling
- `short_name` — abbreviated label (e.g., "pops", "nrsim", "pawrent")

## Naming

- File name: `<project-slug>.json` (no numeric prefix)
- Specialist Oracles (codec, chrome, neon, pixel) do NOT need `project_path` — they have no fixed project
