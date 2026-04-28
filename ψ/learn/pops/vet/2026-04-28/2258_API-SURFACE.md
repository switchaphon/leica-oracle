# POPS Vet — Public / Integration Surface

> Auto-documented by Leica Oracle on 2026-04-28.
> Source: `src/` of the `vet` Next.js frontend (Next 15, React 19, TypeScript).
> Read this when integrating with vet, debugging a failing API call, or onboarding onto the auth flow.

---

## 1. GraphQL Backend Integration

### Endpoint

| Context | Value |
|---------|-------|
| Env var | `NEXT_PUBLIC_POPS_API_URL` |
| Path suffix | `/service` (appended in code) |
| Full endpoint | `${NEXT_PUBLIC_POPS_API_URL}/service` |
| Local dev default | `http://localhost:4000/service` (codegen fallback only) |

The env var is read two ways:
- **Client-side**: via `next-runtime-env`'s `env()` — injected at runtime by `<PublicEnvScript>` in `layout.tsx`. Never process.env on the client.
- **Server-side** (authOptions, route handlers): `process.env.NEXT_PUBLIC_POPS_API_URL` directly.

Source: `src/app/_config/config.ts`

### Schema Source

Live introspection against `${NEXT_PUBLIC_POPS_API_URL}/service`. No local SDL file. The backend gateway must be running for `codegen` to succeed.

### Code Generation

- Config: `codegen.ts` (project root)
- Plugin: `@graphql-codegen/client-preset` v5 (preset `'client'`)
- Output directory: `src/__generated__/`
- Naming convention: `keep` (snake_case fields preserved — matches backend convention)
- Fragment masking: not enabled (no `fragmentMasking` config)
- Re-run command: `bun codegen` or `pnpm codegen` (script: `graphql-codegen --config codegen.ts`)
- Watch mode: `bun codegen:watch`

### GraphQL Client Library

`graphql-request` v7 (not Apollo, not urql, not react-query). Client is a singleton `GraphQLClientManager` class in `src/app/_assets/lib/graphql-client.ts`.

SWR (`swr` v2) is used for client-side data fetching hooks — it wraps `graphql-request` calls, not a dedicated GQL client.

### update-frontend-backend-ref.sh

A dev-tooling script that cross-references frontend GraphQL operations against backend resolver files. It:

1. Parses `src/app/_assets/lib/graphql-operations.ts` for all `query X` and `mutation X` names used by the frontend.
2. Scans `../backend/microservices/*/src/**/*.resolver.ts` for `@Query(...)` and `@Mutation(...)` decorators (NestJS pattern).
3. Also extracts REST endpoints from `auth-service/*.controller.ts`.
4. Writes a coverage report to `.claude/backend-api.md` (auto-loaded by Claude Code).
5. Called automatically by `sync-backend.sh` after backend doc updates.
6. Supports `--dry-run` for preview-only.

The output doc lists: ops used by FE, ops available in BE but not used, ops used by FE but missing from BE (mismatch alerts).

---

## 2. GraphQL Operations

All operations are defined inline with `gql\`...\`` in `src/app/_assets/lib/graphql-operations.ts`. Exported as a typed `GraphQLOperations` singleton. No separate `.graphql` files.

### Queries

| Name | Purpose |
|------|---------|
| `BranchList` | List clinic branches (id, name, address, phone) — used during login flow |
| `UserList` | List staff users (paginated via `UserListInput`) |
| `UserGetById` | Fetch a single staff user by id |
| `PetList` | List pets with primary owner — accepts `PetListInput` filter |
| `PetGetById` | Fetch a single pet by id |
| `PetSummary` | Aggregate pet stats (total, capacity, species/status breakdown) |
| `PetPopular` | Top breeds by count |
| `PetFamily` | Pet + family (owners, related pets, address) by pet id |
| `OwnerList` | List owners — accepts `OwnerListInput` (server filter + client-side fallback) |
| `OwnerGetById` | Fetch a single owner by id |
| `OwnerSummary` | Owner count + MoM trend |
| `VetSummary` | Aggregate vet stats (gender, specialty, schedule, attendance breakdown) |
| `VetList` | List vets with schedules and specialties |
| `VetGetById` | Fetch a single vet by id |
| `VetScheduleGetById` | Fetch a vet schedule slot by id (available/booked hours) |
| `QueueList` | List queue items — accepts `QueueListInput` |
| `QueueGetById` | Fetch a single queue item by id |
| `QueueSummary` | Today/active queue breakdown by status and service type |
| `QueueGetByVetId` | Paginated queue list scoped to a vet |
| `QueueTimeline` | Timeline of actions for a queue item |
| `RoomList` | List clinic rooms (id, name, capacity, type) |
| `AppointmentList` | List all appointments — NOTE: no pagination, prefer `AppointmentsByDate` |
| `AppointmentGetById` | Fetch a single appointment |
| `AppointmentGetByVetId` | Paginated appointments scoped to a vet |
| `AppointmentSummary` | Today/my/upcoming-3d appointment counts and breakdowns |

