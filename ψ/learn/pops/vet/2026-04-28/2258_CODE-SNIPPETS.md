# POPs Vet — Idiomatic Code Snippets
> Curated 2026-04-28. Each snippet teaches one pattern. Read these before writing new vet code.

---

## 1. Root Layout / App Shell

**Path:** `src/app/layout.tsx`

The three global providers wired at the root: `SessionProviderWrapper` (NextAuth), `SWRProvider` (data fetching), and `PublicEnvScript` (runtime env vars via `next-runtime-env`). IBM Plex Sans Thai is loaded via `@fontsource` — never via Google CDN.

```tsx
import { SWRProvider } from '@/_assets/lib/swr-config';
import SessionProviderWrapper from '@/_components/providers/SessionProviderWrapper';
import WebVitalsReporter from '@/_components/providers/WebVitalsReporter';
import '@/_styles/globals.css';
import '@fontsource/ibm-plex-sans-thai/400.css';
import '@fontsource/ibm-plex-sans-thai/600.css';
import '@fontsource/ibm-plex-sans-thai/700.css';
import { PublicEnvScript } from 'next-runtime-env';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='en' suppressHydrationWarning>
      <head>
        <PublicEnvScript />
      </head>
      <body suppressHydrationWarning={true}>
        <WebVitalsReporter />
        <SessionProviderWrapper>
          <SWRProvider>{children}</SWRProvider>
        </SessionProviderWrapper>
      </body>
    </html>
  );
}
```

**SWR global config** (`src/app/_assets/lib/swr-config.tsx`) — no focus-revalidation, retry only on 5xx:

```tsx
const swrConfig: SWRConfiguration = {
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  dedupingInterval: 2000,
  shouldRetryOnError: (error) => {
    if (error?.response?.status >= 400 && error?.response?.status < 500) return false;
    return true;
  },
  errorRetryCount: 3,
  errorRetryInterval: 5000,
};
```

---

## 2. A Representative Page Route

**Path:** `src/app/(routes)/queue/page.tsx`

Pages are thin shells — they `dynamic`-import the actual `_pages/` component with a loading fallback. This keeps the route file minimal and defers the heavy component bundle.

```tsx
import dynamic from 'next/dynamic';
import Loading from '@/_components/shared/Loading';

const Queue = dynamic(() => import('@/_pages/Queue'), {
  loading: () => <Loading />,
});

export default function QueuePage() {
  return <Queue />;
}
```

**Pattern to follow:** Route files in `(routes)/` are always this shape — one `dynamic()` import pointing into `_pages/`. All logic lives in `_pages/`, not in the route file.

---

## 3. Auth Flow

### 3a. Middleware — route guard + RBAC gate

**Path:** `src/middleware.ts`

Reads the NextAuth JWT, guards all non-public routes, and enforces admin-only access to `/setting/admin` based on `token.role`.

```ts
import { getToken } from 'next-auth/jwt';
import { NextRequest, NextResponse } from 'next/server';

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (pathname.startsWith('/api')) return NextResponse.next();

  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });

  // Guard: /activate requires ?token=
  if (pathname === '/activate' && !req.nextUrl.searchParams.get('token')?.trim()) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  const publicPages = ['/login', '/activate'];
  const isPublicPage = publicPages.includes(pathname);

  // Unauthenticated → login
  if (!isPublicPage && !token) {
    const to = new URL('/login', req.url);
    to.searchParams.set('callbackUrl', req.nextUrl.pathname + req.nextUrl.search);
    return NextResponse.redirect(to);
  }

  // RBAC: settings pages are admin-only
  if (token && pathname.startsWith('/setting/admin')) {
    const role = (token as Record<string, unknown>).role as string | undefined;
    const adminRoles = ['clinic-owner', 'admin', 'OWNER', 'ADMIN'];
    if (!role || !adminRoles.includes(role)) {
      return NextResponse.redirect(new URL('/dashboard', req.url));
    }
  }

  // Logged-in users trying to access login → dashboard
  if (token && isPublicPage) {
    if (pathname === '/login' && !req.cookies.get('selected_tenant')?.value) {
      return NextResponse.next(); // allow: still in OAuth tenant selection
    }
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|images).*)'],
};
```

