# Next.js App Router: The Only Layout Escape Is a Different Directory

**Date**: 2026-06-16
**Project**: pops/vet prototype
**Context**: Building a print-preview page that must render without the prototype sidebar/topbar

## The Pattern

In Next.js App Router, **layouts are always additive and cannot be opted out of from within a child route**. A page at `src/app/prototype/print/page.tsx` will always inherit `src/app/prototype/layout.tsx` and `src/app/layout.tsx` — no exceptions.

Three failed approaches confirmed this:
1. `isPrintPreview` early-return inside a layout component → custom app error (Next.js internal chunk manifest invariant violated)
2. Route group `prototype/(print)/page.tsx` → route groups only strip the segment from the URL; the layout inheritance is unchanged
3. Combined route group + early-return → `clientReferenceManifest` invariant error during build

## The Solution

Place the page in a **completely different directory branch** that does not have the unwanted layout:

```
src/app/
├── prototype/
│   └── layout.tsx      ← has NavBar + Sidebar
│   └── queue/          ← inherits prototype layout
└── print/              ← only inherits src/app/layout.tsx
    └── receipt/
        └── [receipt_no]/
            └── page.tsx ← no NavBar, no Sidebar ✓
```

`src/app/layout.tsx` (root) only wraps `SessionProvider` + `SWRProvider` — no shell components.

## Corollary: Check Middleware for New Top-Level Routes

Any new route outside `/api` and `/prototype` falls under the auth middleware guard by default. Add the prefix to the bypass list:

```ts
// src/middleware.ts
if (pathname.startsWith('/api') || pathname.startsWith('/prototype') || pathname.startsWith('/print')) {
  return NextResponse.next();
}
```

## When to Apply

Any time a page needs to "opt out" of a parent layout:
- Print views
- Embed/iframe targets  
- Full-screen kiosk pages
- OAuth callback pages

The answer is always: new directory branch, not clever workarounds inside the existing tree.
