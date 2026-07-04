# Lesson: Reuse Over Rebuild — The Prototype Principle

**Date**: 2026-04-29
**Source**: Prototype build session — corrected twice by user
**Confidence**: High (validated through failure)

## Pattern

When prototyping in a real codebase, the default action must be **reuse existing components with mock providers**, not build new components that look similar.

## Evidence

1. Built a custom sidebar → user caught it immediately ("ทำไมไม่เหมือน /dashboard")
2. Built custom Card divs → user caught it immediately ("ไม่เหมือน /dashboard")
3. Both fixes were simple: import real component + wrap with mock provider

## Checklist (before creating ANY component)

1. Grep the repo: does this component already exist?
2. If yes → import it. If it needs auth/backend → mock the provider, not the component.
3. If no → tell the user before creating. "ตัวนี้ไม่มีใน repo ผมจะสร้างใหม่ / ใช้ default shadcn"
4. Never silently create a new version of something that exists.

## Technical patterns learned

- `SessionProvider session={mockSession}` wraps auth-dependent components
- `SWRConfig value={{ provider: () => new Map() }}` prevents real API calls
- `PathnameContext.Provider value="/lab"` overrides sidebar active state
- `dynamic(() => import('Component'), { ssr: false })` avoids hydration mismatch from context overrides

## Also learned: read pops-gem FIRST

The design bible (pops-gem/) defines product principles, personas, and scenarios. Should be read before building any prototype, not after.