### 3b. SessionGuard — refresh token error handler

**Path:** `src/app/_components/providers/SessionProviderWrapper.tsx`

Watches `session.error` for `RefreshAccessTokenError` and clears all cookies before calling `signOut`. Runs client-side so it can react to any session invalidation from the JWT callback.

```tsx
'use client';

function SessionGuard({ children }: { children: ReactNode }) {
  const { data: session } = useSession();

  useEffect(() => {
    if (session?.error === 'RefreshAccessTokenError') {
      clearGraphQLTokenCache();
      Cookies.remove('access_token', { path: '/' });
      Cookies.remove('selected_tenant', { path: '/' });
      Cookies.remove('selected_branch', { path: '/' });
      Cookies.remove('tenant_access_token', { path: '/' });
      signOut({ redirect: true, callbackUrl: '/login' });
    }
  }, [session?.error]);

  return <>{children}</>;
}
```

### 3c. Token refresh + tenant re-scope (authOptions)

**Path:** `src/app/api/auth/authOptions.ts`

The JWT callback auto-refreshes the access token and re-scopes it to the previously selected tenant/branch. Key invariant: the backend's `UserRefreshToken` mutation returns a non-tenant-scoped token, so `refreshAndRescope` must call `UserSelectTenant` again after refresh.

```ts
// Access token expired → silent refresh + re-scope
async function refreshAndRescope(token: JWT): Promise<JWT> {
  const refreshed = await revalidateToken(token.refreshToken ?? '');
  if (!refreshed?.access_token) {
    return { ...token, error: 'RefreshAccessTokenError' };
  }

  let accessToken = refreshed.access_token;

  // Re-scope to tenant if previously selected
  if (token.tenantCode) {
    const t = await selectTenant(token.tenantCode, accessToken);
    accessToken = t.access_token;
  }

  // Re-scope to branch if previously selected (best-effort)
  if (token.branchId) {
    try {
      const b = await selectBranch(token.branchId, accessToken);
      accessToken = b.access_token;
    } catch { /* non-fatal — tenant token still usable */ }
  }

  const payload = decodeJwtPayload(accessToken);
  return {
    ...token,
    accessToken,
    refreshToken: refreshed.refresh_token ?? token.refreshToken,
    role: (payload?.role as string) ?? token.role,
    error: undefined,
  };
}

// In jwt callback:
if (!isTokenExpired(token.accessToken)) return token; // still valid
if (token.refreshToken) return refreshAndRescope(token);
return { ...token, error: 'RefreshAccessTokenError' };
```

---

## 4. Data Fetching

### 4a. GraphQL client initialisation

**Path:** `src/app/_utils/initGraphQL/initGraphQLClient.ts`

`initGraphQLClient()` is the single entry point for all GraphQL calls. It reads the auth token from the NextAuth session (not from cookies) and caches it for 30 s on the client side. Call it at the top of every fetcher function.

```ts
export const initGraphQLClient = async (requireAuth = true): Promise<GraphQLClient> => {
  const client = graphQLClientManager.getClient();
  if (!requireAuth) return client;

  // Client-side: cache token for 30 s to avoid a session() call per request
  const now = Date.now();
  if (!cachedToken || now - tokenCachedAt > TOKEN_TTL_MS) {
    cachedToken = await readSessionToken(); // reads session.tenantAccessToken ?? session.accessToken
    tokenCachedAt = now;
  }

  if (cachedToken) graphQLClientManager.setAuthToken(cachedToken);
  return client;
};

// After login / logout / tenant switch — invalidate immediately:
export const clearGraphQLTokenCache = () => {
  cachedToken = null;
  tokenCachedAt = 0;
};
```

### 4b. SWR data hook — typed GraphQL query

**Path:** `src/app/_utils/hook/pet.ts`

SWR hook wrapping a typed GraphQL operation. The SWR key is `[CONSTANT_STRING, input]` so cache invalidation by prefix is easy via `mutate((key) => Array.isArray(key) && key[0] === PET_LIST_KEY)`.

