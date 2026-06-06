# Nat's Gists — Learning Index

## Source
- **Author**: nazt (Nat)
- **GitHub**: https://gist.github.com/nazt

## Explorations

### 2026-06-06 1933 (batch — 13 gists)

#### Hermes Agent
- [[2026-06-06/1933_hermes-agent_OVERVIEW|Hermes Agent Overview]] — what hermes-agent is
- [[2026-06-06/1933_hermes-agent_API-SURFACE|API Surface]] — full API docs (~21KB)
- [[2026-06-06/1933_hermes-agent_ISSUES-COMMITS|Philosophy via Issues+Commits]] — project history analysis
- [[2026-06-06/1933_hermes-agent_TESTING|Testing Patterns]] — test structure
- [[2026-06-06/1933_hermes-mcp-big-picture|Hermes MCP Big Picture]] — fat agent -> thin tool provider

#### Maw & Team Agents
- [[2026-06-06/1933_maw-tmux-claude-field-guide|CLI Field Guide]] — maw, tmux, claude operator's guide (~18KB)
- [[2026-06-06/1933_maw-cli-cheatsheet|Maw CLI Cheatsheet]] — team, swarm, worktree, peek, federation
- [[2026-06-06/1933_cli-reference-team-agents|8 CLI Flags for Team-Agents]] — protocol reference for spawn
- [[2026-06-06/1933_team-agent-commands|Team-Agent Commands]] — quick command reference
- [[2026-06-06/1933_maw-team-demo|Maw Team Demo]] — agent reincarnation engine lifecycle
- [[2026-06-06/1933_maw-team-demo.sh|Maw Team Demo Script]] — shell demo
- [[2026-06-06/1933_install-team-agent.sh|Team-Agent Installer]] — one-shot curl installer (~140KB)

#### Multi-Agent Coordination (Book + Guides)
- [[2026-06-06/1933_book-fleet-as-team|The Fleet As Team (Book)]] — cross-session multi-agent coordination (~39KB)
- [[2026-06-06/1933_spawn-send-roundtrip|Spawn/Send Roundtrip]] — every step of message going out and back
- [[2026-06-06/1933_manual-spawn-stepbystep|Manual Spawn Step-by-Step]] — doing team-agents by hand

#### Comparisons & Analysis
- [[2026-06-06/1933_four-systems-compared|Four Systems Compared]] — openclaw vs hermes vs maw-js vs claude channels
- [[2026-06-06/1933_thclaws-oracle-backlog|THClaws Oracle Backlog]] — book backlog convergence narrative
- [[2026-06-06/1933_thclaws-oracle-summary|THClaws Oracle Summary]] — human-readable summary

### 2026-06-06 1806
- [[2026-06-06/1806_MAW-TOKEN-DEEP-DIG|maw token — CLI plugin deep dig]]

**Key insights**:
- Nat is building maw — the multi-agent orchestration CLI for Claude Code
- Hermes is the message bus; maw wraps it as CLI. Key pivot: hermes MCP went from fat agent to thin tool provider
- "The Fleet As Team" is a 39KB book on cross-session multi-agent coordination — essential reading
- Team-agent spawn protocol: 8 CLI flags control lifecycle (--name, --repo, --prompt, --timeout, etc.)
- `maw token` manages OAuth tokens + .envrc across 47+ oracles via GPG-encrypted `pass` vault
