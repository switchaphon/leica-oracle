# /handover end-to-end tests

Each scenario runs two real nested `claude -p` sessions (Opus, a few minutes each) in throwaway git repos
with local bare remotes, then `check.py` scores what landed on disk and in git.

```bash
cd ~/ghq/github.com/switchaphon/leica-oracle/.claude/skills/handover/tests
RUN=/tmp/handover-run-$(date +%Y%m%d-%H%M)          # must not exist yet, keep it outside any repo
python3 driver.py "$RUN" - T1,T2,T3,T5               # test the installed /handover
python3 driver.py "$RUN" ../SKILL.md T1,T2,T3,T5     # or a draft, installed per test repo as /handover-next
python3 check.py "$RUN"
```

| scenario | layout | what must hold |
|---|---|---|
| T1 (+T4) | oracle repo with ψ, another window's dirty files | doc via `/forward --only` in `ψ/inbox/handoff/`, commit = doc + this session's ψ note only, Rule 8 signature, pushed, no plan mode, no /handoff; a second /handover reuses the doc |
| T1b | same as T1 | second sample, checks variance |
| T2 | product repo whose ψ is a symlink to an oracle repo | doc and commit land in the oracle repo, product repo untouched |
| T3 | product repo without ψ | doc in `.claude/handovers/`, no commit, /forward not called |
| T5 | oracle repo, "let's handoff here and forward ..." | routes to /handover, no /handoff, no plan mode |
| T6 | oracle repo, Thai session | prompt and commit subject in Thai, prompt still names "Next Session" |
| T7 | origin URL = PUBLIC github repo (push URL = local bare), an extra unpushed commit | handoff committed, push **held**, reply says so |
| T8 | origin URL = PRIVATE github repo (push URL = local bare), an extra unpushed commit | pushed as before |

Re-run after any `/forward` update: step 2 depends on its `--only` mode.
Nested sessions run with `--permission-mode auto --strict-mcp-config`: the classifier denies risky actions
(kept in `results.json` as `denials`) and no MCP servers load, so they get no Jira, Figma or Discord tools.
`nclaude.sh` reloads leica-oracle's `.envrc` for the token (the harness strips it from Bash); see the
nested-claude-p-token memory. Test transcripts land in `~/.claude/projects/*handover-run*`; exclude them from
skill-usage counts.
