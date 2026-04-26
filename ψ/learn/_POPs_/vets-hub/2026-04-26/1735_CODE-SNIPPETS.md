# VetsHub Code Snippets
> Explored: 2026-04-26 | Monorepo: `/Users/switchaphon/_POPs_/vets-hub`
> Stack: NestJS (API) + Next.js 15 App Router (Web) + Prisma + PostgreSQL + pnpm workspaces + Turborepo

---

## Architecture at a Glance

```
vets-hub/
├── apps/
│   ├── api/          # NestJS REST API (port 4000), serves /api/v1/*
│   └── web/          # Next.js 15 App Router (port 3000)
├── packages/
│   ├── shared/       # Zod schemas, enums, types, Thai calendar utils
│   └── db/           # PrismaClient re-export from @prisma/client
└── turbo.json        # Turborepo pipeline
```

**Domain**: กรมปศุสัตว์ (Department of Livestock Development, Thailand) national veterinary clinic statistics system. Clinics submit สสป.1–4 forms monthly (animal counts, vaccinations, medical treatments, surgical treatments). Data flows from daily entries → monthly aggregation → annual submission.

---

## 1. Main Entry Points

### 1.1 API Bootstrap — `apps/api/src/main.ts`

NestJS app with versioned REST API, Helmet security, multi-origin CORS, global validation pipe, and conditional Swagger.

```typescript
async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  app.set('trust proxy', true);

  // Raise body parser limit to 10MB to support base64 image attachments
  app.useBodyParser('json', { limit: '10mb' });

  app.use(helmet());

  // Supports comma-separated origins for Vercel preview + custom domain
  const allowedOrigins = (process.env.FRONTEND_URL || 'http://localhost:3000')
    .split(',')
    .map((o) => o.trim());
  app.enableCors({ origin: allowedOrigins, credentials: true });

  // All REST endpoints live under /api/v1/
  app.enableVersioning({ type: VersioningType.URI, prefix: 'api/v' });

  app.useGlobalPipes(new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }));

  app.useGlobalFilters(new AllExceptionsFilter());

  if (process.env.NODE_ENV !== 'production' || process.env.ENABLE_SWAGGER === 'true') {
    setupSwagger(app);
  }

  await app.listen(process.env.PORT || 4000);
}
```

### 1.2 API Root Module — `apps/api/src/app.module.ts`

Global throttler (100 req/min), in-memory cache (5 min TTL, 200 items), all feature modules registered.

```typescript
@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, envFilePath: '../../.env' }),
    ThrottlerModule.forRoot([{ ttl: 60000, limit: 100 }]),
    CacheModule.register({ ttl: 300_000, max: 200, isGlobal: true }),
    PrismaModule, AuthModule, ClinicsModule, SubmissionsModule,
    AdminModule, ReportsModule, ApiKeysModule, ReferenceModule,
    DailyEntriesModule, FeedbackModule, AuditModule,
  ],
  providers: [{ provide: APP_GUARD, useClass: ThrottlerGuard }],
})
export class AppModule {}
```

### 1.3 Web Root Layout — `apps/web/app/layout.tsx`

Noto Sans Thai font, Thai locale, global Sonner toaster, NextAuth session wrapping.

```tsx
const notoSansThai = Noto_Sans_Thai({
  subsets: ['thai'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-noto-sans-thai',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'VetsHub - ศูนย์กลางสถานพยาบาลสัตว์แห่งชาติ',
  description: 'ระบบรายงานสถิติสัตว์ป่วย (สสป.) กองสวัสดิภาพสัตว์และสัตวแพทย์บริการ กรมปศุสัตว์',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th" className={notoSansThai.variable}>
      <body className="font-sans antialiased">
        <SessionProvider>{children}</SessionProvider>
        <Toaster position="top-right" richColors closeButton />
      </body>
    </html>
  );
}
```

### 1.4 PrismaService — `apps/api/src/prisma/prisma.service.ts`

Minimal NestJS lifecycle wrapper — graceful connect on init, graceful disconnect on destroy.

```typescript
@Injectable()
export class PrismaService extends PrismaClient implements OnModuleInit, OnModuleDestroy {
  async onModuleInit() {
    try {
      await this.$connect();
    } catch {
      this.logger.warn('Could not connect to database. Start PostgreSQL with: docker compose up -d');
    }
  }

  async onModuleDestroy() {
    await this.$disconnect();
  }
}
```

---

## 2. Authentication

### 2.1 NextAuth v5 Config — `apps/web/lib/auth.ts`

Credentials provider bridges to NestJS backend. Forwards real client IP for audit logging. JWT strategy stores `accessToken` from the backend JWT into the Next.js session.