### Mutations

| Name | Purpose |
|------|---------|
| `UserLogin` | Credential login — returns `access_token`, `refresh_token`, `tenants[]` |
| `UserGoogleLogin` | Google OAuth → backend bridge — takes `id_token` from Google |
| `UserRefreshToken` | Rotate access token using refresh token |
| `UserSelectTenant` | Mint tenant-scoped access token from non-scoped token |
| `UserSelectBranch` | Mint branch-scoped access token from tenant-scoped token |
| `UserCreate` | Create a staff user |
| `UserUpdate` | Update a staff user |
| `UserDelete` | Soft-delete a staff user |
| `UserActivate` | Activate user account |
| `UserResendActivation` | Re-send activation email |
| `UserReactivate` | Re-activate a deactivated user |
| `UserForgotPassword` | Trigger forgot-password flow |
| `UserVerifyPassword` | Check a password is valid (no hash exposure) |
| `UserChangePassword` | Change own password |
| `UserUpdateAvatar` | Upload new avatar URL for a staff user |
| `UserResetPassword` | Admin: reset a user's password |
| `PetCreate` | Create a pet and link owners |
| `PetUpdate` | Update pet profile |
| `PetUpdateAvatar` | Update pet avatar URL |
| `PetDelete` | Delete a pet |
| `FamilyTransferPet` | Change primary owner of a pet |
| `FamilyUnlinkPet` | Remove a pet from a family |
| `FamilyUnlinkOwner` | Remove an owner from a family |
| `FamilyDelete` | Delete a family group |
| `OwnerCreate` | Create an owner and link to pets |
| `OwnerUpdate` | Update owner profile |
| `OwnerUpdateAvatar` | Update owner avatar URL |
| `VetScheduleCreate` | Create/update vet schedule slots |
| `QueueCreate` | Create a queue entry (walk-in or from appointment) |
| `QueueUpdate` | Update queue status/assignment |
| `AppointmentCreate` | Create an appointment |
| `AppointmentUpdate` | Update appointment details |
| `AppointmentUpdateStatus` | Change appointment status only |
| `AppointmentCancel` | Cancel an appointment with reason |
| `AppointmentDelete` | Hard-delete an appointment |

### Subscriptions

None. No WebSocket/subscription operations found.

### Fragments

None defined. Operations inline all fields directly — no fragment reuse.

---

## 3. Auth Surface

### Provider

NextAuth v4 (`next-auth`). Strategy: JWT (no database sessions).

### Login Flows

**Credentials (username/password)**
- Client calls `signIn('credentials', { username, password, remember })` via NextAuth.
- NextAuth `authorize` callback calls `UserLogin` GraphQL mutation directly against backend.
- Returns: `access_token` (short-lived JWT), `refresh_token` (long-lived), `tenants[]`, `must_change_password`.

**Google OAuth**
- Client click triggers Google OAuth standard flow.
- NextAuth `signIn` callback receives `account.id_token` from Google.
- Backend bridge: `UserGoogleLogin` mutation called with the Google `id_token`.
- Result cached in an in-memory `Map` for 60 seconds to survive the NextAuth callback handoff.
- Error path: redirects to `/login?error=google_not_registered` if user not registered.

### Multi-Tenant: Token Scoping Flow

After initial login, the access token is NOT yet tenant-scoped. The user must:

1. **Select Tenant** — POST `/api/auth/select-tenant` with `{ tenantCode }`.
   - Route calls `UserSelectTenant` mutation with the `loginAccessToken`.
   - Returns tenant-scoped `access_token`.
   - Client calls `session.update({ accessToken, tenantAccessToken, tenantCode })` to persist in NextAuth JWT.
   - Advisory cookie `selected_tenant` written via `js-cookie` for legacy readers.

