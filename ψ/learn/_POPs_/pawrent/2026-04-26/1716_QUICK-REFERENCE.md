# Pawrent Quick-Reference Guide

**Version:** 0.4.1 | **Last Updated:** 2026-04-26 | **Target Audience:** New developers

---

## What Pawrent Does

Pawrent is a **B2C pet health operating system** for Thai pet owners. It's a mobile-first Progressive Web App (PWA) built on the LINE LIFF platform that helps users:

- **Manage pet health records** — Create pet profiles, track vaccinations, parasite prevention, and health events (lab results, diagnoses, checkups)
- **Broadcast emergency SOS alerts** — When pets go missing, users broadcast alerts with GPS location, get notifications of nearby alerts within 5km
- **Share pet moments** — Community feed for photo posts with optional pet tags
- **Find veterinary hospitals** — Interactive map of vet clinics with details, hours, and specialists
- **Profile management** — Editable avatars, pet counts, and PDPA-compliant privacy notice

**Key Constraint:** PDPA-regulated data (Thailand privacy law). Pet health records and user profiles are personal data with ฿5M criminal / ฿1M admin liability per infringement.

---

## Installation & Setup

### Prerequisites
- Node.js 18+
- npm 9+
- A Supabase project
- A LINE Login channel (LIFF)
- An Upstash Redis instance

### Quick Start
```bash
# Clone and install
git clone <repo>
cd pawrent
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local — see Environment Variables section below

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Mobile-first development — open browser DevTools and set viewport to mobile (375x667).

### Environment Variables (Required)

Create `.env.local` with these variables:

#### Supabase (shared across all environments)
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
```

#### Upstash Redis (required for rate limiting)
```
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-redis-token
```

#### LINE LIFF (DIFFERENT per environment — production/preview/development)
```
NEXT_PUBLIC_LIFF_ID=your-liff-id
LINE_CHANNEL_ID=your-line-channel-id
```

#### LINE Messaging API (for Rich Menu & webhooks)
```
LINE_CHANNEL_ACCESS_TOKEN=your-messaging-api-channel-access-token
LINE_CHANNEL_SECRET=your-messaging-api-channel-secret
```

**Vercel Deployment:** Use `vercel env add` to set env vars per environment:
```bash
vercel env add LINE_CHANNEL_SECRET production --value "xxx"
vercel env add LINE_CHANNEL_SECRET preview --value "xxx"
vercel env pull .env.local
```

---

## Key Features

### 1. Pet Management
- Create pet profiles with species (14 types), breed, DOB, microchip, special notes
- Photo gallery — up to 10 photos per pet with lightbox viewer
- **Vaccination tracking** — Protected / Due Soon / Overdue status with auto-calculated next-due dates
- **Parasite prevention logs** — Circular countdown timers
- **Health events** — Lab results, diagnoses, checkups with attachments

### 2. SOS Lost Pet Alerts
- Broadcast emergency alerts with GPS last-seen location
- Optional video evidence (MP4/MOV, max 50MB)
- Description auto-filled from pet's special notes
- Notification feed shows nearby alerts (<5km via Haversine distance) and recently found pets (7-day window)
- Resolution tracking: "found" or "given up"
- **Rate limited:** 3 alerts per 5 minutes per user

### 3. Community Feed
- Photo posts with optional pet tag and caption
- Like system via Supabase RPC (atomic, prevents race conditions)
- Optimistic UI updates
- 20 posts per load, ordered by recency

### 4. Hospital Finder
- Interactive Leaflet map with vet clinic markers
- Auto-centers on user GPS (fallback: Bangkok 13.7563, 100.5018)
- Clinic details: hours, phone, specialists, certified badge
- Direct call and Google Maps directions links
- **Important:** Leaflet components must use `dynamic(() => import(...), { ssr: false })`

### 5. User Profile
- Editable avatar (with React Easy Crop image cropper)
- Display name, pet count, SOS alert stats
- PDPA privacy compliance notice
- In-app feedback submission (supports anonymous, rate-limited by IP)

