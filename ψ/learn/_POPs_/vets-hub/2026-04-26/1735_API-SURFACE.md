# vets-hub — API Surface
**Captured:** 2026-04-26  
**Source:** `/Users/switchaphon/_POPs_/vets-hub`

---

## Overview

vets-hub is a Thai national veterinary clinic reporting platform operated under the Department of Livestock Development (กรมปศุสัตว์). Clinics submit monthly animal-health statistics (SSP forms สสป.1–4) through a web portal or via third-party clinic software using an API key integration.

**Monorepo layout:**

| Path | Role |
|---|---|
| `apps/api` | NestJS REST API (port 4000) |
| `apps/web` | Next.js 15 web app (port 3000) |
| `packages/db` | Prisma client + schema (PostgreSQL / Supabase) |
| `packages/shared` | Shared TypeScript types, constants, Zod schemas |

All REST endpoints are versioned: `GET /api/v1/<resource>`.  
Global rate limit: 100 requests/minute per IP (NestJS Throttler).  
Body size limit: 10 MB (for base64 image feedback).

---

## 1. HTTP API Routes — `apps/api`

Base prefix: `/api/v1/`  
Auth methods: **Bearer JWT** (`Authorization: Bearer <token>`) or **API Key** (`X-API-Key: <key>`).

### 1.1 Auth — `/api/v1/auth`

| Method | Path | Auth | Rate limit | Description |
|---|---|---|---|---|
| POST | `/auth/register` | None | 5/min | Register new clinic user |
| POST | `/auth/login` | None | 10/min | Login, returns JWT |
| GET | `/auth/me` | JWT | — | Get current user profile |

**POST /auth/register body:**
```json
{
  "email": "string (required)",
  "password": "string (min 8, required)",
  "nameTh": "string (optional)",
  "namePrefix": "string (optional, e.g. น.สพ.)",
  "phone": "string (optional)"
}
```

**POST /auth/login body:**
```json
{
  "email": "string",
  "password": "string (min 8)"
}
```

**Auth response shape (register + login):**
```json
{
  "accessToken": "string (JWT)",
  "userId": "string (cuid)",
  "email": "string",
  "role": "SUPER_ADMIN | PROVINCIAL_OFFICER | CLINIC_OWNER"
}
```

JWT payload: `{ sub: userId, email, role }`. Expiry: `JWT_EXPIRATION` (default `7d`). Role is re-validated from DB on every request (stale JWT role is not trusted).

---

### 1.2 Clinics — `/api/v1/clinics`

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/clinics/license/:licenseNumber` | JWT or API Key | any | Lookup clinic by license number |
| GET | `/clinics` | JWT | SUPER_ADMIN | List all clinics (paginated) |
| POST | `/clinics` | JWT | SUPER_ADMIN | Create clinic |
| POST | `/clinics/link` | JWT | SUPER_ADMIN | Link user to clinic |
| GET | `/clinics/my-clinics` | JWT | any | Get current user's clinics |
| GET | `/clinics/:id` | JWT | any | Get clinic by ID |

**GET /clinics query params:**  
`provinceId`, `status`, `take` (default 50), `skip` (default 0)

**POST /clinics body:** (`CreateClinicInput`)
```json
{
  "licenseNumber": "string (required)",
  "name": "string (required)",
  "type": "CLINIC | HOSPITAL | FIRST_CLASS_CLINIC | SECOND_CLASS_CLINIC",
  "address": "string?",
  "provinceId": "number?",
  "districtId": "number?",
  "subDistrictId": "number?",
  "zipCode": "string?",
  "phone": "string?",
  "email": "string?",
  "founderPrefix": "string?",
  "founderName": "string?",
  "operatorPrefix": "string?",
  "operatorName": "string?"
}
```

**POST /clinics/link body:**
```json
{ "userId": "string", "clinicId": "string" }
```

---

### 1.3 Daily Entries — `/api/v1/daily-entries`

The primary data-entry surface. All guarded by `ClinicMembershipGuard` (verifies the requesting user is linked to the clinic that owns the monthly submission).

#### Monthly Submission Lifecycle

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/daily-entries/monthly/:id/detail` | JWT or API Key | Full monthly detail with all daily entries |
| GET | `/daily-entries/monthly/:clinicId/:year` | JWT or API Key | List all monthly submissions for a year |
| POST | `/daily-entries/monthly/:clinicId/:year/:month` | JWT or API Key | Get-or-create monthly submission |
| POST | `/daily-entries/monthly/:id/submit` | JWT | Submit (finalize) a month |
| POST | `/daily-entries/monthly/:clinicId/:year/:month/zero` | JWT | Submit zero report (no activity month) |
| POST | `/daily-entries/monthly/:id/aggregate` | JWT | Preview aggregated monthly totals before submitting |
| POST | `/daily-entries/monthly/:clinicId/:year/:month/summary` | JWT | Save monthly summary (all 4 SSP forms at once) |
| GET | `/daily-entries/monthly/:clinicId/:year/:month/summary` | JWT or API Key | Read monthly summary |

