---
title: PM-as-Oracle Architecture (2026-04-28)
tags: [architecture, oracle-pattern, federation, pm-as-oracle, awakening, maw-bugs, filesystem-federation, naming-convention, form-formless, sketch-confirm-write]
created: 2026-04-28
source: rrr --deep: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# PM-as-Oracle Architecture (2026-04-28)

PM-as-Oracle Architecture (2026-04-28)

A Claude subagent at <project>/.claude/agents/pm.md holds project knowledge but is structurally limited: no memory across sessions, unreachable from other Oracles, cannot consult specialists, dies when project's Claude session closes.

A full Oracle repo (<project>-oracle/) with own ψ/ brain, maw node, and federation identity solves all four limits.

Decision Rule: If context will outlive any single conversation AND needs to be addressable by other Oracles, it is an Oracle, not a subagent. If bounded to one project's actions in one session, it stays a subagent.

Naming: PM Oracle name = project repo name + '-oracle' (e.g. pawrent-oracle, vets-hub-oracle). Permanent convention.

Three layers in the team:
1. Specialist Oracles (codec, neon, chrome, flux, static, wire, pixel) = stateless general experts, read project context just-in-time when consulted by a PM
2. PM Oracles (pawrent-oracle, vets-hub-oracle, ...) = stateful actors, own project context permanently, dispatch project-local subagents, consult specialists
3. Project subagents in <project>/.claude/agents/ = execute file work, pre-loaded with project conventions

Federation Corollary — Filesystem Beats Wrappers: When maw hey has bugs, drop to file-based federation: write <oracle>/ψ/inbox/<ISO-timestamp>_<topic>.md with YAML front-matter. Lower-level transports (filesystem, tmux send-keys) outlive higher-level wrappers. Nothing is Deleted applies to communication too — inbox files are git-trackable.

Maw alpha bugs found in alpha.22: (1) maw hey window naming (looks for <agent> not <agent>-oracle), (2) maw inbox ψ→psi path normalization, (3) maw wake/workon worktree default wrong for awakening (use cd <repo> && claude instead).

Awakening Birth Checklist: 1) commit identity files, 2) git push origin main (birth incomplete until remote knows), 3) first federation message as proof of life, 4) update parent Oracle's CLAUDE.md to reference the new child.

Sketch → Confirm → Write was applied this session. Zero write rejections vs 3 in 2026-04-26 session. The lesson stuck — operational, not decorative.

Form and Formless (Principle 5) operationalised: Pawrent-oracle = form (project-bounded), Codec-oracle = formless (universal craft). Today's session enacted the rupa/sunyata distinction concretely.

---
*Added via Oracle Learn*