```ts
export const PET_LIST_KEY = 'pet-list';

export function usePetList(input?: PetListInput) {
  const { data = [], isLoading, error, mutate } = useSWR<PetListItem[]>(
    [PET_LIST_KEY, input],
    async ([, inp]) => {
      const client = await initGraphQLClient();
      const response = await client.request<{ PetList: PetListItem[] }>(
        GraphQLOperations.pets.queries.GET_PET_LISTS,
        { input: inp ?? { page: 1, limit: 20 } },
      );
      return response.PetList ?? [];
    },
  );

  const refetch = useCallback(() => mutate(), [mutate]);

  // Use a ref so searchPets has a stable identity — avoids re-triggering effects
  const dataRef = useRef(data);
  dataRef.current = data;

  const searchPets = useCallback((query: string): PetListItem[] => {
    if (!query) return dataRef.current;
    const q = query.toLowerCase();
    return dataRef.current.filter(({ pet, primary_owner }) =>
      pet.name_th?.toLowerCase().includes(q) ||
      pet.hn_no?.toLowerCase().includes(q) ||
      primary_owner?.first_name?.toLowerCase().includes(q),
    );
  }, []);

  return { data, isLoading, error, refetch, searchPets, count: data.length };
}
```

### 4c. GraphQL mutation function

**Path:** `src/app/_utils/hook/pet.ts`

Mutations are plain `async` functions (not hooks). They call `initGraphQLClient()`, handle errors with `console.warn`, and accept an optional `onSuccess` callback so callers can trigger SWR revalidation after success.

```ts
export async function updatePet(
  id: string,
  input: PetUpdateInput,
  onSuccess?: () => void,
): Promise<PetUpdateOutput | null> {
  try {
    const client = await initGraphQLClient();
    const response = await client.request<{ PetUpdate: PetUpdateOutput }>(
      GraphQLOperations.pets.mutations.UPDATE_PET,
      { id, input },
    );
    if (response.PetUpdate) onSuccess?.();
    return response.PetUpdate ?? null;
  } catch (err: unknown) {
    console.warn('[pet] PetUpdate:', (err as Error).message);
    return null;
  }
}
```

### 4d. GraphQL operations registry

**Path:** `src/app/_assets/lib/graphql-operations.ts`

All GQL documents live in one file grouped by domain. Always import from `GraphQLOperations` — never write inline `gql` strings in hooks.

```ts
// Query example
export const PET_QUERIES = {
  GET_PET_LISTS: gql`
    query PetList($input: PetListInput) {
      PetList(input: $input) {
        pet { id  hn_no  name_th  species  breed  avatar_url  status }
        primary_owner { id  first_name  last_name  phone }
      }
    }
  `,
} as const;

// Mutation example
export const PET_MUTATIONS = {
  UPDATE_PET: gql`
    mutation PetUpdate($id: ID!, $input: PetUpdateInput!) {
      PetUpdate(id: $id, input: $input) {
        id  hn_no  name_th  species  breed  weight  status
      }
    }
  `,
} as const;

// Central singleton — import this everywhere
export const GraphQLOperations = {
  pets: { queries: PET_QUERIES, mutations: PET_MUTATIONS },
  owners: { queries: OWNER_QUERIES, mutations: OWNER_MUTATIONS },
  queues: { queries: QUEUE_QUERIES, mutations: QUEUE_MUTATIONS },
  // ...
} as const;
```

---

## 5. RBAC / Permissions

### 5a. Permission computation

**Path:** `src/app/_utils/rbac/computeEffectivePermissions.ts`

Permissions are computed from a `Role` (base) plus per-user `UserSeat` overrides (grants/revokes). The `can()` helper is what components call.