```typescript
export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      async authorize(credentials, request) {
        // Forward real client IP and user-agent to the backend
        const clientIp =
          request?.headers?.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';

        const response = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Real-Client-IP': clientIp,
            'User-Agent': request?.headers?.get('user-agent') || '',
          },
          body: JSON.stringify({ email: credentials.email, password: credentials.password }),
        });

        if (!response.ok) return null;
        const data = await response.json();
        return { id: data.userId, email: data.email, role: data.role, accessToken: data.accessToken };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.accessToken = user.accessToken;
        token.userId = user.id!;
      }
      return token;
    },
    async session({ session, token }) {
      return {
        ...session,
        accessToken: token.accessToken as string,
        user: { ...session.user, id: token.userId as string, role: token.role as string, accessToken: token.accessToken },
      };
    },
  },
  pages: { signIn: '/login' },
  session: { strategy: 'jwt' },
});
```

### 2.2 Next.js Middleware (Route Guard) — `apps/web/middleware.ts`

Role-based routing: public routes pass through, unauthenticated users redirect to `/login` with `callbackUrl`, `SUPER_ADMIN` is redirected from clinic portal to admin dashboard.

```typescript
export default auth((req) => {
  const { pathname } = req.nextUrl;
  const isAuthenticated = !!req.auth;
  const userRole = req.auth?.user?.role;

  const publicRoutes = ['/login', '/register', '/dashboard', '/map', '/', '/components-showcase'];
  if (publicRoutes.some((r) => pathname === r || pathname.startsWith('/api/auth'))) {
    return NextResponse.next();
  }

  if (!isAuthenticated) {
    const loginUrl = new URL('/login', req.url);
    loginUrl.searchParams.set('callbackUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname.startsWith('/admin') && userRole !== 'SUPER_ADMIN') {
    return NextResponse.redirect(new URL('/clinic', req.url));
  }

  // SUPER_ADMIN visiting clinic root → redirect to admin dashboard
  if (pathname === '/clinic' && userRole === 'SUPER_ADMIN') {
    return NextResponse.redirect(new URL('/admin/dashboard', req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|geo|images|api/auth).*)'],
};
```

### 2.3 JWT Strategy — `apps/api/src/auth/jwt.strategy.ts`

Critical pattern: role is **re-fetched from DB** on every request, not trusted from the JWT payload, preventing stale-role attacks.

```typescript
async validate(payload: { sub: string; email: string; role: string }) {
  const user = await this.prisma.user.findUnique({
    where: { id: payload.sub },
    select: { id: true, email: true, role: true, isActive: true },
  });

  if (!user || !user.isActive) {
    throw new UnauthorizedException('บัญชีนี้ถูกระงับการใช้งาน');
  }

  // Return fresh role from DB, not stale JWT payload
  return { sub: user.id, email: user.email, role: user.role };
}
```

### 2.4 Dual-Auth Guard — `apps/api/src/api-keys/jwt-or-api-key.guard.ts`

Public API endpoints accept either an `X-API-Key` header or a `Bearer` JWT — API key checked first.

```typescript
async canActivate(context: ExecutionContext): Promise<boolean> {
  const request = context.switchToHttp().getRequest();

  // Try API key first
  const apiKey = request.headers['x-api-key'];
  if (apiKey) {
    const validKey = await this.apiKeysService.validate(apiKey);
    if (validKey) {
      request.apiKey = validKey;
      return true;
    }
    throw new UnauthorizedException('API Key ไม่ถูกต้องหรือหมดอายุ');
  }

  // Fall through to JWT Bearer
  const token = request.headers.authorization?.slice(7);
  if (token) {
    const payload = await this.jwtService.verifyAsync(token, { secret: ... });
    request.user = payload;
    return true;
  }

  throw new UnauthorizedException('กรุณาระบุ X-API-Key header หรือ Authorization: Bearer token');
}
```

---

## 3. Core Business Logic

### 3.1 Daily Entry Service — upsert with atomic increments — `apps/api/src/daily-entries/daily-entries.service.ts`

The `addToDailyData` method uses Prisma `{ increment }` for append-mode entry (barcode-scanner style), while `setDailyData` does a full delete-then-recreate (PUT semantics). Both fan out with `Promise.all` over all child tables.