**POST /monthly/:id/submit body:**
```json
{
  "unfilledDayActions": {
    "YYYY-MM-DD": "ZERO | FILL_MANUALLY"
  }
}
```

#### Daily Entry CRUD

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/daily-entries/entry/:monthlySubmissionId/:date` | JWT or API Key | Get-or-create daily entry for a date |
| GET | `/daily-entries/entry/:monthlySubmissionId/:date` | JWT or API Key | Read daily entry by date (read-only) |
| GET | `/daily-entries/entry/:id` | JWT or API Key | Get daily entry by ID |
| GET | `/daily-entries/entries/:monthlySubmissionId` | JWT or API Key | All daily entries for a month |
| PUT | `/daily-entries/entry/:id/set` | JWT or API Key | Replace daily data directly |
| PUT | `/daily-entries/entry/:id/autosave` | JWT or API Key | Auto-save partial data |
| POST | `/daily-entries/entry/:id/add` | JWT or API Key | Atomic increment of daily counts |
| POST | `/daily-entries/entry/:monthlySubmissionId/:date/zero` | JWT or API Key | Mark a day as zero |
| POST | `/daily-entries/entry/:monthlySubmissionId/copy` | JWT | Copy data from source date to target date |
| POST | `/daily-entries/entry/:monthlySubmissionId/batch` | JWT or API Key | Create multiple daily entries at once |

**UpsertDailyData body** (used for set, autosave, add, summary, batch entries):
```json
{
  "animalCounts": [
    { "animalType": "สุนัข | แมว | custom", "count": 5 }
  ],
  "vaccinations": [
    { "vaccineName": "string", "animalType": "string", "count": 3, "vaccineBrands": "string?" }
  ],
  "medicalTreatments": [
    { "diseaseGroup": "string", "animalType": "string", "count": 2 }
  ],
  "surgicalTreatments": [
    { "procedureGroup": "string", "animalType": "string", "count": 1 }
  ]
}
```

**BatchEntry body:**
```json
{
  "entries": [
    { "date": "YYYY-MM-DD", ...UpsertDailyData fields }
  ]
}
```

#### Progress & Calendar

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/daily-entries/progress/:monthlySubmissionId` | JWT or API Key | Month completion progress |
| GET | `/daily-entries/calendar/:clinicId/:year/:month` | JWT or API Key | Calendar view (per-day entry status) |
| GET | `/daily-entries/unfilled/:monthlySubmissionId` | JWT or API Key | List days with no data entered |
| GET | `/daily-entries/overdue/:clinicId/:year` | JWT or API Key | Overdue months list |

---

### 1.4 Submissions — `/api/v1/submissions`

