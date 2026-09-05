# A label that encodes data has a source -- find it before you build a table

**Date**: 2026-08-28
**Context**: Renaming RunCat Neo's Claude usage cards
**Cost**: two implementations built and discarded, four rounds of the user's attention

## What happened

Un asked for card names with a parenthetical suffix. Round one: `Un (Th)`. Round two:
`Un (Thu/10PM)`. Both times I built a hand-maintained dict mapping token key -> full
display string, and both times I asked him to supply the suffix for accounts he had not
named yet.

The suffix was the account's rate-limit reset time. The statusline payload had been
carrying it the entire time as `rate_limits.seven_day.resets_at`, a Unix timestamp.
`~/.claude/statusline-command.sh` already parsed it on lines 49 and 51 -- **a file I had
grepped earlier in the same session**, looking for `CLAUDE_TOKEN_NAME` on line 234.

Once derived instead of stored, the hand-kept table shrank from four full display strings
to four nicknames, the two accounts I had no data for filled themselves in correctly, and
the value stays right forever without maintenance.

## The tell

A day of the week could be a human label. A day **and an hour** could not. `10PM` is
rendered machine output, and rendered output has a producer.

Generalised: **when a requested string contains something that looks computed -- a
timestamp, a percentage, a count, a version, an ID -- treat it as a view of existing data
until proven otherwise.** The question is not "what should this say" but "where does this
already come from".

## What I should have asked, in minute one

> "What does `(Th)` mean?"

One question. The answer names the source, the source kills the table.

I never asked, because the request was answerable without asking. That is the trap:
*matching* the request is not *understanding* it, and a request you can satisfy without
understanding is exactly where you build the wrong mechanism confidently.

## Corollary -- read the file, not the match

I had `statusline-command.sh` open and grepped it for one variable name. Two lines that
answered my next question were 180 lines above the hit and I never saw them. When a file
is small enough to read, a targeted grep is a way to miss things. Same failure family as
[[rtk_mangles_strings]]: a narrow instrument returning exactly what you asked for, while
the thing you needed sits outside the query.

## How to apply

Before writing any lookup table of display strings, ask of each value: *is any part of
this derivable?* If yes, derive it -- a derived value cannot drift, cannot go stale, and
needs no entry for cases you have not seen yet. Reserve hand-kept tables for what is
genuinely arbitrary. Here that was exactly four nicknames.

Related: [[runcat-name-layers]] (what the mechanism became),
[[trio-account-cancelled]] (a same-session cousin: an acceptance test that proves format
while the thing it checks is dead).
