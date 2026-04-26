# Pawrent Codebase - Code Snippets Reference

**Project:** Pawrent - Pet Passport & Safety Dashboard  
**Type:** Next.js 16 React 19 TypeScript + Supabase + LINE LIFF  
**Recorded:** 2026-04-26  

---

## 1. Main Entry Point & Root Layout

### Root Layout with Providers (app/layout.tsx)

The root layout sets up the entire app with Thai font, multiple context providers, and responsive viewport settings. It establishes the provider hierarchy that wraps all child routes.

```typescript
import type { Metadata, Viewport } from "next";
import { Noto_Sans_Thai } from "next/font/google";
import { LiffProvider } from "@/components/liff-provider";
import { LocationProvider } from "@/components/location-provider";
import { NavigationShell } from "@/components/navigation-shell";
import { ToastProvider } from "@/components/ui/toast";
import { DebugConsole } from "@/components/debug-console";
import "./globals.css";

const notoSansThai = Noto_Sans_Thai({
  variable: "--font-noto-sans-thai",
  subsets: ["thai", "latin"],
  weight: ["400", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Pawrent | Pet OS Dashboard",
  description: "Your all-in-one Pet Passport & Safety Dashboard",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#FF8263",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th">
      <body className={`${notoSansThai.variable} font-sans antialiased`}>
        <DebugConsole />
        <ToastProvider>
          <LiffProvider>
            <LocationProvider>
              <NavigationShell>{children}</NavigationShell>
            </LocationProvider>
          </LiffProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
```

**Key Patterns:**
- Thai font loaded via `next/font/google` with display="swap"
- Nested providers for authentication (LIFF), location, toast notifications
- Viewport locked for mobile app experience (no zoom)
- Theme color set to match app branding

---

## 2. Core Authentication & Context Management

### LIFF Provider with LINE Authentication (components/liff-provider.tsx)

Manages LINE LIFF initialization and exchanges LINE ID tokens for Supabase JWT tokens. Uses React Context to provide user authentication state across the app.

```typescript
"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { initializeLiff, getLiffIdToken, isInLiffBrowser, liffLogin, liffLogout } from "@/lib/liff";
import { setAuthToken } from "@/lib/auth-token";
import type { Profile } from "@/lib/types/common";

interface AuthContextType {
  user: Profile | null;
  loading: boolean;
  isInLiff: boolean;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function LiffProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isInLiff, setIsInLiff] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        await initializeLiff();
        if (cancelled) return;

        const inLiff = isInLiffBrowser();
        setIsInLiff(inLiff);

        const idToken = getLiffIdToken();
        if (!idToken) {
          // In external browser, redirect to LINE Login
          if (!inLiff) {
            liffLogin();
          }
          setLoading(false);
          return;
        }

        // Exchange LINE ID token for Supabase JWT
        const res = await fetch("/api/auth/line", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idToken }),
        });

        if (!res.ok) {
          setLoading(false);
          return;
        }

        const data = await res.json();
        if (cancelled) return;

        setAuthToken(data.access_token);
        setUser(data.user);
      } catch {
        // LIFF init or auth exchange failed
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, []);

  const signOut = useCallback(() => {
    liffLogout();
    setAuthToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, isInLiff, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within a LiffProvider");
  }
  return context;
}
```

**Key Patterns:**
- Cleanup function prevents state updates after unmount
- Deferred loading state management
- Context-based provider pattern for global auth state
- Token exchange happens client-side after LIFF init

---

## 3. Location Management with Geolocation API

### Location Provider (components/location-provider.tsx)

Manages browser geolocation with fallback to Bangkok default and comprehensive error handling. Caches location for 5 minutes.

