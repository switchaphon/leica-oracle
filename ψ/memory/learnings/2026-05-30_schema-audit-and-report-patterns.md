# Learning — Schema-Gap Audit + Interactive Report Patterns

**Date**: 2026-05-30
**Source**: pops/vet 3-way schema↔docs↔prototype gap audit + HTML report build
**Confidence**: High (verified by building + shipping the artifacts)

## Pattern 1 — "Verify there is ONE schema before auditing the schema" ⭐ (highest value)

When asked to audit a data model against docs/prototype, **don't assume there's a single schema**. In this session, "the schema" turned out to be **two incompatible generations**:
- pg_dump (`_db-schema/*.sql`, PostgreSQL 17, `taxonomy.id` UUID) — main app DB
- rx-inv-files (`SCHEMA_TABLES.md`, Supabase, migrations 001-016, `taxonomy.id` INT/SERIAL) — Inventory module

Same `lab_orders` table name, completely different definitions (OPD/queue-coupled `{DRAFT,SENT,…}` vs catalog/panel-coupled `{ORDERED,…,REVIEWED}` + `lab_results`). This collision was the single most important finding and **only surfaced when the user offered a 4th source to compare**.

**How to apply**: Early in any schema audit, grep for multiple schema sources (different dirs, `migrations/` vs pg_dump, "FINAL"/"v2"/"visual" dictionary variants). When a user says "compare with X too," treat it as possibly inverting the premise, not just adding detail. A finding that ties two domains together (here Diagnostic ↔ Inventory) is usually the load-bearing one.

## Pattern 2 — Self-contained interactive report that survives grilling

For a report that must render anytime/offline and be used live in a grill:
- Data as `<script type="application/json">…</script>` → `JSON.parse` (clean Thai/quote handling, no JS-escaping pitfalls).
- Render + filter with vanilla JS from that array (dashboards/heatmaps/counts compute from the same data → auto-update when data changes).
- Hand-built CSS/SVG visuals (enum-presence matrix, vs-diagrams) — **no Mermaid/CDN deps** so it never fails to load mid-grill.
- Google Fonts `<link>` with a **system-font fallback** stack (renders offline too).
- A tiny `fmt()` that HTML-escapes then applies `` `code` `` / `**bold**` markup.

**Verify generated HTML two ways**: Playwright CLI element-screenshots of each component, AND `node --check` on the extracted `<script>` + `JSON.parse` on each data block. The screenshot proves it renders; the syntax-check proves the JS parses.

## Pattern 3 — Don't hand-write fragile JS into generated HTML ⚠️

A nested ternary returning a **template literal with inline HTML attributes** silently broke the entire render (0 findings, "Invalid or unexpected token"). Avoid:
```js
// fragile — broke the parse
const chip = dec==='BUG' ? '<span title="…">🐞</span>' : dec==='INFO' ? '<span>…</span>' : `<span title="…${dec}">→ ${dec}</span>`;
```
Use plain string concatenation instead:
```js
const txt = dec==='BUG' ? '🐞 fix' : dec==='INFO' ? '📖 read' : '→ '+dec;
const cls = dec==='BUG' ? ' bug' : dec==='INFO' ? ' info' : '';
const chip = '<span class="dec-chip'+cls+'">'+txt+'</span>';
```
On a standalone HTML file there's no build step/linter — **you are the linter**. Always `node --check` the emitted script.

## Pattern 4 — 6-agent 3-way comparison audit

Per-domain agent (appointment / diagnostic / queue-opd / billing / rx-inventory / core), each given: exact file list (literal paths), a strict category framework (GAP-SCHEMA / GAP-DOC / GAP-PROTO / CONFLICT-NAME / -STATE / -TYPE / -ID / -RELATION), severity scale, and "return a compact digest, not file dumps." Main agent merges digests + **verifies the provable claims (the insert-blocking bugs) directly** rather than trusting the digest. Keeps context clean, parallel, mergeable.

## Pattern 5 — Decision-tagging makes a big audit actionable

Map every finding to the decision that resolves it (`→ D1…D8`), or `🐞 fix` (provable bug, no decision) / `📖 read` (info only). Add a filter by decision. Turns "review 82 findings" into "make 8 calls + forward 3 bugs." When grilling decision Dx, filter `→ Dx` to see exactly its evidence. Each decision card shows its finding count.

## Environment note
rtk proxy swallows plain `ls`/`cat` (empty output, exit 0) — use `/bin/ls` or the Read tool. See [[reference_rtk_swallows_ls_output]]. Next.js validation hooks fire on static `docs/*.html` files (next/font, 'use client') — **not applicable**, disregard; these are static assets, not React.