```typescript
// APPEND MODE — atomic increment per (dailyEntryId, animalType)
async addToDailyData(dailyEntryId: string, data: UpsertDailyDataDto) {
  const operations: Promise<any>[] = [];

  if (data.animalCounts) {
    for (const ac of data.animalCounts) {
      if (ac.count < 0) throw new BadRequestException('จำนวนที่เพิ่มต้องไม่ติดลบ');
      operations.push(
        this.prisma.dailyAnimalCount.upsert({
          where: { dailyEntryId_animalType: { dailyEntryId, animalType: ac.animalType } },
          update: { count: { increment: ac.count } },   // atomic increment
          create: { dailyEntryId, animalType: ac.animalType, count: ac.count },
        }),
      );
    }
  }
  // ... same pattern for vaccinations, medicalTreatments, surgicalTreatments

  await Promise.all(operations);

  // Clear isZeroDay flag if actual data was saved
  if (operations.length > 0) {
    await this.prisma.dailyEntry.update({ where: { id: dailyEntryId }, data: { isZeroDay: false } });
  }
}

// REPLACE MODE — delete all children first (PUT semantics)
async setDailyData(dailyEntryId: string, data: UpsertDailyDataDto) {
  await Promise.all([
    this.prisma.dailyAnimalCount.deleteMany({ where: { dailyEntryId } }),
    this.prisma.dailyVaccination.deleteMany({ where: { dailyEntryId } }),
    this.prisma.dailyMedicalTreatment.deleteMany({ where: { dailyEntryId } }),
    this.prisma.dailySurgicalTreatment.deleteMany({ where: { dailyEntryId } }),
  ]);
  // ... then recreate with fresh values

  // If no data at all → delete the entry so the day returns to "unfilled"
  if (operations.length === 0) {
    await this.prisma.dailyEntry.delete({ where: { id: dailyEntryId } });
    return { deleted: true, id: dailyEntryId };
  }
}
```

### 3.2 Thai Year Helpers — `packages/shared/src/utils/index.ts`

Buddhist Era (พ.ศ.) = Gregorian + 543. All year parameters in API and DB are stored as Thai years.

```typescript
export function toThaiYear(gregorianYear: number): number {
  return gregorianYear + 543;
}

export function toGregorianYear(thaiYear: number): number {
  return thaiYear - 543;
}

export function getCurrentThaiYear(): number {
  return toThaiYear(new Date().getFullYear());
}

// Used throughout services to get today's date in Asia/Bangkok timezone
private getTodayThai(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Bangkok' });
}

// Days in month: Thai year converted to Gregorian before calling Date()
private getDaysInMonth(thaiYear: number, month: number): number {
  const gregorianYear = thaiYear - 543;
  return new Date(gregorianYear, month, 0).getDate();
}
```

### 3.3 Monthly Submission Lifecycle & Materialization — `apps/api/src/daily-entries/monthly-submission.service.ts`

The critical `submitMonth` transaction: handle unfilled days → aggregate totals via SQL `groupBy` → materialize into the annual `Submission` table → mark SUBMITTED → check if all 12 months done → flush report cache.

```typescript
async submitMonth(monthlySubmissionId: string, submittedBy: string, unfilledDayActions?) {
  const result = await this.prisma.$transaction(async (tx) => {
    const ms = await tx.monthlySubmission.findUnique({ where: { id: monthlySubmissionId }, include: { clinic: true } });

    if (ms.status === 'SUBMITTED') return ms; // idempotent

    // 1. Handle unfilled days (ZERO or FILL_MANUALLY)
    if (unfilledDayActions && !hasBulkEntry) {
      for (const [dateStr, action] of Object.entries(unfilledDayActions)) {
        if (dateStr > todayStr) continue; // no future days
        if (action === 'ZERO') {
          // findFirst + create/update — avoids Prisma @db.Date composite-key issue
          const existing = await tx.dailyEntry.findFirst({ where: { monthlySubmissionId, date, isSummary: false } });
          existing
            ? await tx.dailyEntry.update({ where: { id: existing.id }, data: { isZeroDay: true } })
            : await tx.dailyEntry.create({ data: { monthlySubmissionId, date, isZeroDay: true, isSummary: false } });
        }
      }
    }

    // 2. SQL-level aggregation — never loads all rows into JS
    const [animalCountGroups, vaccinationGroups, medicalGroups, surgicalGroups] = await Promise.all([
      tx.dailyAnimalCount.groupBy({ by: ['animalType'], _sum: { count: true }, where: { dailyEntry: { monthlySubmissionId } } }),
      tx.dailyVaccination.groupBy({ by: ['vaccineName', 'animalType'], _sum: { count: true }, where: { dailyEntry: { monthlySubmissionId } } }),
      tx.dailyMedicalTreatment.groupBy({ by: ['diseaseGroup', 'animalType'], _sum: { count: true }, where: { dailyEntry: { monthlySubmissionId } } }),
      tx.dailySurgicalTreatment.groupBy({ by: ['procedureGroup', 'animalType'], _sum: { count: true }, where: { dailyEntry: { monthlySubmissionId } } }),
    ]);

    // 3. Upsert aggregated rows into annual Submission child tables
    await this.materializeToSubmissionInTx(tx, ms, totals);

    // 4. Check if all 12 months SUBMITTED → flip annual Submission to SUBMITTED
    const submittedCount = await tx.monthlySubmission.count({
      where: { clinicId: ms.clinicId, year: ms.year, status: 'SUBMITTED' },
    });
    if (submittedCount === 12 && ms.submissionId) {
      await tx.submission.update({ where: { id: ms.submissionId }, data: { status: 'SUBMITTED', submittedAt: new Date() } });
    }
  }, {
    isolationLevel: Prisma.TransactionIsolationLevel.ReadCommitted,
    maxWait: 10000,
    timeout: 30000,
  });

  await this.cacheManager.clear(); // invalidate report cache
}
```

