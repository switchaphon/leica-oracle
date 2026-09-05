# A written lesson is not a held lesson -- and "might overflow" is a guess wearing a finding's clothes

**Date**: 2026-08-28
**Context**: RunCat Neo menu bar labels, immediately after writing
[[a-label-that-encodes-data-has-a-source]]
**Gap between writing the lesson and repeating it**: about one hour

## What happened

At 20:50 I wrote a lesson whose corollary was *"read the file, not the match"* -- I had
grepped a file for one variable and missed two lines that answered my next question.

By 21:50 I had done it again, in the same session, on a different repository. The RunCat
Neo source was cloned locally. I grepped it three separate times today (`displayName`,
`snapshot.title`, rename affordances) and each grep returned exactly what I asked for.
None made me read `IndicatorKind.swift`, which contains:

```swift
static let customValueLabelMaxWidth = 80.0          // hard cap on the bar label
case categoryIcon: CGSize(width: 22.0, height: 16.0) // icon, drawn unconditionally
```

Those two constants had been governing the entire task from the first minute.

## The two failures they caused

**1. A guess survived four rounds of revision.** I told the user the new format would be
"roughly 50% wider and might overflow", shipped it, and let him judge it on his own screen.
He said it was too cramped. Reading the source, `Un (Th): 9/17` at 13 characters was very
likely being **clipped** by the 80pt cap -- a defect, not a matter of taste. I had a real
measuring instrument (`screencapture`) and a real constant (on disk) and used neither.

**2. I optimised the smaller half.** Four bar items carry a fixed **88pt** of identical
`staroflife` icon that identifies nothing. The labels I shrank across three rounds went
from ~13 characters to 7. The icons were always the dominant, information-free cost --
exactly what [[macos-menubar-two-line]] recorded on 07-29 -- and I measured them only
after every decision had been made.

## The uncomfortable part

Writing a retrospective changed what I could *recall*. It did not change what I *did*, one
hour later, under mild time pressure, on a task that felt small. Documentation is not a
control; only a changed default is.

## How to apply

- **When a repo is cloned and relevant, read its shape once** -- list the directory, skim
  the small files -- instead of only ever querying it with narrow greps. A grep returns
  what you asked for and silently withholds what you did not think to ask.
- **When a limit plausibly exists, go find the constant** before describing the behaviour.
  "Might overflow" / "should be fine" / "roughly 50% wider" are guesses; if the number is
  on disk, a guess is a choice.
- **"It looks wrong" from a user may be a bug report.** An aesthetic rejection and a hard
  clipping cap produce identical complaints. Ask what the mechanism is before filing it
  under preference.
- **Measure before optimising, and check which half is actually large.** Three rounds went
  into the cheaper half of the width budget.

Related: [[a-label-that-encodes-data-has-a-source]] (the lesson this one failed to hold),
[[macos-menubar-two-line]] (had already recorded the repeated-icon cost),
[[runcat-name-layers]] (where the measured geometry now lives).
