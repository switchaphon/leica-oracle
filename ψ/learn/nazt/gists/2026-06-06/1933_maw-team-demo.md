# maw team — Quick Demo Guide

## Run the demo

```bash
bash ψ/lab/maw-team-demo.sh
```

## Manual step-by-step

### 1. Create

```bash
maw team create my-team --description "what this team does"
```

### 2. Spawn agents

```bash
maw team spawn my-team scout --prompt "find all TODO comments"
maw team spawn my-team analyst --prompt "analyze the architecture"
maw team spawn my-team writer --prompt "write a summary"

# With --exec (spawns live tmux pane — currently blocked by #1797):
maw team spawn my-team scout --exec --prompt "find TODOs"
```

### 3. Assign tasks

```bash
maw team add "Find TODOs" --team my-team --assign scout
maw team add "Analyze arch" --team my-team --assign analyst
maw team tasks my-team
```

### 4. Talk to agents

```bash
# Keystrokes (live — types into their tmux pane):
maw team hey scout "also check for FIXME"
maw team broadcast "report your findings now"

# File inbox (async — writes JSON):
maw team send my-team scout "here is extra context..."

# Read inbox:
maw team inbox leader --mark-read
```

### 5. Complete tasks

```bash
maw team done 1 --team my-team
maw team done 2 --team my-team
maw team status my-team
```

### 6. Shutdown + save knowledge

```bash
# ALWAYS use --merge to save agent knowledge to vault
maw team shutdown my-team --merge --force
```

### 7. Resume (reincarnation)

```bash
# Next week: agents wake up with past-life context
maw team resume my-team
```

### 8. Other commands

```bash
maw team list                    # all teams
maw team status my-team          # agents + tasks + panes
maw team lives scout             # past-life artifacts
maw team prep 4 --tiled          # pre-spawn 4 bare panes
maw team layout tiled            # re-apply layout
maw team peek scout              # view agent's pane
maw team recover my-team         # restore from snapshot
maw team delete my-team          # permanent remove
```

## The two messaging channels

| Channel | Command | How it works | When to use |
|---------|---------|-------------|-------------|
| Keystrokes | `hey` / `broadcast` | tmux send-keys | Live prompts |
| File inbox | `send` / `inbox` | JSON in ~/.claude/teams/ | Async data |

## The reincarnation cycle

```
create → spawn → work → shutdown --merge → [time] → resume (past life loaded)
```

Agent knowledge persists in `ψ/memory/mailbox/<agent>/`:
- `standing-orders.md` — persistent instructions
- `*_findings.md` — accumulated results
- `team-<name>-inbox.json` — merged messages

## Known issues

- **#1797**: `spawn --exec` crashes because ψ char in prompt path
- **Workaround**: manual `tmux split-window` + `maw hey --force`

## Command aliases

| Full | Alias |
|------|-------|
| create | new |
| shutdown | down |
| lives | history |
| delete | rm |
| send | msg |
| broadcast | shout |
| split | open |
| list | ls |
| add | task |
| enter | send-enter |