### 3.4 Batch Import (Multi-clinic, multi-year Excel) — `apps/api/src/admin/import.service.ts`

Each entry runs in its own transaction to isolate failures. Creates an `ImportJob` record for async progress tracking. Geography names (province/district/sub-district) are pre-resolved with a cache before per-clinic processing.

```typescript
async confirmBatchImport(dto: BatchImportDto, userId: string) {
  const job = await this.prisma.importJob.create({
    data: { type: 'SSP', status: 'PROCESSING', fileName: dto.fileName, total: dto.entries.length, userId },
  });

  let succeeded = 0, skipped = 0, failed = 0;
  const errorDetails: any[] = [];

  // Each entry in its own transaction — a failure in one entry doesn't roll back others
  for (const entry of dto.entries) {
    try {
      await this.prisma.$transaction(async (tx) => {
        let clinic = await tx.clinic.findUnique({ where: { licenseNumber: entry.licenseNumber } });
        if (!clinic) {
          clinic = await tx.clinic.create({ data: { licenseNumber: entry.licenseNumber, name: 'สถานพยาบาลนำเข้า', dataSource: 'EXCEL_IMPORT' } });
        }

        const existing = await tx.submission.findFirst({ where: { clinicId: clinic.id, year: entry.year } });
        if (existing) {
          if (strategy === 'skip') { skipped++; return; }
          await tx.submission.delete({ where: { id: existing.id } }); // overwrite
        }

        const submission = await tx.submission.create({ data: { clinicId: clinic.id, year: entry.year, status: 'SUBMITTED', dataSource: 'EXCEL_IMPORT', submittedAt: new Date() } });
        await this.insertSectionRecords(tx, submission.id, entry.sections);
        succeeded++;
      }, { timeout: 30000 });
    } catch (err: any) {
      failed++;
      errorDetails.push({ licenseNumber: entry.licenseNumber, year: entry.year, error: err?.message });
    }
  }

  await this.prisma.importJob.update({ where: { id: job.id }, data: { status: ..., succeeded, skipped, failed, errorDetails } });
}
```

---

## 4. Shared Package — `packages/shared/`

### 4.1 Zod Schemas for สสป. Forms — `packages/shared/src/validation/ssp-forms.ts`

All 4 SSP form sections validated via Zod. Schemas are shared between the API (via `ZodValidationPipe`) and the web client. Thai-language error messages throughout.

```typescript
// สสป.1 — Animal Count
export const animalCountEntrySchema = z.object({
  animalType: z.string().min(1).max(100, 'ประเภทสัตว์ต้องไม่เกิน 100 ตัวอักษร'),
  count: z.number().int().min(0, 'จำนวนต้องไม่ติดลบ'),
});

// สสป.2 — Vaccination (with optional brand string)
export const vaccinationEntrySchema = z.object({
  vaccineName: z.string().min(1),
  animalType: z.string().min(1),
  count: z.number().int().min(0, 'จำนวนต้องไม่ติดลบ'),
  vaccineBrands: z.string().max(500, 'ยี่ห้อวัคซีนต้องไม่เกิน 500 ตัวอักษร').optional(),
});

// Composite upsert payload (all 4 sections optional)
export const upsertDailyDataSchema = z.object({
  animalCounts: z.array(animalCountEntrySchema).optional(),
  vaccinations: z.array(vaccinationEntrySchema).optional(),
  medicalTreatments: z.array(medicalTreatmentEntrySchema).optional(),
  surgicalTreatments: z.array(surgicalTreatmentEntrySchema).optional(),
});

// Batch entry: array of daily entries each with a date
export const batchEntryItemSchema = upsertDailyDataSchema.extend({
  date: z.string().min(1).max(10).regex(/^\d{4}-\d{2}-\d{2}$/, 'รูปแบบวันที่ไม่ถูกต้อง (YYYY-MM-DD)'),
});

// Unfilled day action enum
export const submitMonthSchema = z.object({
  unfilledDayActions: z.record(z.string(), z.enum(['ZERO', 'FILL_MANUALLY'])).optional(),
});
```

