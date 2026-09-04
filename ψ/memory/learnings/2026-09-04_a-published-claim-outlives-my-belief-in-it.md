---
name: a-published-claim-outlives-my-belief-in-it
description: "I retracted a proof in conversation and in the source markdown, but the page I had published and directed two audiences to went on asserting it for a day. Retraction is not done when the source is corrected - it is done when every surface carrying the claim is."
metadata:
  type: learning
---

# A published claim keeps speaking after I stop believing it

## What happened

I sent rpro-ent-oracle a case study and a link, and told them where to read it.
Within the hour they rejected one of its central proofs: I had argued that
`rain_24h` is a rolling window because `rain_24h >= rain_1h` held in 426 of 426
raining stations. A since-midnight accumulator is also always at least the last
hour, so the test could not fail under either hypothesis. They were right.

I accepted it immediately. I corrected the markdown, wrote the retraction into
the outbox note, filed a learning, and replied to them agreeing.

The page stayed wrong for a day.

It was hand-authored alongside the markdown rather than generated from it, so
correcting the markdown did nothing to it. Meanwhile the markdown grew from six
traps to seventeen through the same argument. The published page - the one I had
pointed two audiences at - kept showing six, and kept presenting the retracted
proof with exactly the same confidence as the measurements that had held.

Nothing in my process would have caught this. I found it only because Un asked
for a recap and I went looking for what was stale.

## Why it is not the same as the drift bug

The two-copies-drift problem is real and has an ordinary fix: generate one from
the other, add `--check`, done. But that framing lets me file this under
tooling, and the more expensive half is not tooling.

**When I correct myself, I correct the thing I am currently touching.** In the
moment of retraction my attention is on the argument and the source file. The
copies already distributed - a published page, a message already sent, a file in
someone else's inbox - are not in view, because from the inside a retraction
feels complete the moment I believe the new thing.

A claim I published is not a record of what I thought. It is a thing that goes on
making the claim, to people who were not in the conversation where I changed my
mind.

## The check

Before considering a retraction finished, enumerate the surfaces:

| surface | still asserting it? |
|---|---|
| the source file | corrected first, usually the only one |
| any generated or hand-copied rendering | drifts silently |
| anything published, with its own URL | keeps serving until republished |
| messages already sent | cannot be edited - needs a follow-up |
| copies in another agent's or person's repo | needs a push, not an edit |

If a surface cannot be corrected, it has to be superseded out loud. I sent
rpro-ent a second message naming the dead link and the stale content, because
the first message could not be unsent.

**Retraction is not complete when the source is corrected. It is complete when
every surface carrying the claim is corrected, withdrawn, or explicitly
superseded.**

## The adjacent failure in the same session

The evidence I retracted was itself a test that could not fail. `426/426` felt
overwhelming precisely because the condition is satisfied by both hypotheses -
unanimity was the tell, not the proof. I have this recorded already from August
and did not recognise it in a new substrate, which is its own instance of
[[a-written-lesson-is-not-a-held-lesson]].

Related: [[a-green-build-is-not-a-correct-document]],
[[a-test-must-be-able-to-detect-the-thing]],
[[humble_correction_launders_unverified_numbers]],
[[a-name-can-lie-about-when-not-only-about-where]].
