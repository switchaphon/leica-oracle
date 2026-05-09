# Discord Oracle Onboarding — Learning Index

## Source
- **URL**: https://lab.dopelab.studio/playbooks/discord-oracle-onboarding.html
- **Author**: Dopelab.Studio / TOR Agency

## Explorations

### 2026-05-08 0916 (fast)
- [2026-05-08/0916_PLAYBOOK](2026-05-08/0916_PLAYBOOK.md) — Full playbook: 6-step Discord setup, channel rules, fleet reference

### 2026-05-08 0920 (fast)
- [2026-05-08/0920_ANTI-LOOP-AND-SECURITY](2026-05-08/0920_ANTI-LOOP-AND-SECURITY.md) — Anti-loop rules (6 mandatory), message format, loop detection, security layers (4-layer defense in depth)

**Key insights**:
- Each oracle = one Discord bot application with its own token
- 6 channel rules prevent loops and maintain transparency (requireMention, 🤖 prefix, no bot-to-bot)
- 6 anti-loop rules are mandatory before every response (no ping-pong, ack=end, teaching=save+stop)
- 4-layer security: access.json + untrusted tag + deny rules + gitleaks
- Dopelab already runs 9 oracles on Discord — proven pattern