2. **Select Branch** — POST `/api/auth/select-branch` with `{ branchId, tenantToken }`.
   - Route calls `UserSelectBranch` mutation.
   - Returns branch-scoped `access_token` + branch object.
   - Client calls `session.update({ accessToken, tenantAccessToken, branchId })`.
   - Advisory cookie `selected_branch` written.

Both `tenantCode` and `branchId` are stored inside the NextAuth JWT so the silent refresh can re-scope automatically.

### Token Refresh Flow

Automatic, silent. Triggered in the NextAuth `jwt` callback when the access token is expired (or within 60 seconds of expiry).

**`refreshAndRescope(token)` function** (in `authOptions.ts`):
1. Calls `UserRefreshToken` mutation with `refreshToken` → gets new `access_token` + `refresh_token`.
2. **Workaround for backend bug**: The fresh token from `UserRefreshToken` lacks `tenantCode`/`role` claims (backend does not persist tenant context in the `refresh_tokens` table). So:
   - Re-calls `UserSelectTenant` with `tenantCode` (stored in JWT) using the new token.
   - If `branchId` is set, re-calls `UserSelectBranch` (non-fatal — falls back to tenant token on failure).
3. Decodes `role` from the final scoped token.
4. Returns `error: 'RefreshAccessTokenError'` if any step fails (forces re-login on client).

### Remember-Me / Session Expiry

| Mode | TTL |
|------|-----|
| Remember me = true | 30 days |
| Remember me = false | 1 day |

Cookie upper bound: 30 days (`session.maxAge`). Per-user enforcement runs in the `jwt` callback via `isSessionExpired()`. Google OAuth always defaults to 1-day (no remember-me option exposed).

### Logout / Session Invalidation

- `signOut()` from `next-auth/react` — handled by NextAuth's standard flow.
- SignOut page: `/` (root redirect).
- No server-side session revocation (JWT strategy — tokens expire naturally).
- `clearGraphQLTokenCache()` in `initGraphQLClient.ts` should be called after logout to invalidate the 30-second client-side token cache.

### Tenant Propagation to GraphQL

`initGraphQLClient.ts` reads `session.tenantAccessToken ?? session.accessToken` from NextAuth and sets it as `Authorization: Bearer <token>` on the `GraphQLClient`. On the client-side, the token is cached locally for 30 seconds to avoid excessive session reads. SSR uses a request-scoped read.

---

## 4. API Routes (Next.js Route Handlers)

All routes live under `src/app/api/`. Only the auth subsystem has routes. No general data API routes — all data goes through GraphQL directly from client hooks.

| Method | Path | Auth Required | Purpose |
|--------|------|---------------|---------|
| GET + POST | `/api/auth/[...nextauth]` | No | NextAuth catch-all — handles OAuth callbacks, session reads, CSRF, signOut |
| POST | `/api/auth/select-tenant` | Yes (NextAuth session with `loginAccessToken`) | Exchange login token for tenant-scoped token via `UserSelectTenant` mutation |
| POST | `/api/auth/select-branch` | No (caller passes `tenantToken` in body) | Exchange tenant token for branch-scoped token via `UserSelectBranch` mutation |
| POST | `/api/auth/branch-list` | No (caller passes `tenantToken` in body) | Fetch available branches via `BranchList` query |

Note: `/api/auth/select-branch` and `/api/auth/branch-list` accept `tenantToken` in the request body rather than reading from session — this lets the login UI pass the token before the session is fully updated.

---

## 5. Middleware

File: `src/middleware.ts`

Runs on all paths except `_next/static`, `_next/image`, `favicon.ico`, and `images/`.

**What it does:**

| Check | Action |
|-------|--------|
| Path starts with `/api` | Pass through (no auth check) |
| Path is `/activate` without `?token=` param | Redirect to `/login` |
| Path is not public and no NextAuth JWT | Redirect to `/login?callbackUrl=<original path>` |
| Path starts with `/setting/admin` and role is not `clinic-owner`/`admin`/`OWNER`/`ADMIN` | Redirect to `/dashboard` |
| Authenticated user visits `/login` but no `selected_tenant` cookie | Allow through (OAuth flow needs tenant selection) |
| Authenticated user visits any public page (non-OAuth case) | Redirect to `/dashboard` |

**Public pages:** `/login`, `/activate`

**RBAC in middleware:** Route-level only — `setting/admin` restricted to admin roles. Feature-level RBAC is handled in the UI layer (see Section 7).

Token extraction: `getToken({ req, secret: NEXTAUTH_SECRET })` from `next-auth/jwt`.

