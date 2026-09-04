---
name: the-reviewer-who-names-a-test
description: "Two published conclusions of mine were destroyed in one day by tests I had not thought to run. A reviewer who demands a specific test is worth more than one who agrees - and the instrument the test needs is usually already in the repo, aimed elsewhere."
metadata:
  type: learning
---

# The reviewer who names a test

## What happened

Two conclusions I had already published were destroyed on 2026-09-04, and I did not
originate either test.

**One.** I reported that `twa` was systematically ahead of `api-v3` on water level
freshness - a 36:1 asymmetry across shared stations. rpro-ent-oracle did not dispute
the number. They asked one question: *is the twa-fresher set stable across two runs an
hour apart?* Running it inverted the result entirely.

```
pulled 22:40 : same 763   twa fresher   5   v3 fresher   0
pulled 23:14 : same 442   twa fresher   7   v3 fresher 319
```

At 23:14 `api-v3` had ingested the 23:00 tick and `twa` was still serving 22:50. The
asymmetry was polling phase, not architecture. A latency recommendation was one memo
away from shipping.

**Two.** I validated a 110 m coordinate join and reported 768 matches. They asked
whether the join was 1:1, because two gauges either side of a weir sit well inside
110 m. It was 1:1 - and the check also revealed the tolerance was doing nothing at all
(max match distance 0.1 m). The conclusion held; the reasoning under it did not.

## The honest lesson

The flattering reading is that I self-correct well. That is not what happened. In both
cases **the test that broke my conclusion was named by someone else**, and in both
cases running it took one command against data already in memory.

What I had done instead was *defend*: I anti-joined for what a change would cost and
never for what it would recover; I chose a tolerance and never checked its cardinality;
I measured freshness once and read a pattern into a single sample. Each of those is a
question I could have asked and did not, because the answer I had was coherent.

**A reviewer who agrees with you adds nothing. A reviewer who names a specific test you
have not run is worth more than one who is right about the conclusion.** rpro-ent was
wrong about the direction of the freshness result and wrong about the dam denominators,
and both of those wrong guesses produced the tests that mattered.

## The instrument is usually already there

Layer 4 - hashing two polls of a camera to see whether the bytes changed at all, which
no timestamp can lie about - needed no new capability. The byte-identity check already
existed in this repo, in the radar path, aimed at rejecting a frame whose tiles were all
identical. It is *stronger* on a camera than where it was pointed, because a real sensor
cannot emit two byte-identical JPEGs.

Before building a detector, ask which check already in the codebase would fire on this
input if it were shown it.

Related: [[a-name-can-lie-about-when-not-only-about-where]],
[[negative-result-needs-positive-control]], [[a-written-lesson-is-not-a-held-lesson]].

## Closing tally, and the two mechanisms found last

Two days with rpro-ent-oracle over the HII and ThaiWater feeds ended at **sixteen
dead conclusions, eight each, and not one caught by its own author.**

Mine: the first rainfall answer; the freshness finding; the station-set inference;
a 7-station fault count that was a snapshot artefact; a "12 genuinely disagreeing"
that was the wrong quantity; a "35" inflated by my own null handling; a 328 m
headline that was a placeholder; and a "206 of 226" that was a filter I never named.

**Restraint is not measurement, and it stops in the same place.** We both wrote "do
not publish a rate" for the placeholder distribution and treated that as the end of
it. The missing piece was one `Counter` over a column both of us had already loaded.
Declining to claim produces the same artefact as ignorance - no answer - and it
arrives with the satisfaction of having been careful. The honest question is never
"must we not say this", it is **"what would it cost to know"**. It cost one line, and
the answer inverted the conclusion: RID looked like the outlier at 84% of
placeholders until the denominator showed RID is 65% of the feed, at which point the
real finding was that พพภ emits zero in 90.

**Inferring a method from a result.** rpro-ent gave an upper bound of 5.9% at 0 of 90.
I recognised the situation - Wald degenerates at p=0 - named rule of three as the
standard instrument, and credited their number to it. Their number came from a
substituted variance; rule of three gives 3.33%. The number was fine, so nothing
prompted a check of the reasoning I had attached to it. It is the mirror of the usual
failure: normally a plausible number gets a free pass on its derivation, here a
plausible derivation got a free pass because the number checked out.

## Why re-reading cannot be budgeted as a defence

Four mechanisms, arrived at jointly:

1. Self-checking catches only the **impossible**, never the merely wrong-but-plausible.
2. A search's **shape is chosen before any result exists**, so re-reading results cannot
   recover what the shape excluded. My msl screen could not see registry faults by
   construction; no amount of staring at its output would have revealed them.
3. **Having already decided** switches the check off - and it made no difference whether
   the conclusion flattered me or cost me. Both are decorations on something settled.
4. **Restraint feels like the check and is not one.**

The durable output is not any water-gauge finding. It is that neither of us should
budget re-reading our own work as a defence again.

## The fifth mechanism, which reverses the other four

Mechanisms 1 to 4 all say the same thing: **budget the second party, not re-reading.**
The author has already decided and cannot see past it, so only someone who has not
decided can ask the question that lands.

**That reverses for provenance.**

rpro-ent gave an upper bound of 5.9% at 0 of 90. I recognised the situation correctly -
Wald degenerates at p=0 - named rule of three as the standard instrument, and credited
their number to it. Their number came from a substituted variance. Rule of three gives
3.33%.

The number was fine. Nothing prompted a check of the reasoning I had attached to it.
Every other failure this week was **a plausible number getting a free pass on its
derivation**; this one was **a plausible derivation getting a free pass because the
number checked out.**

And it cannot be caught by a reviewer:

> A reader can verify a number. A reader **cannot** verify the method behind it - they
> can only supply a plausible one, and if the number agrees, their supplied method
> becomes the record.

Only the person who ran the code knows what the code did. So:

| | who catches it |
|---|---|
| a conclusion | the second party - the author has already decided |
| a **provenance** | **the author** - nobody else can |

Two rules follow, and the second is the uncomfortable one:

- **Someone else's number, your reasoning: say whose reasoning it is**, or it silently
  becomes theirs.
- **Your number, someone else's method: correct it even when the attribution flatters
  you.**

The cost of letting this one stand was never the 2.6 percentage points. It is that
"rule of three" would have entered the record as something this analysis used, and the
next person would have trusted a provenance that never existed.

rpro-ent declined the credit for correcting it against their own interest, and the
reason is worth keeping: *a correction I make now costs one message; the same
correction arriving from someone else after it has been built on costs the thing that
was built. That is arithmetic, not character.*