```typescript
"use client";

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";

interface LocationContextType {
  location: { lat: number; lng: number } | null;
  loading: boolean;
  error: string | null;
  requestLocation: () => void;
}

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export function LocationProvider({ children }: { children: ReactNode }) {
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        });
        setLoading(false);
      },
      (err) => {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setError("Location access denied. Some features may be limited.");
            break;
          case err.POSITION_UNAVAILABLE:
            setError("Location information unavailable.");
            break;
          case err.TIMEOUT:
            setError("Location request timed out.");
            break;
          default:
            setError("An unknown error occurred.");
        }
        // Set a default location (Bangkok) when permission denied
        setLocation({ lat: 13.7563, lng: 100.5018 });
        setLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000, // 5 minutes cache
      }
    );
  }, []);

  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  return (
    <LocationContext.Provider value={{ location, loading, error, requestLocation }}>
      {children}
    </LocationContext.Provider>
  );
}

export function useLocation() {
  const context = useContext(LocationContext);
  if (context === undefined) {
    throw new Error("useLocation must be used within a LocationProvider");
  }
  return context;
}
```

**Key Patterns:**
- Browser API integration with graceful degradation
- Specific error handling for each geolocation error type
- Fallback location (Bangkok) for denied permissions
- Cache strategy (5 minutes) to reduce location requests

---

## 4. Database Operations Layer

### Core Supabase Operations (lib/db.ts)

Comprehensive data layer with typed operations for pets, vaccinations, health events, and reports. Uses Supabase client with proper error handling.

```typescript
import { supabase } from "./supabase";
import type {
  Pet,
  Vaccination,
  ParasiteLog,
  HealthEvent,
  PetReport,
  Profile,
  Feedback,
  PetPhoto,
} from "./types";

// Profile Operations
export async function getProfile(userId: string) {
  const { data, error } = await supabase.from("profiles").select("*").eq("id", userId).single();
  return { data: data as Profile | null, error };
}

export async function upsertProfile(profile: Partial<Profile> & { id: string }) {
  const { data, error } = await supabase.from("profiles").upsert(profile).select().single();
  return { data: data as Profile | null, error };
}

// Pet Operations
export async function getPets(ownerId: string) {
  const { data, error } = await supabase
    .from("pets")
    .select("*")
    .eq("owner_id", ownerId)
    .order("created_at", { ascending: false });
  if (error) {
    console.error("[getPets] error:", error.message, error.code);
  }
  console.log("[getPets] ownerId:", ownerId, "results:", data?.length ?? 0);
  return { data: data as Pet[] | null, error };
}

export async function getPetWithDetails(petId: string) {
  const { data: pet, error: petError } = await supabase
    .from("pets")
    .select("*")
    .eq("id", petId)
    .single();

  if (petError) return { data: null, error: petError };

  const [vaccinations, parasiteLogs, healthEvents] = await Promise.all([
    supabase.from("vaccinations").select("*").eq("pet_id", petId),
    supabase
      .from("parasite_logs")
      .select("*")
      .eq("pet_id", petId)
      .order("created_at", { ascending: false })
      .limit(1),
    supabase
      .from("health_events")
      .select("*")
      .eq("pet_id", petId)
      .order("event_date", { ascending: false }),
  ]);

  return {
    data: {
      pet: pet as Pet,
      vaccinations: vaccinations.data as Vaccination[],
      latestParasiteLog: parasiteLogs.data?.[0] as ParasiteLog | undefined,
      healthEvents: healthEvents.data as HealthEvent[],
    },
    error: null,
  };
}

// Haversine Distance Calculation
export function calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371; // Earth's radius in km
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function toRad(deg: number): number {
  return deg * (Math.PI / 180);
}
```

**Key Patterns:**
- Consistent error-first return pattern `{ data, error }`
- Parallel data fetching with `Promise.all()` for related data
- Haversine formula for geographic distance calculations
- Structured logging with context-specific prefixes

---

## 5. API Route Handlers with Authentication & Rate Limiting

### Pet Reports API (app/api/post/route.ts)

RESTful handler for creating and querying pet reports with rate limiting, data denormalization, and Supabase RPC integration.