### 4.2 Domain Enums — `packages/shared/src/types/index.ts`

`DataSource` enum tracks provenance — web form vs third-party API vs Excel import vs daily aggregation. `SubmissionStatus` has reserved values commented out for a future review workflow.

```typescript
export enum DataSource {
  WEB_FORM = 'WEB_FORM',
  API_THIRD_PARTY = 'API_THIRD_PARTY',
  API_CLINIC_OS = 'API_CLINIC_OS',
  EXCEL_IMPORT = 'EXCEL_IMPORT',
  DAILY_AGGREGATION = 'DAILY_AGGREGATION',
}

export enum SubmissionStatus {
  DRAFT = 'DRAFT',
  SUBMITTED = 'SUBMITTED',
  UNDER_REVIEW = 'UNDER_REVIEW',   // Reserved — bypassed in MVP v1.2.3
  APPROVED = 'APPROVED',           // Reserved — bypassed in MVP v1.2.3
  REJECTED = 'REJECTED',           // Reserved — bypassed in MVP v1.2.3
  REVISION_REQUESTED = 'REVISION_REQUESTED', // Reserved — bypassed in MVP v1.2.3
}

export type UnfilledDayAction = 'ZERO' | 'FILL_MANUALLY';
```

### 4.3 SSP Form Constants — `packages/shared/src/constants/ssp-forms.ts`

Official government form category lists used on both client and server for rendering and validation.

```typescript
export const ANIMAL_TYPES = ['สุนัข', 'แมว'] as const;

export const MEDICAL_DISEASE_GROUPS = [
  'ผิวหนัง', 'ระบบทางเดินหายใจ', 'ระบบทางเดินอาหาร', 'ระบบทางเดินปัสสาวะ',
  'ระบบโครงสร้าง', 'ระบบประสาท', 'ระบบสืบพันธุ์', 'โรคตา', 'โรคหู',
] as const;

export const SURGICAL_PROCEDURE_GROUPS = [
  'ทำหมันเพศผู้', 'ทำหมันเพศเมีย', 'ผิวหนัง', 'ระบบทางเดินหายใจ',
  'ระบบทางเดินอาหาร', 'ระบบทางเดินปัสสาวะ', 'ระบบโครงสร้าง', 'ระบบประสาท', 'ระบบสืบพันธุ์',
] as const;

export const SSP_SECTION_NAMES = {
  ssp1: { short: 'สสป.1', full: 'สัตว์ป่วยที่เข้ารับการรักษา' },
  ssp2: { short: 'สสป.2', full: 'การป้องกันโรคสัตว์' },
  ssp3: { short: 'สสป.3', full: 'การรักษาทางอายุรกรรม' },
  ssp4: { short: 'สสป.4', full: 'การรักษาทางศัลยกรรม' },
} as const;
```

---

## 5. Error Handling

### 5.1 Global Exception Filter — `apps/api/src/common/filters/all-exceptions.filter.ts`

Skips non-HTTP contexts (GraphQL errors handled by Apollo separately). Logs 5xx with stack trace, returns structured JSON.

```typescript
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    if (host.getType<string>() !== 'http') return; // skip GraphQL context

    const status = exception instanceof HttpException
      ? exception.getStatus()
      : HttpStatus.INTERNAL_SERVER_ERROR;

    if (status >= 500) {
      this.logger.error(`${request.method} ${request.url} ${status}`, exception instanceof Error ? exception.stack : undefined);
    }

    response.status(status).json({
      statusCode: status,
      message: typeof message === 'string' ? message : (message as any).message,
      timestamp: new Date().toISOString(),
      path: request.url,
    });
  }
}
```

### 5.2 Global Error Boundary — `apps/web/app/global-error.tsx`

Root-level React error boundary. Must use plain `<html>/<body>` and `<a href>` (not Next.js `<Link>`) since the React tree above it may be broken.

```tsx
'use client';

export default function GlobalError({ error: _error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="th">
      <body>
        {/* inline styles only — Tailwind not available at this boundary level */}
        <button onClick={reset}>ลองใหม่</button>
        {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
        <a href="/">กลับหน้าหลัก</a>
        {/* Must use <a> not <Link> — error boundary breaks React tree dependency */}
      </body>
    </html>
  );
}
```

### 5.3 Fire-and-Forget Audit Logging — `apps/api/src/audit/audit.service.ts`

Audit logs are written asynchronously (never throws, never blocks the request path). Thai midnight offset for "today's" stats.

