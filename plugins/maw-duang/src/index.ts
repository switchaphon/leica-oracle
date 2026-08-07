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
import * as S from "./siam";

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

/**
 * The distinctly-Thai layer. Requires the birth weekday (for ทักษา) so it is rendered
 * for a chart plus, optionally, the natal chart it should be read against.
 */
export function renderThai(c: Chart, natal?: Chart): string {
  const [y, m, d] = c.input.date.split("-").map(Number);
  const [hh, mm] = c.input.time.split(":").map(Number);
  const L: string[] = [];
  const k = S.kalaYoka(y, m, d);
  const weekday = new Date(Date.UTC(y, m - 1, d)).getUTCDay();

  L.push("");
  L.push(`กาลโยค  จ.ศ. ${k.chulasakarat}   (วันเกิดเหตุ = ${S.WEEKDAY_TH[weekday]})`);
  L.push("─".repeat(52));
  const hit = (v: number) => (v === weekday ? "  ← ตรงวันนี้" : "");
  L.push(`  ธงชัย ${S.WEEKDAY_TH[k.thongchai]}${hit(k.thongchai)}   อธิบดี ${S.WEEKDAY_TH[k.athibodi]}${hit(k.athibodi)}`);
  L.push(`  อุบาทว์ ${S.WEEKDAY_TH[k.ubat]}${hit(k.ubat)}   โลกาวินาศ ${S.WEEKDAY_TH[k.lokawinat]}${hit(k.lokawinat)}`);

  const moon = c.placements.find((p) => p.graha.num === 2)!.lon;
  const sun = c.placements.find((p) => p.graha.num === 1)!.lon;
  const nk = S.nakshatraOf(moon);
  const rk = S.reukOf(nk);
  const dt = S.dithi(sun, moon);
  const ym = S.yamOf(hh + mm / 60);

  L.push("");
  L.push("ฤกษ์ / ดิถี / ยาม");
  L.push("─".repeat(52));
  L.push(`  นักษัตร ${nk} ${S.NAKSHATRA_TH[nk - 1]}  →  ฤกษ์ ${rk} ${S.REUK_9[rk - 1].th}ฤกษ์`);
  L.push(`     ${S.REUK_9[rk - 1].use}`);
  L.push(`  ดิถี ${dt.phase} ${dt.kam} ค่ำ${dt.n === k.dithiUbat ? "  ← ดิถีอุบาทว์" : ""}`);
  L.push(`  ยาม${ym.half}ที่ ${ym.n}${ym.n === k.yamUbat ? "  ← ยามอุบาทว์" : `   (ยามอุบาทว์ปีนี้ = ยามที่ ${k.yamUbat})`}`);

  if (natal) {
    const [ny, nm, nd] = natal.input.date.split("-").map(Number);
    const nwd = new Date(Date.UTC(ny, nm - 1, nd)).getUTCDay();
    const t = S.thaksa(nwd);
    const kg = GRAHAS.find((g) => g.num === t.kalakini)!;
    const inNatal = natal.placements.find((p) => p.graha.num === t.kalakini)!;
    const inTransit = c.placements.find((p) => p.graha.num === t.kalakini)!;
    const bh = ((inTransit.rasi - natal.lagna.rasi + 12) % 12) + 1;

    L.push("");
    L.push(`ทักษา  (เจ้าชะตาเกิดวัน${S.WEEKDAY_TH[nwd]})`);
    L.push("─".repeat(52));
    L.push("  " + S.THAKSA_BHAVA.map((b) => `${b} ${toThaiNum(t.byBhava[b])}`).join("  "));
    L.push(`  กาลกิณี = ${toThaiNum(t.kalakini)} ${kg.th}`);
    L.push(`     ในดวงกำเนิด : ภพ ${inNatal.bhava} ${BHAVA[inNatal.bhava - 1].th}`);
    L.push(`     จรวันนี้     : ภพ ${bh} ${BHAVA[bh - 1].th} (นับจากลัคนากำเนิด)`);
  }

  L.push("");
  L.push("  * กาลโยคสอบเทียบกับ จ.ศ.1387 ที่ตีพิมพ์แล้ว");
  L.push("  * คุณภาพของฤกษ์ทั้ง ๙ ยังไม่ได้สอบกับตำราต้นฉบับ — เลขนักษัตรแม่น แต่ความหมายถือเป็นร่าง");
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
  --thai             add กาลโยค / ฤกษ์ / ดิถี / ยาม / ทักษา
  --natal <d> <t>    natal date+time, so ทักษา and ภพ read from the birth chart
  --json             machine-readable output
  --help

example:
  maw duang 1987-09-07 18:33 --tz 7`;

function parseArgs(argv: string[]): { opts?: ChartOptions; json: boolean; thai?: boolean; help: boolean; error?: string } {
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
    thai: argv.includes("--thai"),
    help: false,
  };
}

/** A bare token is positional unless it is sitting right after a value-taking flag. */
function isFlagValue(argv: string[], token: string): boolean {
  const i = argv.indexOf(token);
  if (i <= 0) return false;
  return ["--tz", "--lat", "--lon", "--ayanamsa", "--natal"].includes(argv[i - 1])
    || (argv[i - 2] === "--natal");
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
    if (parsed.json) return { ok: true, output: JSON.stringify(chart, null, 2) };
    let out = renderChart(chart);
    if (parsed.thai) {
      const ni = argv.indexOf("--natal");
      const natal =
        ni >= 0 && argv[ni + 1] && argv[ni + 2]
          ? computeChart({ ...parsed.opts!, date: argv[ni + 1], time: argv[ni + 2] })
          : undefined;
      out += "\n" + renderThai(chart, natal);
    }
    return { ok: true, output: out };
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