```typescript
import { createApiClient } from "@/lib/supabase-api";
import { lostPetAlertSchema, resolveReportSchema, resolveAlertSchema } from "@/lib/validations";
import { createRateLimiter, checkRateLimit } from "@/lib/rate-limit";
import { encodeCursor, decodeCursor } from "@/lib/pagination";
import { NextRequest, NextResponse } from "next/server";

const postLimiter = createRateLimiter(3, "24 h");
const putLimiter = createRateLimiter(10, "1 m");

export async function POST(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const supabase = createApiClient(authHeader);
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Invalid token" }, { status: 401 });

  const rateLimited = await checkRateLimit(postLimiter, user.id);
  if (rateLimited) return rateLimited;

  const body = await request.json();
  const result = lostPetAlertSchema.safeParse(body);
  if (!result.success) {
    return NextResponse.json({ error: result.error.issues[0].message }, { status: 400 });
  }

  // Auto-snapshot pet data from pets table
  const { data: pet, error: petError } = await supabase
    .from("pets")
    .select("name, species, breed, color, sex, date_of_birth, neutered, microchip_number")
    .eq("id", result.data.pet_id)
    .eq("owner_id", user.id)
    .single();

  if (petError || !pet) {
    return NextResponse.json({ error: "Pet not found" }, { status: 404 });
  }

  // Fetch pet photos from pet_photos table
  const { data: petPhotos } = await supabase
    .from("pet_photos")
    .select("photo_url")
    .eq("pet_id", result.data.pet_id)
    .order("display_order", { ascending: true });

  const profilePhotoUrls = (petPhotos ?? []).map((p) => p.photo_url);
  // Merge profile photos with user-submitted photos (dedup)
  const allPhotoUrls = [...new Set([...profilePhotoUrls, ...result.data.photo_urls])].slice(0, 5);

  const { data, error } = await supabase
    .from("pet_reports")
    .insert({
      pet_id: result.data.pet_id,
      owner_id: user.id,
      alert_type: "lost" as const,
      status: "active" as const,
      is_active: true,
      lat: result.data.lat,
      lng: result.data.lng,
      lost_date: result.data.lost_date,
      lost_time: result.data.lost_time ?? null,
      location_description: result.data.location_description ?? null,
      description: result.data.description ?? null,
      distinguishing_marks: result.data.distinguishing_marks ?? null,
      photo_urls: allPhotoUrls,
      reward_amount: result.data.reward_amount,
      reward_note: result.data.reward_note ?? null,
      contact_phone: result.data.contact_phone ?? null,
      // Denormalized pet snapshot
      pet_name: pet.name,
      pet_species: pet.species,
      pet_breed: pet.breed,
      pet_color: pet.color,
      pet_sex: pet.sex,
      pet_date_of_birth: pet.date_of_birth,
      pet_neutered: pet.neutered,
      pet_microchip: pet.microchip_number,
      pet_photo_url: profilePhotoUrls[0] ?? null,
      video_url: null,
    })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

export async function GET(request: NextRequest) {
  const authHeader = request.headers.get("authorization");
  if (!authHeader) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const supabase = createApiClient(authHeader);
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Invalid token" }, { status: 401 });

  const { searchParams } = new URL(request.url);

  // List via nearby_reports() RPC
  const alertType = searchParams.get("alert_type") ?? undefined;
  const species = searchParams.get("species") ?? undefined;
  const latParam = searchParams.get("lat");
  const lngParam = searchParams.get("lng");
  const radiusParam = searchParams.get("radius");
  const cursorParam = searchParams.get("cursor") ?? undefined;
  const limitParam = searchParams.get("limit");

  const lat = latParam ? parseFloat(latParam) : null;
  const lng = lngParam ? parseFloat(lngParam) : null;
  const radiusM = radiusParam ? parseFloat(radiusParam) : 1000;
  const limit = limitParam ? Math.min(parseInt(limitParam, 10), 50) : 20;

  if (lat !== null && lng !== null) {
    // Use nearby_reports() RPC for geo-sorted results
    const { data: rpcData, error: rpcError } = await supabase.rpc("nearby_reports", {
      p_lat: lat,
      p_lng: lng,
      p_radius_m: radiusM,
      p_limit: limit + 1,
    });

    if (rpcError) {
      return NextResponse.json({ error: rpcError.message }, { status: 500 });
    }

    let results = rpcData ?? [];

    // Filter by alert_type if specified
    if (alertType) {
      results = results.filter((r: Record<string, unknown>) => r.alert_type === alertType);
    }
    // Filter by species if specified
    if (species) {
      results = results.filter(
        (r: Record<string, unknown>) =>
          (r.pet_species as string)?.toLowerCase() === species.toLowerCase()
      );
    }

    const hasMore = results.length > limit;
    if (hasMore) results = results.slice(0, limit);

    const nextCursor =
      hasMore && results.length > 0
        ? encodeCursor(
            (results[results.length - 1] as Record<string, string>).created_at,
            (results[results.length - 1] as Record<string, string>).id
          )
        : null;

    return NextResponse.json({ data: results, cursor: nextCursor, hasMore });
  }

  // Fallback: non-geo listing with cursor pagination
  let query = supabase
    .from("pet_reports")
    .select("*")
    .eq("is_active", true)
    .order("created_at", { ascending: false })
    .order("id", { ascending: false })
    .limit(limit + 1);

  if (alertType) {
    query = query.eq("alert_type", alertType);
  }
  if (species) {
    query = query.ilike("pet_species", species);
  }

  if (cursorParam) {
    const decoded = decodeCursor(cursorParam);
    if (decoded) {
      query = query.or(
        `created_at.lt.${decoded.created_at},and(created_at.eq.${decoded.created_at},id.lt.${decoded.id})`
      );
    }
  }

  const { data: listData, error: listError } = await query;

  if (listError) {
    return NextResponse.json({ error: listError.message }, { status: 500 });
  }

  const rows = listData ?? [];
  const hasMore = rows.length > limit;
  const page = hasMore ? rows.slice(0, limit) : rows;

  const nextCursor =
    hasMore && page.length > 0
      ? encodeCursor(page[page.length - 1].created_at, page[page.length - 1].id)
      : null;

  return NextResponse.json({ data: page, cursor: nextCursor, hasMore });
}
```