```typescript
/** Fire-and-forget audit log — never throws */
async log(input: AuditLogInput): Promise<void> {
  try {
    await this.prisma.auditLog.create({
      data: {
        userId: input.userId,
        action: input.action,
        entity: input.entity,
        entityId: input.entityId,
        details: input.details ?? Prisma.JsonNull,
        ipAddress: input.ipAddress,
      },
    });
  } catch (error) {
    this.logger.error('Failed to write audit log', error); // swallowed
  }
}

// Thai midnight (UTC+7): "today" starts at 17:00 UTC yesterday
const todayStart = new Date();
todayStart.setUTCHours(-7, 0, 0, 0);
```

---

## 6. Interesting Patterns & Idioms

### 6.1 Zod Validation Pipe for NestJS — `apps/api/src/common/pipes/zod-validation.pipe.ts`

Bridges Zod schemas (from `packages/shared`) into NestJS pipes, reusing the same validation logic on both API and client.

```typescript
@Injectable()
export class ZodValidationPipe implements PipeTransform {
  constructor(private schema: ZodSchema) {}

  transform(value: unknown) {
    const result = this.schema.safeParse(value);
    if (!result.success) {
      throw new BadRequestException(result.error.errors);
    }
    return result.data;
  }
}
```

### 6.2 RBAC via Decorator + Guard — `apps/api/src/common/`

`@Roles()` sets metadata; `RolesGuard` reads it via `Reflector`. User role is read from `request.user.role` which comes from the refreshed DB value in `JwtStrategy.validate()`.

```typescript
// Decorator
export const Roles = (...roles: UserRole[]) => SetMetadata(ROLES_KEY, roles);

// Guard
canActivate(context: ExecutionContext): boolean {
  const requiredRoles = this.reflector.getAllAndOverride<string[]>(ROLES_KEY, [
    context.getHandler(),
    context.getClass(),
  ]);
  if (!requiredRoles) return true;
  const { user } = context.switchToHttp().getRequest();
  return requiredRoles.includes(user?.role);
}

// Usage on controller
@Roles(UserRole.SUPER_ADMIN)
@UseGuards(JwtAuthGuard, RolesGuard)
@Get('admin/users')
```

### 6.3 Clinic Membership Guard — `apps/api/src/daily-entries/guards/clinic-membership.guard.ts`

Resolves `clinicId` from multiple param shapes (direct `clinicId`, `monthlySubmissionId`, or `dailyEntry.id`). Supports both JWT users and API-key-scoped access.

```typescript
async canActivate(context: ExecutionContext): Promise<boolean> {
  let clinicId: string | null = null;

  if (params.clinicId) {
    clinicId = params.clinicId;
  } else if (params.monthlySubmissionId || params.id) {
    // Traverse: monthlySubmissionId → clinicId, or dailyEntry → monthlySubmission → clinicId
    const ms = await this.prisma.monthlySubmission.findUnique({ where: { id: msId }, select: { clinicId: true } });
    if (ms) clinicId = ms.clinicId;
    else {
      const entry = await this.prisma.dailyEntry.findUnique({
        where: { id: msId },
        select: { monthlySubmission: { select: { clinicId: true } } },
      });
      if (entry) clinicId = entry.monthlySubmission.clinicId;
    }
  }

  // API key: check if key is scoped to this specific clinic
  if (apiKey && apiKey.clinicId && apiKey.clinicId !== clinicId) {
    throw new ForbiddenException('API Key ไม่มีสิทธิ์เข้าถึงคลินิกนี้');
  }

  // JWT: require a ClinicUser membership row
  const membership = await this.prisma.clinicUser.findUnique({
    where: { userId_clinicId: { userId, clinicId } },
  });
  if (!membership) throw new ForbiddenException('ไม่มีสิทธิ์เข้าถึงคลินิกนี้');
  return true;
}
```

### 6.4 Auto-Save Hook — `apps/web/lib/hooks/useAutoSave.ts`

Generic debounced auto-save for any serializable data. Uses JSON-stringified comparison to detect real changes (not reference identity). `saveFnRef` pattern prevents stale closure issues.

```typescript
export function useAutoSave<T>({ data, saveFn, debounceMs = 500 }: UseAutoSaveOptions<T>) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevDataRef = useRef<string>(JSON.stringify(data));
  const saveFnRef = useRef(saveFn);

  // Keep ref current each render — prevents stale closure
  saveFnRef.current = saveFn;

  useEffect(() => {
    const currentData = JSON.stringify(data);
    if (currentData === prevDataRef.current) return; // no change
    prevDataRef.current = currentData;

    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => doSave(data), debounceMs);

    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [data, debounceMs, doSave]);

  // saveNow: cancel pending debounce and flush immediately
  const saveNow = useCallback(async () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    await doSave(dataRef.current);
  }, [doSave]);
}
```

### 6.5 SQL Injection Prevention — `apps/api/src/reports/reports.utils.ts`

Section names from user input are whitelisted via a frozen map before being interpolated into raw SQL.