### 6. PWA & Offline
- Service worker via Serwist for offline fallback
- Installable via manifest.json
- Progressive enhancement

---

## Project Structure

```
pawrent/
├── app/                      # Next.js 16 App Router
│   ├── page.tsx              # Home (community feed)
│   ├── layout.tsx            # Root layout + providers
│   ├── api/                  # 10 API route groups
│   │   ├── pets/             # CRUD pets (POST/PUT/DELETE)
│   │   ├── sos/              # SOS alerts (POST/PUT)
│   │   ├── posts/            # Feed posts (POST)
│   │   ├── posts/like/       # Like toggle (POST)
│   │   ├── feedback/         # Feedback submission (POST)
│   │   ├── profile/          # User profile (PUT)
│   │   ├── vaccinations/     # Vaccination logs (POST)
│   │   ├── parasite-logs/    # Parasite logs (POST)
│   │   ├── pet-photos/       # Photo upload (POST/DELETE)
│   │   ├── hospitals/        # Hospital listing (GET, public)
│   │   ├── line/             # LINE webhooks
│   │   └── og/               # OG image generation
│   ├── pets/                 # Pet management routes
│   ├── sos/                  # SOS alert creation
│   ├── notifications/        # SOS alert feed
│   ├── hospital/             # Map page
│   ├── profile/              # User settings
│   ├── feedback/             # Feedback form
│   ├── offline/              # PWA fallback
│   ├── post/                 # Post creation/detail
│   ├── conversations/        # LINE conversations
│   └── sw.ts                 # Service worker (Serwist)
│
├── components/               # 34+ React components
│   ├── ui/                   # Shadcn/Radix UI primitives
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── card.tsx
│   │   ├── avatar.tsx
│   │   └── ... more
│   ├── auth-form.tsx         # Login/signup (Zod validation)
│   ├── auth-provider.tsx     # Supabase auth context (deprecated in favor of LiffProvider)
│   ├── liff-provider.tsx     # LINE LIFF auth context (USE THIS)
│   ├── create-pet-form.tsx   # Pet creation form
│   ├── edit-pet-form.tsx     # Pet editing form
│   ├── hospital-map.tsx      # Leaflet map + markers
│   ├── map-picker.tsx        # Geolocation picker for SOS
│   ├── image-cropper.tsx     # Reusable crop tool
│   ├── bottom-nav.tsx        # 5-tab navigation bar
│   ├── location-banner.tsx   # GPS status banner
│   ├── debug-console.tsx     # vconsole for mobile debugging
│   ├── add-vaccine-form.tsx
│   ├── add-parasite-log-form.tsx
│   ├── health-timeline.tsx
│   └── ... form components
│
├── lib/                      # Utilities and clients
│   ├── db.ts                 # Data access layer (42 functions)
│   ├── api.ts                # API fetch helper with auth
│   ├── types/                # TypeScript interfaces
│   │   ├── common.ts         # Profile, Pet, Vaccination, etc.
│   │   ├── pets.ts
│   │   ├── pet-report.ts
│   │   ├── posts.ts
│   │   ├── geospatial.ts
│   │   ├── found.ts
│   │   ├── conversations.ts
│   │   ├── push.ts
│   │   ├── health.ts
│   │   └── index.ts          # Barrel re-export
│   ├── validations/          # Zod schemas
│   │   ├── common.ts
│   │   ├── pets.ts
│   │   ├── pet-report.ts
│   │   ├── posts.ts
│   │   ├── auth.ts
│   │   ├── found.ts
│   │   ├── push.ts
│   │   ├── health.ts
│   │   └── index.ts          # Barrel re-export
│   ├── supabase.ts           # Supabase client (Client Components)
│   ├── supabase-server.ts    # Supabase client (Server Components)
│   ├── supabase-api.ts       # Supabase client (Route Handlers)
│   ├── rate-limit.ts         # Upstash Redis rate limiting
│   ├── liff.ts               # LINE LIFF SDK wrapper
│   ├── auth-token.ts         # Auth token storage
│   ├── pet-utils.ts          # Pet status/health calculations
│   ├── pagination.ts         # Cursor-based pagination helper
│   ├── utils.ts              # cn() for classNames
│   ├── line/                 # LINE integrations
│   │   └── ... LINE helpers
│   └── line-templates/       # LINE message templates
│
├── data/                     # Static data files
│   ├── species.json          # 14 pet species with icons
│   ├── breeds.json           # 200+ dog/cat breeds
│   ├── vaccines.ts           # Standard pet vaccines database
│   ├── parasite-prevention.ts # Parasite medicines database
│   └── hospitals.json        # Vet clinic directory
│
├── __tests__/                # 375 unit/component tests
│   ├── lib/
│   ├── components/
│   └── app/api/
│
├── e2e/                      # 46 Playwright E2E specs
│   ├── smoke.spec.ts         # Critical paths
│   ├── pet-management.spec.ts
│   ├── sos-alerts.spec.ts
│   ├── community-feed.spec.ts
│   └── ... more
│
├── conductor/                # Project state & pipeline
│   ├── index.md              # Current status
│   ├── state.md              # Phase and PRP tracking
│   ├── active-tasks.md       # Claimed tasks
│   ├── pipeline-status.md    # Current PRP step
│   ├── decisions.md          # Architecture decisions
│   ├── product.md            # Product requirements
│   ├── tech-stack.md         # Technology decisions
│   ├── agent-teams.md        # Team protocols
│   ├── workflow.md           # Development workflow
│   └── code_styleguides/     # Component conventions
│
├── PRPs/                     # Product Requirements Plans
│   ├── PRP-01-09/            # Completed PRPs
│   ├── PRP-10-12/            # Spec'd PRPs
│   └── ... individual PRPs
│
├── public/                   # Static assets
│   ├── leaflet-icons/        # Marker icons
│   ├── manifest.json         # PWA manifest
│   └── ... images
│
├── .next/                    # Build output (gitignored)
├── coverage/                 # Test coverage (gitignored)
├── node_modules/             # Dependencies (gitignored)
├── .env.local                # Environment vars (gitignored, use .env.example)
├── .env.example              # Template
├── package.json              # Dependencies & scripts
├── tsconfig.json             # TypeScript config
├── vitest.config.ts          # Unit test config
├── playwright.config.ts      # E2E test config
├── next.config.ts            # Next.js config (Serwist PWA)
├── tailwind.config.ts        # Tailwind CSS config
├── .husky/                   # Git hooks (pre-commit lint)
├── commitlint.config.ts      # Commit message rules
├── CLAUDE.md                 # Agent instructions
├── CHANGELOG.md              # Release notes
└── README.md                 # High-level overview
```

