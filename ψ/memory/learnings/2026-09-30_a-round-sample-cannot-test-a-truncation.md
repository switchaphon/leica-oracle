---
name: a-round-sample-cannot-test-a-truncation
description: "I verified the RunCat reset format against a real 7d timestamp that was exactly on the hour. The format drops minutes, so that check could not fail. The 5h row, same formatter, read 4PM for a 16:40 reset. Test a lossy transform on an input that contains what it could lose."
metadata:
  type: learning
---

# A round sample cannot test a truncation

## What happened

On 2026-08-28 I put reset times on the RunCat Neo card rows with `%a/%-I%p` and wrote into memory:

> Verified against a real payload 2026-08-28: `seven_day.resets_at = 1788447600` resolves to
> `Thu 03 Sep 2026 22:00` -> `Thu/10PM`, matching what Un independently reported.

True in every word. `1788447600 / 3600 = 496791` exactly: the timestamp is on the hour.
`%-I%p` drops minutes, and on an input with no minutes it drops nothing. The check passed
because the sample was the one kind of input the format cannot damage.

The same `reset_suffix()` formats the 5h row. On 2026-09-30 Un asked for `day/hh:mm`. After
the one-line change to `%a/%H:%M`, this session's own statusline rewrote `runcat-kla.json`:

```
14:41     5h (Wed/4PM): 35%     <- old format
14:42:53  5h (Wed/16:40): 36%   <- same window, new format
14:49:25  5h (Wed/16:40): 36%   <- next write, stable: the window's reset, not jitter
```

The 5h reset was at 16:40, and the row had said `4PM`: 40 minutes early today, and up to 59
minutes early on any 5h window that did not start on the hour. Nobody reported it. `4PM`
looks exactly like a complete time.

## Why it happened

**The check had no power against the defect.** A truncating transform is lossless on aligned
input, so an aligned sample is the same as no test. This is
[[negative-result-needs-positive-control]] moved from "is it absent?" to "is it lossless?".
The question that would have caught it: what would a broken formatter print for this sample?
Answer: exactly what a working one prints. That answer is the signal to change the sample,
not to accept the result.

**I verified a caller and credited the function.** One formatter, two input populations. The
two 7d resets I have seen at full precision were both on the hour (n=2: `1788447600`, and
kla's `Wed/05:00` today). The one 5h reset I have seen at full precision was not, and one
counterexample is enough to say the 5h series is not hour-aligned. I chose the 7d sample
because it came with Un's independent report, a free answer key. The free answer key
selected the one field where the bug could not show.

**Nothing downstream could catch it.** A truncated time passes every check a whole one
passes. Commit `3606452` (2026-09-05) is the same shape: a JPEG cut at the 400,000-byte read
cap "begins exactly like a whole one", so the magic-byte check passed three half-rendered
frames. Two silent truncators in one month, each invisible to any check that looks only at
whether the output is well-formed.

## How it was found

Not by reasoning. I read `%-I%p` at 14:40 and saw a style to replace, not a defect. It
surfaced only because the session's token was `kla`, its statusline rewrites
`runcat-kla.json` every turn, and I read that file after the edit to prove the edit worked.
Had the request been `day/hh`, the error would have shipped intact under a new format.

## What to do instead

- **Test a lossy transform on an input that contains what it could lose.** Time format: a
  non-zero minute, midnight, noon. Cap: cap + 1. Rounding: a value on the half. If the
  sample is round, the test is decoration.
- **Verify per input population, not per function.** When one function serves several
  fields, sample each field's real data. The field that comes with an answer key picks
  itself; pick the other one too.
- **After the synthetic green, read the live output as an audit.** Synthetic inputs prove
  the code does what I meant. Only live data shows what the world sends. Today the live read
  was a victory lap that happened to be the audit. Make it the audit on purpose.
- **Treat a display format as a precision claim.** `4PM` reads as "at four", not "some time
  in the four o'clock hour". If the data has minutes and the format does not, the display
  asserts something false.

Related: [[runcat-name-layers]], [[rtk-mangles-strings]], and
`2026-09-05_a-passed-check-is-not-a-finished-question.md` (a check's coverage ends at its
instrument; this is the case where the instrument was the sample).
