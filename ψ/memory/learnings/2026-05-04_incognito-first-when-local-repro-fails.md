# Lesson — Incognito First When Local Repro Fails

**Date**: 2026-05-04
**Session**: 1225_prototype-pages-rebuild-and-incognito-lesson.md
**Confidence**: High (this is the second documented instance of the same trap; first was 09:31 today)

## The Rule

**When a user reports a visual bug you cannot reproduce in your own dev environment, ask them to test in incognito (or with extensions disabled) BEFORE running another code-side diagnostic.**

## Why

Cost asymmetry is enormous. Asking the user to open incognito takes 30 seconds and a single message. Running another round of "let me check the CSS / let me run Playwright at more viewports / let me grep for max-width" costs 5–15 minutes of back-and-forth and produces the same result you got the first time.

When my local evidence and the user's evidence disagree, the diagnostic question is not "is the code correct" — it's "what is different between our environments." Incognito eliminates the most common environment differences in one shot:

- Browser cache / stale CSS / stale JS
- Browser extensions (ad blockers, dark-mode forcers, Grammarly, password managers, accessibility tools)
- Stale service workers
- DevTools state and docking position
- Persistent localStorage that affects layout

If incognito reproduces the bug → environment is ruled out, dig into code.
If incognito fixes it → it was environment, not code. Done in one minute.

## How to Apply

**Decision rule:**

1. First failed local repro at the user's stated viewport → re-run with verbose logging. Fine.
2. Second failed repro → STOP iterating on code-side theories. Send: *"Can you try this in an incognito window? While you're there, note `[innerWidth, innerHeight]` from the console. That'll tell us if this is environment or code."*
3. Only after incognito test should you keep digging in code.

**Phrasing matters:**
- ✅ "Try incognito — takes 30 seconds and rules out cache/extensions"
- ❌ "I cannot reproduce this on my end" *(this is defensive and shifts burden)*
- ❌ "Your browser window must not actually be 1920" *(this is a guess presented as fact)*

## Origin

This session (2026-05-04, 12:25 GMT+7) lost ~45 minutes to a horizontal-scroll / empty-space report on `/prototype/dashboard`. I ran Playwright sweeps across 10 viewports in 2 browsers — all clean. I argued the "browser window not maximized" theory across multiple rounds. The user finally opened incognito themselves; the issue disappeared. Root cause was browser cache or extension state.

The same morning's retro (09:31) had already documented Lesson 6: *"When symptoms don't match where you're looking, inspect outside before tearing your own work apart. A hard reload is a 5-second check that saves 20 minutes."* I had the lesson and didn't apply it. The "hard reload" lesson covered Claude's own dev environment; this lesson covers the **user's** browser, which is the same logic generalized.

## Connections to Past Learnings

- **Supersedes (in scope)** Lesson 6 of `2026-05-04_prototype-layout-and-scroll-discipline.md` — that one was about my browser; this one is about the user's. Same principle.
- **Reinforces** `feedback_verify_production_via_browser.md` — verify via browser, not by reading source.
- **Anti-pattern of** my behavior in this session: producing more local evidence to defend a theory the user has already rejected.

## Test for Whether You're Following This

Next time a user reports a visual bug you can't reproduce after one round of local testing, count the messages before you say the word "incognito." If it's more than two messages from the user's report, you're not applying this lesson.