---

## Architecture Rules (Must Follow)

### 1. Three Supabase Clients — Use the Right One
- **`lib/supabase.ts`** — Client Components ONLY (uses browser SDK)
- **`lib/supabase-server.ts`** — Server Components ONLY (uses Node.js client)
- **`lib/supabase-api.ts`** — Route Handlers ONLY (creates API-scoped client with `createApiClient(authHeader)`)

Using the wrong client breaks auth or causes hydration errors.

### 2. Mobile-First Development
- **TARGET:** Thailand LINE OA users opening via Rich Menu on mobile
- **Design mobile viewport first** (375x667), then ensure desktop works
- Test on DevTools mobile mode or actual phone via ngrok
- Use `device-width` viewport with `maximumScale: 1` to prevent zoom
- Theme color: `#FF8263` (orange accent)

### 3. Default to Server Components
- Use Server Components by default
- Add `"use client"` ONLY for hooks (useState, useEffect, useContext) or event handlers (onClick, onChange)
- Example: A page that fetches data is a Server Component; a form with useState is a Client Component

### 4. API Route Pattern: Auth → Rate-Limit → Validate → Query
```typescript
// Route handlers follow this pattern:
export async function POST(request: NextRequest) {
  // 1. Auth — extract Bearer token
  const auth = await getAuthUser(request);
  if (!auth) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  // 2. Rate-limit — check Upstash Redis
  const rateLimited = await checkRateLimit(limiter, auth.user.id);
  if (rateLimited) return rateLimited;

  // 3. Validate — parse and validate body with Zod
  const result = petSchema.safeParse(body);
  if (!result.success) {
    return NextResponse.json({ error: result.error.issues[0].message }, { status: 400 });
  }

  // 4. Query — execute database operation
  const { data, error } = await auth.supabase.from("pets").insert(...);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}
```