Legacy annual-report submission endpoints (MVP v1 flow). The newer daily-entry flow above supersedes this for active data entry.

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/submissions/draft` | JWT | Create a draft annual submission |
| GET | `/submissions/:id` | JWT or API Key | Get submission by ID |
| PUT | `/submissions/:id/animal-count` | JWT | Update a single animal count cell (สสป.1) |
| PUT | `/submissions/:id/auto-save` | JWT | Auto-save a partial section |
| POST | `/submissions/:id/submit` | JWT | Submit the annual report |
| GET | `/submissions/clinic/:clinicId` | JWT | All submissions for a clinic |

**PUT /submissions/:id/animal-count body:**
```json
{ "animalType": "string", "month": 1, "count": 5 }
```

**PUT /submissions/:id/auto-save body:**
```json
{ "section": "animalCounts | vaccinations | medicalTreatments | surgicalTreatments", "data": {} }
```

---

### 1.5 External API — `/api/v1/external` (API Key only)

Designed for third-party clinic management software (e.g., ClinicOS). Requires `X-API-Key` header. Uses license number (not internal clinic ID) as the identifier.

| Method | Path | Description |
|---|---|---|
| GET | `/external/clinic/:licenseNumber` | Lookup clinic info |
| GET | `/external/clinic/:licenseNumber/year/:thaiYear` | Year overview (all months) |
| GET | `/external/clinic/:licenseNumber/year/:thaiYear/month/:month/status` | Monthly submission status |
| GET | `/external/clinic/:licenseNumber/year/:thaiYear/month/:month/data` | Read submitted data |
| POST | `/external/clinic/:licenseNumber/year/:thaiYear/month/:month/summary` | Submit monthly summary (all 4 SSP forms) |
| POST | `/external/clinic/:licenseNumber/year/:thaiYear/month/:month/batch` | Submit batch daily entries |
| POST | `/external/clinic/:licenseNumber/year/:thaiYear/month/:month/zero` | Submit zero report |
| POST | `/external/clinic/:licenseNumber/year/:thaiYear/month/:month/finalize` | Finalize and submit month |

**Response — ClinicInfoResponse:**
```json
{
  "licenseNumber": "string",
  "name": "string",
  "type": "CLINIC | HOSPITAL | ...",
  "status": "ACTIVE | CANCELLED | SUSPENDED",
  "provinceName": "string?",
  "districtName": "string?"
}
```

**Response — MonthlyStatusResponse:**
```json
{
  "licenseNumber": "string",
  "thaiYear": 2568,
  "month": 5,
  "status": "NOT_STARTED | OPEN | SUBMITTED",
  "enteredDays": 10,
  "totalDays": 31,
  "percentage": 32
}
```

---

### 1.6 Reports — `/api/v1/reports`

All public unless marked SUPER_ADMIN. Responses are cached for 5 minutes (NestJS CacheInterceptor).

#### Public Endpoints

| Method | Path | Query Params | Description |
|---|---|---|---|
| GET | `/reports/dashboard-stats` | `year`, `provinceId?` | KPI summary for public dashboard |
| GET | `/reports/by-province` | `year`, `section?`, `provinceId?` | Aggregate by province |
| GET | `/reports/by-month` | `year`, `section?`, `provinceId?` | Aggregate by month |
| GET | `/reports/by-disease` | `year`, `provinceId?` | Cases by disease group |
| GET | `/reports/disease-by-province` | `year`, `diseaseGroup` | Disease cases per province |
| GET | `/reports/by-animal-type` | `year`, `provinceId?` | Cases by animal species |
| GET | `/reports/vaccination-coverage` | `year`, `provinceId?` | Vaccination totals |
| GET | `/reports/by-surgical-procedure` | `year`, `provinceId?` | Surgery by procedure group (สสป.4) |
| GET | `/reports/surgical-by-species` | `year`, `provinceId?` | Surgery by procedure × species |
| GET | `/reports/by-month-species` | `year`, `provinceId?` | Monthly volume by species |
| GET | `/reports/yoy-comparison` | `year` | Year-over-year (last 5 years) |
| GET | `/reports/sick-vs-prevention` | `year`, `provinceId?` | Sick animals vs. vaccinated |
| GET | `/reports/disease-by-month` | `year`, `provinceId?` | Disease cases by month |
| GET | `/reports/disease-by-species` | `year`, `provinceId?` | Disease by group × species |
| GET | `/reports/vaccination-by-month` | `year`, `provinceId?` | Vaccines by month (rabies/core/other) |
| GET | `/reports/vaccination-by-species` | `year`, `provinceId?` | Vaccines by name × species |
| GET | `/reports/surgical-by-month` | `year`, `provinceId?` | Surgery by month |
| GET | `/reports/sterilization-by-species` | `year`, `provinceId?` | Sterilization by species × sex |
| GET | `/reports/by-district` | `year`, `provinceId`, `section?` | Aggregate by district |
| GET | `/reports/district-vaccination-rate` | `year`, `provinceId` | Vaccination rate per district |
| GET | `/reports/district-submission-rate` | `year`, `provinceId` | Submission rate per district |
| GET | `/reports/multi-year-trend` | `startYear`, `endYear` | Multi-year trend (max 10 yr range) |
| GET | `/reports/multi-year-disease` | `startYear`, `endYear` | Multi-year disease trend |
| GET | `/reports/multi-year-vaccination` | `startYear`, `endYear` | Multi-year vaccination trend |
| GET | `/reports/multi-year-sterilization` | `startYear`, `endYear` | Multi-year sterilization trend |
| GET | `/reports/regional-trend` | `provinceId`, `startYear`, `endYear` | Provincial trend |
| GET | `/reports/regional-vs-national` | `provinceId`, `year` | Province vs. national benchmarks |
| GET | `/reports/seasonal-pattern` | `startYear`, `endYear`, `provinceId?` | Seasonal animal count patterns |
| GET | `/reports/seasonal-forecast` | `year`, `month` | 3-year moving average forecast |
| GET | `/reports/outbreak-alerts` | `year`, `month` | Alert: cases > mean + 2σ by province |
| GET | `/reports/submission-progress` | `year` | Submission % by province |
| GET | `/reports/national-averages` | `year` | National KPI averages (6 metrics) |

#### SUPER_ADMIN Only

| Method | Path | Query Params | Description |
|---|---|---|---|
| GET | `/reports/compliance` | `year` | Submission compliance by province |
| GET | `/reports/clinic-locations` | `provinceId?` | Clinic lat/lng for map |
| GET | `/reports/district-clinic-density` | `provinceId?` | Clinic count per district |
| GET | `/reports/clinic-benchmarks` | `clinicId`, `year` | 6-dimension clinic performance |
| GET | `/reports/clinic-scatter` | `year` | All-clinic scatter plot data |
| GET | `/reports/clinic-registration-history` | — | Annual registration history |
| GET | `/reports/operator-demographics` | — | Operator gender breakdown |
| GET | `/reports/clinic-naming-keywords` | — | Keyword frequency in clinic names |
| GET | `/reports/vaccine-brand-share` | `year`, `provinceId?` | Vaccine brand market share |

The `section` query parameter accepts: `animalCounts`, `vaccinations`, `medicalTreatments`, `surgicalTreatments`.  
Year values use **Buddhist Era** (พ.ศ.) — e.g., 2568 = Gregorian 2025.

---

### 1.7 Admin — `/api/v1/admin` (SUPER_ADMIN only, JWT)

| Method | Path | Query Params | Description |
|---|---|---|---|
| GET | `/admin/dashboard/stats` | `year?` | Submission statistics |
| GET | `/admin/monthly-log` | `year`, `month?`, `status?`, `search?`, `page?`, `limit?` | Clinic submission tracking log |
| GET | `/admin/submissions` | `status?`, `page?`, `limit?` | All submissions |
| GET | `/admin/users` | `role?` | All users |
| PUT | `/admin/users/:id/role` | — | Change user role |
| GET | `/admin/audit-logs` | `action?`, `entity?`, `userId?`, `startDate?`, `endDate?`, `page?`, `limit?` | Audit trail |
| POST | `/admin/import/parse` | — | Parse Excel SSP data (single clinic) |
| POST | `/admin/import/confirm` | — | Confirm single-clinic Excel import |
| POST | `/admin/import/parse-batch` | — | Parse batch SSP import (conflict check) |
| POST | `/admin/import/confirm-batch` | — | Confirm multi-clinic/multi-year import |
| POST | `/admin/import/clinic/confirm` | — | Bulk import clinic list |
| GET | `/admin/import/jobs/:jobId/status` | — | Check import job status |
| GET | `/admin/import/history` | — | Import job history |

**PUT /admin/users/:id/role body:**
```json
{ "role": "SUPER_ADMIN | PROVINCIAL_OFFICER | CLINIC_OWNER" }
```

**Audit log action values:** `LOGIN`, `REGISTER`, `CREATE`, `UPDATE`, `DELETE`, `SUBMIT`  
**Audit log entity values:** `user`, `clinic`, `submission`, `daily-entry`

---

### 1.8 API Keys — `/api/v1/api-keys` (SUPER_ADMIN only, JWT)

| Method | Path | Description |
|---|---|---|
| POST | `/api-keys` | Generate new API key |
| GET | `/api-keys` | List all API keys |
| DELETE | `/api-keys/:id` | Revoke API key |

**POST /api-keys body:**
```json
{
  "name": "string (vendor name)",
  "permissions": ["submit", "read"]
}
```

The raw key is returned only once on generation. Stored as SHA-256 hash. Header: `X-API-Key: <key>`.

---

### 1.9 Reference — `/api/v1/reference` (no auth)

| Method | Path | Description |
|---|---|---|
| GET | `/reference/provinces` | 77 Thai provinces (id, nameTh, nameEn) |
| GET | `/reference/vaccines` | สสป.2 vaccine list |
| GET | `/reference/diseases` | สสป.3 disease group list |
| GET | `/reference/procedures` | สสป.4 surgical procedure list |

---

### 1.10 Feedback — `/api/v1/feedback` (no auth)

| Method | Path | Rate limit | Description |
|---|---|---|---|
| POST | `/feedback` | 5/min | Submit bug report / suggestion |

**POST /feedback body:**
```json
{
  "message": "string (10–5000 chars, required)",
  "imageBase64": "data:image/jpeg;base64,... (optional, ≤5 MB)",
  "imageUrl": "string (optional)",
  "imageName": "string (optional)",
  "source": "LOGIN_PAGE | SIDEBAR (required)",
  "userName": "string (optional)",
  "userEmail": "string (optional)"
}
```

---

## 2. Shared TypeScript Types — `packages/shared`

Package name: `@vets-hub/shared`

### 2.1 Enums

```typescript
enum UserRole        { SUPER_ADMIN, PROVINCIAL_OFFICER, CLINIC_OWNER }
enum ClinicType      { CLINIC, HOSPITAL, FIRST_CLASS_CLINIC, SECOND_CLASS_CLINIC }
enum ClinicStatus    { ACTIVE, CANCELLED, SUSPENDED }
enum DataSource      { WEB_FORM, API_THIRD_PARTY, API_CLINIC_OS, EXCEL_IMPORT, DAILY_AGGREGATION }
enum SubmissionStatus { DRAFT, SUBMITTED, UNDER_REVIEW*, APPROVED*, REJECTED*, REVISION_REQUESTED* }
enum MonthlySubmissionStatus { OPEN, SUBMITTED }
// * reserved for future review workflow, currently bypassed
```

### 2.2 Core Entity Interfaces

```typescript
interface Province      { id: number; nameTh: string; nameEn: string }
interface District      { id: number; nameTh: string; nameEn: string; provinceId: number }
interface SubDistrict   { id: number; nameTh: string; nameEn: string; zipCode: string|null; districtId: number }
interface ClinicSummary { id: string; licenseNumber: string; name: string; type: ClinicType; status: ClinicStatus; provinceName: string }
interface SubmissionSummary { id: string; clinicName: string; year: number; status: SubmissionStatus; submittedAt: string|null }
```

### 2.3 Daily Entry Interfaces

```typescript
interface MonthlySubmission {
  id, clinicId, year, month, status: MonthlySubmissionStatus,
  isZeroReport, submittedAt, submittedBy, submissionId,
  enteredDays, totalDays, createdAt, updatedAt
}