**Key Patterns:**
- Bearer token authentication from Authorization header
- Rate limiting per user ID (3 posts/24h, 10 updates/1m)
- Data denormalization (snapshot pet data into report record)
- Photo deduplication with Set and array slicing
- Supabase RPC integration for geo-queries
- Cursor-based pagination (not offset-based)
- Multi-branch GET: single fetch, owner filters, geo-nearby

---

## 6. Rate Limiting with Upstash Redis

### Rate Limit Module (lib/rate-limit.ts)

Sliding window rate limiting using Upstash Redis. Returns standard HTTP 429 response with Retry-After header.

```typescript
import { Ratelimit, type Duration } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";
import { NextResponse, type NextRequest } from "next/server";

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

export function createRateLimiter(requests: number, window: Duration) {
  return new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(requests, window),
  });
}

export function getClientIp(request: NextRequest): string {
  return (
    request.headers.get("x-real-ip") ??
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "127.0.0.1"
  );
}

export async function checkRateLimit(
  limiter: Ratelimit,
  identifier: string
): Promise<NextResponse | null> {
  const { success, reset } = await limiter.limit(identifier);
  if (!success) {
    const retryAfter = Math.ceil((reset - Date.now()) / 1000);
    return NextResponse.json(
      { error: "Too many requests" },
      {
        status: 429,
        headers: { "Retry-After": String(Math.max(retryAfter, 1)) },
      }
    );
  }
  return null;
}
```

**Key Patterns:**
- Reusable limiter factory for creating pre-configured limiters
- Sliding window algorithm (not fixed window)
- Returns null on success, NextResponse on failure (short-circuit in handlers)
- Proper Retry-After header calculation in seconds

---

## 7. Cursor-Based Pagination

### Pagination Helpers (lib/pagination.ts)

Base64-URL encoding of cursor state for keyset pagination. Stateless, URL-safe cursors.

```typescript
/**
 * Cursor-based pagination helpers.
 * Cursor = base64-encoded JSON { created_at, id }.
 */

interface CursorPayload {
  created_at: string;
  id: string;
}

export function encodeCursor(createdAt: string, id: string): string {
  const payload: CursorPayload = { created_at: createdAt, id };
  return Buffer.from(JSON.stringify(payload)).toString("base64url");
}

export function decodeCursor(cursor: string): CursorPayload | null {
  try {
    const json = Buffer.from(cursor, "base64url").toString("utf-8");
    const parsed = JSON.parse(json) as CursorPayload;
    if (typeof parsed.created_at === "string" && typeof parsed.id === "string") {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}
```

