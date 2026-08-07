// The Thai layer: sidereal conversion, the ten grahas, the twelve rasi, the twelve bhava.
//
// Thai astrology reads a NIRAYANA (sidereal) zodiac. Everything in astro.ts is tropical,
// so exactly one subtraction separates the two systems — and it is currently ~24°, which
// is most of a whole sign. That subtraction is the entire difference between a Thai chart
// and a Western one drawn from the same birth moment.

import { norm360 } from "./astro";

/** Lahiri (Chitrapaksha) ayanamsa in degrees. T = Julian centuries from J2000. */
export function lahiriAyanamsa(T: number): number {
  return 23.853194 + 1.396042 * T + 0.0003086 * T * T;
}

export const THAI_DIGITS = ["๐", "๑", "๒", "๓", "๔", "๕", "๖", "๗", "๘", "๙"];
export const toThaiNum = (n: number) =>
  String(n).split("").map((c) => THAI_DIGITS[+c] ?? c).join("");

export type Graha = {
  num: number;       // the number it is written as in a Thai chart
  th: string;        // Thai name
  en: string;        // body used to compute it
  letter: string;    // ทักษา letter
  benefic: boolean;  // ศุภเคราะห์ true / บาปเคราะห์ false
  inThaksa: boolean; // ทักษา uses eight, not ten
};

/** Written in chart order ๑–๙ then ๐, which is how a Thai chart lists them. */
export const GRAHAS: Graha[] = [
  { num: 1, th: "อาทิตย์", en: "sun",     letter: "อ", benefic: false, inThaksa: true },
  { num: 2, th: "จันทร์",  en: "moon",    letter: "จ", benefic: true,  inThaksa: true },
  { num: 3, th: "อังคาร",  en: "mars",    letter: "ภ", benefic: false, inThaksa: true },
  { num: 4, th: "พุธ",     en: "mercury", letter: "ว", benefic: true,  inThaksa: true },
  { num: 5, th: "พฤหัสฯ",  en: "jupiter", letter: "ช", benefic: true,  inThaksa: true },
  { num: 6, th: "ศุกร์",   en: "venus",   letter: "ศ", benefic: true,  inThaksa: true },
  { num: 7, th: "เสาร์",   en: "saturn",  letter: "ส", benefic: false, inThaksa: true },
  { num: 8, th: "ราหู",    en: "rahu",    letter: "ร", benefic: false, inThaksa: true },
  { num: 9, th: "เกตุ",    en: "ketu",    letter: "ก", benefic: false, inThaksa: false },
  { num: 0, th: "มฤตยู",   en: "uranus",  letter: "ม", benefic: false, inThaksa: false },
];

export const RASI = [
  "เมษ", "พฤษภ", "เมถุน", "กรกฎ", "สิงห์", "กันย์",
  "ตุล", "พิจิก", "ธนู", "มังกร", "กุมภ์", "มีน",
];

/** เกษตร — the graha that owns each rasi. เกตุ and มฤตยู own nothing. */
export const RASI_LORD = [3, 6, 4, 2, 1, 4, 6, 3, 5, 7, 7, 5];

export const BHAVA = [
  { th: "ตนุ",     means: "ตัวตน ร่างกาย บุคลิก" },
  { th: "กดุมภะ",  means: "ทรัพย์สิน เงินทอง" },
  { th: "สหัชชะ",  means: "พี่น้อง เพื่อน การสื่อสาร เดินทางใกล้" },
  { th: "พันธุ",   means: "บ้าน ที่อยู่ พ่อแม่ ญาติ" },
  { th: "ปุตตะ",   means: "บุตร ความรัก การสร้างสรรค์" },
  { th: "อริ",     means: "ศัตรู โรคภัย หนี้สิน อุปสรรค" },
  { th: "ปัตนิ",   means: "คู่ครอง หุ้นส่วน การสมาคม" },
  { th: "มรณะ",    means: "ความตาย ความลับ การเปลี่ยนแปลง" },
  { th: "ศุภะ",    means: "บุญ โชค ครูบาอาจารย์ เดินทางไกล" },
  { th: "กัมมะ",   means: "การงาน เกียรติยศ ตำแหน่ง" },
  { th: "ลาภะ",    means: "ลาภ มิตร ความสำเร็จ" },
  { th: "วินาศ",   means: "ความสูญเสีย รายจ่าย ที่ลับ" },
];

export type Placement = {
  graha: Graha;
  lon: number;      // sidereal ecliptic longitude, degrees
  rasi: number;     // 0-11
  degInRasi: number;
  bhava: number;    // 1-12, counted from lagna
  retro: boolean;
};

export const rasiOf = (lon: number) => Math.floor(norm360(lon) / 30);

/** Whole-sign houses: bhava 1 IS the lagna's whole sign, not a 30° arc from the lagna degree. */
export const bhavaOf = (lon: number, lagnaLon: number) =>
  ((rasiOf(lon) - rasiOf(lagnaLon) + 12) % 12) + 1;

/** 12°34' — the form a Thai chart writes a position in. */
export function fmtDeg(degInRasi: number): string {
  const d = Math.floor(degInRasi);
  const m = Math.floor((degInRasi - d) * 60);
  return `${String(d).padStart(2, " ")}°${String(m).padStart(2, "0")}'`;
}
