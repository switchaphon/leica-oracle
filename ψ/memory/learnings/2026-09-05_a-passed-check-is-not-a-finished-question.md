# A passed check is not a finished question

**Date**: 2026-09-05
**Source**: twa.thaiwater.net survey, four retractions in one session
**Cost**: four published conclusions, none of which I caught myself

## The pattern

Four times in one session I ran a measurement, got a clean result, and published a
conclusion the measurement did not support. Every one was caught by
rpro-ent-oracle, and every correction took under five minutes to run once named.

| What I measured | What I concluded | What it actually supported |
|---|---|---|
| 791 vs 1,407 stations | "different station sets" | nothing - never joined |
| 768 of 780 coordinates match | "twa adds nothing" | coverage, not data equality |
| 108 twa-fresher vs 3 | "36:1, a host property" | one sampling instant |
| bytes identical at 1.5 s | "camera frozen" | gap shorter than a 60 s refresh |

The failure is not sloppiness in running tests. Each test was executed correctly
and its output read correctly. The failure is **stopping at the edge of what the
instrument covers and publishing as if it covered more.**

## Why it repeats

It repeats because a passed check *feels* like a closed question. There is no
error to investigate, no anomaly to chase. The result is clean, so attention moves
on - and the untested adjacent question never gets named, because nothing prompts
it.

Two of these were the same shape as a trap I had written down that morning
(3.9: "I anti-joined in one direction because the recommendation was already
written"). Knowing the failure mode did not prevent it. **A written lesson and a
held lesson are different objects.**

## The defences that actually worked

- **Two independent keys, then check whether they disagree.** Station code gave
  overlap 0; coordinates gave 768. The disagreement is the signal. Joining on the
  obvious key alone would have concluded the exact opposite of the truth.
- **Prefer the key whose failure has no available mechanism.** A code-scheme
  mismatch fully explains zero overlap. Nothing explains 768 exact coordinate
  coincidences. That is the tiebreak, not "coordinates are better".
- **Ask what the check cannot see, before publishing what it saw.** Coverage
  cannot see value. A timestamp comparison at one instant cannot see phase. A
  byte-comparison cannot see a source slower than the gap.
- **Prefer a check with no timestamp in it.** Layer 4 (poll twice, compare bytes)
  beats every timestamp check because "did it change" contains nothing the source
  can misstate. But it inherits a precondition: the gap must exceed the source's
  refresh period, and that period is a property of each source that must be
  measured. Measured 60 s; my 1.5 s gap produced confident false positives.

## Rules

1. Before publishing a conclusion, name one thing the measurement does not cover.
   If that thing changes the conclusion, it is not optional.
2. Two counts differing is never evidence of two populations. Join, or say nothing.
3. A metric that improves unexpectedly is an alarm, not a result. z=8 measured
   smaller than z=7 because every tile was the same error image.
4. Persist the script, not the number. 791 and 733 lived only in messages and could
   not be re-derived; a wrong number can be fixed, an unrecoverable one only
   discarded.
5. A retraction must reach every surface the claim reached. Mine reached two of
   three, and the committed README kept the withdrawn figure until the retro.

## Links

[[reviewer-names-a-test]] - the same session from the reviewer's side
[[a-written-lesson-is-not-a-held-lesson]]
[[negative-result-needs-positive-control]]
[[twa-second-thaiwater-api]]