**Key Patterns:**
- Base64URL encoding (URL-safe, no padding)
- Keyset pagination (created_at + id) for efficient database queries
- Graceful null return on invalid cursor
- No external dependencies

---

## 8. Client-Side API Wrapper

### API Fetch with Auth (lib/api.ts)

Lightweight wrapper around fetch that injects Bearer token and ensures JSON content-type.

```typescript
import { getAuthToken } from "./auth-token";

export async function apiFetch(url: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(url, { ...options, headers });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}
```

**Key Patterns:**
- Auth token injection from localStorage
- FormData detection (avoids Content-Type header for multipart)
- Automatic JSON parsing and error throwing

---

## 9. LINE LIFF Initialization with Singleton Pattern

### LIFF Module (lib/liff.ts)

Ensures LIFF initializes only once. Exposes LINE SDK methods with graceful fallbacks.

```typescript
import liff from "@line/liff";

let initPromise: Promise<void> | null = null;

export async function initializeLiff(): Promise<void> {
  if (initPromise) return initPromise;
  initPromise = liff.init({ liffId: process.env.NEXT_PUBLIC_LIFF_ID! });
  try {
    await initPromise;
  } catch (error) {
    initPromise = null;
    throw error;
  }
}

export function getLiffProfile() {
  return liff.getProfile();
}

export function getLiffIdToken(): string | null {
  return liff.getIDToken();
}

export function isInLiffBrowser(): boolean {
  return liff.isInClient();
}

export function liffLogin(): void {
  if (!liff.isLoggedIn()) {
    liff.login();
  }
}

export function liffLogout(): void {
  liff.logout();
}

/**
 * Share content via LINE's shareTargetPicker.
 * Gracefully falls back if not in LIFF browser or feature unavailable.
 * Returns true if share was successful, false otherwise.
 */
export async function liffShareTargetPicker(
  messages: Parameters<typeof liff.shareTargetPicker>[0]
): Promise<boolean> {
  try {
    if (!liff.isInClient()) {
      return false;
    }
    if (!liff.isApiAvailable("shareTargetPicker")) {
      return false;
    }
    const result = await liff.shareTargetPicker(messages);
    // shareTargetPicker resolves with undefined when user cancels
    return result !== undefined;
  } catch {
    return false;
  }
}

/** Reset singleton state — for testing only */
export function resetLiffState(): void {
  initPromise = null;
}
```

**Key Patterns:**
- Singleton pattern with cached promise
- Feature availability check before calling API
- Boolean return values instead of throwing
- Test helper (resetLiffState)

---

## 10. Complex Dashboard State Management

### Home Dashboard Page (app/page.tsx)

Large component with multiple independent data fetches, useMemo caching, and responsive UI composition. Shows client component patterns with auth dependency.

```typescript
"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/components/liff-provider";
import { getPets } from "@/lib/db";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import { SkeletonCard, SkeletonLine } from "@/components/skeleton-card";

interface Pet {
  id: string;
  name: string;
  species: string | null;
  breed: string | null;
  photo_url: string | null;
  date_of_birth: string | null;
  vaccine_due_date?: string | null;
  parasite_due_date?: string | null;
  weight_logged_at?: string | null;
}

function HomeDashboard() {
  const { user } = useAuth();
  const [pets, setPets] = useState<Pet[]>([]);
  const [petsLoading, setPetsLoading] = useState(true);
  const [nearbyAlerts, setNearbyAlerts] = useState<NearbyAlert[]>([]);
  const [alertsLoading, setAlertsLoading] = useState(true);

  useEffect(() => {
    async function fetchPets() {
      if (!user) return;
      const { data } = await getPets(user.id);
      setPets((data || []) as Pet[]);
      setPetsLoading(false);
    }
    fetchPets();
  }, [user]);

  useEffect(() => {
    async function fetchAlerts() {
      try {
        const data = await apiFetch("/api/post?status=active&alert_type=lost&limit=3");
        setNearbyAlerts(data.alerts || data.data || []);
      } catch {
        setNearbyAlerts([]);
      } finally {
        setAlertsLoading(false);
      }
    }
    fetchAlerts();
  }, []);

  const userName =
    (user as { displayName?: string; name?: string; line_display_name?: string } | null)
      ?.displayName ||
    (user as { name?: string } | null)?.name ||
    (user as { line_display_name?: string } | null)?.line_display_name ||
    "ชาวป๊อปส์";

  return (
    <div className="min-h-screen pb-24 bg-gradient-to-b from-background to-surface-alt/40">
      <main className="max-w-md mx-auto px-4 pt-4 space-y-3">
        <GreetingHeader userName={userName} />
        <WeatherStrip />
        <PetStatusRow pets={pets} loading={petsLoading} />
        <UrgentAlertsCard pets={pets} />
        <LostPetsNearby alerts={nearbyAlerts} loading={alertsLoading} />
        <HealthReminders pets={pets} />
        <QuickActionsRow />
      </main>
    </div>
  );
}

export default function HomePage() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-full bg-pops-gradient shadow-glow flex items-center justify-center mx-auto animate-pulse">
            <span className="text-2xl" aria-hidden>
              🐾
            </span>
          </div>
          <p className="text-text-muted text-sm">กำลังเข้าสู่ระบบ…</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-full bg-pops-gradient shadow-glow flex items-center justify-center mx-auto animate-pulse">
            <span className="text-2xl" aria-hidden>
              🐾
            </span>
          </div>
          <p className="text-text-muted text-sm">กำลังเข้าสู่ระบบผ่าน LINE…</p>
        </div>
      </div>
    );
  }

  return <HomeDashboard />;
}
```

