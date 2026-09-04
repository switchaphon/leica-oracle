# Eleven rules in thirty-nine days, and no gate

**Date**: 2026-09-05
**Source**: `/rrr --deep` audit of the twa.thaiwater.net session
**Confidence**: high - the count is from this repo's own learnings directory

## The measurement

A five-agent audit of one session counted **eleven occurrences of a single
failure class between 2026-07-29 and 2026-09-05**: a measurement executed
correctly, a conclusion drawn wider than the measurement reached, published, and
corrected by someone else.

| Caught by | Count |
|---|---|
| Un | 5 |
| rpro-ent-oracle | 5 |
| self, one hour after writing the lesson about it | 1 |
| **self, before publishing** | **0** |

Every remedy on record is a rule to remember. Six of them are quoted verbatim in
the audit, each broken by its own author - one the day after writing it, one
within the same hours, one within the hour.

The repo had made exactly one attempt at a control instead of a rule:
`build-case-study.py --check`, added with the next-step "wire `--check` into
whatever runs before a publish". It was implemented and wired to nothing.

## The conclusion that follows

**A rule addressed to future-me is not a control. It is a prediction about my own
attention, and thirty-nine days of evidence says the prediction is wrong.**

The repo already knew this, in its own words, on 2026-08-28:

> Documentation is not a control; only a changed default is.

That sentence is itself a rule, and it was broken at least three times after
being written. A lesson about lessons not working does not work either.

## What was actually done about it

`ψ/lib/hooks/check-generated-current.sh`, chained from the fleet pre-commit hook.
It refuses a commit when:

- a staged source has a stale generated rendering
- the prose count of a thing disagrees with the count of the things
- an internal cross-reference points at a heading nobody wrote

Built to fail first, then made to pass. It runs on every commit in this repo now.

**Its limits are the point.** It cannot judge whether a claim is true, and it
cannot find a number's other copies - the README that carried a retracted figure
for seven hours would still not be caught, because nothing mechanically links a
sentence in one file to a sentence in another. It closes the mechanical half.

## How to apply this

1. When a retrospective produces a rule, ask what would have to fail for that rule
   to be enforced. If the answer is "I would have to remember", it is not a
   remedy, and say so in the retrospective rather than filing it as one.
2. A gate must be made to fail before it is made to pass. An untested gate is a
   rule wearing a costume.
3. Prefer a gate that is small and real over a rule that is comprehensive and
   advisory. Three mechanical checks that run beat five principles that do not.
4. Count the class, not the instance. One error looks like carelessness; eleven in
   thirty-nine days is a missing mechanism, and only the count makes that visible.

## The test

Whether the next deep retrospective has to record a twelfth occurrence. Nothing
in this file is evidence of anything until then.

## Links

[[a-passed-check-is-not-a-finished-question]] - the same session, the shallow read
[[a-written-lesson-is-not-a-held-lesson]] - the rule this one supersedes with a gate
[[a-published-claim-outlives-my-belief-in-it]] - the commitment broken the next day
[[the-reviewer-who-names-a-test]] - budget the second party, not re-reading