```ts
// Merge role permissions with per-user grants and revokes
export function computeEffective(role: Role | undefined, seat?: UserSeat): Permission[] {
  const map = new Map<FeatureKey, Set<CrudAction>>();
  role?.permissions.forEach((p) => map.set(p.feature, new Set(p.actions)));

  seat?.grants.forEach((g) => {
    const set = map.get(g.feature) ?? new Set<CrudAction>();
    g.actions.forEach((a) => set.add(a));
    map.set(g.feature, set);
  });

  seat?.revokes.forEach((r) => {
    const set = map.get(r.feature);
    if (!set) return;
    r.actions.forEach((a) => set.delete(a));
    if (set.size === 0) map.delete(r.feature);
  });

  return [...map.entries()].map(([feature, actions]) => ({ feature, actions: [...actions] }));
}

// Single permission check — use this in components
export function can(perms: Permission[], action: CrudAction, feature: FeatureKey): boolean {
  return perms.find((p) => p.feature === feature)?.actions.includes(action) ?? false;
}
```

### 5b. RBAC hook — combine roles

**Path:** `src/app/_utils/hook/useRbac.ts`

`combineRoles` unions permissions from 2+ roles into a new Custom Role. Permissions snapshot at creation time; the `derivedFrom` field records which roles were combined and when.

```ts
const combineRoles = useCallback(
  (sourceRoleIds: string[], input: { name: string; description?: string }): Role | null => {
    if (sourceRoleIds.length < 2) return null;
    const sources = sourceRoleIds
      .map((id) => roles.find((r) => r.id === id))
      .filter((r): r is Role => Boolean(r));

    const ts = Date.now();
    const combined: Role = {
      id: `role_custom_${ts}`,
      key: `combined_${ts}`,
      name: input.name.trim(),
      description: input.description?.trim() || `ผสมจาก ${sources.map((s) => s.name).join(' + ')}`,
      isSystem: false,
      permissions: unionPermissions(sources),       // set-union of all role permissions
      derivedFrom: {
        sourceRoleKeys: sources.map((s) => s.key),
        snapshotAt: new Date(ts).toISOString(),
      },
    };

    setRoles((prev) => { const next = [...prev, combined]; saveRoles(next); return next; });
    return combined;
  },
  [roles],
);
```

### 5c. Middleware RBAC gate (route-level)

**Path:** `src/middleware.ts` (see Section 3a above for full code)

For coarse-grained page-level guards, check `token.role` in middleware — no hook required:

```ts
if (token && pathname.startsWith('/setting/admin')) {
  const role = (token as Record<string, unknown>).role as string | undefined;
  const adminRoles = ['clinic-owner', 'admin', 'OWNER', 'ADMIN'];
  if (!role || !adminRoles.includes(role)) {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }
}
```

---

## 6. Form Handling

**Path:** `src/app/_components/owner-pet/EditPetModal.tsx`

Zod schema + `react-hook-form` + `zodResolver`. Schema is defined at module level (not inside the component). SWR cache is invalidated with wildcard `mutate()` after a successful save.

```tsx
// --- Schema (module level) ---
const petSchema = z.object({
  hn: z.string().min(1, 'กรุณากรอกรหัส HN'),
  status: z.string().min(1, 'กรุณาเลือกสถานะ'),
  petNameThai: z.string().min(1, 'กรุณากรอกชื่อสัตว์เลี้ยง'),
  petType: z.enum(['cat', 'dog', 'other']),
  gender: z.enum(['MALE', 'FEMALE', 'unspecified']),
  weight: z.string().optional().refine(
    val => !val || (!isNaN(Number(val)) && Number(val) >= 0),
    'น้ำหนักต้องเป็นตัวเลขที่ไม่ติดลบ',
  ),
  temperament: z.array(z.string()).default([]),
  details: z.string().max(100, 'รายละเอียดต้องไม่เกิน 100 ตัวอักษร').optional(),
});

type PetFormData = z.infer<typeof petSchema>;

// --- Component ---
const EditPetModal = ({ openModal, onOpenChange, onClose, petId }: EditPetModalProps) => {
  const { mutate } = useSWRConfig();
  const { data: pet } = usePetGetById(petId ?? null);

  const { register, handleSubmit, formState: { errors }, setValue, watch, reset } =
    useForm<PetFormData>({
      resolver: zodResolver(petSchema) as Resolver<PetFormData>,
      defaultValues: { hn: '', status: 'ACTIVE', petType: 'other', /* ... */ },
    });

  // Populate form when remote data loads
  useEffect(() => {
    if (!pet) return;
    reset({ hn: pet.hn_no ?? '', petNameThai: pet.name_th ?? '', /* ... */ });
  }, [pet, reset]);

  const onSubmit = async (data: PetFormData) => {
    const result = await updatePet(petId!, { name_th: data.petNameThai, /* ... */ });
    if (result) {
      toast.success('บันทึกข้อมูลสำเร็จ');
      // Wildcard invalidation: revalidate all keys that start with PET_LIST_KEY
      mutate((key: unknown) => Array.isArray(key) && key[0] === PET_LIST_KEY);
      mutate(PET_SUMMARY_KEY);
      onClose();
    } else {
      toast.error('บันทึกข้อมูลไม่สำเร็จ กรุณาลองอีกครั้ง');
    }
  };

  return (
    <Modals open={openModal} onOpenChange={onOpenChange} onClose={onClose} disableFooter>
      <form onSubmit={handleSubmit(onSubmit)} className='flex flex-col h-full'>
        {/* ... field components receive register, watch, setValue, errors ... */}
        <div className='flex justify-end gap-3 border-t p-4'>
          <Button type='button' variant='ghost' onClick={onClose}>ยกเลิก</Button>
          <Button type='submit'>บันทึกข้อมูล</Button>
        </div>
      </form>
    </Modals>
  );
};
```

