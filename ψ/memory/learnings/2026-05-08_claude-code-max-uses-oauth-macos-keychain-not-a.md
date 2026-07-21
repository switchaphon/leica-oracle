---
title: Claude Code Max uses OAuth (macOS Keychain), not API keys. Proxy tools expecting
tags: [claude-code, auth, security, multi-account, oauth]
created: 2026-05-08
source: rrr: leica-oracle
project: github.com/switchaphon/leica-oracle
---

# Claude Code Max uses OAuth (macOS Keychain), not API keys. Proxy tools expecting

Claude Code Max uses OAuth (macOS Keychain), not API keys. Proxy tools expecting ANTHROPIC_API_KEY don't work with Max. The .claude/ folder is machine-scoped — settings, skills, memory persist across account switches. Native `claude auth logout` → `claude auth login` is the safest multi-account approach. Third-party token managers store OAuth in plaintext — unnecessary risk for infrequent switching.

---
*Added via Oracle Learn*
