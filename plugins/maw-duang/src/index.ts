// maw duang — แมวดวง. A Thai (nirayana) natal chart engine.
//
// Every chart it prints declares the three choices that produced it: zodiac system,
// ayanamsa value, and ephemeris. Two astrologers who disagree about a reading cannot
// tell whether they disagree about the rules or about the sky unless those three are
// on the page. So they are always on the page.

import {
  julianDay, deltaTSeconds, obliquity, sunLongitude, moonLongitude,
  rahuLongitude, planetLongitude, gmst, ascendant, norm360,
} from "./astro";
import {
  lahiriAyanamsa, GRAHAS, RASI, RASI_LORD, BHAVA, rasiOf, bhavaOf,
  fmtDeg, toThaiNum, type Placement,
} from "./thai";

type InvokeContext = { source: "cli" | "api"; args: string[] | Record<string, unknown>; writer?: (...a: any[]) => void };
type PluginResult = { ok: boolean; output?: string; error?: string };

const BANGKOK = { lat: 13.7563, lon: 100.5018 };

export type ChartOptions = {
  date: string;      // YYYY-MM-DD
  time: string;      // HH:MM
  tz: number;        // hours east of UTC
  lat: number;
  lon: number;
  sidereal: boolean;
  ayanamsaOverride?: number;
};

export type Chart = {
  input: ChartOptions;
  system: { zodiac: string; ayanamsa: number; ayanamsaName: string; ephemeris: string };
  jdUT: number;
  lagna: { lon: number; rasi: number; degInRasi: number };
  placements: Placement[];
};

/** Tropical longitude of every body we carry, keyed by the name astro.ts knows. */
function tropicalLongitudes(T_tt: number): Record<string, number> {
  const rahu = rahuLongitude(T_tt);
  return {
    sun: sunLongitude(T_tt),
    moon: moonLongitude(T_tt),
    mercury: planetLongitude("mercury", T_tt),
    venus: planetLongitude("venus", T_tt),
    mars: planetLongitude("mars", T_tt),
    jupiter: planetLongitude("jupiter", T_tt),
    saturn: planetLongitude("saturn", T_tt),
    uranus: planetLongitude("uranus", T_tt),
    rahu,
    ketu: norm360(rahu + 180),
  };
}

export function computeChart(o: ChartOptions): Chart {
  const [y, m, d] = o.date.split("-").map(Number);
  const [hh, mm] = o.time.split(":").map(Number);
  if (!y || !m || !d || Number.isNaN(hh) || Number.isNaN(mm)) {
    throw new Error(`bad date/time: "${o.date} ${o.time}" — expected YYYY-MM-DD HH:MM`);
  }

  const hourLocal = hh + mm / 60;
  const jdUT = julianDay(y, m, d, hourLocal - o.tz);
  const jdTT = jdUT + deltaTSeconds(y) / 86400;

  const T_ut = (jdUT - 2451545.0) / 36525;
  const T_tt = (jdTT - 2451545.0) / 36525;

  const ayan = o.sidereal ? (o.ayanamsaOverride ?? lahiriAyanamsa(T_tt)) : 0;
  const shift = (tropical: number) => norm360(tropical - ayan);

  const trop = tropicalLongitudes(T_tt);
  // A second sample one hour on, only to label direct vs retrograde.
  const tropNext = tropicalLongitudes(T_tt + 1 / 24 / 36525);

  const lagnaTrop = ascendant(norm360(gmst(jdUT) + o.lon), o.lat, obliquity(T_ut));
  const lagnaLon = shift(lagnaTrop);

  const placements: Placement[] = GRAHAS.map((g) => {
    const lon = shift(trop[g.en]);
    let retro = false;
    if (g.en === "rahu" || g.en === "ketu") {
      retro = true; // the mean node only ever moves backwards
    } else if (g.en !== "sun" && g.en !== "moon") {
      let delta = tropNext[g.en] - trop[g.en];
      if (delta > 180) delta -= 360;
      if (delta < -180) delta += 360;
      retro = delta < 0;
    }
    return {
      graha: g,
      lon,
      rasi: rasiOf(lon),
      degInRasi: norm360(lon) % 30,
      bhava: bhavaOf(lon, lagnaLon),
      retro,
    };
  });

  return {
    input: o,
    system: {
      zodiac: o.sidereal ? "นิรายนะ (sidereal)" : "สายนะ (tropical)",
      ayanamsa: ayan,
      ayanamsaName: o.sidereal ? (o.ayanamsaOverride != null ? "override" : "ลาหิรี (Lahiri)") : "—",
      ephemeris: "built-in (Meeus + JPL approximate elements)",
    },
    jdUT,
    lagna: { lon: lagnaLon, rasi: rasiOf(lagnaLon), degInRasi: norm360(lagnaLon) % 30 },
    placements,
  };
}

