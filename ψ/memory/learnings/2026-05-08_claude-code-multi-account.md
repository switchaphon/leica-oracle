# Claude Code Multi-Account Switching

**Date**: 2026-05-08
**Source**: Research session — Un has 2 Max accounts
**Tags**: claude-code, auth, security

## Key Facts

1. **Max plan uses OAuth** (macOS Keychain), not API keys — proxy tools expecting `ANTHROPIC_API_KEY` don't work with Max subscriptions
2. **`.claude/` folder is machine-scoped** — settings, skills, memory, CLAUDE.md all persist across account switches. Only the OAuth token changes.
3. **Claude Code proxy projects** (1rgs, fuergaosi233, agentgateway) solve model routing (use Gemini/GPT through Claude Code), NOT account switching
4. **Native switching** = `claude auth logout` → `claude auth login` — safest, no dependencies
5. **Third-party tools** (claude-swap, CCS) exist but store OAuth tokens in plaintext — unnecessary risk for infrequent switching
6. **No native multi-profile support** — feature request open at anthropics/claude-code#44687

## Pattern

When evaluating third-party auth tools: if the native approach takes 10 seconds and the tool saves you 8 of those seconds but requires trusting a stranger with your OAuth tokens — the native approach wins.
