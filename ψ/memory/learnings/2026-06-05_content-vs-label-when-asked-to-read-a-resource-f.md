---
title: Content vs Label — When asked to read a resource for a specific type of content 
tags: [discord, content-vs-label, honest-reporting, patterns-over-intentions, external-urls, dharma, tipitaka, fetch-failures, clarification]
created: 2026-06-05
source: rrr --deep: leica-oracle 2026-06-05
project: github.com/switchaphon/leica-oracle
---

# Content vs Label — When asked to read a resource for a specific type of content 

Content vs Label — When asked to read a resource for a specific type of content (dharma teachings, specs, tutorials), do NOT try to extract the expected content from unexpected data. Report what is actually there, surface the mismatch clearly, and let the human redirect.

Key rules:
1. "Read X for Y" → fetch X, check if Y exists, report both what IS there AND whether Y was found
2. Do not hallucinate expected content just because it was requested
3. When content type is ambiguous (channel messages vs embedded URLs vs attachments), clarify which layer is meant upfront
4. External URLs shared in Discord may be inaccessible from Leica's machine (internal servers, geo-restricted, down) — one attempt, clear failure message, offer alternatives

Connected principle: Patterns Over Intentions (#2) — what the data actually is beats what it was labelled or intended to be.

Today's example: Un asked Leica to "learn the Dharma" from a Discord channel. The channel contained 100 messages of AI agents building a digital Tipitaka database — all technical dev discussion, zero dharma text. Honest report delivered. Un clarified to fetch URL links inside the messages. URLs were ECONNREFUSED from Leica's machine. Honest second report delivered.

Companion learnings from same day:
- DISCORD_STATE_DIR env var silently redirects all config reads (silent config override class of bug)
- maw wake = correct spawn verb, maw workon = defunct (CLI drift after multi-week gaps)
- Goodnight ritual non-negotiable: 26-day gap left 5 learnings uncommitted — institutionsal memory at risk

---
*Added via Oracle Learn*