export function renderChart(c: Chart): string {
  const L: string[] = [];
  const tzSign = c.input.tz >= 0 ? "+" : "";

  L.push(`ดวงชะตา  ${c.input.date} ${c.input.time} (UTC${tzSign}${c.input.tz})`);
  L.push(`พิกัด    ${c.input.lat.toFixed(4)}N ${c.input.lon.toFixed(4)}E    JD(UT) ${c.jdUT.toFixed(5)}`);
  L.push("");
  // The declaration. Never omitted, never abbreviated.
  L.push(`ระบบ     ${c.system.zodiac}`);
  L.push(`อายนางศ  ${c.system.ayanamsa.toFixed(4)}°  (${c.system.ayanamsaName})`);
  L.push(`ปฏิทิน   ${c.system.ephemeris}`);
  L.push("");

  const lagnaLord = GRAHAS.find((g) => g.num === RASI_LORD[c.lagna.rasi]);
  L.push(
    `ลัคนา    ${fmtDeg(c.lagna.degInRasi)} ราศี${RASI[c.lagna.rasi]}` +
      `   (เจ้าเรือน = ${toThaiNum(lagnaLord!.num)} ${lagnaLord!.th})`
  );
  L.push("");
  L.push("ดาว                องศา     ราศี      ภพ");
  L.push("─".repeat(52));

  for (const p of c.placements) {
    const num = toThaiNum(p.graha.num);
    const name = (p.graha.th + (p.retro ? " (พักร์)" : "")).padEnd(14, " ");
    const rasi = RASI[p.rasi].padEnd(8, " ");
    const bh = `${String(p.bhava).padStart(2, " ")} ${BHAVA[p.bhava - 1].th}`;
    L.push(`${num} ${name} ${fmtDeg(p.degInRasi)}  ${rasi} ${bh}`);
  }

  L.push("");
  L.push("ภพ (นับจากลัคนา — whole sign)");
  L.push("─".repeat(52));
  for (let i = 0; i < 12; i++) {
    const rasiIdx = (c.lagna.rasi + i) % 12;
    const occupants = c.placements
      .filter((p) => p.rasi === rasiIdx)
      .map((p) => toThaiNum(p.graha.num))
      .join(" ");
    const label = `${String(i + 1).padStart(2, " ")} ${BHAVA[i].th}`.padEnd(12, " ");
    L.push(`${label} ราศี${RASI[rasiIdx].padEnd(7, " ")} ${occupants || "—"}`);
  }

  return L.join("\n");
}

const HELP = `maw duang — แมวดวง, Thai nirayana natal chart

  maw duang <YYYY-MM-DD> <HH:MM> [options]

options:
  --tz <hours>       timezone east of UTC        (default 7)
  --lat <deg>        latitude north              (default 13.7563, Bangkok)
  --lon <deg>        longitude east              (default 100.5018, Bangkok)
  --ayanamsa <deg>   pin the ayanamsa by hand    (default: Lahiri for the date)
  --tropical         read สายนะ instead of นิรายนะ (ayanamsa = 0)
  --json             machine-readable output
  --help

example:
  maw duang 1987-09-07 18:33 --tz 7`;

function parseArgs(argv: string[]): { opts?: ChartOptions; json: boolean; help: boolean; error?: string } {
  if (argv.includes("--help") || argv.includes("-h") || argv.length === 0) {
    return { json: false, help: true };
  }
  const positional = argv.filter((a) => !a.startsWith("--") && !isFlagValue(argv, a));
  const flag = (name: string): string | undefined => {
    const i = argv.indexOf(`--${name}`);
    return i >= 0 ? argv[i + 1] : undefined;
  };
  const num = (name: string, dflt: number): number | undefined => {
    const raw = flag(name);
    if (raw === undefined) return dflt;
    const v = Number(raw);
    return Number.isFinite(v) ? v : undefined;
  };

  const [date, time] = positional;
  if (!date || !time) {
    return { json: false, help: false, error: "usage: maw duang <YYYY-MM-DD> <HH:MM> [--tz 7]" };
  }

  const tz = num("tz", 7);
  const lat = num("lat", BANGKOK.lat);
  const lon = num("lon", BANGKOK.lon);
  if (tz === undefined || lat === undefined || lon === undefined) {
    return { json: false, help: false, error: "--tz / --lat / --lon must be numbers" };
  }

  let ayanamsaOverride: number | undefined;
  const rawAyan = flag("ayanamsa");
  if (rawAyan !== undefined) {
    const v = Number(rawAyan);
    if (!Number.isFinite(v)) return { json: false, help: false, error: "--ayanamsa must be a number" };
    ayanamsaOverride = v;
  }

  return {
    opts: { date, time, tz, lat, lon, sidereal: !argv.includes("--tropical"), ayanamsaOverride },
    json: argv.includes("--json"),
    help: false,
  };
}

/** A bare token is positional unless it is sitting right after a value-taking flag. */
function isFlagValue(argv: string[], token: string): boolean {
  const i = argv.indexOf(token);
  if (i <= 0) return false;
  return ["--tz", "--lat", "--lon", "--ayanamsa"].includes(argv[i - 1]);
}

export async function handler(ctx: InvokeContext): Promise<PluginResult> {
  const argv = Array.isArray(ctx.args)
    ? ctx.args
    : Object.entries(ctx.args as Record<string, unknown>).flatMap(([k, v]) =>
        k === "_" ? (v as string[]) : [`--${k}`, String(v)]
      );

  const parsed = parseArgs(argv);
  if (parsed.help) return { ok: true, output: HELP };
  if (parsed.error) return { ok: false, error: parsed.error };

  try {
    const chart = computeChart(parsed.opts!);
    return { ok: true, output: parsed.json ? JSON.stringify(chart, null, 2) : renderChart(chart) };
  } catch (e: any) {
    return { ok: false, error: e?.message ?? String(e) };
  }
}

export const command = {
  name: ["duang"],
  description: "แมวดวง — Thai nirayana natal chart",
};

export default handler;

// maw-rs runs plugins as `bun <entry> <args>`. Without this, the module only defines
// its exports and exits 0 — a silent no-op that looks exactly like success.
if (import.meta.main) {
  const result = await handler({ source: "cli", args: process.argv.slice(2) });
  if (result.output) console.log(result.output);
  if (result.error) console.error(result.error);
  process.exit(result.ok ? 0 : 1);
}