---

## 6. External Integrations

### File Storage (Images / Avatars)

**MinIO** — S3-compatible object storage.

- Configured in `next.config.ts` as allowed remote image patterns:
  - `https://minio-api-dev.pops.vet` (dev/staging)
  - `https://minio.pops.vet` (production)
- Used for: pet avatars, owner avatars, staff avatars, vet license files.
- The frontend sends pre-signed URLs or paths received from GraphQL mutations (`avatar_url`, `license_file_url` fields). There is no direct S3/MinIO SDK call from the frontend — the backend handles the actual upload and returns the URL.

### Web Vitals / Observability

**Custom endpoint** — `WebVitalsReporter.tsx`

- Collects Core Web Vitals (LCP, FID, CLS, etc.) via `useReportWebVitals`.
- In production: sends to `NEXT_PUBLIC_WEB_VITALS_ENDPOINT` via `navigator.sendBeacon` (with `fetch` fallback).
- Env var: `NEXT_PUBLIC_WEB_VITALS_ENDPOINT` (optional — no-op if unset).
- Payload: `{ name, value, rating, id, navigationType, url }`.

No Sentry, Datadog, LogRocket, or other observability SDK found in the codebase.

### Analytics

No Mixpanel, Amplitude, Google Analytics, or tracking SDK found.

### Fonts

`@fontsource/ibm-plex-sans-thai` — loaded via CSS imports in `layout.tsx` (weights 400, 600, 700). No `next/font` — self-hosted via fontsource npm package.

### No Integrations Found For

- Payment (Stripe, Omise, 2C2P) — none
- Push / SMS (LINE, FCM, Twilio) — none
- Maps (Google Maps, Mapbox) — none
- Email sending — none (backend-only)

---

## 7. RBAC Integration Surface

### Permission Schema (v3)

Defined in `src/app/_types/rbac.ts` and `src/app/_constants/rbacFeatures.ts`.

**Types:**
- `CrudAction`: `'create' | 'read' | 'update' | 'delete'`
- `ExtendedAction`: `'export' | 'print' | 'approve' | 'share' | 'sign' | 'lock'`
- `DataScope`: `'all' | 'branch' | 'assigned' | 'own'`
- `FeatureKey`: 13 features across 7 groups (see below)

**Feature catalog (Thai labels → group):**

| Feature Key | Thai Label | Group |
|-------------|-----------|-------|
| `owners` | เจ้าของสัตว์ | Clinical |
| `pets` | สัตว์เลี้ยง | Clinical |
| `medical_records` | เวชระเบียน | Clinical |
| `queue` | คิวบริการ | Operations |
| `appointments` | นัดหมาย | Operations |
| `veterinarians` | สัตวแพทย์ | Staff |
| `staff` | พนักงาน | Staff |
| `inventory` | คลังสินค้า | Inventory |
| `pos` | POS / Cashier | Finance |
| `financial_report` | รายงานการเงิน | Finance |
| `dashboard` | แดชบอร์ด | Insights |
| `settings.users` | จัดการผู้ใช้ | Admin |
| `settings.roles` | จัดการสิทธิ์ | Admin |

**System roles:**

| Role Key | Name | Full Access |
|----------|------|-------------|
| `vet` | Veterinarian | Clinical CRUD, queue/appointment read+update, vet read, dashboard read |
| `staff` | Staff | Owners/pets/queue/appointment CRUD, POS read, dashboard read |
| `clinic_owner` | Clinic Owner | All features, all CRUD |
| `admin` | Admin | All features, all CRUD |

### How Permissions Are Loaded

Currently a **mock/localStorage store** — `src/app/_utils/rbac/mockStore.ts`.

- Roles seeded from `SYSTEM_ROLES` on first load, persisted in `localStorage` under key `pops-vet:rbac:roles:v1`.
- Seats (per-user role assignments + grants/revokes) under `pops-vet:rbac:seats:v2`.
- Users mock data under `pops-vet:rbac:users:v2`.
- Branches mock data under `pops-vet:rbac:branches:v1`.

This is the POPS-104 FE prototype. The intent is that roles/seats will eventually come from the backend (likely via GraphQL or a dedicated auth service). The mock store is the FE prototype surface — not production-wired to the backend RBAC system yet.

### Permission Check API

**`useRbac.ts`** exports two hooks:

