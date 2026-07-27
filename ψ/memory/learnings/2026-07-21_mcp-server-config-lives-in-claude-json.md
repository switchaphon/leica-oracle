---
title: MCP server registration uses claude mcp add, not settings.json
date: 2026-07-21
source: "rrr: leica-oracle"
concepts: [claude-code, mcp, configuration, jira]
---

## Pattern

Claude Code MCP servers must be registered via `claude mcp add -s user <name> -- <command>`, which writes to `~/.claude.json`. The `mcpServers` block in `~/.claude/settings.json` is NOT picked up.

## Evidence

4 failed attempts editing `settings.json` mcpServers. Env var interpolation (`${VAR}`) doesn't work in the JSON config — values are passed literally. The solution: wrapper scripts in `~/.claude/mcp-scripts/` that source `~/.zshenv` and map custom env var names to the package's expected names, registered via `claude mcp add`.

## Application

When adding any new MCP server:
1. Write a wrapper script if env var mapping is needed
2. Use `claude mcp add -s user <name> -- <script-path>`
3. Verify with `claude mcp list`
4. Restart session for tools to load