interface DailyEntry {
  id, monthlySubmissionId, date, isZeroDay, note, createdBy, updatedBy, createdAt, updatedAt,
  animalCounts?: DailyAnimalCountData[],
  vaccinations?: DailyVaccinationData[],
  medicalTreatments?: DailyMedicalTreatmentData[],
  surgicalTreatments?: DailySurgicalTreatmentData[]
}

interface DailyAnimalCountData     { animalType: string; count: number }
interface DailyVaccinationData     { vaccineName: string; animalType: string; count: number; vaccineBrands?: string|null }
interface DailyMedicalTreatmentData  { diseaseGroup: string; animalType: string; count: number }
interface DailySurgicalTreatmentData { procedureGroup: string; animalType: string; count: number }

interface MonthProgress {
  enteredDays, totalDays, percentage,
  missingDates: string[],
  isOverdue: boolean
}

interface CalendarDay {
  date: string; hasEntry: boolean; isZeroDay: boolean;
  totalAnimalCount: number; totalAll: number
}

type UnfilledDayAction = 'ZERO' | 'FILL_MANUALLY'
```

### 2.4 Dashboard Module Types (`packages/shared/src/types/dashboard.ts`)

```typescript
type DashboardModule = 'overview' | 'patient-volume' | 'disease-surveillance' | 'prevention' |
  'surgery' | 'geospatial' | 'benchmarking' | 'market-intelligence' | 'multi-year' | 'regional' | 'analytics'