- **`useRoles()`** — Load/mutate roles from the mock store. Methods: `upsertRole`, `deleteRole`, `resetRoleToDefault`, `cloneRole`, `combineRoles`, `reset`.
- **`useUserSeats()`** — Load/mutate user seats. Methods: `upsertSeat`, `inviteUser`, `deactivateUser`, `reactivateUser`, `isEmailTaken`.

**`computeEffectivePermissions.ts`** exports pure functions:

- **`computeEffective(role, seat?)`** → `Permission[]` — Applies seat-level grants and revokes on top of the role's base permissions.
- **`can(perms, action, feature)`** → `boolean` — Check if a given action is allowed for a feature.
- **`diffPermissions(base, effective)`** → `{ grants, revokes }` — Compute delta between base role and effective permissions.
- **`unionPermissions(roles[])`** → `Permission[]` — Union of permissions across multiple roles (used by "combine" flow).

### Combine Flow

`combineRoles(sourceRoleIds, { name, description, key })` in `useRoles`:

1. Validates at least 2 source role IDs.
2. Calls `unionPermissions(sources)` — set-union of CRUD actions per feature, broadest `DataScope` wins, higher `maxAmount` wins.
3. Creates a new Custom Role with `isSystem: false`, `derivedFrom: { sourceRoleKeys, snapshotAt }`.
4. Snapshot semantics: Custom Roles created via combine are NOT auto-updated when source roles change. The UI offers a "Re-sync from sources" action.

### Role Decode from JWT

At login and after every token refresh, `role` is decoded from the JWT payload's `role` claim. The middleware uses this to gate `/setting/admin`. The client session exposes `session.role`.

---

## 8. Routing Surface

### Route Groups

| Group | Segment | Description |
|-------|---------|-------------|
| `(auth)` | — | Public auth pages (login, activate) — no nav bar |
| `(routes)` | — | All authenticated app pages — nav bar present |

### Pages

| Path | RBAC Restriction | Notes |
|------|-----------------|-------|
| `/login` | Public | Redirects to `/dashboard` if already authenticated |
| `/activate` | Public | Requires `?token=` query param |
| `/` (root) | Authenticated | Redirect target (root under `(routes)`) |
| `/dashboard` | Authenticated | Clinic KPI summary |
| `/owner-pet` | Authenticated | Pet + owner list |
| `/owner-pet/[petId]` | Authenticated | Pet profile detail |
| `/appointment` | Authenticated | Appointment calendar/list |
| `/queue` | Authenticated | Daily queue board |
| `/veterinarian` | Authenticated | Vet list |
| `/veterinarian/[veterinarianId]` | Authenticated | Vet profile detail |
| `/report` | Authenticated | Report category index |
| `/report/[category]` | Authenticated | Report list for category |
| `/report/[category]/[reportId]` | Authenticated | Individual report view |
| `/setting/admin` | Admin only (`clinic-owner`, `admin`) | Admin settings root |
| `/setting/admin/user` | Admin only | User management |
| `/setting/admin/roles` | Admin only | Role & permission matrix |
| `/setting/admin/help` | Admin only | Admin help |
| `/shop` | Authenticated | Shop/POS (placeholder) |
| `/lab` | Authenticated | Lab results (placeholder) |
| `/ipd` | Authenticated | IPD (inpatient, placeholder) |
| `/help` | Authenticated | Help page |

RBAC at `/setting/admin/*` is enforced in the middleware (role check). Feature-level RBAC within pages is handled by the `useRoles` / `can()` UI layer.

---

## 9. Client-Side Storage

### Cookies (via `js-cookie`)

| Cookie Name | Set By | Purpose | Expiry |
|-------------|--------|---------|--------|
| `selected_tenant` | `useSelectTenant` | Advisory — records the last selected `tenantCode` for middleware check | Session (no-remember) or 30 days |
| `selected_branch` | `useSelectBranch` | Advisory — records the last selected `branchId` | Session (no-remember) or 30 days |
| `next-auth.session-token` (or `__Secure-next-auth.session-token` in prod) | NextAuth | Encrypted JWT session cookie — source of truth for auth | 30 days (upper bound) |
| `next-auth.csrf-token` | NextAuth | CSRF protection for POST endpoints | Session |
| `next-auth.callback-url` | NextAuth | Stores OAuth callback URL | Session |

Cookie flag notes: `selected_tenant` and `selected_branch` use `secure: true` in production, `sameSite: 'lax'`, `path: '/'`.

### localStorage