**Key Patterns:**
- Conditional rendering for auth states (loading, unauthenticated, authenticated)
- Separate loading states for independent data streams
- Dependency arrays with `user` to refetch on auth change
- Type casting for accessing optional user properties
- Two-level component structure (page wrapper → inner dashboard)

---

## 11. Memoized Business Logic with useMemo

### Urgent Alerts Calculation (app/page.tsx excerpt)

Complex derived state calculation that's only recomputed when pets or current time changes.

```typescript
function UrgentAlertsCard({ pets }: { pets: Pet[] }) {
  const [now] = useState(() => Date.now());
  const urgent = useMemo(() => {
    const list: Array<{
      id: string;
      petName: string;
      icon: "pill" | "scale";
      title: string;
      subtitle: string;
      variant: "danger" | "warning";
    }> = [];
    for (const pet of pets) {
      if (pet.parasite_due_date) {
        const due = new Date(pet.parasite_due_date).getTime();
        const diffDays = Math.floor((due - now) / 86400000);
        if (diffDays < 0) {
          list.push({
            id: `parasite-${pet.id}`,
            petName: pet.name,
            icon: "pill",
            title: `ฉีดยาป้องกันเห็บหมัดให้${pet.name}`,
            subtitle: `เลยกำหนด ${Math.abs(diffDays)} วัน`,
            variant: "danger",
          });
        }
      }
      if (pet.weight_logged_at) {
        const logged = new Date(pet.weight_logged_at).getTime();
        const diffDays = Math.floor((now - logged) / 86400000);
        if (diffDays > 30) {
          list.push({
            id: `weight-${pet.id}`,
            petName: pet.name,
            icon: "scale",
            title: `ชั่งน้ำหนัก${pet.name}`,
            subtitle: `ครบ ${diffDays} วัน — ควรบันทึกใหม่`,
            variant: "warning",
          });
        }
      }
    }
    return list;
  }, [pets, now]);

  if (urgent.length === 0) return null;

  return (
    <div className="bg-surface rounded-[24px] shadow-soft border border-border overflow-hidden">
      {urgent.slice(0, 3).map((item, i) => (
        <div key={item.id}>
          {/* item rendering */}
        </div>
      ))}
    </div>
  );
}
```

**Key Patterns:**
- Closure over `now` (single calculation at mount)
- Complex object array building in useMemo
- Conditional checks within loop
- Limiting rendered items with slice()

---

## 12. Service Worker Configuration

### Serwist PWA Setup (app/sw.ts)

Offline-first service worker with precaching, runtime caching, and offline fallback page.

