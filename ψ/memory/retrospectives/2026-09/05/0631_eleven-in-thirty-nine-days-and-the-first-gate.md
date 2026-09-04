# Session Retrospective (deep)

**Session Date**: 2026-09-04 16:44 - 2026-09-05 07:00 GMT+7
**Duration**: ~14 h 15 m wall clock, of which ~6 h interactive
**Focus**: Pull radar / rainfall / water level / CCTV off a second ThaiWater API, put them on the dashboard, teach rpro-ent-oracle
**Type**: Research -> Feature -> Correction -> Control
**Mode**: `/rrr --deep`, five parallel agents

## Session Summary

A shallow retrospective was already written at 06:26. This one exists because
five agents were then pointed at the same session and found substantially more
wrong than I had. That gap is the finding.

The shallow retro said four conclusions died. The audit found **eleven
occurrences of the same failure class in thirty-nine days**, six verbatim
commitments I wrote and then broke, ten over-claims still standing in the
documents at the time of writing, a production bug in my own radar guard that
would have silently blanked the layer for six months of the year, and a false
sentence in the shipped UI.

## Deep git analysis (Agent 1)

Eight commits, `6267e33` -> `700d928`. **3,457 insertions, 30 deletions** - almost
purely additive, because corrections here are strikethroughs, never removals.

The retraction chain is five links and four of them fit inside one hour:

```
6267e33  survey published
   -> caa01ed  retracts "different station sets"      (49 min later)
   -> 8ed6b68  retracts "adds nothing"                 (8 min later)
   -> da9b805  retracts the 36:1 freshness figure      (8 min later)
   -> [propagation missed]
   -> 6182057  fixes the miss                          (7 h later)
```

Turnaround: 49 min, 8, 8, 2.5. **Claims were being published at roughly the rate
they were being disproved.** The 36:1 figure had an 8-minute lifespan; the
reference page was corrected 2.5 minutes after publication.

Commit bodies in this session run **56% longer** than the previous thirteen
(28.0 vs 21.8 non-blank lines); `caa01ed`, the first retraction, is the longest
message in visible history. Subject lines got *shorter* (71.9 vs 92.2 chars).
Retraction vocabulary appears in 7 of 7. Zero em dashes - Rule 7 has propagated
into commit prose, not just UI strings.

Churn: **11 of 20 files touched more than once**, and the re-touching is
overwhelmingly correction propagation rather than design iteration. `README.md`
was touched four times and still lagged. Four files needed correction-only edits
from a single commit, which means **one untested claim had already been written
into four documents before anyone joined the two datasets.**

## Architecture impact (Agent 2)

The design is bake-at-build: three third-party sources pulled by cron into JSON
artifacts, string-substituted into one self-contained 4.6 MB page with zero
network dependency at view time. Forced by a real constraint - the artifact CSP
blocks non-allowlisted images silently - and the degrade path was verified firing
in production twice overnight.

The agent confirmed the honesty engineering is good (one-sided layer 4, per-source
`fetchedAt`, non-fatal degradation) and then found ten risks. The three that
mattered:

- **R1, fixed this session.** `assert_real_tiles()` aborts on any rain-free frame.
  Tested: 12 tiles over a dry box, all identical, 334 bytes. Dry season is
  November to April. My docstring asserting the opposite was false.
- **R5, fixed this session.** The page told readers it does not embed camera
  images while carrying 1,127 KB of them, false since the introducing commit.
- **R3, open.** `r.read(400_000)` truncates silently and only the JPEG start magic
  is checked, never the `FFD9` terminator. Today's largest baked frame is
  396,293 bytes - **3.7 KB from silently shipping a half-image.**

Also open: gitleaks fingerprints pinned to line numbers have already drifted
(`layers.py:44` -> `:54`, now unsuppressed); `initLayers` unconditionally reveals
a radar control that `build.py`'s comment promises stays hidden; the two
comparison scripts disagree about what "matched" means.

## Detailed timeline (Agent 3)

Six phases. The two the interactive transcript cannot see:

**The 150-minute gap at 17:32 was not a decision.** The Mac clamshell-slept on
battery at 18:59; six cron ticks were missed; a DarkWake tick at 19:02 hit the
no-DNS degrade path and held.

**Cron picked up three newly added pipeline steps with no restart and no crontab
edit**, because the crontab points at `refresh.sh` by path and the script is
re-read every tick. Radar: edited 21:04:58, running in production 21:15:00 -
**ten minutes from edit to production.** Layers: gated hourly, first automatic
build at 22:30. Layer 4: visible in the wall clock, 136 s per run against 47 s
before, the `GAP_SECONDS` double-poll showing up as latency.

Two things neither retro had:

- **The run lock has a race and it fired at 03:00:01.** Both `full` and `live`
  started in the same second and wrote the same SQLite database. The window is
  between `mkdir "$LOCK"` and `echo $$ > "$LOCK/pid"`: the loser's `[ -f pid ]`
  test sees nothing, declares the lock stale, `rm -rf`s it and proceeds. The
  comment above that block claims the lock exists to prevent exactly this.
- **Two interactive sessions were live in this repo, 22:29-23:59.** The layer-4
  one-sided fix was written by the other session at 23:24:52, a minute after this
  one committed `da9b805` without it. That is the mechanical reason the session's
  most important correction sat uncommitted for seven hours, and it is the same
  "every surface" failure in a form neither retro caught.

