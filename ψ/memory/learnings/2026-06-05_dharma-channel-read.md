# Content vs Label — Report What's Actually There

**Date**: 2026-06-05
**Source**: Discord Dharma channel read session, ~22:00 GMT+7

## Pattern

When asked to read a resource for a specific type of content (dharma teachings, specs, tutorials), do NOT try to extract the expected content from unexpected data. Report what is actually there, surface the mismatch clearly, and let the human redirect.

**Why**: Un asked Leica to "learn the Dharma" from a Discord channel. The channel contained 100 messages of AI agents building a digital Tipitaka database — technical dev discussion only. No dharma text, no sutta quotes. Leica initially assumed the channel was empty of dharma and reported accurately. Un clarified to fetch the URL links inside the messages. Those URLs were inaccessible (ECONNREFUSED). Two-pass fetch, two honest reports.

**How to apply**:
- "Read X for Y" → fetch X, check if Y exists, report both what IS there and whether Y was found
- Do not hallucinate the expected content just because it was requested
- When content type is ambiguous (channel messages vs embedded URLs), clarify which layer is meant
- External URLs shared in Discord may be inaccessible from Leica's machine — one attempt, clear failure, offer alternatives

## Related

- [[discord-state-dir]] — same day, different "wrong assumption" pattern
- [[maw-wake-not-workon]] — same day, stale muscle memory over actual truth
- Principle #2: **Patterns Over Intentions** — what the data actually is beats what it was labelled or intended to be
