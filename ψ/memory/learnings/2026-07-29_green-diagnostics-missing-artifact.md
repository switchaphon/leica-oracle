# When every diagnostic is green and the artifact is still missing, the constraint is outside your process

**Date**: 2026-07-29
**Repo**: leica-oracle
**Discovered while**: building TwoLineBar, a two-line menu bar readout for 5 Claude tokens

---

## The situation

Five status items created from five JSON files. One — `por` — was not on screen.
Every reading from inside the app said it was healthy:

```
[twolinebar] files=6 loaded=5 [kla,por,trio,tul,un]
[twolinebar]   runcat-por.json visible=true len=-1.0 img=53x22 frame=532.0
```

`isVisible = true`. A valid 53×22 image. A plausible frame at x=532. No exception, no
warning, no nil. The item existed by every measure the process could take — and it was
not rendered.

## The cause

macOS gives the menu bar to the frontmost app's menu titles first, and silently drops
the **leftmost** status items when those titles grow into their space. iTerm2 has nine
menus (`iTerm2 Shell Edit View Session Scripts Profiles Window Help`) running to about
x=530. `por` sat at 532.

The compositor's decision is not exposed to the owning process. `isVisible` reports
what *I* asked for, not what the window server did with it.

## The test that broke it open

```bash
osascript -e 'tell application "Finder" to activate'   # 3 menus instead of 9
```

`por` appeared instantly. Two seconds, and it relocated the bug from my code to the
environment.

## The generalisation

**Instrumentation reports the inside of your process. When the inside is uniformly
healthy and the outside artifact is still wrong, adding log lines cannot reach the
cause — change something in the environment and observe the delta.**

The failure mode is recursive instrumentation: each green reading feels like progress
while narrowing toward a place the answer is not. The exit is a controlled change to a
variable outside the process — a different frontmost app, a different display, a
different user, a different terminal — and watching whether the symptom moves.

Related shape: [[negative-result-needs-positive-control]] — an absence you cannot
explain is not evidence until you prove your instrument can detect a presence.

## Corollaries from the same session

- **A single-line API is not a single-line medium.** `NSStatusItem.title` is a `String`,
  so RunCat Neo's `metricsBarValue` truncates `"AA\nBB"` to `A…`. Drawing an `NSImage`
  instead lifts the limit entirely. Find which *layer* imposes a constraint before
  accepting it as the platform's.
- **Repeated identical decoration is not free.** Five copies of the same `staroflife`
  glyph cost 65pt of a contested shared budget and identified nothing the token name
  did not. Removing them fixed the overflow *and* improved the readout.
- **Command Line Tools build real macOS apps.** `swiftc` + AppKit + a hand-written
  `LSUIElement` Info.plist + `codesign --sign -` is a complete menu bar app. The
  Xcode-only gates are exactly `xcodebuild` and `actool`.

## Cost

~15 minutes of confident, useless logging before switching apps.
