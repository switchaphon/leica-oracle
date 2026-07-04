# Session Retrospective

**Session Date**: 2026-06-11
**Start/End**: ~23:00 - 06:11 GMT+7
**Duration**: ~7 hours (with AFK breaks)
**Focus**: QuickCreate Appointment — grill → design → implement → DS unification
**Type**: Feature (POC) + Design System refinement

## Session Summary

Grilled the QuickCreate appointment variant from scratch — 15 design decisions locked across service_type, time format, vet_id, chip feedback, create timing, UI form factor, label format, date range, and more. Then dispatched 3 Codex rounds to implement: (1) AppointmentChipV2 + plan-diagnostic-2 POC page, (2) DS fixes + search field standardization, (3) apply to all 4 existing flows. Lead-reviewed every round with Playwright browser testing. Fixed width drift bug manually (OrderSummaryPane `min-w-0 overflow-hidden`).

## Timeline

| Time | Activity |
|------|----------|
| ~23:00 | Read handover, asked about 5 uncommitted files |
| ~23:10 | Started QuickCreate grill — service_type, time, vet_id |
| ~23:30 | Deep grill: UI form factor (dropdown + inline calendar), label format |
| ~23:50 | All 15 decisions locked, wrote BRIEF-quickcreate-appointment.md |
| ~23:55 | Spawned Codex round 1 (tmux), user went AFK |
| 00:05 | Codex round 1 done — reviewed AppointmentChipV2, found 5 issues |
| 00:15 | User returned, reviewed findings, identified search field inconsistency |
| 00:20 | Grilled search field DS: canonical spec, h-10, ring-brand |
| 00:35 | Wrote BRIEF-codex-fix-round2.md, spawned Codex round 2 |
| 00:45 | Codex round 2 done — verified 10/10 tasks, 1 minor issue (Settings2 leftover) |
| 00:50 | Browser testing with Playwright — found width drift bug |
| 01:00 | Fixed manually: OrderSummaryPane min-w-0, search field padding, flex ratio |
| 01:10 | Playwright verified width stable (342px across all states) |
| 01:15 | User requested: button labels, hint text, calendar icon color, apply to 4 flows |
| 01:20 | Fixed labels + hint + icon manually, wrote BRIEF-codex-apply-4-flows.md |
| 01:25 | Spawned Codex round 3, applied to all 4 flows |
| 01:35 | Codex round 3 done — verified all 4 pages: variant, payload comment, guides |

## Files Modified

### New files
- `src/app/prototype/opd/_components/diagnostic/AppointmentChipV2.tsx`
- `src/app/prototype/opd/plan-diagnostic-2/page.tsx`
- `BRIEF-quickcreate-appointment.md`
- `BRIEF-codex-fix-round2.md`
- `BRIEF-codex-apply-4-flows.md`

### Modified files (key)
- `OrderSummaryPane.tsx` — variant prop + flex-[2] + min-w-0 overflow-hidden
- `OpdOrderFlowShell.tsx` — diagnosticAppointmentChipVariant prop
- `OpdPageBody.tsx` — prop threading
- `SOAPContent.tsx` — prop threading + DarkPill gray-900
- `LabTestSelector.tsx` — search field DS + button label + appointmentChipVariant
- `XRayStudySelector.tsx` — same
- `UltrasoundStudySelector.tsx` — button label
- `DrugDoseSelector.tsx` — search field DS, removed Settings2
- `ServiceFeeSelector.tsx` — search field DS
- `AdvanceConfirmPopup.tsx` — button label "ยืนยัน"
- `design-system/page.tsx` — Search Input section + Filter Bar h-10 update
- `prototype/page.tsx` — index cards + changelog entries
- 4 flow pages — quick-create variant + FE hidden payload comment + guide steps

## AI Diary

This session felt like the ideal lead-implementer workflow finally clicking into place. The grill session was thorough — 15 decisions in under 30 minutes, each one locked with concrete API evidence. I learned to ground every UX question in the actual `AppointmentCreateInput` type and the appointment-flow.html reference doc, which prevented the usual drift into hypothetical territory.

The Codex dispatches were clean but imperfect. Round 1 delivered 90% right but violated scope constraints (modified forbidden files, changed flex ratios). Round 2 was more surgical. Round 3 was the simplest — just prop + comment + guide changes across 4 pages. The pattern is clear now: brief quality directly determines output quality. Vague briefs = scope creep. Precise file lists + "Do NOT" sections = targeted changes.

The width drift bug was the most satisfying catch. Playwright bounding box measurements proved the layout shifted from 528px to 436px when switching appointments — a 92px jump caused by popover `min-w-[320px]` pushing the flex container. The fix was two CSS classes: `min-w-0 overflow-hidden`. This is the kind of bug that users feel but can't articulate, and it would have shipped without the automated measurement.

The search field standardization was Un's insight — he noticed the inconsistency across Lab/DrugDose/ServiceFee that I had normalized in my head. Three different border styles, three heights, three focus states. Now there's one canonical spec in the DS page. This is how design systems should work: notice drift, lock the spec, apply everywhere, add to the reference.

I'm genuinely proud of the FE hidden payload comment block. It's not code — it's communication. Every page now tells the next developer exactly what the frontend auto-fills and why the user only sees a calendar.

## Honest Feedback

**1. Codex scope discipline is still weak.** Despite explicit "Do NOT modify" rules in the brief, Codex round 1 changed flex ratios, modified V1 chip, and rewrote guide text in forbidden files. I had to manually verify and revert. The brief format needs a stronger "FORBIDDEN FILES" section, not buried in "Do NOT" — maybe a separate allowlist: "You may ONLY modify these files: [list]."

**2. Grill sessions need a running tally visible to the user.** By question 5 we were already referencing decisions from question 1, and the user had to trust my mental model of what was locked. A live decision table updated after each lock would reduce cognitive load. I did produce one at the end but should have maintained it incrementally.

**3. Playwright testing adds significant value but the tool ergonomics are rough.** Strict mode violations on `text=18` (matched phone number), `role=dialog` (matched 2 elements), and aria-label format mismatches burned multiple retries. Need to default to more specific selectors (data-guide, aria-label with full text) from the start.

## Lessons Learned

1. **`min-w-0 overflow-hidden` on flex children prevents content-driven layout shift** — when a popover or absolute element has `min-w`, it can push a flex child wider than its ratio, and the parent never shrinks it back. `min-w-0` allows the flex algorithm to size correctly.

2. **Codex brief quality = output quality** — allowlist of modifiable files is more effective than a denylist. "Do NOT" lists get ignored; "ONLY touch these files" gets followed.

3. **Design system sections should be standalone, not embedded** — search input spec was hidden inside Filter Bar section, so 3 different components invented their own pattern. Extracting it as a standalone DS section with its own nav anchor prevents future drift.

## Next Steps

- [ ] Browser test all 4 flows (not just plan-diagnostic-2)
- [ ] Review + commit with user approval (10+ prototype commits unpushed)
- [ ] CHANGELOG.md update (deferred until all flows confirmed)
- [ ] Remaining handover items: index cards for /opd/calculate-drug-dose + /opd/add-service-fees
- [ ] Final gate: pnpm build + UAT suite re-run
- [ ] Brain commit #2 (pops-clinic-oracle ψ/)
