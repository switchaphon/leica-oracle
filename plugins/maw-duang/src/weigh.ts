// Weighing a mechanism before believing it.
//
// From the 6 August calibration case (mahamodo-engine, 2026-08-07). Three findings
// came out of it, and all three are checks a machine can run but a reader will skip:
//
//   1. A mechanism that holds for 446 days cannot explain one Thursday. Its timescale
//      must match the question's. I wrote that rule down before the answer was known,
//      argued from it, and still failed to apply it to my own reading — so it is
//      encoded here rather than left as a principle I can forget under pressure.
//
//   2. "Nothing blocks the path" is not "it will happen". The native was not obstructed
//      on his way to dinner; his evening was CLAIMED from elsewhere — his partner's
//      family arrived. The house of the thing asked about was clear. Nobody looked at
//      the houses that could compete for the same hours.
//
//   3. A contact is only evidence if it is rare. Null tests on that day put a sub-1°
//      transit-to-natal contact at 37–50% base rate: near a coin flip, so its presence
//      explains almost nothing even when the verdict it supported turns out right.

import { computeChart, type Chart } from "./index";
import { BHAVA, GRAHAS } from "./thai";

/** Advance a date string by n days. */
function addDays(date: string, n: number): string {
  const [y, m, d] = date.split("-").map(Number);
  const t = new Date(Date.UTC(y, m - 1, d));
  t.setUTCDate(t.getUTCDate() + n);
  return t.toISOString().slice(0, 10);
}

export type Dwell = {
  graha: number;
  bhava: number;
  daysHeld: number;      // total span the graha sits in this bhava
  daysRemaining: number; // how much of it is still ahead
  verdict: "เฉพาะวัน" | "เฉพาะสัปดาห์" | "เฉพาะเดือน" | "ภูมิอากาศ";
};

/**
 * How long a transiting graha stays in the bhava it currently occupies, counted from
 * the natal lagna. This is the number that decides whether a placement is an *event*
 * or merely the *weather* a whole season is happening inside.
 */
export function dwell(
  grahaNum: number,
  date: string,
  natalLagnaRasi: number,
  base: { tz: number; lat: number; lon: number }
): Dwell {
  const bhavaAt = (d: string) => {
    const c = computeChart({ date: d, time: "12:00", sidereal: true, ...base });
    const p = c.placements.find((x) => x.graha.num === grahaNum)!;
    return ((p.rasi - natalLagnaRasi + 12) % 12) + 1;
  };

  const here = bhavaAt(date);
  // 500 days is past the point where "event" is arguable for anything.
  const LIMIT = 500;
  let back = 0;
  while (back < LIMIT && bhavaAt(addDays(date, -(back + 1))) === here) back++;
  let fwd = 0;
  while (fwd < LIMIT && bhavaAt(addDays(date, fwd + 1)) === here) fwd++;

  const daysHeld = back + fwd + 1;
  const verdict =
    daysHeld <= 3 ? "เฉพาะวัน"
    : daysHeld <= 14 ? "เฉพาะสัปดาห์"
    : daysHeld <= 60 ? "เฉพาะเดือน"
    : "ภูมิอากาศ";

  return { graha: grahaNum, bhava: here, daysHeld, daysRemaining: fwd, verdict };
}

/**
 * Base rate of a "tight contact" on a given day, measured over synthetic natal charts.
 *
 * Answers the only question that makes a contact evidence: how often would I have found
 * one anyway? Nine grahas against nine natal points is 81 chances per day, so a narrow
 * hit is not the coincidence it looks like.
 */
export function contactBaseRate(
  onDate: string,
  atTime: string,
  base: { tz: number; lat: number; lon: number },
  opts: { orbDeg?: number; samples?: number; startYear?: number; endYear?: number } = {}
): { rate: number; hits: number; samples: number; orbDeg: number } {
  const orbDeg = opts.orbDeg ?? 1.0;
  const samples = opts.samples ?? 24;
  const y0 = opts.startYear ?? 1965;
  const y1 = opts.endYear ?? 2000;

  const transit = computeChart({ date: onDate, time: atTime, sidereal: true, ...base });
  let hits = 0;

  for (let i = 0; i < samples; i++) {
    // Deterministic spread across the window — no RNG, so the number is reproducible.
    const frac = i / samples;
    const year = Math.floor(y0 + frac * (y1 - y0));
    const dayOfYear = Math.floor(((i * 137) % 360) + 1);
    const synth = new Date(Date.UTC(year, 0, dayOfYear));
    const fake = synth.toISOString().slice(0, 10);

    const natal = computeChart({ date: fake, time: "12:00", sidereal: true, ...base });
    const found = transit.placements.some((t) =>
      natal.placements.some((n) => {
        let sep = Math.abs(t.lon - n.lon) % 360;
        if (sep > 180) sep = 360 - sep;
        return sep <= orbDeg;
      })
    );
    if (found) hits++;
  }

  return { rate: hits / samples, hits, samples, orbDeg };
}