### 5. Zod Schemas & Types
- All form inputs validated with Zod schemas in `lib/validations/<domain>.ts`
- All database types in `lib/types/<domain>.ts`
- Barrel re-exports: `lib/types/index.ts` and `lib/validations/index.ts`
- Import via `@/lib/types` and `@/lib/validations`, not individual files

### 6. Cursor-Based Pagination Only
- Never use offset pagination — use cursor-based (`lib/pagination.ts`)
- Prevents race conditions with real-time data (Supabase RLS)

### 7. Leaflet Maps
- MUST use `dynamic(() => import(...), { ssr: false })`
- Leaflet doesn't support server-side rendering
- Example: `const HospitalMap = dynamic(() => import("@/components/hospital-map"), { ssr: false })`

### 8. Conditional Styles
- Use `cn()` from `@/lib/utils` for merging classNames
- `cn()` handles Tailwind class conflicts automatically
- Example: `cn("px-4", isActive && "bg-blue-500")`

### 9. Database Tables with RLS
- ALL 11 tables have Row-Level Security policies
- ALL child records CASCADE DELETE when parent deleted
- Example: Delete a pet → all vaccinations, photos, and health events auto-delete

### 10. No Admin Roles
- All authenticated users have equal permissions
- Ownership checks on all PUT/DELETE operations
- Example: Can only edit your own pets: `owner_id === auth.user.id`

---

## Configuration Options

### Build & Dev Server
- **Dev server:** `npm run dev --webpack` (Turbopack in dev, webpack for PWA)
- **Build:** `npm run build --webpack` (webpack required for Serwist PWA bundle)
- **Production:** `npm run start`

### Testing Configuration
- **Unit/component tests:** Vitest (jsdom environment, 375 tests, 96.48% coverage)
- **Coverage thresholds:** 90% statements/functions, 85% branches (per-file enforced)
- **E2E tests:** Playwright (Chromium + Firefox, 46 specs)
- **Coverage:** Test coverage defined in `vitest.config.ts`

### Tailwind CSS
- Version 4 with `@tailwindcss/postcss`
- Configured in `tailwind.config.ts`
- Theme color: `#FF8263` (orange)
- Font: Noto Sans Thai (Google Fonts, 400/600/700/800 weights)

### PWA Configuration (Serwist)
- Service worker source: `app/sw.ts`
- Output: `public/sw.js`
- Configured in `next.config.ts`
- **Note:** Build requires webpack flag for PWA bundle to work

### Next.js Configuration
- App Router (Next.js 16.2.2)
- Remote image patterns: Supabase storage URLs
- Allowed dev origins: `*.ngrok-free.dev`

### Line LIFF Configuration
- Initialization in `lib/liff.ts` — single call per session
- LIFF ID per environment (production/preview/development must be different)
- LINE Messaging API for Rich Menu and webhooks
- See `Docs/environment-setup.md` for full env var matrix

---

## Common Workflows

### 1. Creating a New Pet (Happy Path)
1. User clicks "Add Pet" button on `/pets`
2. `<CreatePetForm>` renders with species dropdown and image cropper
3. Form submits to `POST /api/pets` with validated petSchema
4. API route checks auth, rate-limit, validates, creates pet + auto-creates profile if missing
5. Photo uploaded to Supabase Storage (`/storage/v1/object/public/pet-photos/`)
6. Page refetches pets list and shows confirmation