interface PatientVolumeKPIs     { totalSickAnimals, dogCount, catCount, othersCount, yoyGrowthPercent }
interface MonthlySpeciesData    { month, dog, cat, others }
interface YoYComparisonData     { year, dog, cat, others, total }
interface SickVsPreventionData  { sickTotal, preventionTotal, ratio }
interface DiseaseSurveillanceKPIs { totalMedicalCases, topDiseaseGroup, topDiseaseCount, seasonalTrend }
interface DiseaseByMonthData    { month, diseaseGroup, count }
interface DiseaseBySpeciesData  { diseaseGroup, dog, cat, others }
interface SurgicalBySpeciesData { procedureGroup, dog, cat, others }
interface VaccinationByMonthData { month, rabies, core, other }
interface VaccinationBySpeciesData { vaccineName, dog, cat, others }
interface SurgicalByMonthData   { month, routine, advanced }
interface SterilizationBySpeciesData { species, male, female }
interface ClinicLocationData    { clinicId, name, lat, lng, status, districtName }
interface DistrictClinicDensityData { districtId, districtName, activeCount, cancelledCount, totalCount }
interface ClinicBenchmarkData   { sickPreventionRatio, medSurgRatio, complexityScore, vaccineCompliance, speciesConcentration, surgicalCapacity }
interface NationalAveragesData  { (same 6 fields) }
interface ClinicScatterData     { clinicId, clinicName, patientVolume, complexityScore }
interface ClinicRegistrationHistoryData { year, newRegistrations, stillActive, cancelled }
interface OperatorDemographicsData { male, female, unknown }
interface VaccineBrandShareData { brand, count }
interface MultiYearTrendData    { year, dog, cat, others, total }
interface SeasonalForecastData  { predictions: SeasonalForecastPrediction[] }
interface OutbreakAlertData     { provinceId, provinceName, diseaseGroup, currentCount, average, stdDev, isAlert }
interface SubmissionProgressData { provinceId, provinceName, totalClinics, submitted, percentage }
type ClinicArchetype = 'CAT_CLINIC' | 'DOG_CLINIC' | 'GENERAL_PRACTICE'
```

### 2.5 Zod Validation Schemas (`packages/shared/src/validation/`)

| Schema | Used for |
|---|---|
| `loginSchema` | Frontend + API auth validation |
| `registerSchema` | Frontend + API registration |
| `clinicSchema` | Clinic creation form validation |
| `animalCountEntrySchema` | สสป.1 daily entry item |
| `vaccinationEntrySchema` | สสป.2 daily entry item |
| `medicalTreatmentEntrySchema` | สสป.3 daily entry item |
| `surgicalTreatmentEntrySchema` | สสป.4 daily entry item |
| `upsertDailyDataSchema` | Full day payload (all 4 sections optional) |
| `batchEntryItemSchema` | Single item in batch: `upsertDailyDataSchema + date` |
| `batchEntrySchema` | `{ entries: batchEntryItemSchema[] (min 1) }` |
| `submitMonthSchema` | `{ unfilledDayActions?: Record<date, 'ZERO' | 'FILL_MANUALLY'> }` |

### 2.6 SSP Form Constants (`packages/shared/src/constants/ssp-forms.ts`)

```typescript
ANIMAL_TYPES        = ['สุนัข', 'แมว']  // สสป.1 defaults; custom "อื่น ๆ" allowed
VACCINE_TYPES       = 7 vaccines (rabies, canine_distemper, canine_parvo, canine_corona,
                       feline_panleukopenia, feline_leukemia, feline_fip)
