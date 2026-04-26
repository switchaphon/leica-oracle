# Pawrent — Architecture Documentation

**Project:** Pawrent (v0.4.1)  
**Type:** Next.js 16 + React 19 + TypeScript + Supabase PWA  
**Date:** 2026-04-26  
**Purpose:** Pet health & safety platform with LINE messaging integration, lost/found reporting, and geospatial discovery

---

## Table of Contents

1. [Directory Structure & Organization](#directory-structure--organization)
2. [Entry Points](#entry-points)
3. [Core Abstractions & Relationships](#core-abstractions--relationships)
4. [Tech Stack & Dependencies](#tech-stack--dependencies)
5. [Data Architecture](#data-architecture)
6. [Authentication & Authorization](#authentication--authorization)
7. [API Routes & Request Handling](#api-routes--request-handling)
8. [State Management & Context](#state-management--context)
9. [Component Architecture](#component-architecture)
10. [TYPE & VALIDATION SPLIT](#type--validation-split)
11. [Build & Runtime Configuration](#build--runtime-configuration)

---

## Directory Structure & Organization

### Root-Level Layout

```
/Users/switchaphon/_POPs_/pawrent/
├── app/                          # Next.js App Router (pages + API routes)
├── components/                   # React components (UI + client logic)
├── lib/                           # Utilities, types, validations, database
├── conductor/                     # Project notes & decisions (not code)
├── public/                        # Static assets, PWA manifest, fonts
├── supabase/                      # Database migrations & schema
├── __tests__/                     # Unit & integration tests (Vitest)
├── e2e/                           # End-to-end tests (Playwright)
├── PRPs/                          # Product planning docs (roadmap)
├── CHANGELOG.md                   # Release notes
├── CLAUDE.md                      # Agent working guidelines
├── package.json                   # Dependencies
├── next.config.ts                 # Next.js configuration
├── tsconfig.json                  # TypeScript configuration
├── playwright.config.ts           # E2E test configuration
├── vitest.config.ts               # Unit test configuration
└── .vercel/                       # Vercel deployment config
```

### app/ Directory Tree

```
app/
├── api/                           # Route handlers (server-only)
│   ├── alerts/                    # Push notification endpoints
│   ├── auth/                      # Authentication endpoints
│   │   └── line/                  # LINE OAuth token exchange
│   ├── conversations/             # Community chat
│   ├── cron/                      # Scheduled jobs (health reminders, celebrations)
│   ├── feedback/                  # Bug reports & feature requests
│   ├── found-reports/             # Found pet reporting
│   ├── hospitals/                 # Hospital search & location data
│   ├── line/                      # LINE messaging webhooks & rich menu
│   ├── og/                        # Open Graph image generation
│   ├── parasite-logs/             # Parasite prevention tracking
│   ├── pet-photos/                # Photo uploads
│   ├── pet-weight/                # Weight logging
│   ├── pets/                      # Pet CRUD operations
│   ├── post/                      # Lost/found post management
│   ├── posts/                     # Post discovery & feed
│   ├── poster/                    # Poster/flyer generation
│   ├── profile/                   # User profile operations
│   ├── share-card/                # Sharing & social features
│   ├── sightings/                 # Lost pet sighting updates
│   ├── vaccinations/              # Vaccine tracking
│   └── voice/                     # Voice message uploads
├── conversations/                 # Community chat UI
├── feedback/                      # Feedback form page
├── hospital/                      # Hospital discovery map
├── notifications/                 # Push notification center
├── offline/                       # Offline fallback page
├── pets/                          # Pet management dashboard
│   ├── [id]/                      # Pet detail pages
│   └── page.tsx                   # Pet list page
├── post/                          # Lost/found posts
│   ├── [id]/                      # Post detail page
│   ├── found/                     # Found pet reporting flow
│   ├── lost/                      # Lost pet reporting flow
│   └── page.tsx                   # Post feed page
├── profile/                       # User profile page
├── sos/                           # Emergency/SOS page (Pet Reports)
├── layout.tsx                     # Root layout with providers
├── page.tsx                       # Home dashboard
├── error.tsx                      # Error boundary
├── not-found.tsx                  # 404 page
├── loading.tsx                    # Loading skeleton
├── globals.css                    # Tailwind CSS & design tokens
└── sw.ts                          # Service worker (PWA)
```

### components/ Directory Tree

```
components/
├── ui/                            # ShadCN UI primitives
│   ├── avatar.tsx                 # User/pet avatars
│   ├── badge.tsx                  # Status badges
│   ├── button.tsx                 # Button component
│   ├── card.tsx                   # Card layout
│   ├── input.tsx                  # Form input
│   ├── label.tsx                  # Form labels
│   ├── pill-tag.tsx               # Inline tags
│   └── toast.tsx                  # Toast notifications
├── post/                          # Post feature components
│   ├── alert-card.tsx             # Lost pet alert display
│   ├── found-report-card.tsx       # Found pet card
│   ├── poster-buttons.tsx          # Share/print buttons
│   ├── radius-selector.tsx         # Map radius filter
│   ├── species-filter.tsx          # Species filter UI
│   ├── voice-player.tsx            # Audio playback
│   └── types.ts                   # Post component types
├── add-parasite-log-form.tsx       # Parasite prevention form
├── add-vaccine-form.tsx            # Vaccination form
├── bottom-nav.tsx                 # Mobile bottom navigation
├── confirm-dialog.tsx              # Confirmation modal
├── create-pet-form.tsx             # Pet creation flow
├── create-post-form.tsx            # Post creation (lost/found)
├── debug-console.tsx               # Development console
├── edit-pet-form.tsx               # Pet editing form
├── empty-state.tsx                 # Empty state UI
├── error-state.tsx                 # Error display
├── health-timeline.tsx             # Health milestone visualization
├── hospital-map.tsx                # Hospital discovery map
├── image-cropper.tsx               # Image cropping tool
├── liff-provider.tsx               # LINE auth context provider
├── location-banner.tsx             # Location permission banner
├── location-provider.tsx            # Geolocation context provider
├── map-picker.tsx                  # Map-based location picker
├── milestone-timeline.tsx           # Pet milestone tracker
├── navigation-shell.tsx             # Main navigation wrapper
├── pet-card.tsx                    # Pet card component
├── pet-profile-card.tsx             # Pet detail card
├── photo-gallery.tsx               # Photo grid display
├── photo-lightbox.tsx              # Full-screen photo viewer
├── report-button.tsx               # Lost/found report button
├── searchable-select.tsx            # Searchable dropdown
├── skeleton-card.tsx                # Loading skeleton
├── vaccine-status-bar.tsx           # Vaccination status indicator
├── voice-recorder.tsx              # Audio recording
└── weight-chart.tsx                # Weight tracking visualization
```

### lib/ Directory Tree

```
lib/
├── api.ts                         # API client fetch wrapper
├── auth-token.ts                  # Token storage (cookies, LocalStorage fallback)
├── db.ts                          # Database helper functions
├── liff.ts                        # LINE LIFF SDK wrapper
├── line-messaging.ts              # LINE message formatting
├── line-templates/                # MESSAGE TEMPLATES
│   ├── celebration.ts             # Birthday/milestone msgs
│   ├── found-pet-alert.ts         # Found pet notifications
│   ├── health-reminder.ts         # Vaccine/parasite reminders
│   ├── lost-pet-alert.ts          # Lost pet notifications
│   ├── match-found.ts             # Matching alerts
│   └── sighting-update.ts         # Sighting follow-ups
├── line/                          # LINE BOT SDK
│   ├── client.ts                  # LINE Messaging API client
│   ├── rich-menu.ts               # Rich menu management
│   └── webhook.ts                 # Webhook handler
├── pagination.ts                  # Cursor-based pagination
├── pet-utils.ts                   # Pet data utilities
├── rate-limit.ts                  # Upstash Redis rate limiting
├── supabase.ts                    # CLIENT Supabase instance
├── supabase-server.ts             # SERVER Supabase instance
├── supabase-api.ts                # API ROUTE Supabase instance
├── utils.ts                       # General utilities (cn, etc.)
├── types/                         # TYPE DEFINITIONS (SPLIT BY DOMAIN)
│   ├── index.ts                   # Barrel re-export
│   ├── common.ts                  # User, Profile types
│   ├── conversations.ts            # Chat/community types
│   ├── found.ts                   # Found pet types
│   ├── geospatial.ts              # Location types
│   ├── health.ts                  # Health event types
│   ├── pet-report.ts              # Lost/found report types
│   ├── pets.ts                    # Pet types
│   ├── posts.ts                   # Social post types
│   └── push.ts                    # Push notification types
└── validations/                   # ZOD SCHEMAS (SPLIT BY DOMAIN)
    ├── index.ts                   # Barrel re-export
    ├── auth.ts                    # Auth validation schemas
    ├── common.ts                  # Common schemas
    ├── found.ts                   # Found pet schemas
    ├── health.ts                  # Health schemas
    ├── pet-report.ts              # Report schemas
    ├── pets.ts                    # Pet schemas
    ├── posts.ts                   # Post schemas
    └── push.ts                    # Push notification schemas
```

### supabase/ Migrations

```
supabase/migrations/
├── 20260412000001_enable_postgis.sql
├── 20260412000002_add_geography_columns.sql
├── 20260412000003_backfill_geog_trigger.sql
├── 20260412000004_geospatial_rpc.sql
├── 20260412000005_geospatial_rls.sql
├── 20260413000001_rename_sos_to_pet_reports.sql
├── 20260414000001_add_pet_neutered.sql
├── 20260414000002_lost_pet_columns.sql
├── 20260414000003_fix_nearby_reports_rpc.sql
├── 20260414000005_readd_lost_pet_columns.sql
├── 20260414000006_found_reports_tables.sql
├── 20260414100000_pet_health_passport.sql
└── 20260414100001_push_notifications.sql
```

### public/ Assets

```
public/
├── fonts/                         # Thai font (Sarabun)
│   ├── Sarabun-Bold.ttf
│   └── Sarabun-Regular.ttf
├── leaflet/                       # Leaflet map icons
│   ├── marker-icon.png
│   ├── marker-icon-2x.png
│   └── marker-shadow.png
├── landing/                       # Marketing landing page
│   ├── index.html
│   ├── assets/
│   ├── analytics.js
│   ├── tailwind.css
│   └── README.md
├── manifest.json                  # PWA manifest
├── sw.js                          # Service worker (built from app/sw.ts)
└── *.svg, *.ico                   # Static assets
```

---

## Entry Points

### 1. Web Application

| Entry Point                  | Type        | Purpose                    |
| ---------------------------- | ----------- | -------------------------- |
| `app/layout.tsx`             | Server      | Root layout with providers |
| `app/page.tsx`               | Client      | Home dashboard             |
| `app/sw.ts`                  | Browser     | Service worker for PWA     |
| `public/manifest.json`       | PWA         | PWA metadata               |

### 2. API Routes (Next.js Route Handlers)

**Authentication:**
- `app/api/auth/line/route.ts` - POST: Exchange LINE ID token → Supabase JWT

**Pet Management:**
- `app/api/pets/route.ts` - GET, POST, PUT, DELETE pet CRUD

**Pet Health:**
- `app/api/vaccinations/route.ts` - Vaccination tracking
- `app/api/parasite-logs/route.ts` - Parasite prevention logs
- `app/api/pet-weight/route.ts` - Weight tracking

**Lost/Found Reports:**
- `app/api/post/route.ts` - POST: Create lost/found alert
- `app/api/posts/route.ts` - GET: List posts with pagination
- `app/api/found-reports/route.ts` - Found pet reporting

**Notifications & Messaging:**
- `app/api/line/webhook/route.ts` - LINE bot webhook
- `app/api/line/rich-menu/route.ts` - Rich menu API
- `app/api/alerts/push/route.ts` - Push notifications

**Social & Discovery:**
- `app/api/post/[id]/route.ts` - Individual post details
- `app/api/sightings/route.ts` - Sighting updates
- `app/api/hospitals/route.ts` - Hospital search
- `app/api/conversations/route.ts` - Community chat

**Media:**
- `app/api/pet-photos/route.ts` - Photo uploads
- `app/api/voice/route.ts` - Voice messages
- `app/api/share-card/route.ts` - Sharing cards
- `app/api/poster/route.ts` - Poster generation
- `app/api/og/route.ts` - Open Graph images

**User:**
- `app/api/profile/route.ts` - User profile

**Utilities:**
- `app/api/cron/health-reminders/route.ts` - Scheduled health reminders
- `app/api/cron/celebrations/route.ts` - Birthday reminders
- `app/api/feedback/route.ts` - Bug reports

### 3. Configuration Entry Points

| File                 | Purpose                                      |
| -------------------- | -------------------------------------------- |
| `next.config.ts`     | Next.js + Serwist PWA configuration          |
| `tsconfig.json`      | TypeScript strict mode, path aliases (@/*)   |
| `vitest.config.ts`   | Unit/component testing                       |
| `playwright.config.ts`| E2E testing                                   |
| `tailwind.config.mjs` | (Generated) CSS-first Tailwind v4             |
| `postcss.config.mjs`  | Tailwind CSS processing                      |

---

## Core Abstractions & Relationships

### 1. Authentication & Authorization

```
LiffProvider (Context)
    ↓
    ├─ initializeLiff() → LINE LIFF SDK
    ├─ getLiffIdToken() → ID token
    ├─ /api/auth/line → Supabase JWT
    └─ setAuthToken() → Token storage

useAuth() hook
    ↓
    ├─ user: Profile | null
    ├─ loading: boolean
    └─ isInLiff: boolean
```

**Flow:**
1. `LiffProvider` initializes LINE LIFF SDK on mount
2. Gets LINE ID token from LIFF context
3. POSTs to `/api/auth/line` with ID token
4. Server verifies token via LINE OAuth API
5. Creates/updates user in Supabase auth
6. Returns Supabase JWT + Profile object
7. Token stored in cookies (Supabase SSR) + fallback to LocalStorage

**Key Files:**
- `lib/liff.ts` - LIFF wrapper
- `components/liff-provider.tsx` - Auth context
- `lib/auth-token.ts` - Token persistence
- `app/api/auth/line/route.ts` - Token exchange
- `lib/supabase.ts` - Client Supabase (uses auth token)

### 2. Data Layer (Three Supabase Clients)

Each context uses the appropriate Supabase client:

```
                ┌─────────────────────────────────────┐
                │         Supabase Postgres          │
                │  (Pets, Profiles, Reports, Posts)  │
                │  + RLS (Row-Level Security)        │
                │  + Postgis (Geospatial)            │
                │  + Realtime                        │
                └─────────────────────────────────────┘
                        ↑         ↑         ↑
       ┌────────────────┴─────────┼─────────┴─────────────┐
       │                          │                       │
lib/supabase.ts          lib/supabase-server.ts  lib/supabase-api.ts
(Client Components)      (Server Components)     (Route Handlers)
```

**lib/supabase.ts** (Client-side):
- Used in client components (`"use client"`)
- Passes auth token via callback
- Non-persistent sessions (LIFF owns auth state)
- Example: `app/page.tsx`, `components/pet-card.tsx`

**lib/supabase-server.ts** (Server-side):
- Used in Server Components & server actions
- Reads/manages auth from cookies
- Can refresh tokens via middleware
- Example: `app/api` routes (v0.5 migration target)

**lib/supabase-api.ts** (API context):
- Used in Route Handlers only
- Takes auth token from request headers
- No session persistence
- Example: `app/api/pets/route.ts`, `app/api/post/route.ts`

### 3. Database Operations

**Main Pattern:**

```
Component/Route
    ↓
lib/db.ts (Helper functions)
    ├─ getPets(ownerId)
    ├─ getPetWithDetails(petId)
    ├─ createPet(pet)
    ├─ updatePet(petId, updates)
    ├─ uploadPetPhoto(file, petId)
    └─ ... (50+ functions)
    ↓
Supabase Client (one of three above)
    ↓
Postgres Database + RLS
```

**RLS (Row-Level Security):**
- All policies enforce `user_id` matching
- Users can only see/edit their own pets, profiles, reports
- Posts are public for discovery
- Sightings require authentication

### 4. Validation & Type Safety

**All inputs validated with Zod schemas:**

```
Request
    ↓
Body.json()
    ↓
Schema.safeParse(body)  [Zod]
    ├─ .success? → Return typed data
    └─ .error? → Return 400 with message
    ↓
Database operation
```

**Types & Schemas split by domain:**
- `lib/types/pets.ts` + `lib/validations/pets.ts`
- `lib/types/posts.ts` + `lib/validations/posts.ts`
- `lib/types/pet-report.ts` + `lib/validations/pet-report.ts`
- etc.

**Barrel re-exports** for convenience:
- `@/lib/types` → all domains
- `@/lib/validations` → all domains

### 5. Rate Limiting

```
Upstash Redis (via @upstash/redis)
    ↓
createRateLimiter(maxRequests, window)  [lib/rate-limit.ts]
    ↓
checkRateLimit(limiter, userId)
    ├─ 429 Too Many Requests? → Return error
    └─ OK? → Proceed
```

**Examples:**
- LINE auth: 10 req/min per user
- Create post: 3 req/24h per user (anti-spam)
- Pet CRUD: 10-20 req/min per user

### 6. LINE Messaging Integration

```
User in LINE              External Browser
       ↓                         ↓
   LIFF Auth            ← LIFF URL with redirectUri
       ↓
  ID Token → Exchange  → Supabase JWT
                 ↓
             Use in app ←──────────┐
                 ↓
    /api/line/webhook ← LINE Bot messages
       ↓
  Send LINE messages ← lib/line-messaging.ts
       ├─ Lost pet alert template
       ├─ Found pet notification
       ├─ Health reminder
       ├─ Match found
       └─ Celebration
```

**LINE Rich Menu:**
- Top navigation for LIFF app
- Managed via `lib/line/rich-menu.ts`
- Configured by PRPs (lost-pet, found-pet, discovery, etc.)

---

## Tech Stack & Dependencies

### Runtime & Framework

```json
{
  "next": "^16.2.2",          // App Router, image optimization
  "react": "19.2.3",          // Latest with use-cache support
  "react-dom": "19.2.3",
  "typescript": "^5"          // Strict mode
}
```

### UI & Styling

```json
{
  "tailwindcss": "^4",              // CSS-first, no config file
  "@tailwindcss/postcss": "^4",
  "lucide-react": "^0.562.0",       // Icons
  "@radix-ui/react-avatar": "^1.1.11",
  "@radix-ui/react-label": "^2.1.8",
  "@radix-ui/react-slot": "^1.2.4",
  "class-variance-authority": "^0.7.1",  // CVA for variants
  "clsx": "^2.1.1",                      // Conditional classes
  "tailwind-merge": "^3.4.0"             // Merge Tailwind classes
}
```

### Database & Auth

```json
{
  "@supabase/supabase-js": "^2.90.1",      // Client SDK
  "@supabase/ssr": "^0.10.0",              // Server auth
  "@upstash/redis": "^1.37.0",             // Rate limiting
  "@upstash/ratelimit": "^2.0.8"           // Rate limiter
}
```

### LINE Messaging

```json
{
  "@line/bot-sdk": "^11.0.0",       // Server-side bot
  "@line/liff": "^2.28.0"           // Client-side LIFF
}
```

### Maps & Location

```json
{
  "leaflet": "^1.9.4",              // Maps library
  "react-leaflet": "^5.0.0"         // React wrapper
}
```

### Media & Files

```json
{
  "react-easy-crop": "^5.5.6",      // Image cropping
  "pdf-lib": "^1.17.1",             // PDF generation
  "@pdf-lib/fontkit": "^1.1.1",
  "qrcode": "^1.5.4",               // QR code generation
  "@types/qrcode": "^1.5.6"
}
```

### PWA

```json
{
  "@serwist/next": "^9.5.7",        // PWA service worker
  "serwist": "^9.5.7"
}
```

### Validation & Security

```json
{
  "zod": "^4.3.6",                  // Schema validation
  "jose": "^6.2.2"                  // JWT signing/verification
}
```

### Development & Testing

```json
{
  "vitest": "^4.1.2",                     // Unit testing
  "@testing-library/react": "^16.3.2",
  "@testing-library/jest-dom": "^6.9.1",
  "@playwright/test": "^1.59.1",          // E2E testing
  "eslint": "^9",                         // Linting
  "prettier": "^3.8.1",                   // Formatting
  "husky": "^9.1.7",                      // Git hooks
  "lint-staged": "^16.4.0",               // Staged linting
  "@commitlint/cli": "^20.5.0"            // Commit validation
}
```

### Debug & DevTools

```json
{
  "vconsole": "^3.15.1"             // Mobile console for debugging
}
```

---

## Data Architecture

### Core Tables (Supabase Postgres)

#### Users & Profiles

```sql
-- auth.users (managed by Supabase)
id UUID (PK)
email TEXT UNIQUE
line_user_id TEXT UNIQUE -- Denormalized from LINE token
created_at TIMESTAMP

-- public.profiles
id UUID (PK, FK → auth.users.id)
email TEXT
line_display_name TEXT
avatar_url TEXT
created_at TIMESTAMP
```

#### Pets

```sql
public.pets
id UUID (PK)
owner_id UUID (FK → profiles.id, RLS enforced)
name TEXT NOT NULL
species ENUM ('dog', 'cat', 'bird', 'rabbit', ...)
breed TEXT
color TEXT
sex ENUM ('male', 'female', 'unknown')
date_of_birth DATE
microchip_number TEXT
neutered BOOLEAN
photo_url TEXT
created_at TIMESTAMP
```

#### Health Records

```sql
public.vaccinations
id UUID (PK)
pet_id UUID (FK → pets.id, RLS)
vaccine_name TEXT
date_administered DATE
due_date DATE (calculated)
notes TEXT
created_at TIMESTAMP

public.parasite_logs
id UUID (PK)
pet_id UUID (FK)
parasite_type ENUM ('flea', 'tick', 'worm')
date_administered DATE
due_date DATE (calculated)
created_at TIMESTAMP

public.health_events
id UUID (PK)
pet_id UUID (FK)
event_type ENUM ('surgery', 'illness', 'checkup', ...)
event_date DATE
description TEXT
created_at TIMESTAMP

public.pet_weight_logs
id UUID (PK)
pet_id UUID (FK)
weight_kg DECIMAL
measured_at TIMESTAMP
created_at TIMESTAMP

public.pet_photos
id UUID (PK)
pet_id UUID (FK)
photo_url TEXT
display_order INTEGER
created_at TIMESTAMP
```

#### Lost/Found Reports

```sql
public.pet_reports
id UUID (PK)
pet_id UUID (FK → pets.id)
owner_id UUID (FK)
alert_type ENUM ('lost', 'found')
status ENUM ('active', 'resolved')
is_active BOOLEAN
lost_date DATE
location_description TEXT
lat DECIMAL
lng DECIMAL
distance_km DECIMAL (calculated by RPC)
pet_name TEXT (snapshot)
pet_species TEXT (snapshot)
pet_breed TEXT (snapshot)
pet_color TEXT (snapshot)
pet_age_text TEXT (snapshot)
pet_sex ENUM (snapshot)
pet_neutered BOOLEAN (snapshot)
microchip_number TEXT (snapshot)
photo_urls TEXT[] (array of URLs)
reward_amount DECIMAL
resolution_status ENUM ('found', 'given_up')
resolved_at TIMESTAMP
created_at TIMESTAMP
```

#### Posts & Social

```sql
public.posts
id UUID (PK)
user_id UUID (FK → profiles.id)
post_type ENUM ('lost_alert', 'found_alert', 'community_photo', 'quiz')
content TEXT
photo_urls TEXT[]
created_at TIMESTAMP

public.post_likes
post_id UUID (FK → posts.id)
user_id UUID (FK → profiles.id)
created_at TIMESTAMP
(composite PK)

public.sightings
id UUID (PK)
report_id UUID (FK → pet_reports.id)
sighter_id UUID (FK → profiles.id)
sighting_location TEXT
sighting_date DATE
description TEXT
created_at TIMESTAMP
```

#### Communities & Chat

```sql
public.conversations
id UUID (PK)
topic TEXT
created_by UUID (FK → profiles.id)
created_at TIMESTAMP

public.conversation_messages
id UUID (PK)
conversation_id UUID (FK)
user_id UUID (FK)
message TEXT
voice_message_url TEXT
created_at TIMESTAMP
```

#### Push Notifications

```sql
public.push_subscriptions
id UUID (PK)
user_id UUID (FK)
endpoint TEXT UNIQUE
auth TEXT
p256dh TEXT
created_at TIMESTAMP

public.push_events
id UUID (PK)
user_id UUID (FK)
event_type ENUM ('lost_pet_alert', 'vaccine_reminder', 'found_match', ...)
title TEXT
body TEXT
icon_url TEXT
data JSONB (custom data)
sent_at TIMESTAMP
created_at TIMESTAMP
```

### Geospatial Features (PostGIS)

```sql
-- Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- Add geography column for distance queries
public.pet_reports
ADD COLUMN location geography(POINT, 4326);

-- Create RPC for nearby reports
CREATE OR REPLACE FUNCTION nearby_reports(
  user_lat DECIMAL,
  user_lng DECIMAL,
  radius_km DECIMAL
) RETURNS TABLE AS ... LANGUAGE SQL
-- Uses ST_DWithin for efficient distance queries
```

---

## Authentication & Authorization

### LINE LIFF → Supabase Flow

**Step 1: LIFF Context**

In LINE app, user clicks link with LIFF URL:
```
https://pawrent.vercel.app/
  (inside LINE WebView context)
```

**Step 2: Get ID Token**

```typescript
// lib/liff.ts
await liff.init()
const idToken = liff.getIDToken()  // JWT signed by LINE
```

**Step 3: Exchange for Supabase JWT**

```typescript
// components/liff-provider.tsx
const response = await fetch('/api/auth/line', {
  method: 'POST',
  body: JSON.stringify({ idToken })
})
// Returns: { access_token, user: Profile }
```

**Step 4: Server Verification**

```typescript
// app/api/auth/line/route.ts
const lineProfile = await verifyLineIdToken(idToken)
// Calls LINE API to verify signature

// Upsert profile in Supabase
const profile = await getOrCreateProfile(lineProfile)

// Sign Supabase JWT
const supabaseJwt = await signSupabaseJwt(userId)
```

**Step 5: Use in App**

```typescript
// lib/auth-token.ts
setAuthToken(supabaseJwt)  // Store in cookies

// lib/supabase.ts
const token = getAuthToken()
return token || ""  // Passed to Supabase client
```

### External Browser (Non-LIFF)

When user is NOT in LINE WebView (e.g., desktop share):
```
1. Redirect to LINE Login (liffLogin())
2. LINE asks for permission
3. Redirect back to app with auth token
4. Same flow as above
```

### Token Refresh & Expiry

- **Supabase JWT:** 1 hour expiry
- **LINE ID Token:** Tied to LINE session
- **Cookie:** HttpOnly, Secure, SameSite=Strict
- **Fallback:** LocalStorage (for LIFF browser compatibility)

### Authorization (RLS)

All Supabase tables use Row-Level Security:

```sql
-- Example: Only owner can see their pets
CREATE POLICY "users_can_read_own_pets" ON public.pets
  FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "users_can_insert_own_pets" ON public.pets
  FOR INSERT WITH CHECK (auth.uid() = owner_id);

-- Example: Anyone can read public posts
CREATE POLICY "posts_are_public" ON public.posts
  FOR SELECT USING (true);
```

---

## API Routes & Request Handling

### Anatomy of a Route Handler

All route handlers follow this pattern:

```typescript
// app/api/resource/route.ts
import { NextRequest, NextResponse } from "next/server";
import { createApiClient } from "@/lib/supabase-api";
import { resourceSchema } from "@/lib/validations";
import { createRateLimiter, checkRateLimit } from "@/lib/rate-limit";

const limiter = createRateLimiter(10, "1 m");

// 1. Get authenticated user
async function getAuthUser(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (!authHeader) return null;
  const supabase = createApiClient(authHeader);
  const { data: { user } } = await supabase.auth.getUser();
  return user ? { user, supabase } : null;
}

// 2. POST handler
export async function POST(request: NextRequest) {
  // Rate limit
  const auth = await getAuthUser(request);
  if (!auth) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  
  const rateLimited = await checkRateLimit(limiter, auth.user.id);
  if (rateLimited) return rateLimited;

  // Validate input
  const body = await request.json();
  const result = resourceSchema.safeParse(body);
  if (!result.success) {
    return NextResponse.json(
      { error: result.error.issues[0].message },
      { status: 400 }
    );
  }

  // Execute
  const { data, error } = await auth.supabase
    .from("resources")
    .insert({ ...result.data, owner_id: auth.user.id })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}

// 3. GET handler
export async function GET(request: NextRequest) {
  // ... similar pattern
}
```

### API Route Families

**Authentication:**
- `POST /api/auth/line` - Exchange LINE token → Supabase JWT

**Pet Management:**
- `GET /api/pets` - List user's pets
- `POST /api/pets` - Create pet
- `PUT /api/pets` - Update pet
- `DELETE /api/pets?id=` - Delete pet

**Health Tracking:**
- `POST /api/vaccinations` - Add vaccination
- `PUT /api/vaccinations` - Update vaccination
- `DELETE /api/vaccinations?id=` - Delete
- `POST /api/parasite-logs` - Log parasite treatment
- `POST /api/pet-weight` - Log weight

**Lost/Found Reports:**
- `POST /api/post` - Create lost/found alert (rate-limited 3/24h)
- `GET /api/posts?limit=&offset=&alert_type=lost` - List posts
- `GET /api/posts/[id]` - Get post details
- `PUT /api/post/[id]/resolve` - Mark as found

**Photos & Media:**
- `POST /api/pet-photos` - Upload pet photo
- `POST /api/voice` - Upload voice message
- `POST /api/poster` - Generate shareable poster
- `GET /api/share-card/[id]` - Generate share card

**Messaging:**
- `POST /api/line/webhook` - LINE bot incoming messages
- `POST /api/line/rich-menu` - Update rich menu

**Push Notifications:**
- `POST /api/alerts/push` - Send push alert
- `POST /api/alerts/subscribe` - Subscribe to notifications

**Utilities:**
- `GET /api/hospitals?lat=&lng=&radius=` - Find nearby hospitals
- `POST /api/cron/health-reminders` - Scheduled job
- `POST /api/feedback` - Submit bug report

---

## State Management & Context

### LiffProvider (Authentication)

**Location:** `components/liff-provider.tsx`

```typescript
interface AuthContextType {
  user: Profile | null;
  loading: boolean;
  isInLiff: boolean;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType>();
export function LiffProvider({ children }) { ... }
export function useAuth() { ... }
```

**Usage:**
```typescript
const { user, loading, isInLiff, signOut } = useAuth();
```

### LocationProvider (Geolocation)

**Location:** `components/location-provider.tsx`

Manages user's current location for:
- Lost pet report location
- Hospital search radius
- Nearby alerts filter

### Other Context Patterns

**ToastProvider:** Toast notifications

**DebugConsole:** Development console (vconsole wrapper)

---

## Component Architecture

### Component Types

**1. Pages (App Router)**

Located in `app/` directory:
- `app/page.tsx` - Home dashboard
- `app/pets/page.tsx` - Pet list
- `app/post/page.tsx` - Lost/found feed
- etc.

All client components using `useAuth()` hook for auth.

**2. Feature Components**

Larger, feature-scoped components:
- `components/create-pet-form.tsx` - Pet onboarding
- `components/create-post-form.tsx` - Report lost/found
- `components/hospital-map.tsx` - Hospital discovery
- etc.

Most are client components (`"use client"`) but can include server actions.

**3. UI Primitives (ShadCN)**

Located in `components/ui/`:
- `Button` - Styled button
- `Card` - Card layout
- `Input` - Form input
- `Badge` - Status badge
- etc.

Fully composable and accessible.

**4. Post-Related Components**

Grouped in `components/post/`:
- `alert-card.tsx` - Display lost/found alert
- `voice-player.tsx` - Audio playback
- `radius-selector.tsx` - Map radius filter
- `species-filter.tsx` - Filter by species

### Component Lifecycle & Data Flow

```
Page (Client Component)
  ├─ useAuth() → LiffProvider
  ├─ useState() for local state
  └─ useEffect() for data fetching
       ↓
    apiFetch("/api/resource", options)
       ↓
    lib/api.ts (wrapper)
       ↓
    fetch() with auth header
       ↓
    Route Handler (/api/resource/route.ts)
       ↓
    getAuthUser() → extract JWT
       ↓
    Supabase API (lib/supabase-api.ts)
       ↓
    Postgres DB (with RLS)
       ↓
    Return response → setData()
```

### Form Pattern

```typescript
// components/create-pet-form.tsx
export function CreatePetForm() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);

  const onSubmit = async (formData: Pet) => {
    // 1. Validate with Zod schema
    const validated = petSchema.parse(formData);

    // 2. POST to API
    setLoading(true);
    const result = await apiFetch("/api/pets", {
      method: "POST",
      body: validated
    });

    // 3. Handle response
    if (result.error) {
      setError(result.error);
    } else {
      navigate(`/pets?id=${result.id}`);
    }
  };

  return <form onSubmit={onSubmit}>...</form>;
}
```

---

## TYPE & VALIDATION SPLIT

### Why Split by Domain?

In large projects, having all types in one file causes merge conflicts. **Pawrent splits types and validations by feature domain.**

### Domain Files

| Domain       | Types File              | Validations File             |
| ------------ | ----------------------- | ---------------------------- |
| Shared       | `lib/types/common.ts`   | `lib/validations/common.ts`   |
| Pets         | `lib/types/pets.ts`     | `lib/validations/pets.ts`     |
| Pet Reports  | `lib/types/pet-report.ts` | `lib/validations/pet-report.ts` |
| Posts/Social | `lib/types/posts.ts`    | `lib/validations/posts.ts`    |
| Found Pets   | `lib/types/found.ts`    | `lib/validations/found.ts`    |
| Geospatial  | `lib/types/geospatial.ts` | `lib/validations/geospatial.ts` |
| Conversations | `lib/types/conversations.ts` | `lib/validations/conversations.ts` |
| Health       | `lib/types/health.ts`   | `lib/validations/health.ts`   |
| Notifications | `lib/types/push.ts`    | `lib/validations/push.ts`     |

### Barrel Re-Exports

```typescript
// lib/types/index.ts
export * from "./common";
export * from "./pets";
export * from "./pet-report";
export * from "./posts";
export * from "./geospatial";
export * from "./found";
export * from "./conversations";
export * from "./push";
export * from "./health";

// Usage:
import { Pet, Vaccination } from "@/lib/types";
```

### Adding a New Domain

1. Create `lib/types/newdomain.ts` with type defs
2. Create `lib/validations/newdomain.ts` with Zod schemas
3. Add exports to `lib/types/index.ts` and `lib/validations/index.ts`
4. No changes needed in components (barrel re-exports handle it)

---

## Build & Runtime Configuration

### next.config.ts

```typescript
import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",       // Service worker source
  swDest: "public/sw.js",   // Built output
});

const nextConfig = {
  allowedDevOrigins: ["*.ngrok-free.dev"],  // ngrok for local testing
  
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "[supabase-url].supabase.co",
        pathname: "/storage/v1/object/public/**",  // Supabase storage
      },
    ],
  },
};

export default withSerwist(nextConfig);
```

**Key Features:**
- **Serwist PWA:** Service worker for offline capability
- **Image optimization:** Remote image optimization from Supabase
- **Dev origins:** ngrok support for local LINE LIFF testing

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "strict": true,              // Full strict mode
    "jsx": "react-jsx",          // React 19 JSX transform
    "moduleResolution": "bundler", // Bundler resolution
    "paths": { "@/*": ["./*"] }  // Path aliases
  }
}
```

### Styling (Tailwind v4)

**CSS-first config:**
- No `tailwind.config.js` file needed
- All config in `app/globals.css`
- Design tokens via CSS variables

```css
/* app/globals.css */
@import "tailwindcss";

@layer theme {
  :root {
    --primary: #FF8263;
    --surface: #FFFFFF;
    /* ... */
  }
}
```

### Build Output

**Next.js Output:**
- `output: "standalone"` configured for Docker/self-hosting
- Minimal dependencies in standalone mode
- Suitable for Kubernetes deployment

---

## Development Workflow

### Project Scripts

```json
{
  "dev": "next dev --webpack",              // Local dev with Webpack
  "build": "next build --webpack",          // Production build
  "start": "next start",                    // Production start
  "lint": "eslint",                         // Linting
  "test": "vitest run",                     // Unit tests
  "test:coverage": "vitest run --coverage", // Coverage
  "test:watch": "vitest",                   // Watch mode
  "test:e2e": "playwright test",            // E2E tests
  "format": "prettier --write .",           // Format code
  "format:check": "prettier --check .",     // Check format
  "type-check": "tsc --noEmit"              // TypeScript check
}
```

### Pre-commit Hooks (Husky)

Via `lint-staged`:
- Format TypeScript/TSX files with Prettier
- Lint with ESLint --fix
- Format JSON/MD/CSS

### Commit Linting

Via `@commitlint`:
- Enforces conventional commits (feat, fix, docs, etc.)
- Prevents non-standard commit messages

---

## Summary

**Pawrent** is a comprehensive pet health & safety platform built on:

- **Frontend:** Next.js 16 App Router + React 19, Tailwind v4 CSS
- **Backend:** Supabase Postgres with PostGIS, RLS policies, Realtime
- **Auth:** LINE LIFF OAuth → Supabase SSR JWT
- **Mobile:** PWA (Serwist), responsive design, location-based features
- **Messaging:** LINE Bot API for notifications (health reminders, lost pet alerts)
- **Testing:** Vitest + Playwright, E2E coverage on major flows
- **Quality:** Strict TypeScript, Zod validation, ESLint, Prettier, Husky hooks

The architecture emphasizes **type safety, multi-agent collaboration (type/validation domain split), offline-first UX (PWA), and Thai cultural localization (Thai font, Thai language strings, Thai datetime formats).**

