# Lesson — Prototype layout & scroll discipline

**Date**: 2026-05-04
**Repo**: pops/app/vet (Pops-Vet — Next.js 15 / React 19 / Tailwind 3 / Shadcn-UI)
**Source session**: rrr --deep — dashboard rebuild iterations

## The lessons (in order of how often I screwed up)

### 1. Single-container scroll is the only pattern that works inside `PrototypeShell`

`PrototypeShell` makes `#main-content` `flex-grow flex flex-col lg:min-h-0 lg:h-full lg:overflow-hidden`. At lg+ the parent does **not** scroll, so each prototype page must own its scroll.

**Wrong (the pattern I keep reaching for):**
```tsx
<div className='flex flex-col h-full'>
  <div className='sticky top-0 ...'>{topBar}</div>      {/* sibling — sticky has nothing to stick to */}
  <div className='flex-1 overflow-y-auto'>              {/* nested scroller — wheel events get captured */}
    {content}
  </div>
</div>
```

**Right:**
```tsx
<div className='h-full overflow-y-auto'>
  <div className='sticky top-0 ...'>{topBar}</div>      {/* now a child of the scroller */}
  <div className='px-6 py-5'>{content}</div>
</div>
```

I broke this 3 times in one session despite the handover pre-warning me about it. Trigger phrase: any time I reach for `flex-1 overflow-y-auto`, stop and ask "is this the inner pattern."

### 2. Verify production by visiting the URL or tracing every sub-component

When the user asks "does prod match X", do not answer from a single source-file read. Either:
- Navigate the deployed URL via Playwright + screenshot, OR
- Open every sub-component the page renders (not just the wrapper)

The dashboard page wrapper was sparse; the title and 5 KPI cards lived in `<DashboardStatBox />` one component down. I missed it and made a confident wrong claim.

### 3. Use Figma Desktop Bridge (`mcp__figma-console__*`), not the static plugin

The Desktop Bridge gives live access to the user's open canvas, current selection, and the ability to write back. Use it as the default for any Figma inspection/edit work.

### 4. In prototype space, prefer full-width single-column over Figma's 2-col-with-sidebar

Figma frames are designed at one width (1280 here). The prototype directory has an established responsive convention in `pickup-queue-to-opd` and `diagnostic-request-list`: top bar → KPI cards → optional inline strip → filter row → full-width table → pagination. Follow that.

When Figma has a sidebar (calendar + appointments etc.), translate it into a horizontal strip above the table and let the topbar's existing icon be the entry point for the calendar. Don't transcribe the 296px sidebar literally — at modern widescreen viewports it leaves visible empty space.

This is a prototype-only rule. Production `_pages/Dashboard.tsx` keeps the 2-col layout because that's what's deployed and matches the official Figma.

### 5. At full bleed, never use `w-[Npx] shrink-0` flex children

Fixed-width cards in a flex row leave an empty tail past the last card at wide viewports. Use a responsive grid:
```tsx
grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4
```
Fixed widths are fine inside an `overflow-x-auto` container where the empty-tail doesn't show.

### 6. When symptoms don't match where you're looking, inspect outside

If the user reports horizontal scroll and your component looks fine, inspect the outer shell's rendered DOM before tearing your own work apart. HMR transient state can break Tailwind classes (`fixed`, `w-16`) — a hard reload is a 5-second check that saves 20 minutes.

## Confidence

- Lessons 1–4: **high** — directly demonstrated and corrected by user this session.
- Lesson 5: **high** — confirmed by user pointing at empty space.
- Lesson 6: **medium** — the HMR transient was the actual root cause but reproducible only intermittently.

## Connections

- Project CLAUDE.md tells me to ask before `git commit` — I did this correctly. The cost was that `/prototype/dashboard` rebuild has 1,418 lines uncommitted at end of session, which is a lot of unsaved work. Mitigation: ask once for approval to commit the WIP at end of session even if work isn't "done."
- The four memory files I wrote map 1:1 to lessons 1–4 above. They are loaded automatically next session.