**Files involved:**
- `/app/pets/page.tsx` — Page
- `/components/create-pet-form.tsx` — Form component
- `/lib/validations/pets.ts` — Zod schema
- `/app/api/pets/route.ts` — POST handler

### 2. Tracking a Vaccination (Happy Path)
1. User opens a pet detail page (`/pets/[id]`) and clicks "Add Vaccination"
2. `<AddVaccineForm>` renders with vaccine dropdown from `data/vaccines.ts`
3. Form submits to `POST /api/vaccinations` with validated schema
4. API checks ownership, rate-limit, validates, inserts vaccination record
5. Status calculated automatically: "protected" (future date), "due_soon", or "overdue"
6. Timeline updates with new vaccine record

**Files involved:**
- `/app/pets/[id]/page.tsx` — Pet detail page
- `/components/add-vaccine-form.tsx` — Form component
- `/lib/validations/health.ts` — Zod schema
- `/app/api/vaccinations/route.ts` — POST handler
- `/data/vaccines.ts` — Vaccine database

### 3. Broadcasting an SOS Alert (Happy Path)
1. User clicks "SOS" from bottom nav, lands on `/sos`
2. Map picker shows current location via geolocation (fallback: Bangkok)
3. User confirms location and submits alert with optional video upload
4. `POST /api/sos` → auth, rate-limit (3/5min), validate, insert alert
5. Notification sent to LINE users in Pawrent ecosystem within 5km (Haversine distance)
6. Other users see alert in `/notifications` feed

**Files involved:**
- `/app/sos/page.tsx` — SOS creation page
- `/components/map-picker.tsx` — Geolocation map
- `/lib/validations/found.ts` — Zod schema
- `/app/api/sos/route.ts` — POST/PUT handlers
- Haversine distance in database queries

### 4. Viewing Community Feed (Happy Path)
1. User opens home page (`/`) — Server Component fetches first 20 posts
2. Each post shows photo, pet tag (if any), caption, like count
3. User clicks like → `POST /api/posts/like` with Supabase RPC
4. RPC is atomic (prevents double-likes via upsert)
5. UI updates optimistically while request in flight
6. User scrolls → cursor pagination loads next 20 posts

**Files involved:**
- `/app/page.tsx` — Home page (Server Component)
- `/components/post-card.tsx` — Post display
- `/lib/db.ts` — getPosts() with cursor pagination
- `/app/api/posts/like/route.ts` — Like toggle

### 5. Finding a Vet (Happy Path)
1. User opens `/hospital` → Server Component loads hospital list from database
2. `<HospitalMap>` (dynamic component, SSR false) initializes Leaflet map
3. Map auto-centers on user's geolocation (fallback: Bangkok)
4. Markers show vet clinics with details: hours, phone, specialists, certified badge
5. Click marker → open clinic details
6. "Call" button → `tel:` link, "Directions" → Google Maps link

**Files involved:**
- `/app/hospital/page.tsx` — Hospital page
- `/components/hospital-map.tsx` — Leaflet map (must be dynamic)
- `/lib/db.ts` — getHospitals()
- `/data/hospitals.json` — Clinic data

### 6. Editing User Profile (Happy Path)
1. User opens `/profile` and clicks "Edit Avatar"
2. Image cropper opens (react-easy-crop)
3. User crops image and submits
4. `PUT /api/profile` uploads image to Supabase Storage, updates profile row
5. Avatar updated in nav bar

**Files involved:**
- `/app/profile/page.tsx` — Profile page
- `/components/image-cropper.tsx` — Crop tool
- `/lib/db.ts` — uploadProfileAvatar()
- `/app/api/profile/route.ts` — PUT handler

