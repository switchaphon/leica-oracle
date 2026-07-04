# Project Conventions Override Skill Defaults

**Date**: 2026-06-06
**Source**: /rrr retro — pet profile redesign grill session
**Context**: /to-prd skill published PRD to GitHub Issues, but pops/vet keeps PRDs as local .md files in `prototype/prp/`

## Pattern

Skills like /to-prd have default publication paths (e.g., "publish to issue tracker"). These defaults assume a generic project. When a project has its own artifact conventions — like pops/vet storing PRDs in `prototype/prp/*.md` — the project convention wins.

## Rule

Before following any skill's "publish" or "save" step:
1. Check where the project already stores that artifact type (grep for existing files)
2. Check memory for project conventions
3. If conflict, follow project convention and skip the skill's default

## Anti-pattern

Following a skill's instructions mechanically without checking if the project has an established pattern for the same artifact. This creates artifacts in the wrong location that the user then has to clean up.

## Related

- `feedback_never_touch_production.md` — similar principle: scope your output to where the project expects it
- `project_prototype_folder_convention_v2.md` — prototype file organization rules