---

## 7. Error Handling

### 7a. Route-level error boundary

**Path:** `src/app/(routes)/error.tsx`

Next.js `error.tsx` — must be `'use client'`. Provides a Thai-language reset button and a back-to-dashboard escape hatch.

```tsx
'use client';

export default function RouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <ServerCrash className="h-12 w-12 text-muted-foreground" />
      <h1 className="text-lg font-semibold">เกิดข้อผิดพลาดในระบบ</h1>
      <p className="text-sm text-muted-foreground text-center max-w-sm">
        กรุณาลองรีเฟรชหน้าจอ หากปัญหายังคงอยู่ให้ติดต่อผู้ดูแลระบบ
      </p>
      <Button onClick={() => reset()}>รีเฟรชหน้าจอ</Button>
      <Button variant="ghost" asChild>
        <Link href="/dashboard">กลับหน้าหลัก</Link>
      </Button>
    </div>
  );
}
```

### 7b. Not-found page

**Path:** `src/app/not-found.tsx`

```tsx
'use client';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <SearchX className="h-12 w-12 text-muted-foreground" />
      <h1 className="text-lg font-semibold">ไม่พบหน้าที่คุณกำลังมองหา</h1>
      <p className="text-sm text-muted-foreground text-center max-w-sm">
        หน้าที่คุณต้องการอาจถูกย้าย ลบ หรือ URL ไม่ถูกต้อง
      </p>
      <Button asChild>
        <Link href="/dashboard">กลับหน้าหลัก</Link>
      </Button>
    </div>
  );
}
```

### 7c. API error pattern

Backend error strings are mapped to Thai user messages in the hook layer — the component never sees raw backend errors. Pattern from `useLogin.ts`:

```ts
function mapLoginError(rawError: string): string {
  const lower = rawError.toLowerCase();
  if (lower.includes('invalid credentials') || lower.includes('not found')) {
    return 'อีเมลหรือรหัสผ่านไม่ถูกต้อง'; // D-07: never reveal whether email exists
  }
  if (lower.includes('rate limit') || lower.includes('throttler')) {
    return 'คุณลองเข้าสู่ระบบบ่อยเกินไป กรุณารอสักครู่';
  }
  // ...
  return 'อีเมลหรือรหัสผ่านไม่ถูกต้อง'; // generic fallback — never expose raw error
}
```

---

## 8. Reusable Component — Modals

**Path:** `src/app/_components/shared/Modals.tsx`

The project's universal modal/drawer primitive. On mobile (≤480 px) and tablet (≤1024 px) it renders a bottom `Drawer`; on desktop it renders a centred `Dialog`. Controlled via `open` / `onOpenChange`. Callers can opt out of the built-in footer with `disableFooter` and supply their own via `footerContentCustom`.