### 7. Submitting Feedback (Happy Path)
1. User opens `/feedback` and submits form
2. `POST /api/feedback` accepts auth token (optional) + feedback text
3. Rate-limited by IP for anonymous users
4. Inserted into `feedback` table
5. Optional: User notified via LINE OA

**Files involved:**
- `/app/feedback/page.tsx` — Feedback form
- `/lib/validations/common.ts` — Feedback schema
- `/app/api/feedback/route.ts` — POST handler

---

## Notable Gotchas & Common Mistakes

### 1. **Using Wrong Supabase Client**
**Problem:** Hydration errors or auth failures.
**Solution:** 
- Server Components → `lib/supabase-server.ts`
- Client Components → `lib/supabase.ts`
- Route handlers → `lib/supabase-api.ts` with `createApiClient(authHeader)`

### 2. **Leaflet Map Server-Side Rendering**
**Problem:** Map component crashes at build time.
**Solution:** ALWAYS use dynamic import with `ssr: false`:
```typescript
const HospitalMap = dynamic(() => import("@/components/hospital-map"), { ssr: false });
```

### 3. **Missing LIFF Initialization**
**Problem:** `window.liff is undefined` error.
**Solution:** Wrap entire app in `<LiffProvider>` in `layout.tsx`. Check `app/layout.tsx` for provider order.

### 4. **Offset Pagination**
**Problem:** Race conditions, missing records, duplicates.
**Solution:** Always use cursor-based pagination (`lib/pagination.ts`). NO `OFFSET` clauses in Supabase queries.

### 5. **Skipping Rate Limits on New Endpoints**
**Problem:** Abuse, DDoS, Upstash quota overages.
**Solution:** Every mutation endpoint MUST call `checkRateLimit()`. Use appropriate limits:
- User-scoped: `/pets`, `/sos`, `/posts`, `/vaccinations`, `/parasite-logs`, `/pet-photos`, `/profile`
- IP-scoped: `/feedback` (anonymous feedback)

### 6. **Adding Validation Schemas Without Testing**
**Problem:** Silent failures, invalid data in database.
**Solution:** Write Zod schema first, then write test for schema, then implement. Use `schema.safeParse()` in route handlers.

### 7. **PDPA Compliance Miss**
**Problem:** ฿5M criminal liability.
**Solution:**
- All new tables must be included in `/api/me/data-export` response
- All tables must have CASCADE DELETE on parent record deletion
- All data deletions must be logged (audit trail)
- When user deletes account, cascade-delete all personal data
- New feature idea? Check `CLAUDE.md` PDPA section first.

### 8. **Image File Size Limits**
**Problem:** Upload fails silently, or huge images slowing app.
**Solution:** Validate before upload:
- Images: 5MB max (JPEG/PNG/WebP)
- Videos: 50MB max (MP4/MOV)
- Always resize/compress client-side before Supabase upload

### 9. **Missing Ownership Checks on PUT/DELETE**
**Problem:** User A edits/deletes User B's pet.
**Solution:** Every PUT/DELETE route handler MUST verify `owner_id === auth.user.id` or `creator_id === auth.user.id`.

### 10. **Committing `.env.local`**
**Problem:** Secrets leak, Supabase keys exposed.
**Solution:** `.env.local` is gitignored. Use `.env.example` as template only. NEVER hardcode env vars.

### 11. **E2E Tests Out of Sync with Code**
**Problem:** CI fails because test expects old behavior.
**Solution:** If your PR changes UI, auth flow, routing, or page behavior, UPDATE `e2e/` specs before commit. This is the #1 CI failure cause.

### 12. **Forgetting Mobile Viewport**
**Problem:** Desktop-first designs break on phone (our target users).
**Solution:** Always test with DevTools mobile mode or actual phone. Design mobile-first.

### 13. **Not Testing Coverage Before Commit**
**Problem:** CI blocks PR for coverage drop.
**Solution:** Run `npm run test:coverage` before pushing. Per-file thresholds enforced (90% statements/functions, 85% branches).

