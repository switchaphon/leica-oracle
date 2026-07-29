# Skill Usage Census — 2026-07-29

Real measurement across **331 Claude Code session transcripts (663 MB)**. Not an estimate.

## Result

| | |
|---|---|
| Global skills | **120** (2026-05-08 design assumed 88) |
| Ever called | **24** |
| Never called | **96 = 80%** (design estimated 69%) |
| Never-called that are merely new | **0** — newest untouched since 2026-06-19 |

`dig` 10 calls / 9 sessions · `trace` 2 calls / 1 session — a proposed merge of dig into trace
would have deleted the skill used 5× more. Reverted.

## Files

- `census2.py` — the scanner. Runs in ~2.8s. Re-run any time to refresh.
- `clean.json` — results with the measuring session excluded (**use this one**)
- `census2.json` — raw run, includes self-contamination; kept for comparison

## Re-running

```bash
python3 census2.py          # writes census2.json
```

Edit the `CUR` session-id guard to exclude the session you are running from — otherwise reading
`skills/X/SKILL.md` during analysis inflates that skill's own count. Raw `dig`=30 / `trace`=35
fell to 10 / 2 once excluded.

## Method

Four **anchored** capture patterns, then intersected with the real skill list — never bare-name
matching, which would false-positive on skills named `go`, `run`, `review`:

- `<command-name>/X</command-name>`
- `"skill":"X"`
- `Launching skill: X`
- `skills/X/SKILL.md`

Confidence ~85%. A skill invoked without leaving any of these four markers is undercounted.

## Counting traps hit while producing this

Four count discrepancies, **none of them a tool bug**:

1. 120 vs 75 skills — symlinks (`find -type d` does not follow them, `os.path.isdir()` does)
2. 26 vs 27 inbox files — measured an hour apart, a file was written between
3. 644 vs 26 agents — the 644 were agent *worktrees*, not agent definitions
4. 188 vs 182 plugin skills — `glob('**')` skips dotted dirs; here `rtk proxy` was right and
   the "native" check was wrong

**⚠️ Enumerating the 45 symlinks:** `find -maxdepth 1 -type d` returns 75 and every symlink is
invisible to it. Use `-type l` (45) or python `os.path.islink()` (45). The 39 **never-called**
symlinks are the safe reversible first move — a `-type d` pass reports a clean 75 with all 45
symlinks absent from the list.

**⚠️ Do not write "dead" here — it cost a false alarm on 2026-07-29.** In this file "dead" was
being used to mean *never called*. It was later re-read as *dangling*, which produced a
measurement of "45 symlinks, 0 dead", which was mistaken for a contradiction and published as
one. Both figures were always correct and answer different questions:

```
96 never-called  =  39 symlinks  +  57 real directories
45 symlinks total,  0 dangling   (os.path.islink · find -type l · per-target resolve all agree)
```

Say **never-called** or **dangling**. Never "dead".

See memory: `skill_usage_census`, `skill_architecture_three_tiers`, `rtk_mangles_strings`.