```tsx
interface ModalsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onClose: (open: boolean) => void;
  onNextAction?: () => void;
  nextActionTitle?: string;
  children: React.ReactNode;
  title?: string;
  description?: string;
  descriptionContentCustom?: React.ReactNode;
  footerContentCustom?: React.ReactNode;
  className?: string;
  disableFooter?: boolean;
  disableOutsideClick?: boolean;
  hideCloseButton?: boolean;
  notUseDrawer?: boolean;        // force Dialog even on narrow screens
  variant?: 'default' | 'outline' | 'destructive' | 'secondary' | 'ghost' | 'link';
  disabled?: boolean;
  isNextActionDisabled?: boolean;
}

// Usage example (from EditPetModal):
<Modals
  open={openModal}
  onOpenChange={onOpenChange}
  onClose={onClose}
  className='h-[700px] w-[1000px] p-0 overflow-hidden'
  disableFooter          // supply a custom footer inside <form>
>
  <form onSubmit={handleSubmit(onSubmit)}>
    {/* ... */}
    <div className='flex justify-end gap-3 p-4 border-t'>
      <Button type='button' variant='ghost' onClick={onClose}>ยกเลิก</Button>
      <Button type='submit'>บันทึกข้อมูล</Button>
    </div>
  </form>
</Modals>
```

---

## 9. Tests

### 9a. Unit test (Vitest)

**Path:** `src/__tests__/unit/hooks/useLogin.test.ts`

Tests the `useLogin` hook by mocking `next-auth/react` at the module boundary with `vi.hoisted()`. Uses `renderHook` + `act` + fake timers to drive async state transitions without `waitFor`.

```ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Hoist mocks so they are available before module imports resolve
const { mockSignIn, mockGetSession } = vi.hoisted(() => ({
  mockSignIn: vi.fn(),
  mockGetSession: vi.fn(),
}));

vi.mock('next-auth/react', () => ({
  signIn: mockSignIn,
  getSession: mockGetSession,
  useSession: vi.fn(),
}));

import useLogin from '@/_utils/hook/useLogin';

describe('useLogin — success path', () => {
  beforeEach(() => { vi.useFakeTimers(); mockSignIn.mockReset(); mockGetSession.mockReset(); });
  afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });

  it('returns { access_token, tenants } on success', async () => {
    mockSignIn.mockResolvedValue({ error: null });
    mockGetSession.mockResolvedValue({
      accessToken: 'access-abc',
      tenants: [{ tenant_code: 'CLINIC01', display_name: 'คลินิก A', role: 'admin' }],
    });

    const { result } = renderHook(() => useLogin());

    let response: Awaited<ReturnType<typeof result.current.login>>;
    await act(async () => {
      response = await result.current.login({ email: 'vet@clinic.com', password: 'secret' });
      await vi.runAllTimersAsync();
    });

    expect(response!.access_token).toBe('access-abc');
  });

  it('maps "invalid credentials" to Thai error message', async () => {
    mockSignIn.mockResolvedValue({ error: 'Invalid credentials' });
    mockGetSession.mockResolvedValue(null);

    const { result } = renderHook(() => useLogin());
    await act(async () => {
      await result.current.login({ email: 'a@b.com', password: 'pw' }).catch(() => {});
      await vi.runAllTimersAsync();
    });

    expect(result.current.error).toBe('อีเมลหรือรหัสผ่านไม่ถูกต้อง');
  });
});
```

### 9b. E2E test (Playwright)

**Path:** `tests/e2e/auth.spec.ts`

Smoke tests for login UI — no backend required. Tests are organised with `test.describe` + `test.beforeEach(goto)`. Thai UI strings are used directly as selectors — that is intentional and acts as a regression guard on copy changes.

