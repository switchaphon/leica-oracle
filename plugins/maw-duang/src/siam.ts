// The layer that makes Thai astrology Thai.
//
// astro.ts + thai.ts give a chart any Jyotish engine would recognise: grahas, rasi,
// whole-sign bhava. That skeleton is shared with India. What follows is not:
// กาลโยค, ทักษา, ฤกษ์, ดิถี, ยาม. A Thai astrologer asked whether a particular day
// suits a particular act reaches for THESE first, not for transit-to-natal orbs.
//
// Confidence is not uniform here and the code says so per-item. กาลโยค is verified
// against a published year; the ฤกษ์ quality mapping is the conventional nine-cycle
// but I could not confirm it against a primary table, so it is labelled as such.

import { norm360 } from "./astro";

// ─── กาลโยค ────────────────────────────────────────────────────────────────
// Four day-qualities fixed for a whole จุลศักราช year. Formulas reproduce all four
// published values for จ.ศ. 1387 exactly (ธงชัย=ศุกร์ อธิบดี=ศุกร์ อุบาทว์=พฤหัส
// โลกาวินาศ=อาทิตย์), which is the positive control for this block.

export const WEEKDAY_TH = ["อาทิตย์", "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์"];

/** จุลศักราช for a Gregorian date. The year turns at Songkran, not 1 January. */
export function chulasakarat(y: number, m: number, d: number): number {
  const beforeSongkran = m < 4 || (m === 4 && d < 16);
  return y - 638 - (beforeSongkran ? 1 : 0);
}

/** 1..7 → อาทิตย์..เสาร์; the formulas return 0 for เสาร์. */
const dayFromRemainder = (r: number) => (r === 0 ? 7 : r) - 1; // to 0-indexed weekday

export type KalaYoka = {
  chulasakarat: number;
  thongchai: number;   // วันธงชัย — victory, best for undertakings
  athibodi: number;    // วันอธิบดี — authority
  ubat: number;        // วันอุบาทว์ — calamity
  lokawinat: number;   // วันโลกาวินาศ — ruin
  yamUbat: number;     // ยามอุบาทว์ — which of the 8 watches is the bad one
  reukUbat: number;    // ฤกษ์อุบาทว์
  dithiUbat: number;   // ดิถีอุบาทว์
};

export function kalaYoka(y: number, m: number, d: number): KalaYoka {
  const cs = chulasakarat(y, m, d);
  const mod = (n: number, k: number) => ((n % k) + k) % k;
  return {
    chulasakarat: cs,
    thongchai: dayFromRemainder(mod(cs * 10 + 3, 7)),
    athibodi: dayFromRemainder(mod(mod(cs, 498), 7)),
    ubat: dayFromRemainder(mod(cs * 10 + 2, 7)),
    lokawinat: dayFromRemainder(mod(cs + 1120, 7)),
    yamUbat: mod(cs * 10 + 2, 8) || 8,
    reukUbat: mod(cs * 10 + 2, 27) || 27,
    dithiUbat: mod(cs * 10 + 2, 30) || 30,
  };
}

// ─── ทักษา ─────────────────────────────────────────────────────────────────
// Eight grahas on a wheel. The native's birth weekday is placed at บริวาร and the
// remaining seven fall where they fall; whichever lands on กาลกิณี is that person's
// affliction star for life. Note the wheel order is NOT ๑..๘ — เสาร์ precedes พฤหัส.

export const THAKSA_WHEEL = [1, 2, 3, 4, 7, 5, 8, 6]; // อ จ ภ ว ส ช ร ศ
export const THAKSA_BHAVA = [
  "บริวาร", "อายุ", "เดช", "ศรี", "มูละ", "อุตสาหะ", "มนตรี", "กาลกิณี",
];

/** Graha that rules each weekday, ๑..๗ (Wednesday-night births use ๘ ราหู — not handled). */
const WEEKDAY_GRAHA = [1, 2, 3, 4, 5, 6, 7];

export type Thaksa = { byBhava: Record<string, number>; kalakini: number; birthGraha: number };

export function thaksa(birthWeekday: number): Thaksa {
  const birthGraha = WEEKDAY_GRAHA[birthWeekday];
  const start = THAKSA_WHEEL.indexOf(birthGraha);
  const byBhava: Record<string, number> = {};
  for (let i = 0; i < 8; i++) byBhava[THAKSA_BHAVA[i]] = THAKSA_WHEEL[(start + i) % 8];
  return { byBhava, kalakini: byBhava["กาลกิณี"], birthGraha };
}

// ─── ฤกษ์ / นักษัตร ────────────────────────────────────────────────────────

export const NAKSHATRA_TH = [
  "อัศวินี", "ภรณี", "กฤติกา", "โรหิณี", "มฤคศิระ", "อารทรา", "ปุนัพสุ", "ปุษยะ", "อาศเลษา",
  "มฆา", "บุรพผลคุนี", "อุตรผลคุนี", "หัสตะ", "จิตรา", "สวาติ", "วิศาขา", "อนุราธา", "เชษฐา",
  "มูลา", "บุรพาษาฒ", "อุตราษาฒ", "ศรวณะ", "ธนิษฐา", "ศตภิษัช", "บุรพภัทรบท", "อุตรภัทรบท", "เรวดี",
];