### 14. **Importing from `lib/types` Without Barrel**
**Problem:** Circular imports, build errors.
**Solution:** Import from `@/lib/types`, not `@/lib/types/common.ts`. Same for validations.

### 15. **Hardcoding RLS Policies**
**Problem:** Silent failures, data leaks.
**Solution:** All table mutations check RLS policies in Supabase. Never assume a query will work — test in Supabase console first.

---

## Key File Paths (for Quick Navigation)

| Purpose | File(s) |
| --- | --- |
| **Auth context** | `/components/liff-provider.tsx` (use this, not auth-provider) |
| **Database operations** | `/lib/db.ts` (42 data access functions) |
| **API validation** | `/lib/validations/` (Zod schemas by domain) |
| **Database types** | `/lib/types/` (TypeScript interfaces by domain) |
| **Supabase clients** | `/lib/supabase.ts`, `/lib/supabase-server.ts`, `/lib/supabase-api.ts` |
| **Rate limiting** | `/lib/rate-limit.ts` |
| **API fetch helper** | `/lib/api.ts` (with auth injection) |
| **Pet status calculations** | `/lib/pet-utils.ts` |
| **Static data** | `/data/species.json`, `/data/breeds.json`, `/data/vaccines.ts` |
| **Main page** | `/app/page.tsx` (community feed) |
| **Pet routes** | `/app/pets/` (CRUD) |
| **SOS routes** | `/app/sos/` + `/app/notifications/` |
| **Hospital map** | `/app/hospital/page.tsx` + `/components/hospital-map.tsx` |
| **Profile** | `/app/profile/page.tsx` |
| **Feedback** | `/app/feedback/page.tsx` |
| **Bottom nav** | `/components/bottom-nav.tsx` (5-tab navigation) |
| **Agent instructions** | `CLAUDE.md` (read this first) |
| **Conductor state** | `conductor/` (project status, PRPs, decisions) |
| **Tests** | `__tests__/` (375 unit/component), `e2e/` (46 E2E specs) |
| **Config files** | `next.config.ts`, `vitest.config.ts`, `playwright.config.ts` |

---

## Database Schema (11 Tables, All with RLS)

| Table | Purpose | Key Fields | Relationships |
| --- | --- | --- | --- |
| `profiles` | User accounts | `id` (UUID), `name`, `avatar_url`, `email` | 1:N pets, posts |
| `pets` | Pet profiles | `id`, `owner_id`, `species`, `breed`, `dob`, `microchip`, `photo_url` | 1:N vaccinations, parasite_logs, health_events, sos_alerts, pet_photos |
| `vaccinations` | Vaccine records | `id`, `pet_id`, `vaccine_name`, `administered_date`, `next_due_date` | Belongs to pet |
| `parasite_logs` | Parasite prevention | `id`, `pet_id`, `medicine_name`, `administered_date`, `next_due_date` | Belongs to pet |
| `health_events` | Lab results, diagnoses, checkups | `id`, `pet_id`, `event_type`, `event_date`, `notes` | Belongs to pet |
| `sos_alerts` | Lost pet alerts | `id`, `pet_id`, `creator_id`, `lat`, `lng`, `status` | Belongs to pet + profile |
| `posts` | Community feed | `id`, `creator_id`, `pet_id` (optional), `caption` | Belongs to profile, optional pet |
| `post_likes` | Like toggle | `id`, `post_id`, `profile_id` | Belongs to post + profile |
| `pet_photos` | Pet photo gallery | `id`, `pet_id`, `photo_url`, `display_order` | Belongs to pet |
| `feedback` | User feedback | `id`, `profile_id` (optional), `message`, `created_at` | Optional profile |
| `hospitals` | Vet clinic directory | `id`, `name`, `hours`, `phone`, `specialists`, `certified` | Standalone, public read |

All child records **CASCADE DELETE** when parent deleted (e.g., delete pet → delete all vaccinations).