```typescript
export const SECTION_TABLE_MAP: Readonly<Record<string, string>> = Object.freeze({
  animalCounts:      'animal_counts',
  vaccinations:      'vaccinations',
  medicalTreatments: 'medical_treatments',
  surgicalTreatments:'surgical_treatments',
});

export function resolveTableName(section: string): string {
  const table = SECTION_TABLE_MAP[section];
  if (!table) {
    throw new BadRequestException(`Invalid section: ${section}. Must be one of: ${Object.keys(SECTION_TABLE_MAP).join(', ')}`);
  }
  return table;
}
```

### 6.6 Lazy Chart with Intersection Observer — `apps/web/components/dashboard/LazyChart.tsx`

Charts only mount when scrolled into view (+ 200px look-ahead). Prevents rendering dozens of Recharts instances on initial page load.

```tsx
export default function LazyChart({ children, height }: LazyChartProps) {
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: 0.1,
    rootMargin: '200px', // start loading 200px before viewport
  });

  return (
    <div ref={ref} style={{ minHeight: `${height}px` }}>
      {inView ? children : <Skeleton style={{ height: `${height}px` }} />}
    </div>
  );
}
```

### 6.7 Monthly Submit Flow State Machine — `apps/web/lib/hooks/useMonthlySubmitFlow.ts`

Entire multi-step submission wizard (check unfilled days → resolve each as ZERO or FILL_MANUALLY → confirm → submit) encapsulated as a single hook. Popup visibility computed (`effectiveShowPopup`) to suppress parent popup when inline/bulk entry modals are open.

```typescript
const effectiveShowPopup = showUnfilledPopup && !showInlineEntry && !showBulkEntry;

// Step 1: fetch unfilled days and show resolution popup
const handleMonthlySubmitClick = async () => { ... };

// Step 2: resolve each unfilled day; save ZERO entries, then transition to review mode
const handleUnfilledConfirm = async (actions: Record<string, DayAction>) => {
  const fillManuallyDays = Object.entries(actions).filter(([, a]) => a === 'FILL_MANUALLY');
  if (fillManuallyDays.length > 0) return; // wait for user to fill

  if (Object.keys(actions).length === 0) {
    setShowConfirmDialog(true); // all resolved — go to final confirm
    return;
  }
  // batch-save ZERO entries, then re-check
};

// Step 3: final submit
const handleConfirmSubmit = async () => {
  await fetch(`${API_BASE_URL}/api/v1/daily-entries/monthly/${ms.id}/submit`, {
    method: 'POST',
    body: JSON.stringify({ unfilledDayActions: pendingActions }),
  });
};
```

### 6.8 Excel Parser for สสป. Forms — `apps/web/lib/utils/excelParser.ts`

Parses raw 2D cell arrays from XLSX into structured API payloads. Column layout is hardcoded per section spec. License number detected via Thai regex from cover sheet.

```typescript
export function parseSSPExcel(sheetData: any[][], sheetType: string): ParsedSection {
  const dataRows = sheetData.slice(2); // rows 0-1 are headers
  switch (sheetType) {
    case 'สสป.1': return parseAnimalCounts(dataRows);
    case 'สสป.2': return parseVaccinations(dataRows);
    case 'สสป.3': return parseMedicalTreatments(dataRows);
    case 'สสป.4': return parseSurgicalTreatments(dataRows);
  }
}

// Month columns are 1-indexed (column 0 = animalType)
function parseAnimalCounts(dataRows) {
  for (const row of dataRows) {
    for (let month = 1; month <= 12; month++) {
      data.push({ animalType: trimString(row[0]), month, count: safeCount(row[month]) });
    }
  }
}

// License number detection from Thai cover sheet
export function detectLicenseNumber(coverSheetData: any[][]): string | null {
  for (const row of coverSheetData) {
    for (const cell of row) {
      const match = cell.match(/เลขที่ใบอนุญาต[ตั้งและดำเนินการ]*[:\s]+([^\s,]+)/);
      if (match) return match[1].trim();
    }
  }
  return null;
}
```

---

## 7. Cross-App Communication

### 7.1 NextAuth Route Handler — `apps/web/app/api/auth/[...nextauth]/route.ts`

Minimal — just re-exports handlers from `lib/auth.ts`.

```typescript
import { handlers } from '@/lib/auth';
export const { GET, POST } = handlers;
```

### 7.2 API URL Config — `apps/web/lib/config.ts`

Single source of truth: strips `/graphql` suffix from `NEXT_PUBLIC_API_URL` for REST calls. Separate `SERVER_API_URL` for SSR-only server-to-server calls.