/** นพดลฤกษ์ — the nine. Conventional nine-cycle from อัศวินี; NOT verified against a
 *  primary table, so treat the *quality* as provisional even though the number is exact. */
export const REUK_9 = [
  { th: "ทลิทโท",   use: "ขอร้อง ผัดผ่อน ขอหมั้น" },
  { th: "มหัทธโน",  use: "การเงิน เปิดร้าน ขึ้นบ้านใหม่ แต่งงาน" },
  { th: "โจโร",     use: "ท่องเที่ยว แข่งขัน — ห้ามลงทุน" },
  { th: "ภูมิปาโล", use: "ที่ดิน อสังหาฯ ปลูกเรือน" },
  { th: "เทศาตรี",  use: "โรงแรม ร้านอาหาร ตลาด" },
  { th: "เทวี",     use: "ความรัก เสริมสวย ศิลปะ" },
  { th: "เพชฌฆาต",  use: "ตัดสินเด็ดขาด ผ่าตัด — ร้ายที่สุด" },
  { th: "ราชา",     use: "ราชพิธี ราชการ รับตำแหน่ง" },
  { th: "สมโณ",     use: "ศาสนา บวช ปฏิบัติธรรม" },
];

/** 1..27 from the Moon's sidereal longitude. */
export const nakshatraOf = (moonSidereal: number) =>
  Math.floor(norm360(moonSidereal) / (360 / 27)) + 1;

export const reukOf = (nakshatra: number) => ((nakshatra - 1) % 9) + 1;

// ─── ดิถี ──────────────────────────────────────────────────────────────────

export type Dithi = { n: number; phase: "ขึ้น" | "แรม"; kam: number };

/** 1..30 from the Sun–Moon elongation; 1–15 waxing, 16–30 waning. */
export function dithi(sunLon: number, moonLon: number): Dithi {
  const n = Math.floor(norm360(moonLon - sunLon) / 12) + 1;
  return n <= 15
    ? { n, phase: "ขึ้น", kam: n }
    : { n, phase: "แรม", kam: n - 15 };
}

// ─── ยาม ───────────────────────────────────────────────────────────────────
// Eight watches of 1h30 each, day counted from 06:00 and night from 18:00.

export type Yam = { half: "กลางวัน" | "กลางคืน"; n: number };

export function yamOf(hour: number): Yam {
  if (hour >= 6 && hour < 18) return { half: "กลางวัน", n: Math.floor((hour - 6) / 1.5) + 1 };
  const h = hour >= 18 ? hour - 18 : hour + 6;
  return { half: "กลางคืน", n: Math.floor(h / 1.5) + 1 };
}

// ─── มาตรฐานดาว: อุจ / นิจ ─────────────────────────────────────────────────
// Standard exaltation table. Corroborated on two entries by sources consulted:
// อาทิตย์ exalted in เมษ with มหาอุจ at 9–12°, and พุธ exalted in กันย์.
// มหาอุจ is a DEGREE, not the whole sign — the distinction decides how strong a
// placement actually is, and it is the one most often overstated in a reading.

export const UCHA: Record<number, { rasi: number; deg: number }> = {
  1: { rasi: 0,  deg: 10 },  // อาทิตย์ — เมษ 10
  2: { rasi: 1,  deg: 3  },  // จันทร์  — พฤษภ 3
  3: { rasi: 9,  deg: 28 },  // อังคาร  — มังกร 28
  4: { rasi: 5,  deg: 15 },  // พุธ     — กันย์ 15
  5: { rasi: 3,  deg: 5  },  // พฤหัส   — กรกฎ 5
  6: { rasi: 11, deg: 27 },  // ศุกร์   — มีน 27
  7: { rasi: 6,  deg: 20 },  // เสาร์   — ตุล 20
  8: { rasi: 1,  deg: 20 },  // ราหู    — พฤษภ (ตำราต่างกัน)
};

export type Dignity = { label: string; note?: string };

/** เกษตร / อุจ / มหาอุจ / นิจ for a graha at a sidereal longitude. */
export function dignity(grahaNum: number, lon: number, rasiLord: number[]): Dignity {
  const rasi = Math.floor(norm360(lon) / 30);
  const degIn = norm360(lon) % 30;
  const u = UCHA[grahaNum];

  if (u) {
    if (rasi === u.rasi) {
      const off = Math.abs(degIn - u.deg);
      return off <= 2
        ? { label: "มหาอุจ", note: `ห่างองศามหาอุจ ${off.toFixed(2)}°` }
        : { label: "อุจ", note: `อุจโดยราศี แต่ห่างองศามหาอุจ ${off.toFixed(2)}°` };
    }
    if (rasi === (u.rasi + 6) % 12) return { label: "นิจ" };
  }
  if (rasiLord[rasi] === grahaNum) return { label: "เกษตร" };
  return { label: "—" };
}