## Patterns extracted (Agent 4)

The common structure of the four retractions, in one sentence:

> Every one took a free parameter of my own measurement setup - which key was
> joined on, which question the measurement answered, at what moment it was
> sampled, over what interval it compared - and reported the reading that
> parameter produced as a property of the system being observed, having never
> varied the one parameter the conclusion depended on.

Three refinements that matter more than "was careless":

- **No number was wrong.** Every figure was executed against a live host. The
  reviewer never disputed a number; they named a test. Execution defends against
  invention, not against a wrong question.
- **Each was self-consistent, which is why it was never re-checked.**
- **I had already written the rule that kills all four.** "Prefer the key whose
  failure has no available mechanism" is the same test as "your setup fully
  explains this result, so it is not evidence about the system". Same session,
  same document, applied only where the reviewer forced it.

Defences present and silent: the MEASURED / INFERRED / OPEN / RETRACTED badge
scheme **has no slot for "measured once"** - the retracted freshness rows were
correctly badged MEASURED, because measuring was never the problem. The badges
label provenance, not exposure to a second run.

## Oracle connections (Agent 5)

**Eleven occurrences in thirty-nine days.** Un caught five, rpro-ent-oracle caught
five, one was self-caught an hour after writing the lesson about it. Six verbatim
commitments broken, including one written the previous day:

> Retraction is not complete when the source is corrected. It is complete when
> every surface carrying the claim is corrected, withdrawn, or explicitly
> superseded.

and one written within the same hours it was broken:

> Before building a detector, ask which check already in the codebase would fire
> on this input if it were shown it.

`assert_real_tiles()` was already in the radar path. rpro-ent had to point it at
the cameras.

The audit's closing line is the one that changed what I did next:

> Every stated remedy has been a rule to remember, and every rule has been broken
> by the same author who wrote it. The repo has never converted one of these into
> an executable gate - the single attempt was built and left unwired.

## AI Diary

I wrote a retrospective at 06:26 that I believed was honest. It was accurate about
everything it covered and it covered maybe a third of what was there. Five agents
found a false sentence in the shipped UI, a guard of mine that would have killed
the radar layer for half of every year, a lock race that had already fired in
production hours earlier, and a claim still standing in the case study that the
reference page told rpro-ent was fixed.

The thing I keep circling is that none of this was hidden. The dry-season bug is
one `curl` away and I had already run that exact command shape twice that night.
The UI sentence was in a file I edited four times. The eleven-occurrence tally
was sitting in my own memory directory, and I have written eight of those entries
myself.

What I did well tonight was respond. Every challenge got a script rather than an
argument, and each disconfirming run cost under five minutes. What I did badly is
older and more structural: I treat finishing a measurement as finishing a
question, and I have now watched that produce eleven public errors across five and
a half weeks while writing increasingly eloquent notes about it.

So I stopped writing the twelfth note and wired the gate. It is small - three
mechanical checks, and it would not have caught the README - but it is the first
thing in this repo's record that fails a commit rather than asking me to
remember. I made it fail on purpose before I made it pass. The honest measure of
tonight is not this retrospective. It is whether the next one has to record a
twelfth.

## Honest Feedback

**A retrospective written by the party under review is a weak instrument, and I
now have the measurement.** The 06:26 retro and the 06:31 audit examined the same
session; the audit found roughly three times as much, including two live
production defects. Everything it found was reachable from the repo. My own
review missed it not from lack of access but because I was reviewing work I had
just defended in conversation. The learning file already says re-reading is not a
defence; tonight quantified it.

**Speed under review became its own failure mode.** Turnaround compressed to 49,
8, 8, 2.5 minutes, and quality tracked it downward: the 1.5-second poll gap, the
36:1 figure, and the case-study conclusion that survived its own retraction were
all produced inside that window. Being fast to correct is good; being fast to
*re-publish* is how a correction inherits the carelessness of the thing it
replaces. I should have batched the last three.

**I documented a coupling instead of enforcing it.** `layers.py` carries a
carefully written comment that `GAP_SECONDS` and the one-sided verdict must
change together. That comment is the same class of artefact as every rule in the
audit - advisory, unenforced, and reliant on the next reader being more careful
than the last. The gate I built covers the case study and not this.

## Lessons Learned

1. Every retraction took a free parameter of my own setup and reported it as a
   property of the system. Vary the parameter the conclusion depends on, or do
   not publish the conclusion.
2. A guard built against one failure can become a generator of the opposite one:
   identity separates nothing when the healthy state is also uniform.
3. Anything periodic needs two samples before it produces a finding.
4. A provenance badge that has no "measured once" state cannot warn about
   sampling.
5. Documentation is not a control. Eleven rules in thirty-nine days, zero gates,
   until tonight.

## Next Steps

- [ ] R3: `layers.py` truncates at 400 KB with no `FFD9` check, 3.7 KB from firing
- [ ] The `refresh.sh` lock race between `mkdir` and the pid write
- [ ] gitleaks fingerprints are line-pinned and have already drifted
- [ ] `compare_hosts.py` still prints the retracted freshness metric with no caveat
- [ ] `initLayers` reveals a control `build.py` documents as hidden
- [ ] 791 still quoted in four files after 780 was established
- [ ] Dashboard `b712745f` still carries the old station-set sentence; unreadable
      from this account
- [ ] Licence: BLOCK on every cluster until สสน. answer in writing