```typescript
import { defaultCache } from "@serwist/next/worker";
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { Serwist } from "serwist";

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}

declare const self: WorkerGlobalScope & typeof globalThis;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: defaultCache,
  fallbacks: {
    entries: [
      {
        url: "/offline",
        matcher({ request }) {
          return request.destination === "document";
        },
      },
    ],
  },
});

serwist.addEventListeners();
```

**Key Patterns:**
- Precaching manifest injected by build
- Skip waiting + clients claim for instant updates
- Navigation preload for faster navigation
- Fallback page for offline document requests
- Type-safe global scope extension

---

## 13. Next.js Configuration with Image Optimization

### Next Config (next.config.ts)

Serwist PWA integration, Supabase image domain whitelisting, and dev origin handling.

```typescript
import withSerwistInit from "@serwist/next";
import type { NextConfig } from "next";

const withSerwist = withSerwistInit({
  swSrc: "app/sw.ts",
  swDest: "public/sw.js",
});

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseHostname = supabaseUrl ? new URL(supabaseUrl).hostname : "";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["*.ngrok-free.dev"],
  images: {
    remotePatterns: supabaseHostname
      ? [
          {
            protocol: "https",
            hostname: supabaseHostname,
            pathname: "/storage/v1/object/public/**",
          },
        ]
      : [],
  },
};

export default withSerwist(nextConfig);
```

**Key Patterns:**
- Dynamic image domain extraction from env var
- Pattern-based remote image whitelisting
- Dev origin allowlist for ngrok tunneling
- Serwist wrapper factory pattern

---

## 14. Error Boundary

### Error Boundary (app/error.tsx)

Client component error boundary with reset capability.

```typescript
"use client";

import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background px-4">
      <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
        <span className="text-2xl">😿</span>
      </div>
      <h2 className="text-xl font-bold text-text-main mb-2">Something went wrong</h2>
      <p className="text-text-muted text-center mb-6">
        {error.message || "An unexpected error occurred."}
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

**Key Patterns:**
- Error and digest passed to component
- Reset callback to retry
- User-friendly error message display

---

## 15. Type Definitions

### Common Types (lib/types/common.ts)

Shared domain types used across the application.

```typescript
// Shared types used across domains

export interface Profile {
  id: string;
  email: string | null;
  full_name: string | null;
  avatar_url: string | null;
  line_user_id: string | null;
  line_display_name: string | null;
  created_at: string;
}

export interface Feedback {
  id: string;
  user_id: string | null;
  message: string;
  image_url: string | null;
  created_at: string;
}

export interface Hospital {
  id: string;
  name: string;
  address: string | null;
  lat: number;
  lng: number;
  phone: string | null;
  open_hours: string | null;
  certified: boolean;
  specialists: string[];
  type: string;
  created_at: string;
}
```

**Key Patterns:**
- Nullable fields for optional database values
- ISO date strings for consistency
- Array fields for multi-value attributes
- Geographic coordinates (lat, lng) as separate fields

---

## 16. Utility Functions

### className Utilities (lib/utils.ts)

Tailwind class composition using clsx and tailwind-merge.

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Key Patterns:**
- Standard pattern for Tailwind class merging
- Handles conditional classes and conflicts
- Lightweight abstraction over common utility

---

## Summary of Key Architectural Patterns

1. **Provider-based Context**: Auth, Location, Toast use React Context for global state
2. **Error-first Returns**: Database operations return `{ data, error }` objects
3. **Lazy Initialization**: LIFF uses singleton pattern with promise caching
4. **Rate Limiting**: Upstash Redis sliding window limits per user ID
5. **Cursor Pagination**: Keyset pagination with base64URL-encoded cursors
6. **Data Denormalization**: Pet reports snapshot pet data at creation time
7. **Geospatial Queries**: Haversine formula + RPC for distance-sorted results
8. **Graceful Fallbacks**: Geolocation defaults to Bangkok; share API returns boolean
9. **Auth Token Injection**: Client-side fetch wrapper adds Bearer token automatically
10. **Offline-First**: Service worker with fallback page for offline documents
11. **Memoized Calculations**: useMemo for complex derived state
12. **Type Safety**: Interfaces for all domain objects
13. **Accessibility**: ARIA labels, semantic HTML, proper heading hierarchy
14. **Mobile-First**: Fixed viewport, no zoom, responsive layout

