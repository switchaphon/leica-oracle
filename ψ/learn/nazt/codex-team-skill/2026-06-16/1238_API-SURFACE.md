# /codex-team API Surface

## Skill Trigger

```
/codex-team up        # spawn team
/codex-team down      # teardown
/codex-team status    # check all members
/codex-team restart   # fresh start
/codex-team scale N   # show scale template
```

Also triggers on: 'spawn team', 'kill team', 'team status', 'codex coder fleet'

## maw Commands Used

| Command | Form | Purpose |
|---------|------|---------|
| `maw team preflight <path>` | PATH | Check before spawn |
| `maw team up <name>` | NAME | Spawn members |
| `maw team up <name> --only <member>` | NAME | Spawn single member |
| `maw team down <name>` | NAME | Teardown all |
| `maw peek <session>:<member>` | — | View member pane |
| `maw hey <member> "msg"` | — | Dispatch task |
| `maw done <window>` | — | Save WIP + kill |
| `maw ls` | — | List all |
| `maw send-enter <pane>` | — | Force submit stuck input |

## Integration Points

- **gh CLI**: `gh pr list --repo OWNER/REPO --base alpha --state open`
- **tmux**: windows created per member by maw team
- **git worktrees**: one per member, on own branch
- **AGENTS.md + agents/*.md**: Codex reads from project root

## Extension Points

- Charter YAML: add more members → scale
- Engine field: `omx` (codex), `claude` (lead)
- `--only` flag: targeted operations
- `worktree: false`: keep lead on main tree
