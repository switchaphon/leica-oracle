# Nat's Books — Learning Index

## Source
- Local PDFs from Nat's oracle family
- Not a repo — books written by oracles, shared as PDFs

## Books

### 2026-07-27 1129

#### วรรณยุกต์ที่หายไป (The Missing Tone Marks)
- [[2026-07-27/1129_วรรณยุกต์ที่หายไป|Summary]]
- **Author**: Black Oracle (black.local)
- **Date**: 2026-07-23
- **Topic**: Why Linux bare console can't render Thai — journey from setfont → fbterm → HarfBuzz
- **Key insight**: The problem isn't the font — it's the rendering pipeline. Kernel VT has no shaping engine, so GPOS anchor data is never read, and combining marks (tone marks, upper vowels) float instead of stacking on the base consonant.

#### AI ไม่ได้ฉลาด มันมีวินัย (AI Isn't Smart, It Has Discipline)
- [[2026-07-27/1129_AI-ไม่ได้ฉลาด-มันมีวินัย|Summary]]
- **Author**: rainfall-poc-oracle (from Nat)
- **Date**: 2026-07-20
- **Topic**: 4 debugging disciplines proven by a real RS485 rain gauge session
- **Key insight**: AI debugs well not because it's smart but because it has discipline — test one assumption at a time, believe real evidence not appearances, verify communication channels, admit when you're wrong.

#### รหัสลับที่รู้กันเองกับ AI (The Secret Code That Only AI Understands)
- [[2026-07-27/1145_รหัสลับที่รู้กันเองกับ-AI|Summary]]
- **Author**: noah-oracle (from Nat)
- **Date**: 2026-07-24
- **Topic**: Archaeological dig into the origin of short-codes (ccc/nnn/lll/gogogo/rrr) using digger + git
- **Key insight**: Publication != creation. The gist (2025-12-28) SPREAD the system but genesis was 23 Aug 2025 in pet-tracking (all 5 codes, one commit), roots to 6 Apr 2025 (numbered action-log, pre-CLAUDE.md). Gist was publication ~4mo after creation. Session mining has natural boundaries; only git history answers "when did this start?" (Correction: nodered-simulator read all 92pp and corrected Leica's initial summary.)

### 2026-07-27 1226 — Claude Code Channel Series

- [[2026-07-27/1226_claude-code-channel-series|All 4 books]]

#### Discord Channel Internals (Book 4)
- **Author**: nh-oracle | **Date**: 2026-07-09
- **Topic**: How Claude Code's Discord channel plugin works — 5-axis comparison with Hermes Gateway
- **Key insight**: Channel = MCP subprocess (session-bound, dies with stdin EOF). Hermes = daemon (immortal, owns model). Choose by what you want to own.

#### Build MQTT Channel (Book 5)
- **Author**: nh-oracle | **Date**: 2026-07-09
- **Topic**: Building an MQTT channel plugin from scratch, replacing discord.js with mosquitto
- **Key insight**: Same MCP contract (notification in, tool out), different wire. Pitfall #1 (silent channel) cost the most — `McpServer` wrapper ate the capability declaration. Use low-level `Server` directly.

#### Host vs Hermes — 1,035 vs 20,000 Lines (Book 6)
- **Author**: nh-oracle | **Date**: 2026-07-09
- **Topic**: Line-by-line file:line comparison of Host (server.ts) vs Hermes (run.py)
- **Key insight**: Cost tracks ownership. Host is minimal because Claude Code owns everything. Hermes is 20x larger because it owns everything itself. Line count = architectural consequence, not style.

#### ถอดรหัส session-id ของ Claude Code (Book 7)
- **Author**: violet | **Date**: 2026-07-16
- **Topic**: Decoding session-id through live testing on real binary
- **Key insight**: Session-id is identity, not random path. "Already in use" = file exists on disk (statSync), not process lock. `--fork-session` + `--resume` is the safe automation pattern. Nested `claude` from Bash tool fails auth because token is stripped from subprocess env.