| Key | Purpose | Type |
|-----|---------|------|
| `pops-vet:rbac:roles:v1` | RBAC mock store — role definitions | `Role[]` JSON |
| `pops-vet:rbac:seats:v2` | RBAC mock store — per-user seat assignments | `UserSeat[]` JSON |
| `pops-vet:rbac:users:v2` | RBAC mock store — user summaries | `MockUserSummary[]` JSON |
| `pops-vet:rbac:branches:v1` | RBAC mock store — branch list | `MockBranch[]` JSON |

RBAC localStorage data is seeded from `SYSTEM_ROLES` / hardcoded mock data on first load. This is the FE prototype store (POPS-104) — not backed by the production backend.

### sessionStorage

No sessionStorage usage found.

---

## 10. WebSocket / Real-Time

No real-time found. No WebSocket, SSE, EventSource, Socket.IO, or GraphQL subscriptions. Queue and appointment data is fetched via SWR polling (standard REST/GraphQL request cycles).

---

## 11. i18n Surface

**No i18n framework installed.** No `next-intl`, `i18next`, `react-i18next`, or similar library found in `package.json` or source.

The app is effectively Thai-only:
- Thai strings are hardcoded directly in components (not in translation files).
- Error messages in `useLogin.ts` are hardcoded Thai strings with an English-key-to-Thai-message map.
- The RBAC feature catalog (`rbacFeatures.ts`) uses inline Thai labels.
- The HTML root element uses `lang="en"` in `layout.tsx` (likely a TODO — the content is Thai).

Thai font: `@fontsource/ibm-plex-sans-thai` (IBM Plex Sans Thai), weights 400/600/700, loaded in the root layout.

No locale routing, no translation files, no locale detection.

---

## 12. Environment Variables Reference

| Variable | Required | Where Used | Notes |
|----------|---------|------------|-------|
| `NEXT_PUBLIC_POPS_API_URL` | Yes | All GraphQL calls, codegen | Backend gateway base URL. No trailing slash. |
| `NEXTAUTH_SECRET` | Yes | NextAuth JWT signing, middleware `getToken` | Keep secret. Any string in dev. |
| `NEXTAUTH_URL` | Yes (prod) | NextAuth redirect URLs | Must be the canonical app URL. |
| `GOOGLE_CLIENT_ID` | For Google login | `authOptions.ts` GoogleProvider | |
| `GOOGLE_CLIENT_SECRET` | For Google login | `authOptions.ts` GoogleProvider | |
| `NEXT_PUBLIC_WEB_VITALS_ENDPOINT` | No | `WebVitalsReporter.tsx` | If unset, vitals are only logged to console in dev. |
| `NEXT_PUBLIC_WEB_VITALS_DEBUG` | No | `WebVitalsReporter.tsx` | Set `'true'` to force console logging in production. |
| `NEXT_PUBLIC_POPS_VERSION` | Auto | Injected from `package.json` in `next.config.ts` | Read-only build artifact. |

Secrets are injected at runtime via Infisical CLI (referenced in `update-frontend-backend-ref.sh` comments: `docker-entrypoint.sh`). For local dev, use `.env.local`.

---

## 13. Debugging: Common Failure Points

| Symptom | Likely Cause | Where to Look |
|---------|-------------|---------------|
| All GraphQL calls 401 | Token not set / expired | `initGraphQLClient.ts` — check `cachedToken` and `readSessionToken()` |
| Refresh loop / "RefreshAccessTokenError" | `UserRefreshToken` mutation failing, or backend `refresh_tokens` table missing `tenant_code` | `authOptions.ts` `refreshAndRescope()` |
| Token refreshes but no `tenantCode`/`role` claims | Known backend bug — `refresh_tokens` table not persisting tenant context | `refreshAndRescope()` re-scope workaround |
| 401 on first load after tab reopen | `selected_tenant` cookie present but NextAuth session expired | Session enforcement logic in `authOptions.ts` `isSessionExpired()` |
| `/setting/admin` redirects to `/dashboard` | User role not in `['clinic-owner', 'admin', 'OWNER', 'ADMIN']` | `middleware.ts` role check |
| Codegen fails | Backend not running | Start gateway at `NEXT_PUBLIC_POPS_API_URL` before running `bun codegen` |
| MinIO images 400/403 | Domain not in `next.config.ts` `remotePatterns` | Add hostname to `images.remotePatterns` |
| RBAC data stale after role change | localStorage not cleared | Call `resetMockStore()` from `useRoles().reset()` or clear `pops-vet:rbac:*` keys manually |
