# Pawrent — API Surface Reference

> Generated: 2026-04-26
> Source: `/Users/switchaphon/_POPs_/pawrent`

---

## Table of Contents

1. [Auth Flow](#1-auth-flow)
2. [API Routes](#2-api-routes)
3. [Supabase Tables](#3-supabase-tables)
4. [Supabase RPC Functions](#4-supabase-rpc-functions)
5. [TypeScript Domain Types](#5-typescript-domain-types)
6. [Zod Validation Schemas](#6-zod-validation-schemas)
7. [External Integrations](#7-external-integrations)
8. [Rate Limiting Rules](#8-rate-limiting-rules)
9. [Storage Buckets](#9-storage-buckets)
10. [Cron Jobs](#10-cron-jobs)
11. [Environment Variables](#11-environment-variables)

---

## 1. Auth Flow

### Overview

Pawrent uses LINE LIFF as the sole identity provider. There is no native email/password login. The entire flow converts a LINE OIDC `id_token` into a Supabase-compatible JWT signed with `SUPABASE_JWT_SECRET`.

### Step-by-step

```
Client (LIFF)
  │
  ├─ liff.init({ liffId: NEXT_PUBLIC_LIFF_ID })
  ├─ liff.login()  ←  redirects to LINE OAuth
  ├─ liff.getIDToken()  →  id_token (OIDC JWT from LINE)
  │
  ▼
POST /api/auth/line  { idToken }
  │
  ├─ Rate-limit: 10 req / 1 min (by IP)
  ├─ Validate body: lineAuthSchema { idToken: string }
  ├─ POST https://api.line.me/oauth2/v2.1/verify
  │     body: id_token=<token>&client_id=LINE_CHANNEL_ID
  │     → { sub, name, picture, email? }
  │
  ├─ Supabase admin: look up profiles.line_user_id = sub
  │     if found  →  use existing profile
  │     if not    →  auth.admin.createUser(email, user_metadata)
  │                  then profiles.upsert(id, line_user_id, ...)
  │
  ├─ SignJWT({ role: "authenticated", aud: "authenticated" })
  │     alg: HS256, secret: SUPABASE_JWT_SECRET
  │     exp: 1 hour
  │
  └─ return { access_token, user }
```

### Client-side token management

```ts
// lib/auth-token.ts — in-memory singleton
setAuthToken(token: string | null): void
getAuthToken(): string | null
```

All subsequent API calls pass the token as:
```
Authorization: Bearer <access_token>
```

Each protected route handler calls:
```ts
const supabase = createApiClient(authHeader)  // lib/supabase-api.ts
const { data: { user } } = await supabase.auth.getUser()
```

This validates the JWT against Supabase using the anon key + the Bearer token in the `Authorization` global header.

### Email handling

- If LINE provides a real email: use it.
- If LINE does not provide an email: synthetic `<line_sub>@line.local` is stored.
- On re-login with a real email for a previously synthetic-email user: `auth.admin.updateUserById` upgrades the email.

---

## 2. API Routes

### Authentication

#### `POST /api/auth/line`

Exchanges a LINE OIDC `id_token` for a Supabase JWT.

- **Auth required:** No (IP-based rate limit)
- **Rate limit:** 10 req / 1 min (IP)

**Request body:**
```json
{ "idToken": "eyJ..." }
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "user": {
    "id": "uuid",
    "line_user_id": "Uxxxxxxxx",
    "line_display_name": "John",
    "avatar_url": "https://...",
    "email": "john@example.com",
    "full_name": "John",
    "created_at": "2026-04-01T00:00:00Z"
  }
}
```

**Errors:** `400` invalid body, `401` invalid LINE token, `429` rate limited, `500` internal

---

### Profile

#### `PUT /api/profile`

Update the authenticated user's display profile.

- **Auth required:** Yes (Bearer token)
- **Rate limit:** 10 req / 1 min (user ID)

**Request body (all optional):**
```json
{
  "full_name": "Alice",
  "avatar_url": "https://..."
}
```

**Response 200:** Updated `profiles` row.

---

### Pets

#### `POST /api/pets`

Create a new pet.

- **Auth required:** Yes
- **Rate limit:** 10 req / 1 min (user ID)

**Request body (petSchema):**
```json
{
  "name": "Milo",
  "species": "dog",
  "breed": "Shiba Inu",
  "sex": "Male",
  "color": "orange",
  "weight_kg": 8.5,
  "date_of_birth": "2022-03-15",
  "microchip_number": "123456789",
  "neutered": true,
  "special_notes": "Loves cheese"
}
```

**Response 200:** Created `pets` row.

#### `PUT /api/pets`

Update an existing pet (owner-only via RLS).

- **Auth required:** Yes
- **Rate limit:** 20 req / 1 min (user ID)

**Request body:**
```json
{ "petId": "uuid", "name": "Milo", "breed": "Shiba Inu" }
```

**Response 200:** Updated `pets` row. **404** if pet not found.

#### `DELETE /api/pets`

Delete a pet (owner-only via RLS).

- **Auth required:** Yes
- **Rate limit:** 10 req / 1 min (user ID)

**Request body:**
```json
{ "petId": "uuid" }
```

**Response 200:** `{ "success": true }`

---

### Pet Photos

#### `POST /api/pet-photos`

Add a photo to a pet's gallery.

- **Auth required:** Yes
- **Rate limit:** 20 req / 1 min (user ID)

**Request body:**
```json
{ "pet_id": "uuid", "photo_url": "https://...", "display_order": 0 }
```

**Response 200:** Created `pet_photos` row.

#### `DELETE /api/pet-photos`

Remove a pet photo (ownership verified via join).

- **Auth required:** Yes
- **Rate limit:** 20 req / 1 min (user ID)

**Request body:**
```json
{ "photoId": "uuid" }
```

**Response 200:** `{ "success": true }`

---

### Pet Weight

#### `GET /api/pet-weight?pet_id=UUID&limit=12`

Fetch weight history for a pet (most recent first).

- **Auth required:** Yes
- **Rate limit:** 30 req / 1 min (user ID)

**Query params:**
- `pet_id` — UUID (required)
- `limit` — integer 1–100, default 12

**Response 200:** Array of `pet_weight_logs` rows.

#### `POST /api/pet-weight`

Add a weight log entry.

- **Auth required:** Yes
- **Rate limit:** 30 req / 1 min (user ID)

**Request body (weightLogSchema):**
```json
{
  "pet_id": "uuid",
  "weight_kg": 7.2,
  "measured_at": "2026-04-25",
  "note": "After grooming"
}
```

**Response 200:** Created `pet_weight_logs` row.

---

### Vaccinations

#### `POST /api/vaccinations`

Add a vaccination record for a pet.

- **Auth required:** Yes
- **Rate limit:** 20 req / 1 min (user ID)

**Request body (vaccinationSchema):**
```json
{
  "pet_id": "uuid",
  "name": "Rabies",
  "status": "protected",
  "last_date": "2025-06-01",
  "next_due_date": "2026-06-01"
}
```

**Response 200:** Created `vaccinations` row.

**Side effect:** Database trigger `trg_vaccine_reminder` auto-creates a `health_reminders` entry when `next_due_date` is set.

---

### Parasite Logs

#### `POST /api/parasite-logs`

Add a parasite prevention log for a pet.

- **Auth required:** Yes
- **Rate limit:** 20 req / 1 min (user ID)

**Request body (parasiteLogSchema):**
```json
{
  "pet_id": "uuid",
  "medicine_name": "NexGard",
  "administered_date": "2026-04-01",
  "next_due_date": "2026-05-01"
}
```

`next_due_date` must be >= `administered_date`.

**Response 200:** Created `parasite_logs` row.

**Side effect:** Trigger `trg_parasite_reminder` auto-creates a `health_reminders` entry.

---

### Lost / Found Pet Reports (`/api/post`)

Operates on the `pet_reports` table.

#### `POST /api/post`

Create a new lost-pet alert.

- **Auth required:** Yes
- **Rate limit:** 3 req / 24 h (user ID)

**Request body (lostPetAlertSchema):**
```json
{
  "pet_id": "uuid",
  "lost_date": "2026-04-20",
  "lost_time": "14:30:00",
  "lat": 13.7563,
  "lng": 100.5018,
  "location_description": "Near MBK Center",
  "description": "Last seen by fountain",
  "distinguishing_marks": "Scar on left ear",
  "photo_urls": ["https://..."],
  "reward_amount": 5000,
  "reward_note": "Cash only",
  "contact_phone": "0812345678"
}
```

**Auto-snapshot:** Pet's name, species, breed, color, sex, dob, neutered, microchip are copied from `pets` at creation time. Up to 5 photos merged from gallery + submitted (deduplicated).

**Response 200:** Created `pet_reports` row.

#### `GET /api/post`

List or fetch pet reports. Four modes:

1. **Single:** `?id=UUID` — returns one report wrapped in `{ data }`.
2. **Owner's reports:** `?owner_id=UUID[&status=active]` — caller's own reports. `403` if `owner_id != user.id`.
3. **Nearby (geo):** `?lat=13.75&lng=100.5&radius=1000[&alert_type=lost&species=dog&limit=20&cursor=...]` — uses `nearby_reports()` PostGIS RPC, sorted by distance ascending.
4. **Fallback list:** no lat/lng — cursor-paginated, filterable by `alert_type` and `species`.

- **Auth required:** Yes
- **Pagination:** cursor-based (`created_at` + `id` encoded as `base64url` JSON), max 50 per page

**Response 200:**
```json
{ "data": [...], "cursor": "base64url...", "hasMore": true }
```

#### `PUT /api/post`

Resolve an alert (owner only). Supports two formats:

- **Auth required:** Yes
- **Rate limit:** 10 req / 1 min (user ID)

**New format:**
```json
{ "alert_id": "uuid", "status": "resolved_found", "resolution_note": "Found by neighbour" }
```
`status` values: `resolved_found`, `resolved_owner`, `resolved_other`

**Legacy format:**
```json
{ "alertId": "uuid", "resolution": "found" }
```
`resolution` values: `found`, `given_up`

**Response 200:** Updated `pet_reports` row.

---

### Found Reports

#### `POST /api/found-reports`

Report a found or stray pet.

- **Auth required:** Yes
- **Rate limit:** 5 req / 24 h (user ID)

**Request body (foundReportSchema):**
```json
{
  "photo_urls": ["https://..."],
  "lat": 13.7563,
  "lng": 100.5018,
  "species_guess": "cat",
  "breed_guess": "Siamese mix",
  "color_description": "Cream with brown points",
  "size_estimate": "small",
  "description": "Found near parking lot",
  "has_collar": true,
  "collar_description": "Blue collar, no tag",
  "condition": "healthy",
  "custody_status": "with_finder",
  "secret_verification_detail": "Has a star-shaped birthmark"
}
```

`secret_verification_detail` is stored but **never returned** in any API response (`PUBLIC_COLUMNS` explicitly excludes it).

**Response 200:** Public `found_reports` columns only.

#### `GET /api/found-reports`

- **Auth required:** Yes
- **Single:** `?id=UUID` — `{ data }` single report
- **List:** `?species=cat&limit=20&cursor=...` — cursor-paginated active reports
- **Max per page:** 50

---

### Sightings

#### `POST /api/sightings`

Report a sighting of a lost pet (alert must be active).

- **Auth required:** Yes
- **Rate limit:** 10 req / 1 h (user ID)

**Request body (sightingSchema):**
```json
{
  "alert_id": "uuid",
  "lat": 13.76,
  "lng": 100.50,
  "photo_url": "https://...",
  "note": "Running north on Silom"
}
```

**Response 200:** Created `pet_sightings` row.

#### `GET /api/sightings?alert_id=UUID&limit=20&cursor=...`

- **Auth required:** Yes
- Cursor-paginated, max 50

---

### Conversations

#### `POST /api/conversations`

Create or return existing open conversation between alert owner and finder.

- **Auth required:** Yes
- **Rate limit:** 10 req / 1 h (user ID)

**Request body (createConversationSchema):**
```json
{ "alert_id": "uuid", "found_report_id": null, "owner_id": "uuid" }
```

At least one of `alert_id` or `found_report_id` is required. Returns existing open conversation if already exists.

**Response 200:** `conversations` row.

#### `GET /api/conversations?limit=20&cursor=...`

- **Auth required:** Yes
- Lists conversations where user is owner or finder, newest first
- Max 50 per page

---

### Messages

#### `POST /api/conversations/[id]/messages`

Send a message in a conversation.

- **Auth required:** Yes
- **Rate limit:** 30 req / 1 min (user ID)
- **Guards:** User must be owner or finder; conversation must not be `closed`.

**Request body:**
```json
{ "content": "Is this your dog?" }
```

**Response 200:** Created `messages` row.

#### `GET /api/conversations/[id]/messages?limit=50&cursor=...`

- **Auth required:** Yes
- **Guards:** User must be participant.
- Newest messages first, cursor-paginated, max 50

---

### Community Posts

#### `POST /api/posts`

Create a community photo post. Accepts `multipart/form-data`.

- **Auth required:** Yes
- **Rate limit:** 10 req / 1 min (user ID)

**Form fields:**
- `image` — File (JPEG/PNG/WebP, max 5 MB)
- `caption` — string max 500 chars (optional)
- `pet_id` — UUID (optional)

Uploads image to `pet-photos` bucket at `posts/<userId>-<timestamp>.<ext>`.

**Response 200:** Created `posts` row.

#### `POST /api/posts/like`

Toggle like on a post via `toggle_like` RPC.

- **Auth required:** Yes
- **Rate limit:** 30 req / 1 min (user ID)

**Request body:**
```json
{ "postId": "uuid" }
```

**Response 200:** `{ "likes_count": 12 }`

---

### Voice Recording

#### `POST /api/voice`

Upload a voice recording attached to a lost-pet alert.

- **Auth required:** Yes (must own the alert)
- **Rate limit:** 5 req / 1 h (user ID)

**Form fields:**
- `audio` — File, max 2 MB, MIME: `audio/webm` | `audio/ogg` | `audio/mp4` | `audio/mpeg` | `audio/wav`
- `alert_id` — UUID

Uploads to `voice-recordings` bucket, then sets `pet_reports.voice_url`.

**Response 200:** `{ "voice_url": "https://..." }`

---

### Alerts Push Notification

#### `POST /api/alerts/push`

Triggered by a Supabase Database Webhook on `pet_reports` INSERT. Not called directly by clients.

- **Auth:** `Authorization: Bearer <PUSH_WEBHOOK_SECRET>`
- **Rate limit:** 30 req / 1 min (`push:<IP>`)

**Request body (pushWebhookPayloadSchema):**
```json
{
  "alert_id": "uuid",
  "alert_type": "lost",
  "pet_name": "Milo",
  "pet_species": "dog",
  "pet_breed": "Shiba Inu",
  "pet_sex": "Male",
  "photo_url": "https://...",
  "lat": 13.7563,
  "lng": 100.5018,
  "lost_date": "2026-04-20",
  "location_description": "Near MBK",
  "reward_amount": 5000
}
```

**Flow:**
1. Calls `users_within_radius(lat, lng, 5)` RPC to find nearby users.
2. Fetches `push_species_filter`, `push_quiet_start`, `push_quiet_end` per user.
3. Filters out opted-out and users in quiet hours (Asia/Bangkok timezone).
4. Multicasts LINE Flex Message (auto-batched at 500 per call).
5. Logs delivery count to `push_logs`.

**Response 200:** `{ "sent": 42 }` or `{ "sent": 0, "reason": "no_nearby_users" | "all_filtered" }`

---

### Feedback

#### `POST /api/feedback`

Submit feedback (authenticated or anonymous).

- **Auth required:** No (optional auth enriches `user_id`)
- **Rate limit:** 5 req / 1 min (IP)

**Request body (feedbackSchema):**
```json
{ "message": "Love the app!", "image_url": "https://..." }
```

Uses `submit_anonymous_feedback` RPC (bypasses RLS).

**Response 200:** Created feedback record.

---

### Hospitals

#### `GET /api/hospitals`

List up to 100 vet hospitals.

- **Auth required:** No (uses anon key directly, no user token)

**Response 200:** Array of `hospitals` rows.

---

### LINE Webhook

#### `POST /api/line/webhook`

Receives LINE platform events.

- **Auth:** HMAC-SHA256 `x-line-signature` validated against `LINE_CHANNEL_SECRET`.
- Currently handles: `follow` (log), `unfollow` (log). All other events logged.

**Response 200:** `{ "received": N }`

---

### LINE Rich Menu (Admin)

#### `POST /api/line/rich-menu`

Create and activate a rich menu for the LINE OA.

- **Auth:** `x-admin-key` header must equal `LINE_CHANNEL_ACCESS_TOKEN`
- **Rate limit:** 5 req / 1 min (IP)

**Request body:**
```json
{ "imageBase64": "iVBORw0KGgo..." }
```

**Response 200:** `{ "richMenuId": "richmenu-..." }`

#### `DELETE /api/line/rich-menu`

Delete a rich menu.

- **Auth:** Same admin key

**Request body:**
```json
{ "richMenuId": "richmenu-..." }
```

**Response 200:** `{ "deleted": "richmenu-..." }`

---

### Image / Document Generation

#### `GET /api/poster/[alertId]`

Generate an A4 PDF lost-pet poster (Thai-style: yellow/red background, Sarabun font, QR code).

- **Auth required:** Yes (any authenticated user)
- **Rate limit:** 10 req / 1 min (user ID)
- **Response:** `application/pdf`, attachment, `Cache-Control: private, max-age=300`

#### `GET /api/share-card/[alertId]`

Generate a 1080x1350 JPEG share card (Instagram portrait ratio, SVG composited with sharp).

- **Auth required:** Yes
- **Rate limit:** 10 req / 1 min (user ID)
- **Response:** `image/jpeg`, attachment, `Cache-Control: private, max-age=300`

#### `GET /api/og/passport/[petId]`

Generate a 1200x630 OG image for a pet's health passport.

- **Auth required:** No (uses service role key)
- **Runtime:** `nodejs` (forced; bundle exceeds Edge 1 MB limit with @supabase/supabase-js)
- **Response:** PNG via `next/og` `ImageResponse`

---

### Cron Jobs

Both secured by `Authorization: Bearer <CRON_SECRET>`.

#### `GET /api/cron/health-reminders`

Scheduled daily (`0 8 * * *` UTC per `vercel.json`).

Queries `health_reminders` for due entries (overdue or within `remind_days_before` window, up to 30 days ahead). Sends LINE push per owner, marks `is_sent = true`.

**Response 200:** `{ "sent": N, "total": M, "errors": [...] }`

#### `GET /api/cron/celebrations`

Scheduled daily (`0 7 * * *` UTC per `vercel.json`).

Finds pets whose `date_of_birth` or `gotcha_day` month-day matches today. Sends birthday / gotcha-day LINE Flex Messages with up to 4 pet photos and a passport URL.

**Response 200:** `{ "sent": N, "birthdays": M, "gotchaDays": K, "errors": [...] }`

---

## 3. Supabase Tables

### `profiles`

Extends `auth.users`. Created or upserted on first LINE login.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | FK → `auth.users.id` |
| `email` | `text` | Nullable; real or `<sub>@line.local` |
| `full_name` | `text` | From LINE profile |
| `avatar_url` | `text` | LINE picture URL |
| `line_user_id` | `text` | LINE `sub` claim |
| `line_display_name` | `text` | LINE display name |
| `notification_radius_km` | `int` | Default 5; 0 = opted out of push |
| `home_geog` | `geography(Point,4326)` | For push radius queries |
| `push_species_filter` | `text[]` | Default `['dog','cat']` |
| `push_quiet_start` | `time` | e.g. `22:00` |
| `push_quiet_end` | `time` | e.g. `07:00` |
| `created_at` | `timestamptz` | |

Index: GIST on `home_geog` for `users_within_radius` RPC.

### `pets`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `owner_id` | `uuid` | FK → `profiles.id` |
| `name` | `text` | Required, max 100 |
| `species` | `text` | |
| `breed` | `text` | |
| `sex` | `text` | `Male` or `Female` |
| `color` | `text` | max 50 |
| `weight_kg` | `numeric` | 0–500 |
| `date_of_birth` | `date` | Triggers birthday milestone creation |
| `gotcha_day` | `date` | Added PRP-12 |
| `microchip_number` | `text` | max 50 |
| `neutered` | `boolean` | Default false |
| `is_spayed_neutered` | `boolean` | Legacy alias, default false |
| `photo_url` | `text` | Primary profile photo |
| `special_notes` | `text` | max 1000 |
| `created_at` | `timestamptz` | |

### `pet_photos`

Gallery photos for a pet.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` CASCADE |
| `photo_url` | `text` | max 2048 |
| `display_order` | `int` | Ascending display |
| `created_at` | `timestamptz` | |

### `vaccinations`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` |
| `name` | `text` | e.g. `Rabies` |
| `status` | `text` | `protected` \| `due_soon` \| `overdue` |
| `last_date` | `date` | |
| `next_due_date` | `date` | Triggers `health_reminders` insert |
| `created_at` | `timestamptz` | |

### `parasite_logs`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` |
| `medicine_name` | `text` | max 200 |
| `administered_date` | `date` | YYYY-MM-DD |
| `next_due_date` | `date` | Must be >= administered_date; triggers `health_reminders` |
| `created_at` | `timestamptz` | |

### `health_events`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` |
| `event_type` | `text` | `lab` \| `diagnosis` \| `checkup` |
| `title` | `text` | |
| `description` | `text` | |
| `event_date` | `date` | |
| `attachment_urls` | `text[]` | |
| `created_at` | `timestamptz` | |

### `pet_weight_logs`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` CASCADE |
| `weight_kg` | `numeric(5,2)` | > 0 and < 200 |
| `measured_at` | `date` | Default CURRENT_DATE |
| `note` | `text` | max 200 |
| `created_at` | `timestamptz` | |

Index: `(pet_id, measured_at DESC)`

### `pet_milestones`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` CASCADE |
| `type` | `text` | `birthday` \| `gotcha_day` \| `first_vet` \| `first_walk` \| `spayed_neutered` \| `microchipped` \| `custom` |
| `title` | `text` | max 200 |
| `event_date` | `date` | |
| `photo_url` | `text` | |
| `note` | `text` | max 500 |
| `created_at` | `timestamptz` | |

Index: `(pet_id, event_date DESC)`

### `health_reminders`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` CASCADE |
| `owner_id` | `uuid` | FK → `profiles.id` CASCADE |
| `reminder_type` | `text` | `vaccination` \| `parasite_prevention` \| `vet_checkup` \| `medication` \| `custom` |
| `title` | `text` | max 200 |
| `due_date` | `date` | |
| `remind_days_before` | `int` | Default 3 |
| `is_sent` | `boolean` | Default false |
| `sent_at` | `timestamptz` | |
| `is_dismissed` | `boolean` | Default false |
| `created_at` | `timestamptz` | |

Partial index: `(due_date, is_sent) WHERE is_sent = false AND is_dismissed = false`

### `pet_reports`

Core table for lost/found/stray alerts. Renamed from `sos_alerts` in migration PRP-03.1.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `pet_id` | `uuid` | FK → `pets.id` |
| `owner_id` | `uuid` | FK → `profiles.id` |
| `alert_type` | `text` | `lost` \| `found` \| `stray` |
| `status` | `text` | `active` \| `resolved_found` \| `resolved_owner` \| `resolved_other` \| `expired` |
| `is_active` | `boolean` | |
| `lat` / `lng` | `double precision` | |
| `geog` | `geography(Point,4326)` | Auto-synced via trigger |
| `lost_date` | `date` | Required |
| `lost_time` | `time` | |
| `location_description` | `text` | max 500 |
| `description` | `text` | max 2000 |
| `distinguishing_marks` | `text` | max 2000 |
| `photo_urls` | `text[]` | Up to 5 |
| `pet_photo_url` | `text` | First gallery photo |
| `voice_url` | `text` | Set via `/api/voice` |
| `video_url` | `text` | |
| `reward_amount` | `int` | 0–1,000,000 |
| `reward_note` | `text` | max 200 |
| `contact_phone` | `text` | max 20 |
| `resolution_status` | `text` | `found` \| `given_up` |
| `resolved_at` | `timestamptz` | |
| `pet_name` | `text` | Denormalized pet snapshot |
| `pet_species` | `text` | Snapshot |
| `pet_breed` | `text` | Snapshot |
| `pet_color` | `text` | Snapshot |
| `pet_sex` | `text` | Snapshot |
| `pet_date_of_birth` | `date` | Snapshot |
| `pet_neutered` | `boolean` | Snapshot |
| `pet_microchip` | `text` | Snapshot |
| `created_at` | `timestamptz` | |

Index: `(alert_type, status, created_at DESC) WHERE status = 'active'`

### `found_reports`

Reports of stray or found pets by third-party reporters.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `reporter_id` | `uuid` | FK → `profiles.id` SET NULL |
| `reporter_line_hash` | `text` | |
| `photo_urls` | `text[]` | 1–5 |
| `lat` / `lng` | `double precision` | |
| `geog` | `geography(Point,4326)` | Auto-synced |
| `species_guess` | `text` | `dog` \| `cat` \| `other` |
| `breed_guess` | `text` | |
| `color_description` | `text` | max 200 |
| `size_estimate` | `text` | `tiny` \| `small` \| `medium` \| `large` \| `giant` |
| `description` | `text` | max 2000 |
| `has_collar` | `boolean` | |
| `collar_description` | `text` | max 200 |
| `condition` | `text` | `healthy` \| `injured` \| `sick` \| `unknown` |
| `custody_status` | `text` | `with_finder` \| `at_shelter` \| `released_back` \| `still_wandering` |
| `shelter_name` | `text` | max 200 |
| `shelter_address` | `text` | max 500 |
| `secret_verification_detail` | `text` | **Stored but NEVER returned by API** |
| `is_active` | `boolean` | Default true |
| `resolved_at` | `timestamptz` | |
| `created_at` | `timestamptz` | |

### `pet_sightings`

Sightings of a lost pet linked to a `pet_reports` alert.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `alert_id` | `uuid` | FK → `pet_reports.id` CASCADE |
| `reporter_id` | `uuid` | FK → `profiles.id` SET NULL |
| `lat` / `lng` | `double precision` | |
| `geog` | `geography(Point,4326)` | Auto-synced |
| `photo_url` | `text` | |
| `note` | `text` | max 500 |
| `created_at` | `timestamptz` | |

### `conversations`

Contact bridge between a pet owner and a finder.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `alert_id` | `uuid` | FK → `pet_reports.id` nullable |
| `found_report_id` | `uuid` | FK → `found_reports.id` nullable |
| `owner_id` | `uuid` | FK → `profiles.id` CASCADE |
| `finder_id` | `uuid` | FK → `profiles.id` SET NULL |
| `status` | `text` | `open` \| `closed` \| `resolved` |
| `consent_shared` | `boolean` | Default false |
| `created_at` | `timestamptz` | |

RLS: only owner and finder can SELECT, UPDATE; any authenticated user can INSERT.

### `messages`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `conversation_id` | `uuid` | FK → `conversations.id` CASCADE |
| `sender_id` | `uuid` | FK → `profiles.id` CASCADE |
| `content` | `text` | max 2000 |
| `created_at` | `timestamptz` | |

Index: `(conversation_id, created_at DESC)`

### `posts`

Community photo posts.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `owner_id` | `uuid` | FK → `profiles.id` |
| `pet_id` | `uuid` | Nullable |
| `image_url` | `text` | |
| `caption` | `text` | max 500 |
| `likes_count` | `int` | Managed by `toggle_like` RPC |
| `created_at` | `timestamptz` | |

### `post_likes`

| Column | Type | Notes |
|---|---|---|
| `post_id` | `uuid` | FK → `posts.id` |
| `user_id` | `uuid` | FK → `profiles.id` |

### `hospitals`

Static seed data, read-only via API.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `name` | `text` | |
| `address` | `text` | |
| `lat` / `lng` | `double precision` | |
| `geog` | `geography(Point,4326)` | Auto-synced |
| `phone` | `text` | |
| `open_hours` | `text` | |
| `certified` | `boolean` | |
| `specialists` | `text[]` | |
| `type` | `text` | |
| `created_at` | `timestamptz` | |

### `push_logs`

Push delivery audit log. Purged after 30 days (`purge_old_push_logs()` function).

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `alert_id` | `uuid` | FK → `pet_reports.id` CASCADE |
| `alert_type` | `text` | `lost` \| `found` \| `sighting` \| `match` |
| `recipient_count` | `int` | |
| `sent_at` | `timestamptz` | Default now() |

RLS: service role only (read and write).

### `feedback`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid` PK | |
| `user_id` | `uuid` | Nullable (anonymous allowed) |
| `message` | `text` | max 5000 |
| `image_url` | `text` | |
| `created_at` | `timestamptz` | |

---

## 4. Supabase RPC Functions

### `nearby_reports(p_lat, p_lng, p_radius_m, p_limit)`

Returns active `pet_reports` within a radius sorted by distance ascending. Returns all alert columns plus `distance_m double precision`. Permission: `authenticated` only.

```sql
nearby_reports(
  p_lat      double precision,
  p_lng      double precision,
  p_radius_m double precision,
  p_limit    integer DEFAULT 50
)
```

### `reports_within_bbox(p_min_lat, p_min_lng, p_max_lat, p_max_lng, p_limit)`

Returns active `pet_reports` within a bounding box, ordered by `created_at DESC`. Permission: `authenticated` only.

### `snap_to_grid(p_lat, p_lng, p_grid_size)`

Snaps coordinates to a grid for clustering or privacy fuzzing.

```sql
snap_to_grid(p_lat double precision, p_lng double precision, p_grid_size double precision)
RETURNS TABLE (snapped_lat double precision, snapped_lng double precision)
```

Permission: `authenticated` only.

### `users_within_radius(p_lat, p_lng, p_radius_km)`

Returns `line_user_id` for profiles whose `home_geog` falls within the intersection of the alert radius and each user's own `notification_radius_km`. Used by `/api/alerts/push`. `SECURITY DEFINER`.

```sql
users_within_radius(
  p_lat       double precision,
  p_lng       double precision,
  p_radius_km int DEFAULT 5
) RETURNS TABLE (line_user_id text)
```

### `toggle_like(p_post_id, p_user_id)`

Atomically toggles a like on a post. Returns new `likes_count` integer.

### `submit_anonymous_feedback(p_message, p_user_id, p_image_url)`

Inserts feedback bypassing RLS to support unauthenticated callers.

### Database Triggers

| Trigger | Table | Function | Effect |
|---|---|---|---|
| `trg_pet_reports_sync_geog` | `pet_reports` | `sync_geog_from_lat_lng()` | Auto-populate `geog` from `lat`/`lng` |
| `trg_found_reports_sync_geog` | `found_reports` | `sync_geog_from_lat_lng()` | Same |
| `trg_sightings_sync_geog` | `pet_sightings` | `sync_geog_from_lat_lng()` | Same |
| `trg_hospitals_sync_geog` | `hospitals` | `sync_geog_from_lat_lng()` | Same |
| `trg_vaccine_reminder` | `vaccinations` | `auto_create_vaccine_reminder()` | Insert `health_reminders` row when `next_due_date` is set |
| `trg_parasite_reminder` | `parasite_logs` | `auto_create_parasite_reminder()` | Insert `health_reminders` row when `next_due_date` is set |
| `trg_birthday_milestone` | `pets` | `auto_create_birthday_milestone()` | Insert `pet_milestones(type='birthday')` when `date_of_birth` is set |

---

## 5. TypeScript Domain Types

```ts
// lib/types/common.ts
interface Profile {
  id: string; email: string | null; full_name: string | null;
  avatar_url: string | null; line_user_id: string | null;
  line_display_name: string | null; created_at: string;
}
interface Feedback { id: string; user_id: string | null; message: string; image_url: string | null; created_at: string; }
interface Hospital { id: string; name: string; address: string | null; lat: number; lng: number; phone: string | null; open_hours: string | null; certified: boolean; specialists: string[]; type: string; created_at: string; }

// lib/types/pets.ts
interface Pet {
  id: string; owner_id: string; name: string;
  species: string | null; breed: string | null; sex: string | null;
  color: string | null; weight_kg: number | null; date_of_birth: string | null;
  microchip_number: string | null; neutered?: boolean | null;
  photo_url: string | null; special_notes: string | null; created_at: string;
}
interface Vaccination {
  id: string; pet_id: string; name: string;
  status: "protected" | "due_soon" | "overdue";
  last_date: string | null; next_due_date: string | null; created_at: string;
}
interface ParasiteLog {
  id: string; pet_id: string; medicine_name: string | null;
  administered_date: string; next_due_date: string; created_at: string;
}
interface HealthEvent {
  id: string; pet_id: string; event_type: "lab" | "diagnosis" | "checkup";
  title: string; description: string | null; event_date: string;
  attachment_urls: string[] | null; created_at: string;
}
interface PetPhoto { id: string; pet_id: string; photo_url: string; display_order: number; created_at: string; }

// lib/types/pet-report.ts
type AlertType = "lost" | "found" | "stray";
type AlertStatus = "active" | "resolved_found" | "resolved_owner" | "resolved_other" | "expired";

interface LostPetAlert {
  id: string; pet_id: string; owner_id: string; alert_type: AlertType;
  lost_date: string; lost_time: string | null; lat: number; lng: number;
  location_description: string | null; description: string | null;
  distinguishing_marks: string | null; photo_urls: string[];
  voice_url: string | null; video_url: string | null;
  reward_amount: number; reward_note: string | null; contact_phone: string | null;
  // Denormalized pet snapshot at creation time:
  pet_name: string | null; pet_species: string | null; pet_breed: string | null;
  pet_color: string | null; pet_sex: string | null; pet_date_of_birth: string | null;
  pet_neutered: boolean | null; pet_microchip: string | null; pet_photo_url: string | null;
  status: AlertStatus; is_active: boolean; resolved_at: string | null; created_at: string;
  distance_m?: number; // Computed by nearby_reports RPC
}

// lib/types/found.ts
type SpeciesGuess = "dog" | "cat" | "other";
type SizeEstimate = "tiny" | "small" | "medium" | "large" | "giant";
type PetCondition = "healthy" | "injured" | "sick" | "unknown";
type CustodyStatus = "with_finder" | "at_shelter" | "released_back" | "still_wandering";

interface FoundReport {
  id: string; reporter_id: string | null; photo_urls: string[];
  lat: number; lng: number; species_guess: SpeciesGuess | null;
  breed_guess: string | null; color_description: string | null;
  size_estimate: SizeEstimate | null; description: string | null;
  has_collar: boolean; collar_description: string | null;
  condition: PetCondition; custody_status: CustodyStatus;
  shelter_name: string | null; shelter_address: string | null;
  // secret_verification_detail intentionally absent — never in API responses
  is_active: boolean; resolved_at: string | null; created_at: string;
  distance_m?: number;
}
interface PetSighting {
  id: string; alert_id: string; reporter_id: string | null;
  lat: number; lng: number; photo_url: string | null; note: string | null; created_at: string;
}

// lib/types/conversations.ts
type ConversationStatus = "open" | "closed" | "resolved";
interface Conversation {
  id: string; alert_id: string | null; found_report_id: string | null;
  owner_id: string; finder_id: string | null;
  status: ConversationStatus; consent_shared: boolean; created_at: string;
}
interface Message { id: string; conversation_id: string; sender_id: string; content: string; created_at: string; }

// lib/types/posts.ts
interface Post { id: string; pet_id: string | null; owner_id: string; image_url: string; caption: string | null; likes_count: number; created_at: string; }

// lib/types/health.ts
interface PetWeightLog { id: string; pet_id: string; weight_kg: number; measured_at: string; note: string | null; created_at: string; }
interface HealthReminder {
  id: string; pet_id: string; owner_id: string;
  reminder_type: "vaccination" | "parasite_prevention" | "vet_checkup" | "medication" | "custom";
  title: string; due_date: string; remind_days_before: number;
  is_sent: boolean; sent_at: string | null; is_dismissed: boolean; created_at: string;
}
interface PetMilestone {
  id: string; pet_id: string;
  type: "birthday" | "gotcha_day" | "first_vet" | "first_walk" | "spayed_neutered" | "microchipped" | "custom";
  title: string | null; event_date: string; photo_url: string | null; note: string | null; created_at: string;
}

// lib/types/push.ts
interface NotificationPreferences {
  notification_radius_km: number;
  push_species_filter: string[];
  push_quiet_start: string | null; // "HH:MM"
  push_quiet_end: string | null;   // "HH:MM"
}
interface PushWebhookPayload {
  alert_id: string; alert_type: "lost" | "found";
  pet_name: string; pet_species: string | null; pet_breed: string | null; pet_sex: string | null;
  photo_url: string; lat: number; lng: number;
  lost_date: string | null; location_description: string | null; reward_amount: number;
}
```

---

## 6. Zod Validation Schemas

All in `lib/validations/` (barrel re-exported from `lib/validations/index.ts`).

```ts
// auth.ts
lineAuthSchema = z.object({ idToken: z.string().min(1) })

// pets.ts
petSchema = z.object({
  name: z.string().min(1).max(100),
  species: z.string().nullable(),
  breed: z.string().nullable(),
  sex: z.enum(["Male", "Female"]).nullable(),
  color: z.string().max(50).nullable(),
  weight_kg: z.number().min(0).max(500).nullable(),
  date_of_birth: z.string().nullable(),
  microchip_number: z.string().max(50).nullable(),
  neutered: z.boolean().nullable().default(false),
  special_notes: z.string().max(1000).nullable(),
  photo_url: z.string().url().max(2048).nullable().optional(),
})
vaccinationSchema = z.object({ pet_id: uuid, name: min 1, status: enum(protected|due_soon|overdue), last_date: nullable, next_due_date: nullable })
parasiteLogSchema = z.object({ pet_id: uuid, medicine_name: max 200 nullable, administered_date: YYYY-MM-DD, next_due_date: YYYY-MM-DD })
  .refine(next_due_date >= administered_date)

// health.ts  (uses zod/v4)
weightLogSchema = z.object({ pet_id: uuid, weight_kg: positive max 200, measured_at?: date string, note?: max 200 })
milestoneSchema = z.object({ pet_id: uuid, type: enum(7 milestone types), title?: max 200, event_date: date, note?: max 500 })

// pet-report.ts
lostPetAlertSchema = z.object({
  pet_id: uuid, lost_date: date, lost_time?: time,
  lat: -90..90, lng: -180..180,
  location_description?: max 500, description?: max 2000, distinguishing_marks?: max 2000,
  photo_urls: url[] min 1 max 5,
  reward_amount: int 0..1000000 default 0, reward_note?: max 200,
  contact_phone?: max 20, voice_url?: url
})
resolveAlertSchema = z.object({ alert_id: uuid, status: enum(resolved_found|resolved_owner|resolved_other), resolution_note?: max 500 })
resolveReportSchema = z.object({ alertId: uuid, resolution: enum(found|given_up) })  // legacy

// found.ts
foundReportSchema = z.object({
  photo_urls: url[] 1..5, lat, lng,
  species_guess?: enum(dog|cat|other), breed_guess?: max 100,
  color_description?: max 200, size_estimate?: enum(tiny|small|medium|large|giant),
  description?: max 2000, has_collar: bool default false, collar_description?: max 200,
  condition: enum(healthy|injured|sick|unknown) default healthy,
  custody_status: enum(with_finder|at_shelter|released_back|still_wandering) default with_finder,
  shelter_name?: max 200, shelter_address?: max 500,
  secret_verification_detail?: max 500
})
sightingSchema = z.object({ alert_id: uuid, lat, lng, photo_url?: url, note?: max 500 })
createConversationSchema = z.object({ alert_id?: uuid, found_report_id?: uuid, owner_id: uuid })
messageSchema = z.object({ conversation_id: uuid, content: min 1 max 2000 })

// posts.ts
postSchema = z.object({ caption: max 500 nullable, pet_id: uuid nullable })

// common.ts
feedbackSchema = z.object({ message: min 1 max 5000, image_url?: url max 2048 nullable })
imageFileSchema = z.object({ size: max 5MB, type: enum(image/jpeg|image/jpg|image/png|image/webp) })
videoFileSchema = z.object({ size: max 50MB, type: enum(video/mp4|video/quicktime) })

// push.ts
pushWebhookPayloadSchema = z.object({
  alert_id: uuid, alert_type: enum(lost|found),
  pet_name: min 1 max 200, pet_species?: max 50, pet_breed?: max 100, pet_sex?: max 20,
  photo_url: url max 2048, lat, lng, lost_date: nullable, location_description?: max 500,
  reward_amount: int min 0 default 0
})
notificationPreferencesSchema = z.object({
  notification_radius_km: int 0..50,
  push_species_filter: string[] max 10 default ['dog','cat'],
  push_quiet_start: /^\d{2}:\d{2}$/ nullable,
  push_quiet_end: /^\d{2}:\d{2}$/ nullable
})
```

---

## 7. External Integrations

### LINE LIFF (`@line/liff`)

Client-side SDK. Entry point: `lib/liff.ts`.

```ts
initializeLiff()                    // liff.init({ liffId: NEXT_PUBLIC_LIFF_ID }) — singleton
getLiffIdToken(): string | null     // OIDC id_token — passed to POST /api/auth/line
getLiffProfile()                    // { displayName, userId, pictureUrl }
isInLiffBrowser(): boolean          // liff.isInClient()
liffLogin() / liffLogout()
liffShareTargetPicker(messages)     // LINE shareTargetPicker; returns false outside LIFF
```

### LINE Messaging API (`@line/bot-sdk`)

Server-side only. Entry point: `lib/line/client.ts`.

```ts
getLineClient(): messagingApi.MessagingApiClient    // uses LINE_CHANNEL_ACCESS_TOKEN
getLineBlobClient(): MessagingApiBlobClient         // for rich-menu image upload
```

Helpers in `lib/line-messaging.ts`:
- `pushMessage(userId, messages[])` — single-user push
- `multicastMessage(userIds[], messages[])` — auto-batched at 500 per call; returns total sent count
- `isQuietHours(quietStart, quietEnd, now?)` — checks Asia/Bangkok timezone; handles midnight wrap-around

Webhook validation in `lib/line/webhook.ts`:
- HMAC-SHA256 over raw body, validated against `LINE_CHANNEL_SECRET`
- Currently handles `follow` and `unfollow` events (logging only)

### LINE Auth Verification

`POST https://api.line.me/oauth2/v2.1/verify`  
Body: `id_token=<token>&client_id=<LINE_CHANNEL_ID>`  
Returns: `{ sub, name, picture, email? }`

### Supabase (`@supabase/supabase-js`)

Three client patterns:

| Pattern | File | Key | Purpose |
|---|---|---|---|
| `createApiClient(authHeader)` | `lib/supabase-api.ts` | anon key + Bearer header | All protected routes — RLS enforced |
| `createClient(url, SERVICE_ROLE_KEY)` | auth route, cron | service role key | Bypasses RLS (admin operations) |
| `supabase` singleton | `lib/supabase.ts` | anon key | Client-side queries |

PostGIS (`extensions.geography`, EPSG:4326) is used for all geospatial columns with GIST indexes.

### Upstash Redis (`@upstash/ratelimit`, `@upstash/redis`)

Used exclusively for rate limiting (`lib/rate-limit.ts`).

```ts
const redis = new Redis({ url: UPSTASH_REDIS_REST_URL, token: UPSTASH_REDIS_REST_TOKEN })
createRateLimiter(requests: number, window: Duration): Ratelimit
  // Uses Ratelimit.slidingWindow algorithm
checkRateLimit(limiter, identifier): Promise<NextResponse | null>
  // Returns 429 with Retry-After header on limit exceeded; null if allowed
```

Identifiers used: `user.id`, IP (`x-real-ip` or first `x-forwarded-for`), or `"push:<ip>"`.

### `pdf-lib` + `@pdf-lib/fontkit`

Generates A4 PDF posters in `/api/poster/[alertId]`. Thai font files `Sarabun-Bold.ttf` and `Sarabun-Regular.ttf` are loaded from `/public/fonts/` at runtime.

### `sharp`

Composites SVG overlay + pet photo + QR code into 1080×1350 JPEG in `/api/share-card/[alertId]`.

### `qrcode`

Generates QR code PNG buffers linking to `NEXT_PUBLIC_APP_URL/post/<alertId>` in both poster and share-card routes.

### `next/og` (`ImageResponse`)

Generates 1200×630 OG images in `/api/og/passport/[petId]`. Forced to Node.js runtime (`export const runtime = "nodejs"`) because the bundle including `@supabase/supabase-js` exceeds the 1 MB Edge limit.

### `jose`

Signs Supabase-compatible JWTs in `/api/auth/line`:
```ts
new SignJWT({ role: "authenticated", aud: "authenticated" })
  .setProtectedHeader({ alg: "HS256", typ: "JWT" })
  .setSubject(userId)
  .setIssuedAt()
  .setExpirationTime("1h")
  .sign(secret)  // SUPABASE_JWT_SECRET
```

---

## 8. Rate Limiting Rules

All use Upstash Redis sliding-window. Identifier is user ID unless noted.

| Endpoint | Limit | Window | Key |
|---|---|---|---|
| `POST /api/auth/line` | 10 | 1 min | IP |
| `PUT /api/profile` | 10 | 1 min | user ID |
| `POST /api/pets` | 10 | 1 min | user ID |
| `PUT /api/pets` | 20 | 1 min | user ID |
| `DELETE /api/pets` | 10 | 1 min | user ID |
| `POST /api/pet-photos` | 20 | 1 min | user ID |
| `DELETE /api/pet-photos` | 20 | 1 min | user ID |
| `GET /api/pet-weight` | 30 | 1 min | user ID |
| `POST /api/pet-weight` | 30 | 1 min | user ID |
| `POST /api/vaccinations` | 20 | 1 min | user ID |
| `POST /api/parasite-logs` | 20 | 1 min | user ID |
| `POST /api/post` (create alert) | 3 | 24 h | user ID |
| `PUT /api/post` (resolve) | 10 | 1 min | user ID |
| `POST /api/found-reports` | 5 | 24 h | user ID |
| `POST /api/sightings` | 10 | 1 h | user ID |
| `POST /api/conversations` | 10 | 1 h | user ID |
| `POST /api/conversations/[id]/messages` | 30 | 1 min | user ID |
| `POST /api/posts` | 10 | 1 min | user ID |
| `POST /api/posts/like` | 30 | 1 min | user ID |
| `POST /api/voice` | 5 | 1 h | user ID |
| `POST /api/alerts/push` | 30 | 1 min | `push:<IP>` |
| `POST /api/feedback` | 5 | 1 min | IP |
| `POST /api/line/rich-menu` | 5 | 1 min | IP |
| `DELETE /api/line/rich-menu` | 5 | 1 min | IP |
| `GET /api/poster/[alertId]` | 10 | 1 min | user ID |
| `GET /api/share-card/[alertId]` | 10 | 1 min | user ID |

Rate-limit response: HTTP `429` with `Retry-After: <seconds>` header, body `{ "error": "Too many requests" }`.

---

## 9. Storage Buckets

All buckets are Supabase Storage. Public URLs via `getPublicUrl()`.

| Bucket | Purpose | Path pattern |
|---|---|---|
| `pet-photos` | Pet profile photos, gallery images, community post images | `<petId>-<ts>.<ext>` / `gallery/<petId>/<photoId>.<ext>` / `posts/<userId>-<ts>.<ext>` |
| `user-photos` | User avatar uploads | `avatars/<userId>.<ext>` |
| `voice-recordings` | Voice messages on lost-pet alerts | `<alertId>_<ts>.<ext>` |
| `report-media` | Video attachments for pet reports | `<alertId>-<ts>.<ext>` |
| `feedback-images` | Images attached to feedback | `<userId>_<ts>.<ext>` (anonymous: `anonymous_<ts>.<ext>`) |

---

## 10. Cron Jobs

Defined in `vercel.json`. Both protected by `Authorization: Bearer <CRON_SECRET>`.

| Schedule (UTC) | Path | Description |
|---|---|---|
| `0 7 * * *` | `/api/cron/celebrations` | Birthday and gotcha-day LINE push at 07:00 UTC |
| `0 8 * * *` | `/api/cron/health-reminders` | Health reminder LINE push at 08:00 UTC |

Both crons use service role key directly and call `line.pushMessage` per-user (not multicast) to allow personalized content.

---

## 11. Environment Variables

| Variable | Used by | Visibility |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | All | Public |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | All | Public |
| `SUPABASE_SERVICE_ROLE_KEY` | Auth route, cron jobs | Server only — bypasses RLS |
| `SUPABASE_JWT_SECRET` | `/api/auth/line` | Server only — signs custom JWTs |
| `NEXT_PUBLIC_LIFF_ID` | LIFF init, rich-menu URL construction | Public |
| `LINE_CHANNEL_ID` | `/api/auth/line` (LINE verify call) | Server only |
| `LINE_CHANNEL_SECRET` | `/api/line/webhook` (HMAC validation) | Server only |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE client, admin key for rich-menu | Server only |
| `UPSTASH_REDIS_REST_URL` | Rate limiter | Server only |
| `UPSTASH_REDIS_REST_TOKEN` | Rate limiter | Server only |
| `PUSH_WEBHOOK_SECRET` | `/api/alerts/push` (DB webhook auth) | Server only |
| `CRON_SECRET` | `/api/cron/*` (Vercel cron auth) | Server only |
| `NEXT_PUBLIC_APP_URL` | QR codes, passport URLs, cron job links | Public — e.g. `https://www.pops.pet` |
**Version**: 0.4.1

## Overview

Pawrent is a Next.js-based pet management and lost pet alert platform designed for Thai users. It provides:
- Pet profile management with health records
- Lost pet alerts with geospatial search
- Found pet reports
- Health reminders and vaccinations tracking
- Social feed with pet photos
- LINE Bot integration for push notifications
- Conversations between pet owners and finders

All authenticated endpoints require `Authorization: Bearer <jwt_token>` header (Supabase JWT).

---

## Authentication & Authorization

### Auth System

**Provider**: Supabase Auth + LINE OAuth 2.0

**Endpoints**:

#### `POST /api/auth/line`
Creates or updates a user profile via LINE ID token verification.

**Request**:
```json
{
  "idToken": "string"
}
```

**Response** (201 on new, 200 on existing):
```json
{
  "access_token": "jwt_string",
  "user": {
    "id": "uuid",
    "line_user_id": "string",
    "line_display_name": "string",
    "avatar_url": "string|null",
    "email": "string|null",
    "full_name": "string",
    "created_at": "ISO8601"
  }
}
```

**Details**:
- Verifies LINE idToken via `https://api.line.me/oauth2/v2.1/verify`
- Creates auth.users entry with email (real or synthetic `{line_user_id}@line.local`)
- Upserts profile record with LINE metadata
- Signs Supabase-compatible JWT (1h expiry)
- Rate limited: 10 req/min per IP

**Error Codes**:
- 400: Invalid request body
- 401: Invalid LINE token
- 500: User creation or profile upsert failed

---

## Pet Management API

### Pet Profiles

#### `POST /api/pets`
Create a new pet profile.

**Request**:
```json
{
  "name": "Fluffy",
  "species": "cat" | null,
  "breed": "Persian" | null,
  "sex": "Male" | "Female" | null,
  "color": "white" | null,
  "weight_kg": 5.5 | null,
  "date_of_birth": "2020-05-15" | null,
  "microchip_number": "123456789" | null,
  "neutered": true | null,
  "special_notes": "Friendly, likes wet food" | null
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "name": "Fluffy",
  "species": "cat" | null,
  "breed": "Persian" | null,
  "sex": "Male" | null,
  "color": "white" | null,
  "weight_kg": 5.5 | null,
  "date_of_birth": "2020-05-15" | null,
  "microchip_number": "123456789" | null,
  "neutered": true | false | null,
  "photo_url": null,
  "special_notes": "Friendly, likes wet food" | null,
  "created_at": "ISO8601"
}
```

**Rate limit**: 10 POST/min  
**Validation**:
- `name`: required, 1-100 chars
- All other fields: optional
- `sex`: enum [Male, Female]
- `weight_kg`: 0-500

#### `PUT /api/pets`
Update an existing pet profile.

**Request**:
```json
{
  "petId": "uuid",
  "name": "Fluffy Jr" | undefined,
  "species": "cat" | undefined,
  ...other fields optional
}
```

**Response** (200): Updated pet object

**Rate limit**: 20 PUT/min  
**Validation**: Same as POST, all fields optional

#### `DELETE /api/pets`
Delete a pet profile and all associated data.

**Request**:
```json
{
  "petId": "uuid"
}
```

**Response** (200):
```json
{
  "success": true
}
```

**Rate limit**: 10 DELETE/min  
**Error codes**:
- 404: Pet not found or not owned by user

---

### Pet Photos

#### `POST /api/pet-photos`
Add a photo to a pet's profile gallery.

**Request**:
```json
{
  "pet_id": "uuid",
  "photo_url": "https://...",
  "display_order": 0
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "pet_id": "uuid",
  "photo_url": "https://...",
  "display_order": 0,
  "created_at": "ISO8601"
}
```

**Rate limit**: 20 POST/min  
**Validation**:
- `photo_url`: valid URL, max 2048 chars
- `display_order`: non-negative integer

#### `DELETE /api/pet-photos`
Remove a photo from pet gallery.

**Request**:
```json
{
  "photoId": "uuid"
}
```

**Response** (200):
```json
{
  "success": true
}
```

**Rate limit**: 20 DELETE/min

---

### Health Records

#### `POST /api/vaccinations`
Log a vaccination record for a pet.

**Request**:
```json
{
  "pet_id": "uuid",
  "name": "Rabies",
  "status": "protected" | "due_soon" | "overdue",
  "last_date": "2024-06-15" | null,
  "next_due_date": "2026-06-15" | null
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "pet_id": "uuid",
  "name": "Rabies",
  "status": "protected" | "due_soon" | "overdue",
  "last_date": "2024-06-15" | null,
  "next_due_date": "2026-06-15" | null,
  "created_at": "ISO8601"
}
```

**Rate limit**: 20 POST/min

#### `POST /api/parasite-logs`
Record parasite treatment (worm, flea prevention).

**Request**:
```json
{
  "pet_id": "uuid",
  "medicine_name": "Simparica Trio",
  "administered_date": "2026-04-20",
  "next_due_date": "2026-05-20"
}
```

**Response** (201): ParasiteLog record

**Validation**:
- Dates: YYYY-MM-DD format
- `next_due_date >= administered_date`

#### `GET /api/pet-weight?pet_id=<uuid>&limit=12`
Fetch weight history for a pet (most recent first).

**Response** (200):
```json
[
  {
    "id": "uuid",
    "pet_id": "uuid",
    "weight_kg": 5.5,
    "measured_at": "2026-04-20",
    "note": "After diet",
    "created_at": "ISO8601"
  }
]
```

**Query params**:
- `pet_id`: required, UUID
- `limit`: optional, 1-100, default 12

#### `POST /api/pet-weight`
Add a weight log entry.

**Request**:
```json
{
  "pet_id": "uuid",
  "weight_kg": 5.5,
  "measured_at": "2026-04-20" | undefined,
  "note": "After diet" | undefined
}
```

**Response** (201): Weight log record

**Rate limit**: 30 POST/min

---

## Lost Pet Alerts

#### `POST /api/post` (Lost Pet Alert Creation)
Create a lost pet alert with geospatial location.

**Request**:
```json
{
  "pet_id": "uuid",
  "lost_date": "2026-04-20",
  "lost_time": "14:30" | undefined,
  "lat": 13.7563,
  "lng": 100.5018,
  "location_description": "Near MBK Center, Bangkok" | undefined,
  "description": "White fluffy cat, very friendly" | undefined,
  "distinguishing_marks": "Black spot on left ear" | undefined,
  "photo_urls": ["https://...", ...],
  "reward_amount": 500,
  "reward_note": "No questions asked" | undefined,
  "contact_phone": "+66812345678" | undefined,
  "voice_url": "https://..." | undefined
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "pet_id": "uuid",
  "owner_id": "uuid",
  "alert_type": "lost",
  "status": "active",
  "is_active": true,
  "lat": 13.7563,
  "lng": 100.5018,
  "lost_date": "2026-04-20",
  "lost_time": "14:30" | null,
  "location_description": "...",
  "description": "...",
  "distinguishing_marks": "...",
  "photo_urls": ["https://..."],
  "reward_amount": 500,
  "reward_note": "...",
  "contact_phone": "...",
  "pet_name": "Fluffy",
  "pet_species": "cat",
  "pet_breed": "Persian",
  "pet_color": "white",
  "pet_sex": "Female",
  "pet_date_of_birth": "2020-05-15",
  "pet_neutered": true,
  "pet_microchip": "123456789",
  "pet_photo_url": "https://...",
  "video_url": null,
  "created_at": "ISO8601"
}
```

**Details**:
- Automatically snapshots pet data from pets table
- Deduplicates photo URLs (max 5)
- Sets `is_active: true` on creation
- Rate limited: 3 per 24h per user

#### `GET /api/post?id=<alertId>` | `owner_id=<userId>` | `lat=<lat>&lng=<lng>`

Fetch lost pet alerts with flexible filtering.

**Query Parameters**:

**Option 1 - By ID**:
```
GET /api/post?id=uuid
```

**Option 2 - Owner's Own Alerts**:
```
GET /api/post?owner_id=<userId>&status=active|undefined
```

**Option 3 - Nearby Alerts (Geospatial)**:
```
GET /api/post?lat=13.7563&lng=100.5018&radius=1000&alert_type=lost|undefined&species=cat|undefined&limit=20&cursor=<base64>
```

**Response** (200):
```json
{
  "data": [{ ...alert objects... }],
  "cursor": "base64|null",
  "hasMore": true|false
}
```

**Geospatial Details**:
- Uses `nearby_reports()` Supabase RPC for distance sorting
- Default radius: 1000m
- Max limit: 50 (default: 20)
- Cursor pagination for pagination beyond limit
- Filters by `alert_type`, `species` (case-insensitive)

#### `PUT /api/post` (Resolve Alert)
Mark an alert as resolved.

**Request** (new format):
```json
{
  "alert_id": "uuid",
  "status": "resolved_found" | "resolved_owner" | "resolved_other",
  "resolution_note": "Found by shelter" | undefined
}
```

**OR legacy format**:
```json
{
  "alertId": "uuid",
  "resolution": "found" | "given_up"
}
```

**Response** (200): Updated pet_report

**Details**:
- Sets `is_active: false`
- Stores `resolved_at` timestamp
- Maps status to `resolution_status` field
- Rate limited: 10 PUT/min

---

## Found Pet Reports

#### `POST /api/found-reports`
Report a found pet.

**Request**:
```json
{
  "photo_urls": ["https://...", ...],
  "lat": 13.7563,
  "lng": 100.5018,
  "species_guess": "dog" | "cat" | "other" | undefined,
  "breed_guess": "Labrador" | undefined,
  "color_description": "brown and white" | undefined,
  "size_estimate": "tiny" | "small" | "medium" | "large" | "giant" | undefined,
  "description": "Friendly, has collar" | undefined,
  "has_collar": true,
  "collar_description": "Blue leather with tags" | undefined,
  "condition": "healthy" | "injured" | "sick" | "unknown",
  "custody_status": "with_finder" | "at_shelter" | "released_back" | "still_wandering",
  "shelter_name": "Bangkok Pet Shelter" | undefined,
  "shelter_address": "123 Pet Street, Bangkok" | undefined,
  "secret_verification_detail": "Secret marking for verification" | undefined
}
```

**Response** (201): Created found_report (without `secret_verification_detail`)

**Rate limit**: 5 per 24h per user

**Security Note**: `secret_verification_detail` is not returned in API responses. Owners of lost alerts can query it separately to match found pets.

#### `GET /api/found-reports?id=<reportId>` | `species=<species>&cursor=<cursor>&limit=20`

**Parameters**:
- `id`: Fetch single report by ID
- `species`: Filter by species_guess
- `cursor`: Pagination token
- `limit`: 1-50, default 20

**Response** (200): Found report(s) with pagination

---

## Pet Sightings

#### `POST /api/sightings`
Report a sighting of a lost pet.

**Request**:
```json
{
  "alert_id": "uuid",
  "lat": 13.7563,
  "lng": 100.5018,
  "photo_url": "https://..." | undefined,
  "note": "Saw near the park" | undefined
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "alert_id": "uuid",
  "reporter_id": "uuid",
  "lat": 13.7563,
  "lng": 100.5018,
  "photo_url": "https://..." | null,
  "note": "..." | null,
  "created_at": "ISO8601"
}
```

**Validation**:
- Alert must exist and be `is_active: true`
- `lat`: -90 to 90
- `lng`: -180 to 180

**Rate limit**: 10 per 1h per user

#### `GET /api/sightings?alert_id=<alertId>&cursor=<cursor>&limit=20`

Fetch sightings for an alert (most recent first).

**Response** (200):
```json
{
  "data": [{ ...sighting objects... }],
  "cursor": "base64|null",
  "hasMore": true|false
}
```

---

## Conversations & Messaging

#### `POST /api/conversations`
Initiate or retrieve a conversation between owner and finder.

**Request**:
```json
{
  "owner_id": "uuid",
  "alert_id": "uuid" | undefined,
  "found_report_id": "uuid" | undefined
}
```

**Response** (201/200):
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "finder_id": "uuid" | null,
  "alert_id": "uuid" | null,
  "found_report_id": "uuid" | null,
  "status": "open" | "closed",
  "created_at": "ISO8601"
}
```

**Details**:
- Returns existing conversation if both parties already have one
- Sets `finder_id` to current user if they are not the owner
- Rate limited: 10 per 1h per user

#### `GET /api/conversations?cursor=<cursor>&limit=20`

Fetch user's conversations (both as owner and finder).

**Response** (200):
```json
{
  "data": [{ ...conversation objects... }],
  "cursor": "base64|null",
  "hasMore": true|false
}
```

#### `GET /api/conversations/[id]/messages?cursor=<cursor>&limit=20`

Fetch messages in a conversation.

**Response** (200):
```json
{
  "data": [{ ...message objects... }],
  "cursor": "base64|null",
  "hasMore": true|false
}
```

#### `POST /api/conversations/[id]/messages`

Send a message in a conversation.

**Request**:
```json
{
  "content": "Have you seen this pet nearby?"
}
```

**Response** (201): Message object with `sender_id`, `content`, `created_at`

---

## Social Feed

#### `POST /api/posts`
Create a post with pet photo (multipart/form-data).

**Request**:
```
POST /api/posts
Content-Type: multipart/form-data

image: <File>
caption: "My cute fluffy cat!"
pet_id: "uuid" (optional)
```

**Response** (201):
```json
{
  "id": "uuid",
  "owner_id": "uuid",
  "pet_id": "uuid" | null,
  "image_url": "https://...",
  "caption": "...",
  "likes_count": 0,
  "created_at": "ISO8601"
}
```

**Validation**:
- Image: JPEG, PNG, WebP, max 5MB
- Caption: max 500 chars
- Uploads to `pet-photos` Supabase bucket

**Rate limit**: 10 per 1min per user

#### `POST /api/posts/like`
Like or unlike a post.

**Request**:
```json
{
  "post_id": "uuid"
}
```

**Response** (200):
```json
{
  "liked": true | false,
  "likes_count": 5
}
```

---

## Profile Management

#### `PUT /api/profile`
Update user profile.

**Request**:
```json
{
  "full_name": "John Doe" | undefined,
  "avatar_url": "https://..." | undefined
}
```

**Response** (200):
```json
{
  "id": "uuid",
  "full_name": "John Doe",
  "avatar_url": "https://...",
  "email": "user@example.com" | null,
  "created_at": "ISO8601"
}
```

**Rate limit**: 10 per 1min per user

---

## File Upload & Generation

#### `POST /api/voice`
Upload voice message for a lost pet alert (multipart/form-data).

**Request**:
```
POST /api/voice
Content-Type: multipart/form-data

audio: <File>
alert_id: "uuid"
```

**Response** (200):
```json
{
  "voice_url": "https://..."
}
```

**Validation**:
- Audio: webm, ogg, mp4, mpeg, wav, max 2MB
- Alert must exist and belong to user

**Rate limit**: 5 per 1h per user

#### `GET /api/share-card/[alertId]`
Generate an Instagram-style (1080x1350) JPEG share card for a lost pet alert.

**Response** (200): JPEG image/jpeg

**Details**:
- Thai-style bold design (yellow/red backgrounds)
- Pet photo, QR code, reward info
- Generated on-the-fly using sharp

#### `GET /api/poster/[alertId]`
Generate an A4 PDF poster for printing and posting.

**Response** (200): PDF application/pdf

**Details**:
- Thai-style design
- Large, readable text
- QR code linking to alert page
- Embeds pet photo and contact info
- Generated using pdf-lib

---

## Feedback & Support

#### `POST /api/feedback`
Submit anonymous or authenticated feedback.

**Request**:
```json
{
  "message": "Great app! But please add X feature",
  "image_url": "https://..." | undefined
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "user_id": "uuid" | null,
  "message": "...",
  "image_url": "...",
  "created_at": "ISO8601"
}
```

**Details**:
- Auth header optional (anonymous feedback allowed)
- Uses RPC `submit_anonymous_feedback` for privacy
- Rate limited: 5 per 1min per IP

---

## Utilities

#### `GET /api/hospitals`
Fetch list of veterinary hospitals (public, no auth required).

**Response** (200):
```json
[
  {
    "id": "uuid",
    "name": "Pet Care Clinic",
    "address": "123 Pet Street",
    "phone": "+66812345678",
    "lat": 13.7563,
    "lng": 100.5018,
    "created_at": "ISO8601"
  }
]
```

---

## Cron Jobs (Protected by CRON_SECRET)

All cron endpoints require: `Authorization: Bearer <CRON_SECRET>`

#### `GET /api/cron/celebrations` (Daily 07:00 ICT)
Send LINE celebration messages for pet birthdays and gotcha-days.

**Response** (200):
```json
{
  "sent": 5,
  "birthdays": 3,
  "gotchaDays": 2,
  "errors": []
}
```

**Details**:
- Sends formatted Flex Message to LINE users
- Includes pet photos (up to 4 most recent)
- Links to pet passport page
- Catches and logs push failures

#### `GET /api/cron/health-reminders` (Daily 08:00 ICT)
Send health reminder notifications for due vaccinations/parasite treatments.

**Response** (200):
```json
{
  "sent": 12,
  "total": 15,
  "errors": []
}
```

**Details**:
- Checks `health_reminders` table
- Sends reminders for due dates or within reminder window
- Updates `is_sent: true` after sending
- Targets Bangkok timezone (Asia/Bangkok)

#### `POST /api/alerts/push`
Send custom LINE push notification to users (internal API).

**Request**:
```json
{
  "user_ids": ["L123...", "L456..."],
  "message": { messagingApi.Message },
  "quiet_hours": { "start": "22:00", "end": "07:00" } | undefined
}
```

---

## Pagination

All list endpoints use cursor-based pagination:

**Request**:
```
GET /api/resource?cursor=base64_token&limit=20
```

**Response**:
```json
{
  "data": [...],
  "cursor": "base64_token_or_null",
  "hasMore": true|false
}
```

**Cursor Format**:
```
base64(encode(JSON.stringify({ created_at: "ISO8601", id: "uuid" })))
```

---

## Data Models & Schemas

### Core Tables

#### `profiles`
```typescript
{
  id: string (PK, FK auth.users.id)
  email: string | null
  full_name: string | null
  avatar_url: string | null
  line_user_id: string | null (unique)
  line_display_name: string | null
  created_at: ISO8601
}
```

#### `pets`
```typescript
{
  id: string (UUID, PK)
  owner_id: string (UUID, FK profiles.id)
  name: string
  species: string | null
  breed: string | null
  sex: "Male" | "Female" | null
  color: string | null
  weight_kg: number | null
  date_of_birth: string | null (YYYY-MM-DD)
  gotcha_day: string | null (YYYY-MM-DD)
  microchip_number: string | null
  neutered: boolean | null
  special_notes: string | null
  photo_url: string | null
  created_at: ISO8601
}
```

#### `pet_reports` (Lost/Found Alerts)
```typescript
{
  id: string (UUID, PK)
  pet_id: string | null (FK pets.id)
  owner_id: string (UUID, FK profiles.id)
  alert_type: "lost" | "found" (conceptual, stored in found_reports separately)
  status: "active" | "resolved_found" | "resolved_owner" | "resolved_other"
  is_active: boolean
  lat: number
  lng: number
  lost_date: string | null (YYYY-MM-DD)
  lost_time: string | null (HH:MM)
  location_description: string | null
  description: string | null
  distinguishing_marks: string | null
  photo_urls: string[] (JSON array, max 5)
  reward_amount: number
  reward_note: string | null
  contact_phone: string | null
  voice_url: string | null
  // Denormalized pet snapshot
  pet_name: string | null
  pet_species: string | null
  pet_breed: string | null
  pet_color: string | null
  pet_sex: string | null
  pet_date_of_birth: string | null
  pet_neutered: boolean | null
  pet_microchip: string | null
  pet_photo_url: string | null
  video_url: string | null
  resolution_status: "found" | "given_up" | null
  resolved_at: ISO8601 | null
  created_at: ISO8601
}
```

#### `found_reports`
```typescript
{
  id: string (UUID, PK)
  reporter_id: string (UUID, FK profiles.id)
  photo_urls: string[] (JSON array, max 5)
  lat: number
  lng: number
  species_guess: "dog" | "cat" | "other" | null
  breed_guess: string | null
  color_description: string | null
  size_estimate: "tiny" | "small" | "medium" | "large" | "giant" | null
  description: string | null
  has_collar: boolean
  collar_description: string | null
  condition: "healthy" | "injured" | "sick" | "unknown"
  custody_status: "with_finder" | "at_shelter" | "released_back" | "still_wandering"
  shelter_name: string | null
  shelter_address: string | null
  secret_verification_detail: string | null
  is_active: boolean
  resolved_at: ISO8601 | null
  created_at: ISO8601
}
```

#### `pet_sightings`
```typescript
{
  id: string (UUID, PK)
  alert_id: string (UUID, FK pet_reports.id)
  reporter_id: string (UUID, FK profiles.id)
  lat: number
  lng: number
  photo_url: string | null
  note: string | null
  created_at: ISO8601
}
```

#### `vaccinations`
```typescript
{
  id: string (UUID, PK)
  pet_id: string (UUID, FK pets.id)
  name: string
  status: "protected" | "due_soon" | "overdue"
  last_date: string | null (YYYY-MM-DD)
  next_due_date: string | null (YYYY-MM-DD)
  created_at: ISO8601
}
```

#### `parasite_logs`
```typescript
{
  id: string (UUID, PK)
  pet_id: string (UUID, FK pets.id)
  medicine_name: string | null
  administered_date: string (YYYY-MM-DD)
  next_due_date: string (YYYY-MM-DD)
  created_at: ISO8601
}
```

#### `pet_weight_logs`
```typescript
{
  id: string (UUID, PK)
  pet_id: string (UUID, FK pets.id)
  weight_kg: number (positive, max 200)
  measured_at: string (YYYY-MM-DD)
  note: string | null
  created_at: ISO8601
}
```

#### `pet_photos`
```typescript
{
  id: string (UUID, PK)
  pet_id: string (UUID, FK pets.id)
  photo_url: string (URL)
  display_order: number
  created_at: ISO8601
}
```

#### `conversations`
```typescript
{
  id: string (UUID, PK)
  owner_id: string (UUID, FK profiles.id)
  finder_id: string | null (UUID, FK profiles.id)
  alert_id: string | null (UUID, FK pet_reports.id)
  found_report_id: string | null (UUID, FK found_reports.id)
  status: "open" | "closed"
  created_at: ISO8601
}
```

#### `posts`
```typescript
{
  id: string (UUID, PK)
  owner_id: string (UUID, FK profiles.id)
  pet_id: string | null (UUID, FK pets.id)
  image_url: string
  caption: string | null
  likes_count: number
  created_at: ISO8601
}
```

#### `health_reminders`
```typescript
{
  id: string (UUID, PK)
  pet_id: string (UUID, FK pets.id)
  owner_id: string (UUID, FK profiles.id)
  reminder_type: string (e.g., "vaccination", "parasite")
  title: string
  due_date: string (YYYY-MM-DD)
  remind_days_before: number
  is_sent: boolean
  is_dismissed: boolean
  sent_at: ISO8601 | null
  created_at: ISO8601
}
```

#### `hospitals`
```typescript
{
  id: string (UUID, PK)
  name: string
  address: string
  phone: string | null
  lat: number
  lng: number
  created_at: ISO8601
}
```

---

## External Integrations

### LINE Messaging API

**Base URLs**:
- OAuth: `https://api.line.me/oauth2/v2.1/`
- Messaging: `https://api.line-api.line.me/`

**Key Operations**:

1. **ID Token Verification** (`POST /oauth2/v2.1/verify`)
   - Validates LINE idToken
   - Returns: `{ sub, name, picture, email }`

2. **Push Message** (`POST /v3/botMessage/push`)
   - Sends message to single user
   - Used by cron jobs for celebrations, health reminders

3. **Multicast** (`POST /v3/botMessage/multicast`)
   - Sends to max 500 users per call
   - Batches automatically if > 500 recipients

4. **Rich Menu** (`POST /v2/bot/richmenu`)
   - Persistent UI menu at bottom of chat
   - Configured via `/api/line/rich-menu`

**Message Types Used**:
- Flex Message (complex layouts)
- Text Message (simple notifications)
- Button Message (CTA with links)

**Libraries**: `@line/bot-sdk` v11.0.0, `@line/liff` v2.28.0

---

### Supabase

**Service Endpoints**:

1. **Auth API**
   - `supabase.auth.getUser()` - Verify current user
   - `supabase.auth.admin.createUser()` - Create auth user
   - `supabase.auth.admin.updateUserById()` - Update user metadata

2. **Database API** (PostgreSQL)
   - Standard CRUD via `.from(table).select/insert/update/delete()`
   - RPC calls: `supabase.rpc('function_name', params)`
   - Key RPC: `nearby_reports()` for geospatial queries

3. **Storage API**
   - `supabase.storage.from(bucket).upload()` - Upload files
   - `supabase.storage.from(bucket).getPublicUrl()` - Get signed URLs
   - Buckets: `pet-photos`, `voice-recordings`

**Authentication Flow**:
- JWT tokens signed with `SUPABASE_JWT_SECRET`
- Expiry: 1 hour
- Passed via `Authorization: Bearer <token>` header

---

### Rate Limiting

**Implementation**: Upstash Redis + `@upstash/ratelimit`

**Strategy**: Sliding window (token bucket)

**Common Limits**:
- POST operations: 3-10 per 24h to 10 per 1min (depends on endpoint)
- PUT operations: 10-20 per 1min
- DELETE operations: 10 per 1min
- Voice upload: 5 per 1h
- Cron-protected endpoints: bearer token validation only

**Headers**:
- On limit: `429 Too Many Requests`
- Response: `{ error: "Too many requests" }`
- Header: `Retry-After: <seconds>`

---

### File Storage

**Supabase Storage Buckets**:

1. **pet-photos** (public)
   - Supported: JPEG, PNG, WebP
   - Max: 5MB per file
   - Used for: Pet profiles, posts, sightings

2. **voice-recordings** (public)
   - Supported: WebM, OGG, MP4, MPEG, WAV
   - Max: 2MB per file
   - Used for: Voice messages in lost pet alerts

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "error message"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | POST successful |
| 400 | Bad Request | Invalid input, validation failure |
| 401 | Unauthorized | Missing/invalid auth token |
| 403 | Forbidden | User doesn't own resource |
| 404 | Not Found | Resource doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | DB error, service failure |

---

## Authentication

### JWT Token Structure

```typescript
{
  role: "authenticated"
  aud: "authenticated"
  sub: user_id
  iat: issued_at_unix
  exp: expiration_unix (1h)
}
```

### Protected Route Pattern

```typescript
async function getAuthUser(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (!authHeader) return null;
  const supabase = createApiClient(authHeader);
  const { data: { user } } = await supabase.auth.getUser();
  return user ? { user, supabase } : null;
}
```

### Authorization Patterns

1. **User Ownership**: Verify `owner_id === user.id` in database
2. **Transitive Ownership**: Verify pet owner via `pets.owner_id` FK
3. **Shared Access**: Check conversations for bidirectional access (owner/finder)

---

## Performance Optimizations

### Caching

- **Hospitals**: `force-dynamic` disabled (CDN cacheable)
- **Cursor Pagination**: Offset-based for large datasets

### Query Optimization

- **Nearby Reports RPC**: Uses PostGIS for efficient distance queries
- **Denormalization**: pet_reports table includes pet snapshot (avoid joins)
- **Selective Columns**: found_reports excludes `secret_verification_detail` in list responses

### Rate Limiting

Prevents abuse while allowing legitimate usage:
- Health records: 20 per 1min (bulk input allowed)
- Share card/poster generation: 10 per 1min (expensive)
- Feedback: 5 per 1min per IP (anonymous allowed)

---

## Security Considerations

1. **JWT Expiry**: 1 hour (short-lived, requires re-auth from LINE)
2. **Signature Validation**: LINE webhook events verified via HMAC-SHA256
3. **Ownership Verification**: All mutations checked server-side
4. **Secret Fields**: `secret_verification_detail` excluded from list responses
5. **Rate Limiting**: Prevents spam, especially for cron jobs and feedback
6. **CRON_SECRET**: Bearer token protects scheduled jobs from public access

---

## Development Notes

### Validation Library

All endpoints use Zod schemas for input validation. Example:

```typescript
export const petSchema = z.object({
  name: z.string().min(1, "Name required").max(100),
  species: z.string().nullable(),
  weight_kg: z.number().min(0).max(500).nullable(),
  // ...
});
```

### Pagination Helper Functions

```typescript
// Encoding cursor
encodeCursor(created_at: string, id: string): string

// Decoding cursor
decodeCursor(cursor: string): { created_at: string, id: string }
```

### LINE Message Templates

Located in `/lib/line-templates/`:
- `celebration.ts` - Birthday/gotcha-day messages
- `health-reminder.ts` - Vaccination/parasite reminders
- `lost-pet-alert.ts` - Lost pet notifications
- `found-pet-alert.ts` - Found pet notifications
- `match-found.ts` - Match alert for finders
- `sighting-update.ts` - Sighting notifications

### Environment Variables

Required:
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET
LINE_CHANNEL_ID
LINE_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN
CRON_SECRET
NEXT_PUBLIC_APP_URL
```

---

## Version History

- **v0.4.1** (current): Pet weight tracking, improved cron jobs
- **v0.4.0**: Found pet reports, conversations
- **v0.3.0**: Voice message upload, share card/poster generation
- **v0.2.0**: Geospatial alerts, sightings
- **v0.1.0**: Pet profiles, vaccinations, LINE auth

