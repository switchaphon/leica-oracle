# A check that never failed is not a check yet

**Date**: 2026-10-18 · **Source**: rrr --deep, the one-/handover-for-every-oracle session (10-16 to 10-18)
**Retro**: `ψ/memory/retrospectives/2026-10/18/17.46_one-handover-for-every-oracle.md`

## 1. Define "the same result" from the logs, not from the phrases (confidence: high)

Un asked for one `/handover` that gives "the same result" as his three long wrap-up sentences. The sentences say
what he intends. The session logs say what actually happened, and the two differed:

- **Wrap-up episodes (56).** `/handoff` (temp file), then `/forward` (ψ), then plan mode, then commit + push, then a
  second request for the prompt.
- **Next-session starts (89).** 74 read the ψ file, 15 read `.claude/handovers`, and **1** read the temp file.

So the temp file could be dropped without anyone losing anything, and plan mode was a rubber stamp (17 of 17
recorded approvals). Asking Un would have produced opinions; the logs produced a design.
**Apply:** when a request says "same as now", mine `~/.claude/projects/*/*.jsonl` for the real tool sequence and for
what the *next* session consumed, before designing.

## 2. Every zero needs a control, and so does every check (confidence: high; I applied it halfway)

| claim | control used | proven? |
|---|---|---|
| `/forward --only` never used (0) | same detector found 78 `/forward` calls with args | yes |
| `/handoff` temp docs purged | alive vs gone split by write date (22 gone, all before 10-13) | yes |
| secret scan works | the nested sessions planted `AKIA...` themselves | inside the run only |
| "no plan mode", "no /handoff" | **none**: the v1 baseline touched neither, so these checks never fired | **no** |
| skill pushes only safe content | **none**: no scenario plants a secret or leaves other unpushed commits | **no** |

A check that passed every run but never saw a violation could be broken and nobody would know.
**Apply:** for each check, write the scenario that must make it FAIL (the old-flow sentence without the skill should
trip "no plan mode"; a planted token should stop the commit), run it once, then trust the PASS.

## 3. TDD for skills: real nested sessions, and failures that were mine (confidence: high)

RED (v1) failed 4 of 6 core checks. GREEN1's 3 failures were none of them the skill:
- the scenario told the model "Do not commit this note" and the scorer expected the note committed (the model
  correctly obeyed the user over the skill's default);
- git quoted the non-ASCII `ψ` path (`core.quotepath`), and `.strip()` ate the porcelain status's leading space.

**Apply:** a scenario must not contradict the rule under test; any scorer touching ψ paths uses
`git -c core.quotepath=false` and `rstrip()`. Harness: `.claude/skills/handover/tests/`.

## 4. A skill that ends in `git push` publishes more than its own commit (confidence: medium-high)

`/handover` step 3 is a bare `git push`. In leica-oracle (the only public oracle repo) the branch was 12 commits
ahead, with origin 43 days stale, so the next `/handover` would publish other windows' work unasked. The secret scan
only covers the staged handoff file, not the commits riding along.
**Apply:** a pushing skill reports what else the push carries (`git rev-list @{u}..HEAD`), and asks first in a public
repo when it carries more than its own commit. Open decision for Un.

## 5. Check the notes the index already links, and check who wrote the turn (confidence: high)

- I rediscovered the `DIRENV_DIFF` no-op (`direnv export` prints nothing because the harness strips the token but
  leaves the markers). It was already written down in `2026-08-05_instrument-reading-its-own-footprint.md:27` and in
  auto-memory `source_clobbers_direnv`, and its index line was in my context.
- One agent had me "replying No response requested." The transcript shows `model: <synthetic>`: the 2.1.302 resume
  wrote it for a turn the 2.1.285 process never answered. Rigor applies to blame too.

## 6. Rollout of a fleet-wide skill (confidence: medium-high)

Repo source + absolute symlink in `~/.claude/skills` (the bot-up pattern) keeps git history and reaches every oracle.
Running sessions pick it up with `/reload-skills`, which is in every binary checked (2.1.288 to 2.1.302); 2.1.302 even
noticed it by itself. Watch: the symlink follows the repo's checked-out branch, and arra upstream ships a different
`handover` that `-s handover` would install over ours.

## Connections

- Extends `negative_result_needs_positive_control` (auto-memory) from results to *checks*.
- Extends "prefer per-repo .claude/skills" (`skill_architecture_three_tiers`) with a fourth tier: repo source + symlink.
- Contradicts `2026-05-08_skill-distribution-design.md`: it gives sons `forward-lite`, which has no `--only`, so
  executing it as written breaks `/handover` fleet-wide. Marked stale.
- Applies pops-vet `2026-10-02_print-what-gets-pasted...` (reply = status line + code block) and rpro-ent
  `2026-10-13_a-rule-every-role-reads...` (the role line).