MEDICAL_DISEASE_GROUPS  = 9 groups (ผิวหนัง, ระบบทางเดินหายใจ, ระบบทางเดินอาหาร, ระบบทางเดินปัสสาวะ,
                          ระบบโครงสร้าง, ระบบประสาท, ระบบสืบพันธุ์, โรคตา, โรคหู)
SURGICAL_PROCEDURE_GROUPS = 9 groups (ทำหมันเพศผู้, ทำหมันเพศเมีย, + 7 matching disease groups)
ANIMAL_SUB_TYPES    = ['สุนัข', 'แมว', 'อื่น ๆ(ระบุ)']
```

### 2.7 Utility Functions (`packages/shared/src/utils/`)

```typescript
toThaiYear(gregorianYear: number): number      // +543
toGregorianYear(thaiYear: number): number      // -543
getCurrentThaiYear(): number
formatThaiYear(gregorianYear: number): string  // "พ.ศ. 2568"
```

Import validation helpers: `validateAnimalType`, `validateVaccineName`, `validateDiseaseGroup`, `validateProcedureGroup`, `validateMonth`, `validateCount`, `validateImportSection`.

---

## 3. Database Schema — `packages/db/prisma/schema.prisma`

Provider: PostgreSQL (Supabase). Connection pooling via PgBouncer (port 6543); direct URL for migrations (port 5432).

### 3.1 Tables

#### Geography

| Table | Key Columns | Notes |
|---|---|---|
| `provinces` | `id` (Thai province code 10–96), `name_th`, `name_en`, `geo_json` | 77 provinces |
| `districts` | `id`, `name_th`, `name_en`, `province_id` | Thai district code |
| `sub_districts` | `id`, `name_th`, `name_en`, `zip_code`, `district_id` | — |

#### Auth & Users

| Table | Key Columns | Notes |
|---|---|---|
| `users` | `id` (cuid), `email` (unique), `password_hash`, `role` (enum), `name_th`, `name_prefix`, `phone`, `is_active`, `thai_id_verified`, `last_login_at` | Role: SUPER_ADMIN / PROVINCIAL_OFFICER / CLINIC_OWNER |
| `sessions` | `id`, `session_token` (unique), `user_id`, `expires` | NextAuth session store |

#### Clinics

| Table | Key Columns | Notes |
|---|---|---|
| `clinics` | `id` (cuid), `license_number` (unique), `name`, `type` (enum), `status` (enum), `address`, `province_id`, `district_id`, `sub_district_id`, `latitude`, `longitude`, `founder_name`, `operator_name`, `data_source` | Soft-delete via `deleted_at` |
| `clinic_users` | `id`, `user_id`, `clinic_id`, `is_owner` | Many-to-many; unique on `(user_id, clinic_id)` |

#### Annual Submissions (Legacy SSP flow)

| Table | Key Columns | Notes |
|---|---|---|
| `submissions` | `id`, `clinic_id`, `year` (พ.ศ.), `status` (enum), `data_source`, `reporter_name` | Unique on `(clinic_id, year)` |
| `animal_counts` | `id`, `submission_id`, `animal_type`, `month` (1–12), `count` | Unique on `(submission_id, animal_type, month)` |
| `vaccinations` | `id`, `submission_id`, `vaccine_name`, `animal_type`, `month`, `count`, `vaccine_brands` | Unique on `(submission_id, vaccine_name, animal_type, month)` |
| `medical_treatments` | `id`, `submission_id`, `disease_group`, `animal_type`, `month`, `count` | — |
| `surgical_treatments` | `id`, `submission_id`, `procedure_group`, `animal_type`, `month`, `count` | — |

#### Daily Entry System (Current flow)

| Table | Key Columns | Notes |
|---|---|---|
| `monthly_submissions` | `id`, `clinic_id`, `year`, `month`, `status` (OPEN/SUBMITTED), `is_zero_report`, `submitted_by`, `entered_days`, `total_days`, `submission_id` | Unique on `(clinic_id, year, month)` |
| `daily_entries` | `id`, `monthly_submission_id`, `date` (Date), `is_zero_day`, `is_summary`, `note`, `created_by`, `updated_by` | Unique on `(monthly_submission_id, date, is_summary)` |
| `daily_animal_counts` | `id`, `daily_entry_id`, `animal_type`, `count` | Unique on `(daily_entry_id, animal_type)` |
| `daily_vaccinations` | `id`, `daily_entry_id`, `vaccine_name`, `animal_type`, `count`, `vaccine_brands` | Unique on `(daily_entry_id, vaccine_name, animal_type)` |
| `daily_medical_treatments` | `id`, `daily_entry_id`, `disease_group`, `animal_type`, `count` | — |
| `daily_surgical_treatments` | `id`, `daily_entry_id`, `procedure_group`, `animal_type`, `count` | — |

#### Other

| Table | Key Columns | Notes |
|---|---|---|
| `api_keys` | `id`, `name`, `key_hash` (unique, SHA-256), `prefix` (first 8 chars), `permissions` (string[]), `clinic_id?`, `is_active`, `expires_at` | Third-party integrations |
| `audit_logs` | `id`, `user_id?`, `action`, `entity`, `entity_id`, `details` (JSON diff), `ip_address` | Indexed by `(entity, entity_id)`, `user_id`, `created_at` |
| `import_jobs` | `id`, `type` (CLINIC/SSP), `status` (PROCESSING/COMPLETED/FAILED), `file_name`, `total`, `succeeded`, `skipped`, `failed`, `error_details`, `user_id` | — |
| `feedback_reports` | `id`, `message`, `image_base64`, `image_url`, `image_name`, `source`, `user_name`, `user_email` | — |

### 3.2 Key Relationships

```
Province  1──* District 1──* SubDistrict
Province  1──* Clinic
District  1──* Clinic
Clinic    *──* User         (via clinic_users)
Clinic    1──* Submission   (annual)
Clinic    1──* MonthlySubmission
Submission 1──* MonthlySubmission   (FK link)
MonthlySubmission 1──* DailyEntry
DailyEntry 1──* DailyAnimalCount
DailyEntry 1──* DailyVaccination
DailyEntry 1──* DailyMedicalTreatment
DailyEntry 1──* DailySurgicalTreatment
Submission 1──* AnimalCount | Vaccination | MedicalTreatment | SurgicalTreatment
Clinic    1──* ApiKey
User      1──* AuditLog
User      1──* ImportJob
```

### 3.3 Migrations

| Migration | Date | Change |
|---|---|---|
| `20260209145048_init` | 2026-02-09 | Initial schema |
| `20260218004248_add_daily_entries` | 2026-02-18 | Daily entry system |
| `20260218112344_add_is_summary_to_daily_entries` | 2026-02-18 | `is_summary` flag on daily entries |
| `20260307174311_add_performance_indexes` | 2026-03-07 | Performance indexes |
| `20260308000000_unified_entry_unique_constraint` | 2026-03-08 | Unique constraint on `(monthly_submission_id, date, is_summary)` |
| `20260316233042_add_import_job_model` | 2026-03-16 | ImportJob table |
| `20260317073805_add_feedback_report` | 2026-03-17 | FeedbackReport table |
| `20260326034718_add_user_last_login_at` | 2026-03-26 | `last_login_at` on users |

---

## 4. External Service Integrations

| Service | Purpose | SDK / Package | Config Key |
|---|---|---|---|
| **Supabase** | PostgreSQL hosting (PgBouncer pool + direct) | Prisma (`@prisma/client`) | `DATABASE_URL`, `DIRECT_URL` |
| **Supabase Storage** | Feedback image uploads | Supabase JS | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` |
| **Mapbox** | Interactive geospatial maps in dashboard | `mapbox-gl`, `react-map-gl` | `NEXT_PUBLIC_MAPBOX_TOKEN` (free: 50k loads/month) |
| **NextAuth v5** | Session management in `apps/web` | `next-auth@^5.0.0-beta.25` | `NEXTAUTH_SECRET`, `NEXTAUTH_URL` |

