# Session Retrospective — Dashboard rebuild iterations

**Session Date**: 2026-05-04
**Start/End**: 07:00 – 09:31 GMT+7
**Duration**: ~2.5 hours
**Focus**: Visual test the 3 new prototype pages from the previous night, then rebuild `/prototype/dashboard` to match Figma 3:30984 (and later, the prototype's full-width layout convention)
**Type**: Refactoring + UI implementation
**Branch**: `prototype`

## Session Summary

Plan was a routine 6-step "visual test + commit" pass on three new prototype pages (dashboard, appointment, pet) per the 07:00 handover. The session went sideways mid-way: I made an avoidable production-vs-Figma misread, the user redirected me to rebuild `/prototype/dashboard` against Figma 3:30984, and I then iterated through three layout passes (literal Figma 2-col-with-sidebar → full-width with horizontal strip → responsive grid for the strip) before scroll, sidebar HMR, and empty-space issues were all resolved. None of the planned commits landed.

## Timeline

| Time | Activity | Outcome |
|------|----------|---------|
| 07:00–07:15 | Read handover, started dev server, began visual-test pass on the 3 new prototype pages | Pages render; baseline screenshots captured |
| 07:15–07:45 | User redirected: compare `/prototype/dashboard` to Figma 3:30984 + production. I read `_pages/Dashboard.tsx` and claimed prod didn't match Figma | Wrong call — user sent screenshot of `app-dev.pops.vet/dashboard` showing it DID match. Logged `feedback_verify_production_via_browser.md` (title + KPI cards live in `DashboardStatBox.tsx`, one component deeper) |
| 07:45–08:00 | User: "always use figma desktop bridge". Switched from static Figma plugin to live Desktop Bridge (`mcp__figma-console__*`) | Logged `feedback_figma_desktop_bridge.md`; navigated to node 3:30984 via bridge |
| 08:00–08:30 | Rebuilt `/prototype/dashboard` from 6-stat-card layout to Figma's 5-KPI + breakdown layout with right sidebar (calendar + appointments, 296px) | First rebuild shipped — matched Figma 2-col literally |
| 08:30–08:45 | User flagged "weirdly wide" empty space at 1900–1996px. Pointed at `pickup-queue-to-opd` and `diagnostic-request-list` as preferred references | Logged `feedback_prototype_layout_fullwidth.md` — prototype convention is full-width single-column |
| 08:45–09:15 | Refactored: dropped right sidebar, moved appointments to horizontal strip above table, full-width column below | Layout now matches the prototype pattern; second user-pointed empty-space at the strip caught (cards `w-[280px]` left tail empty at wide viewports) |
| 09:15–09:25 | Scroll broke (third recurrence across prototype pages — handover even pre-warned). Used the broken nested `flex-1 overflow-y-auto` pattern again | Logged `feedback_prototype_scroll_pattern.md`; refactored to single-container `h-full overflow-y-auto` with sticky topbar inside |
| 09:25–09:31 | Fixed appointment strip to responsive grid `sm:2 lg:3 xl:4`; verified scroll/layout at 700/900/1100/1280/1996px viewports | Layout fills width edge-to-edge at all viewports tested. Original commits from handover step 6 deferred. |

## Files Modified

**New, untracked** (this session is the first time these touched the working tree from this branch state):
- `src/app/prototype/dashboard/page.tsx` — 908 lines
- `src/app/prototype/dashboard/_mock.ts` — 510 lines (rewritten to support new KPI/appointment data shape)

**Already untracked from prior session** (still untracked, didn't commit):
- `src/app/prototype/{appointment,pet,design-system}/`
- `src/app/prototype/DESIGN_SYSTEM.md`, `OWNERSHIP.md`

**Memory files written** (in `~/.claude/projects/.../memory/`):
- `feedback_figma_desktop_bridge.md`
- `feedback_verify_production_via_browser.md`
- `feedback_prototype_scroll_pattern.md`
- `feedback_prototype_layout_fullwidth.md`

**Pollution at repo root** (~30 PNG screenshots from Playwright, not in `.gitignore`).

## Architecture (after this session)

`/prototype/dashboard` layout, top to bottom:
1. Single scroll container — `<div className='h-full overflow-x-hidden overflow-y-auto'>`
2. Sticky top bar inside the scroller — clinic name + branch dropdown + search + create button + bell + cal + avatar
3. `<h2>สรุปวันนี้</h2>`
4. 5 KPI cards — `grid-cols-1 lg:grid-cols-2 xl:grid-cols-[repeat(2,1.5fr)_repeat(3,1fr)]` (cards 1+2 wider with breakdown column; cards 3–5 narrower)
5. `TodayAppointmentsStrip` — responsive grid `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
6. `ActiveQueuePanel` — "คิวกำลังให้บริการ N คิว" + 2 dropdowns + 6 colored legend dots
7. Filter row — search + chip-style `+ ประเภทสัตว์` `+ ห้องบริการ` + `รีเซ็ต`
8. Full-width table — เวลานัด/มาถึง · สัตว์ · ผู้ดูแล · บริการ · ขั้นตอนถัดไป (CTA black) · ⋮
9. Pagination

## AI Diary

This session was a quiet humiliation, in a productive way. I started by trusting my own code-reading and learned twice over that I shouldn't. The first time was when I told the user production `/dashboard` didn't match Figma — a confident, structured comparison table in three columns — based on reading exactly one file. The user didn't argue with me; they just sent a screenshot of the deployed page and asked me to look. The title and the five KPI cards I claimed were missing were sitting there in `DashboardStatBox.tsx`, one `<DashboardStatBox />` import line away. I felt the small recoil of having been wrong in public, and I wrote it into memory so I'd remember next time. The pattern is now: visit the deployed URL or read every sub-component before saying "X is missing."

The second pattern that bit me, three times, was prototype-page scroll. The handover I started this session with literally pre-warned about it: "If scroll doesn't work, fix wrapper to `h-full overflow-y-auto` instead of `min-h-screen`." I read that note and still reached for `flex-1 overflow-y-auto` as an inner sibling of the sticky top bar — the pattern that doesn't work because `PrototypeShell` makes `#main-content` `lg:overflow-hidden` and the sticky has nothing to stick to. The third time the user caught it I finally wrote the rule down: one container `h-full overflow-y-auto`, sticky top bar inside. I think the reason I keep falling into the nested pattern is that it feels more "structured" — you can see the topbar and the scrollable area as distinct units. But structure that doesn't work isn't structure. I'll trust the single-container shape going forward.

The third learning was about Figma fidelity. I rebuilt the dashboard with a 296px right sidebar exactly because Figma 3:30984 had a 296px right sidebar. The user pointed at two sibling prototype pages and said "those are full-width, this one has empty space on the right." I had been treating the Figma frame as a layout spec when it's really a content spec — the layout convention belongs to the codebase, and the codebase already had a strong opinion expressed in `pickup-queue-to-opd` and `diagnostic-request-list`. I refactored, the calendar moved into the topbar's existing icon (entry point is there for a future popover), the appointments became a horizontal strip, and the table breathed at full bleed.

## Honest Feedback

**1. I diagnosed before I read the whole file tree.** When asked to compare production to Figma, I opened the parent `Dashboard.tsx`, saw a sparse outer shell, and confidently declared "production doesn't match Figma." The title and KPI cards lived inside a child component I never opened. The user had to send a screenshot to correct me. *Lesson:* "I read the file" ≠ "I read the feature." For comparison work, the rendered output is the source of truth — read every component in the tree, or pull a screenshot first.

**2. I matched Figma literally instead of matching the prototype's pattern.** I built a 296px right sidebar because frame 3:30984 had one. At a modern widescreen viewport it had a giant empty gutter. The user pointed at `/prototype/pickup-queue-to-opd` and said "match this." *Lesson:* Figma frames are designed at one width. Before transcribing pixels, check whether the codebase already has an opinion about how class-of-page X lays out at this app's actual viewports.

**3. I chased "horizontal scroll" at the wrong layer.** When the user reported horizontal scroll, I resized viewports, hunted overflows in my own components, second-guessed grid math. Real cause: an HMR transient where `#drawer-menu-wrapper` had lost its `fixed` class, taking 1249px of flow width instead of 64px. *Lesson:* when symptoms don't match where I'm looking, inspect the outer layout's rendered DOM once before tearing my own work apart. A hard reload would have saved 20 minutes.

**4. I shipped flex-of-fixed-width children at full-bleed.** The appointment strip was `w-[280px] shrink-0` cards in a flex row — a sea of empty space past the last card on wide screens. *Lesson:* at full bleed, default to responsive grids; only use fixed widths in horizontally-scrolling containers where the empty-tail problem doesn't exist.

## What Went Well

- **Once corrected, course corrections were tight.** The pivot from sidebar-layout to full-width happened in one pass without re-litigating; the appointment strip refactor was a clean grid swap.
- **Memory writes happened immediately after each correction**, not at session end. The four feedback files codify the recurring failure modes so the next session loads them.
- **Final dashboard matches the prototype's established layout language**, so the upcoming `/prototype/appointment` and `/prototype/pet` work won't have to relitigate the layout question.

## Lessons Learned

1. **Verify production by visiting the URL, not by reading the outer page file.** Trace into every sub-component the page renders, or just open the deployed page in Playwright. (`feedback_verify_production_via_browser.md`)
2. **Always use the Figma Desktop Bridge** (`mcp__figma-console__figma_*`), not the static plugin tools, for inspection/edits. (`feedback_figma_desktop_bridge.md`)
3. **Single-container scroll is the only pattern that works inside `PrototypeShell`** — `<div className='h-full overflow-y-auto'>` with the sticky top bar **inside**. Never use a nested inner scroller as a sibling of the sticky bar. (`feedback_prototype_scroll_pattern.md`)
4. **Prototype pages prefer full-width single-column over Figma's 2-col-with-sidebar.** Translate sidebar content into a horizontal strip above the table. (`feedback_prototype_layout_fullwidth.md`)
5. **Don't ship `w-[Npx] shrink-0` flex children inside a full-width row** — use responsive grid (`grid-cols-1 sm:2 lg:3 xl:4`) so cards distribute evenly.

## Risks / Tech Debt Created

- `MiniCalendar` (lines 393–445 of `dashboard/page.tsx`) is now dead code — leftover from the sidebar layout. Strip before commit.
- Local `FilterChip` (line 362) duplicates `FilterDropdown` pattern — extraction candidate but not blocking.
- KPI grid hardcodes a 5-card width ratio at `xl` breakpoint — fragile if a 6th KPI is added; below `xl` collapses to 2 cols leaving an orphan 5th.
- `dashboard/page.tsx` is 908 lines — should be split into a `_components/` subdirectory before adding more.
- ~30 PNG screenshots at repo root from Playwright validation — need `.gitignore` entry or move to `.playwright-mcp/`.
- Two pending commits never landed: LabTestSelector V2 + editor changes, and the new prototype pages bundle. Both still uncommitted.

## Next Steps

1. **Commit work** — the original handover's step 6 still needs to ship: (a) LabTestSelector V2 + PatientHeader + editor refinements (already-modified files), (b) new prototype pages + design system reference + this dashboard rebuild.
2. **Move on to `/prototype/appointment`** with the rules now codified — single-container scroll, full-width pattern, Desktop Bridge for Figma, no fixed-width flex children.
3. **Add `*.png` to `.gitignore`** at repo root (or use a `screenshots/` subdir) so Playwright artifacts stop polluting status.
4. **Strip dead `MiniCalendar`** from `dashboard/page.tsx` before committing.

## Metrics

- Files modified (this session): 2 (page.tsx + _mock.ts in `prototype/dashboard/`)
- Lines: ~1,418 net new across the two files (entirely net-new untracked)
- Memory files written: 4
- Layout iterations: 3 (Figma-literal → drop-sidebar → responsive-strip)
- Scroll bug recurrences: 3
- Commits this session: **0** (intentional — pending user approval per project CLAUDE.md `git commit` policy)