```typescript
const GRAPHQL_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000/graphql').trim();

export const API_BASE_URL = GRAPHQL_URL.replace('/graphql', '');  // REST base
export const GRAPHQL_ENDPOINT = GRAPHQL_URL;
export const SERVER_API_URL = process.env.API_URL || API_BASE_URL; // SSR only
```

### 7.3 `useDailyEntries` — Complete API Hook — `apps/web/lib/hooks/useDailyEntries.ts`

Exposes the full daily-entry API surface to client components. Authorization header assembled from NextAuth session token. Consistent error→null return pattern (no throw at hook boundary).

```typescript
export function useDailyEntries() {
  const { data: session } = useSession();

  // Bearer token assembled fresh per call (session token may refresh)
  const headers = useCallback(() => {
    const h: Record<string, string> = { 'Content-Type': 'application/json' };
    if (session?.accessToken) h['Authorization'] = `Bearer ${session.accessToken}`;
    return h;
  }, [session?.accessToken]);

  // Returns null on error (never throws to caller)
  const getOrCreateEntry = useCallback(async (monthlySubmissionId: string, date: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/daily-entries/entry/${monthlySubmissionId}/${date}`, {
        method: 'POST',
        headers: headers(),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.message || 'ไม่สามารถสร้างข้อมูลรายงานรายวันได้');
      }
      return await res.json();
    } catch (err: any) {
      setError(err.message);
      return null;
    }
  }, [headers]);

  return { loading, error, getOrCreateEntry, setDailyData, autoSave, addToDailyData, ... };
}
```

### 7.4 Turborepo Pipeline — `turbo.json`

`build` depends on `^build` (packages built before apps). Env vars used in Next.js build are declared so Turbo can bust cache correctly.

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"],
      "env": ["NEXT_PUBLIC_API_URL", "NEXT_PUBLIC_MAPBOX_TOKEN", "NEXTAUTH_SECRET", "NEXTAUTH_URL", "DATABASE_URL", "DIRECT_URL"]
    },
    "dev":  { "cache": false, "persistent": true },
    "test": { "dependsOn": ["^build"], "cache": false }
  }
}
```

---

## 8. Dashboard Reports (Public Analytics)

### 8.1 Province Submission Progress — raw SQL — `apps/api/src/reports/dashboard-reports.service.ts`

Uses `$queryRaw` with `Prisma.raw` for the dynamic status SQL. `CAST(...AS INTEGER)` forces correct JS types from raw Postgres.

```typescript
async getSubmissionProgress(year: number): Promise<SubmissionProgressData[]> {
  const result = await this.prisma.$queryRaw<Array<{ province_id: number; province_name: string; total_clinics: number; submitted: number }>>`
    SELECT
      p.id AS province_id,
      p.name_th AS province_name,
      CAST(COUNT(DISTINCT c.id) AS INTEGER) AS total_clinics,
      CAST(COUNT(DISTINCT CASE WHEN ${Prisma.raw(VISIBLE_STATUS_SQL)} THEN c.id END) AS INTEGER) AS submitted
    FROM provinces p
    LEFT JOIN clinics c ON c.province_id = p.id AND c.deleted_at IS NULL
    LEFT JOIN submissions s ON s.clinic_id = c.id AND s.year = ${year}
    WHERE c.id IS NOT NULL
    GROUP BY p.id, p.name_th
    HAVING COUNT(DISTINCT c.id) > 0
    ORDER BY p.name_th
  `;
  return result.map((row) => ({
    provinceId: Number(row.province_id),
    provinceName: row.province_name,
    totalClinics: Number(row.total_clinics),
    submitted: Number(row.submitted),
    percentage: total > 0 ? Math.round((submitted / total) * 100) : 0,
  }));
}
```

---

## Key Architecture Notes

| Topic | Detail |
|---|---|
| Thai year storage | All `year` fields in DB and API are Buddhist Era (พ.ศ. = Gregorian + 543) |
| Date timezone | All "today" checks use `Asia/Bangkok` via `toLocaleDateString('en-CA', { timeZone: 'Asia/Bangkok' })` |
| Prisma `@db.Date` issue | Composite unique keys on `@db.Date` columns can't be used with `findUnique` in transactions — consistently worked around with `findFirst` + `create`/`update` |
| Cache invalidation | After any submission, `cacheManager.clear()` flushes the entire in-memory report cache |
| Review workflow | `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `REVISION_REQUESTED` statuses exist in schema but are bypassed; gating logic sits in `reports.utils.ts` as stubbed `getVisibleSubmissionWhere()` |
| Route groups | `(admin)`, `(auth)`, `(portal)`, `(public)` — same shared `DashboardLayout` component, different `variant` prop |
| Auth token flow | NextAuth session holds backend JWT → passed as `Authorization: Bearer` on every API call from `useDailyEntries` and `useMonthlySubmitFlow` |