/**
 * Every bhava with transit activity, so the houses that might CLAIM the hours get
 * looked at rather than only the house of the thing being asked about.
 */
export function competingClaims(
  transit: Chart,
  natalLagnaRasi: number,
  questionBhava: number
): { bhava: number; th: string; grahas: number[]; isQuestion: boolean }[] {
  const byBhava = new Map<number, number[]>();
  for (const p of transit.placements) {
    const b = ((p.rasi - natalLagnaRasi + 12) % 12) + 1;
    byBhava.set(b, [...(byBhava.get(b) ?? []), p.graha.num]);
  }
  return [...byBhava.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([bhava, grahas]) => ({
      bhava,
      th: BHAVA[bhava - 1].th,
      grahas,
      isQuestion: bhava === questionBhava,
    }));
}

export { GRAHAS };

// ─── The significator problem ──────────────────────────────────────────────
//
// BLIND-02 scored E1 ✓ E2 ✗ E3 ✓. Jupiter's house at the moment of the event was
// the right instrument all three times — the mechanism never failed. What failed
// was naming which house the question belongs to:
//
//   enter master's 2018   พฤหัส ภพ ๙ ศุภะ    I named ๙   ✓
//   finish master's 2020  พฤหัส ภพ ๑๑ ลาภะ   I named ๑๐  ✗
//   start PhD 2024        พฤหัส ภพ ๔ พันธุ   I named ๔   ✓
//
// A conferred degree is a ลาภ — a thing attained — before it is a กัมมะ, which is
// the occupation you go on to hold. ภพ ๑๑ was not merely mis-ranked in my criteria;
// it was absent from them. The house holding the answer had been excluded before the
// first calculation ran, and no amount of rigour about mechanism lifetimes can
// recover a house that was never on the list.
//
// This is the same error as BLIND-01 wearing different clothes. There I built
// competingClaims() precisely because looking only at the question's house misses
// the cause — then wrote a five-house shortlist into my own criteria one case later.
// Building the tool is not the same as internalising why it exists.

/** Primary sense first. The primary sense is the one that decides; the rest are colour. */
export const BHAVA_SENSE: { primary: string; also: string[] }[] = [
  { primary: "ตัวตน ร่างกาย",   also: ["บุคลิก", "จุดตั้งต้นของทุกเรื่อง"] },
  { primary: "ทรัพย์ที่ถือไว้",  also: ["เงินทอง", "คำพูด", "ครอบครัวใกล้ตัว"] },
  { primary: "พี่น้อง เพื่อนร่วมทาง", also: ["เดินทางใกล้", "ทักษะ", "ความพยายามของตัวเอง"] },
  { primary: "บ้าน ที่ตั้งหลัก",  also: ["พ่อแม่", "ที่ดิน", "การย้ายมาอยู่ที่ใหม่"] },
  { primary: "สิ่งที่สร้างออกมา", also: ["บุตร", "ความรัก", "วิทยานิพนธ์", "ปัญญา"] },
  { primary: "อุปสรรค ศัตรู",    also: ["โรค", "หนี้", "งานประจำที่ต้องทน"] },
  { primary: "คู่ครอง",          also: ["หุ้นส่วน", "การสมาคม", "ฝ่ายตรงข้าม"] },
  { primary: "การเปลี่ยนสภาพ",   also: ["ความตาย", "ความลับ", "ของที่ได้จากผู้อื่น"] },
  { primary: "วิชาชั้นสูง ครูบาอาจารย์", also: ["บุญ", "เดินทางไกล", "ความเชื่อ"] },
  { primary: "อาชีพ สถานะต่อสาธารณะ", also: ["ตำแหน่ง", "เกียรติยศ"] },
  { primary: "ลาภ สิ่งที่ได้มาสมหวัง", also: ["มิตร", "ความสำเร็จตามที่ตั้งใจ", "วุฒิที่ได้รับ"] },
  { primary: "การสูญเสีย รายจ่าย", also: ["ที่ลับ", "ต่างแดน", "การปลีกตัว"] },
];

/**
 * Every one of the twelve, with the transiting graha in each — so a question is
 * answered by ruling houses OUT on the record rather than by never listing them.
 * The shortlist is where BLIND-02 was lost; this function has no shortlist.
 */
export function houseSweep(
  transit: Chart,
  natalLagnaRasi: number
): { bhava: number; th: string; primary: string; grahas: number[] }[] {
  return Array.from({ length: 12 }, (_, i) => {
    const bhava = i + 1;
    const grahas = transit.placements
      .filter((p) => ((p.rasi - natalLagnaRasi + 12) % 12) + 1 === bhava)
      .map((p) => p.graha.num);
    return { bhava, th: BHAVA[i].th, primary: BHAVA_SENSE[i].primary, grahas };
  });
}