No payment, messaging (SMS/email), or push notification services are currently integrated. No external auth provider (OAuth); login is credentials-only via the NestJS backend.

---

## 5. Authentication Flow

### 5.1 Web App (apps/web)

1. User submits email+password on `/login` page.
2. Next.js `auth.ts` (NextAuth v5 Credentials provider) POSTs to `POST /api/v1/auth/login` on the NestJS backend.
   - Forwards real client IP via `X-Real-Client-IP` header.
3. Backend verifies password with bcrypt, records `last_login_at`, writes an audit log entry.
4. Backend returns `{ accessToken, userId, email, role }`.
5. NextAuth stores `accessToken`, `userId`, `role` in the JWT session cookie (strategy: `jwt`).
6. On subsequent requests, the JWT callback merges `accessToken` into the session object.
7. Next.js middleware (`middleware.ts`) enforces route protection:
   - **Public:** `/login`, `/register`, `/dashboard`, `/map`, `/`, `/components-showcase`, `/api/auth/*`
   - **SUPER_ADMIN only:** `/admin/*`
   - **Any authenticated:** `/clinic/*`, `/daily/*`, `/submit/*`, `/history/*`, `/reports/*`
   - SUPER_ADMIN visiting `/clinic` is redirected to `/admin/dashboard`.
