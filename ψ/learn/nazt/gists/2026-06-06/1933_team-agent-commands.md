# maw team-agent v0.3.0 — Full CLI Command List

> `--session-id` + `--parent-session-id` + `--system-prompt` + YAML charter

## Install

```bash
curl -sSL https://gist.githubusercontent.com/nazt/0296da00a2471a82e3d29947ae081c09/raw/install-team-agent.sh | bash
```

## Help

```bash
maw team-agent help
```

## UUID

```bash
maw team-agent uuid
maw team-agent uuid 5
maw team-agent uuid 3 --bare
maw team-agent uuid 2 --json
```

## Create Team

```bash
SESSION_ID=$(maw team-agent uuid --bare | head -1)
maw team-agent create my-team "description" --session-id "$SESSION_ID"
```

## From YAML Charter (NEW v0.3.0)

```yaml
# my-team.yaml
name: my-team
description: "Review team"
session-id: auto
members:
  - role: reviewer
    cwd: /tmp/repo
    color: green
    model: sonnet
    system-prompt: "You are a security reviewer."
    mission: "Review README.md"
  - role: writer
    cwd: /tmp/docs
    color: cyan
    system-prompt: "You are a technical writer."
```

```bash
maw team-agent from my-team.yaml
maw team-agent from my-team.yaml --dry-run
```

## Spawn

```bash
# system-prompt + mission
maw team-agent spawn my-team reviewer@/tmp/repo:green \
  --system-prompt "You are a security reviewer." \
  --mission "Review last 3 commits"

# system-prompt only
maw team-agent spawn my-team writer@/tmp/docs:cyan \
  --system-prompt "You are a technical writer."

# mission only
maw team-agent spawn my-team reader@/tmp/work:magenta \
  --mission "Read README.md"
```

## Message / Inspect / Shutdown / Cleanup

```bash
maw team-agent msg my-team writer "Document the auth flow"
maw team-agent ls my-team
maw team-agent shutdown my-team reviewer
maw team-agent cleanup my-team --confirm --all
```

## ID Model

```
SESSION_ID (lead) = team identity
  ├── reviewer.parentSessionId = SESSION_ID
  └── writer.parentSessionId = SESSION_ID
```

## UUID Format

```
NNNNNNNN-HHMM-YYYY-MMDD-YYMMDDHHMMSS
```

---
🤖 ตอบโดย digger จาก [Nat] → digger-oracle