---

## NPM Scripts Quick Reference

```bash
# Development
npm run dev              # Start dev server (Turbopack)
npm run build            # Production build (--webpack required for PWA)
npm run start            # Production server

# Testing
npm test                 # Run unit/component tests (Vitest)
npm run test:coverage    # Coverage report (per-file thresholds enforced)
npm run test:watch       # Watch mode
npm run test:e2e         # E2E tests (Playwright, Chromium + Firefox)

# Code Quality
npm run lint             # ESLint check
npm run format           # Prettier write
npm run format:check     # Prettier check only
npm run type-check       # TypeScript strict mode (tsc --noEmit)

# Prepare before commit (MANDATORY GATE)
npm run test:coverage    # Must pass
npm run test:e2e         # Must pass
npm run type-check       # Must pass
npm run format           # Format before commit
```

---

## Next Steps for New Developers

1. **Read CLAUDE.md** — Agent instructions, architecture rules, session protocol
2. **Set up environment** — Copy .env.example → .env.local, add your Supabase/Redis/LINE keys
3. **Start dev server** — `npm run dev --webpack`
4. **Test locally** — `npm test` should pass with 96.48% coverage baseline
5. **Pick a task** — Read `conductor/index.md` to see active PRPs and unclaimed tasks
6. **Follow TDD** — RED → GREEN → REFACTOR → GATE for every task
7. **Validate before commit** — `npm run test:coverage && npm run test:e2e && npm run type-check`
8. **Update E2E specs** — If your PR changes UI/auth/routing, update `e2e/` specs
9. **Commit with convention** — `feat|fix|docs|test: <subject>` + CommitLint enforced

---

## Common Commands Cheat Sheet

```bash
# New developer setup
git clone <repo> && cd pawrent && npm install
cp .env.example .env.local
# Edit .env.local with your keys
npm run dev --webpack

# Before committing (mandatory)
npm run format
npm run lint --fix
npm run test:coverage    # Must pass with 90% statements/functions, 85% branches
npm run test:e2e         # Must pass (Chromium + Firefox)
npm run type-check       # Must pass (TypeScript strict)

# During development
npm run test:watch       # Watch unit tests as you code
npm run dev --webpack    # Always run with --webpack for PWA support

# Debugging
npm run test -- <filename>  # Run specific test file
npm run test:e2e -- <spec>  # Run specific E2E spec

# Deployment
vercel env pull .env.local  # Pull Vercel env vars to local
vercel deploy               # Preview deployment
vercel --prod               # Production deployment
```

---

## When You're Stuck

1. **Check `CLAUDE.md`** — Architecture rules, prohibited actions, protocols
2. **Check `conductor/index.md`** — Current status and active PRPs
3. **Search `lib/types/` and `lib/validations/`** — Types and schemas for your domain
4. **Check similar route handler** — `/app/api/pets/route.ts` is a good template
5. **Check test file** — `__tests__/app/api/pets.test.ts` shows usage patterns
6. **Run `npm test:coverage`** — See coverage gaps before implementing
7. **Ask in conductor/decisions.md** — Previous architectural decisions may apply
8. **Check LINE Messaging API docs** — `/lib/line-templates/` for message formats

---

## Quick Links

- **GitHub:** [Pawrent repo](https://github.com/switch-pawrent/pawrent) *(internal)*
- **Supabase:** [Dashboard](https://app.supabase.com)
- **Vercel:** [Deployments](https://vercel.com/dashboard)
- **LINE:** [Console](https://manager.line.biz/)
- **Upstash:** [Redis console](https://console.upstash.com/)
- **Next.js Docs:** https://nextjs.org/docs
- **Supabase Docs:** https://supabase.com/docs
- **Zod Docs:** https://zod.dev
- **Tailwind CSS:** https://tailwindcss.com/docs
- **Playwright:** https://playwright.dev

---

**Last Updated:** April 26, 2026 | **Version:** Pawrent 0.4.1