8. For API calls from server components / actions, the `accessToken` from the session is passed as `Authorization: Bearer <token>`.

### 5.2 API (apps/api)

- JWT: extracted from `Authorization: Bearer` header via `passport-jwt`. Role re-validated from DB on each request (stale JWT role is not trusted — fresh role loaded in `JwtStrategy.validate()`).
- API Key: sent as `X-API-Key` header. Validated against SHA-256 hash in `api_keys` table. Permissions array (`submit`, `read`) is stored per key.
- `JwtOrApiKeyGuard`: tries JWT first, falls back to API key (used on most daily-entry and external endpoints).
- Registration flow also auto-links the user to a clinic if a `clinicId` was provided during registration (handled in `AuthService.register`).

---

## 6. Inter-App Communication

### 6.1 web → api

All communication is HTTP REST. The web app calls the NestJS backend at `NEXT_PUBLIC_API_URL` (browser) or `API_URL` (server-side). No shared in-memory state, no GraphQL (the GraphQL playground mentioned in `main.ts` log output appears to be a placeholder — no GraphQL module is imported in `app.module.ts`).

Key patterns:
- Server components read data on behalf of the user using their stored `accessToken`.
- Client components call the API directly from the browser using `swr` hooks.
- `useAutoSave` and `useDailyEntries` hooks manage optimistic state and debounced API calls.

### 6.2 Shared Packages

Both apps consume `@vets-hub/shared` (TypeScript types, Zod schemas, SSP constants, Thai year utilities).  
`apps/api` also imports `@vets-hub/db` for the Prisma client.

```
apps/web   → @vets-hub/shared
apps/api   → @vets-hub/shared
apps/api   → @vets-hub/db (PrismaClient)
```

---

## 7. Public API Surface — Shared Packages

### `@vets-hub/shared`

**Barrel exports from `src/index.ts`:** constants, types, validation schemas, utility functions.

| Export group | Contents |
|---|---|
| `constants` | `ANIMAL_TYPES`, `VACCINE_TYPES`, `MEDICAL_DISEASE_GROUPS`, `SURGICAL_PROCEDURE_GROUPS`, `ANIMAL_SUB_TYPES`, `THAI_MONTHS`, `THAI_MONTHS_SHORT`, `SSP_SECTION_NAMES`, `STATUS_LABELS`, type aliases |
| `types` | `UserRole`, `ClinicType`, `ClinicStatus`, `DataSource`, `MonthlySubmissionStatus`, `SubmissionStatus`, `Province`, `District`, `SubDistrict`, `ClinicSummary`, `SubmissionSummary`, `MonthlySubmission`, `DailyEntry`, `DailyAnimalCountData`, `DailyVaccinationData`, `DailyMedicalTreatmentData`, `DailySurgicalTreatmentData`, `MonthProgress`, `CalendarDay`, `UnfilledDayAction`, all dashboard types |
| `validation` | Zod schemas (login, register, clinic, all 4 SSP entry schemas, composite upsert/batch/submit schemas); import validation functions |
| `utils` | `toThaiYear`, `toGregorianYear`, `getCurrentThaiYear`, `formatThaiYear` |

### `@vets-hub/db`

Thin re-export wrapper:
```typescript
export { PrismaClient } from '@prisma/client';
export type * from '@prisma/client';
```
Consumers import the Prisma-generated client and all Prisma types directly.

---

## 8. Environment Variables

| Variable | Used by | Required | Notes |
|---|---|---|---|
| `DATABASE_URL` | api, db | Yes | Supabase pooled (PgBouncer, port 6543) |
| `DIRECT_URL` | db migrations | Yes | Supabase direct (port 5432) |
| `JWT_SECRET` | api | Yes | Sign/verify JWTs |
| `JWT_EXPIRATION` | api | No | Default `7d` |
| `NEXTAUTH_SECRET` | web | Yes | NextAuth session encryption |
| `NEXTAUTH_URL` | web | Yes | e.g., `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | web (client) | Yes | Browser-facing API base, e.g. `http://localhost:4000/api/v1` |
| `API_URL` | web (server) | No | Server-side API base; falls back to `NEXT_PUBLIC_API_URL` without `/graphql` |
| `NEXT_PUBLIC_SUPABASE_URL` | web | Yes (storage) | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | web | Yes (storage) | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | web/api | Yes (storage) | Service role key for admin storage ops |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | web | Yes (maps) | Mapbox public token |
| `FRONTEND_URL` | api (CORS) | No | Comma-separated allowed origins; default `http://localhost:3000` |
| `PORT` | api | No | Default `4000` |
| `NODE_ENV` | api | No | Swagger disabled in production unless `ENABLE_SWAGGER=true` |
| `ENABLE_SWAGGER` | api | No | Force-enable Swagger in production |