```ts
import { test, expect } from '@playwright/test';

test.describe('Login Page — UI (smoke)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('submit button is disabled on empty form', async ({ page }) => {
    const submitBtn = page.getByRole('button', { name: /เข้าสู่ระบบด้วยอีเมล/ });
    await expect(submitBtn).toBeDisabled();
  });

  test('shows invalid email format error', async ({ page }) => {
    const emailInput = page.getByPlaceholder('กรอกอีเมลของคุณ');
    await emailInput.fill('notatvalidemail');
    await emailInput.blur();
    await expect(page.getByText('รูปแบบอีเมลไม่ถูกต้อง')).toBeVisible();
  });

  test('submit button enables when both fields are validly filled', async ({ page }) => {
    await page.getByPlaceholder('กรอกอีเมลของคุณ').fill('user@example.com');
    await page.getByPlaceholder('รหัสผ่านของคุณ').fill('password123');
    await expect(page.getByRole('button', { name: /เข้าสู่ระบบด้วยอีเมล/ })).toBeEnabled();
  });

  test('forgot password link opens modal', async ({ page }) => {
    await page.getByRole('button', { name: 'ลืมรหัสผ่าน?' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
  });
});

test.describe('Login Page — URL error params', () => {
  test('?error=google_not_registered shows Thai error', async ({ page }) => {
    await page.goto('/login?error=google_not_registered');
    await expect(page.getByText('บัญชี Google นี้ยังไม่ได้ลงทะเบียนในระบบ')).toBeVisible();
  });
});
```

---

## 10. Storybook Story

**Path:** `src/app/_components/shared/OwnerInfoCard.stories.tsx`

Stories use the `Meta` / `StoryObj` pattern. Each export is a named `Story` object with `args`. Stories cover: full data, minimal data (graceful empty states), and edge cases like missing avatar. JSDoc comments above each story appear in the Storybook UI as the story description.

```tsx
import type { Meta, StoryObj } from '@storybook/react';
import OwnerInfoCard from '@/_components/shared/OwnerInfoCard';

const meta: Meta<typeof OwnerInfoCard> = {
  title: 'Shared/OwnerInfoCard',
  component: OwnerInfoCard,
  parameters: { layout: 'centered' },
};

export default meta;
type Story = StoryObj<typeof OwnerInfoCard>;

const fullOwner = {
  id: 'owner-001',
  first_name: 'สมชาย',
  last_name: 'ใจดี',
  phone: '081-234-5678',
  avatar_url: 'https://i.pravatar.cc/150?img=3',
};

/** แสดงข้อมูลเจ้าของครบทุกฟิลด์ */
export const Default: Story = {
  args: { owner: fullOwner },
};

/** ข้อมูลขั้นต่ำ — ฟิลด์ที่เหลือแสดงค่า "ไม่ระบุ" */
export const MinimalData: Story = {
  args: {
    owner: { first_name: 'มานี', last_name: 'มีทอง', phone: '', avatar_url: null },
  },
};

/** แสดง badge ข้าง HN */
export const WithBadge: Story = {
  args: { owner: fullOwner, badgeText: 'HN001' },
};

/** ไม่มี avatar_url — component ใช้รูป fallback */
export const NoAvatar: Story = {
  args: { owner: { ...fullOwner, avatar_url: null }, avatarIndex: 2 },
};
```

---

## Quick Reference — Key Patterns

| Pattern | Where to look |
|---|---|
| Route file shape | `src/app/(routes)/queue/page.tsx` |
| Global providers | `src/app/layout.tsx` |
| Auth token refresh | `src/app/api/auth/authOptions.ts` → `refreshAndRescope()` |
| GraphQL call | `initGraphQLClient()` → `client.request<T>(OPERATION, vars)` |
| SWR hook key | `[DOMAIN_CONSTANT, input]` — enables wildcard invalidation |
| SWR mutation | Plain `async function`, not a hook. Call `mutate()` on success |
| Form schema | Zod at module level; `z.infer<typeof schema>` for the type |
| SWR cache invalidation | `mutate((key) => Array.isArray(key) && key[0] === DOMAIN_KEY)` |
| Permission check | `can(computeEffective(role, seat), 'read', 'pet_profile')` |
| Modal/Drawer | `<Modals>` — auto-switches to Drawer on ≤1024 px |
| Error pages | `error.tsx` (route-level), `not-found.tsx` (root), always `'use client'` |
| Unit test mock | `vi.hoisted()` + `vi.mock()` before imports |
| E2E test | `test.describe` + `test.beforeEach(goto)`, Thai strings as selectors |
| Story file | `Meta<typeof Comp>` + named `StoryObj` exports with JSDoc descriptions |
