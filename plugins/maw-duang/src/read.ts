// Reading a natal chart for disposition.
//
// A hard line runs through this file and the output says so out loud. Everything in
// astro.ts and siam.ts is CALCULATION — checkable against equinoxes, against Meeus,
// against a published จ.ศ. year, and wrong in a way anyone can demonstrate. Nothing
// below is. These are rule tables from the tradition, applied mechanically. They can
// be applied correctly or incorrectly, but "correct" here means faithful to the
// tradition, not verified against the world.
//
// Keeping that line visible is the whole discipline of the last two days: the numbers
// earned trust by being falsifiable, and interpretation cannot borrow that trust.

import { RASI, BHAVA, GRAHAS, RASI_LORD } from "./thai";
import type { Placement } from "./thai";

/** ลัคนา — the rising sign sets the outward temperament. */
export const LAGNA_NATURE: string[] = [
  "บุกก่อน คิดทีหลัง เริ่มเรื่องเก่งกว่าปิดเรื่อง ตรงจนบางทีแรง",           // เมษ
  "ช้าแต่ไม่ถอย ยึดของที่จับแล้ว ทนได้นานผิดปกติ เปลี่ยนใจยาก",              // พฤษภ
  "สองความคิดพร้อมกัน พูดเก่ง เบื่อเร็ว เรียนอะไรก็ไว แต่ทิ้งกลางคันบ่อย",  // เมถุน
  "อ่านอารมณ์คนอื่นออกก่อนตัวเอง ปกป้องพวกพ้อง เก็บของเก่าไม่ยอมทิ้ง",      // กรกฎ
  "อยากให้เห็น อยากให้ยอมรับ ใจกว้างจริงเวลาได้เป็นที่ตั้ง เสียหน้าไม่ได้",  // สิงห์
  "เห็นข้อผิดก่อนเห็นภาพรวม ละเอียดจนตัวเองเหนื่อย รับใช้เก่ง ชมตัวเองไม่เป็น", // กันย์
  "ชั่งน้ำหนักตลอดเวลา ตัดสินใจช้าเพราะเห็นสองด้านจริง ๆ เกลียดการปะทะ",     // ตุล
  "ลึก ไม่เปิดง่าย จำได้นานทั้งดีและร้าย เอาจริงถึงที่สุดเมื่อเลือกแล้ว",     // พิจิก
  "มองไกล เชื่อในความหมาย พูดตรงแบบไม่ได้ตั้งใจเจ็บ อยู่นิ่งกับกรอบไม่ได้",  // ธนู
  "สร้างทีละก้อน ยอมช้าเพื่อให้มั่น อดทนกับงานที่คนอื่นทิ้ง ดูเย็นกว่าที่เป็น", // มังกร
  "คิดคนละทางกับห้อง เห็นระบบมากกว่าเห็นคน แปลกแยกโดยไม่ได้ตั้งใจ",          // กุมภ์
  "ซึมซับทุกอย่างรอบตัว ขอบเขตบาง เมตตาง่าย เสียหลักง่ายพอกัน",             // มีน
];

/** Where the lagna lord sits — the direction the life-force actually pours into. */
export const LORD_IN_BHAVA: string[] = [
  "แรงทั้งหมดกลับมาที่ตัวเอง พึ่งตัวเองสูง ดื้อกับคนที่มาสั่ง",
  "หมดไปกับการสะสมและความมั่นคง พูดเรื่องเงินและคุณค่าบ่อยกว่าที่รู้ตัว",
  "ลงที่ทักษะและการสื่อสาร ลงมือเองมากกว่าสั่ง พี่น้องเพื่อนฝูงมีน้ำหนัก",
  "ลงที่บ้านและรากฐาน สร้างที่ทางให้ตัวเองก่อนจึงออกไปข้างนอกได้",
  "ลงที่การสร้างของออกมา งานที่มีลายเซ็นตัวเองสำคัญกว่างานที่ได้เงิน",
  "ลงที่การต่อสู้กับอุปสรรค เก่งขึ้นเพราะโดนบีบ ไม่ใช่เพราะโล่ง",
  "ลงที่คู่และการสมาคม ตัวตนคมชัดขึ้นเมื่อมีคนอยู่ตรงข้าม",
  "ลงที่การเปลี่ยนสภาพ ผ่านการรื้อแล้วสร้างใหม่หลายรอบ ของลับของลึกเป็นเรื่องปกติ",
  "ลงที่วิชาและความเชื่อ ต้องมีครูหรือหลักให้ยึด เดินทางไกลเปลี่ยนคนคนนี้ได้",
  "ลงที่งานและสถานะ วัดตัวเองด้วยสิ่งที่ทำสำเร็จ พักไม่ค่อยเป็น",
  "ลงที่มิตรและเครือข่าย ได้มาด้วยคนรอบตัวมากกว่าด้วยลำพัง",
  "ลงที่ที่ลับและการปลีกตัว ทำงานได้ดีตอนไม่มีใครดู เสียพลังกับที่ที่ไม่มีใครเห็น",
];

/**
 * Provenance label carried by every line of a reading.
 *
 * Adopted from mawduang, whose reasoning beats mine: a caveat at the top of a page
 * is read once, but sentences are read one at a time — and when someone copies a
 * paragraph elsewhere, the caveat does not travel with it while the label does.
 * My caveat sat in a single block under the reading, which meant it protected the
 * page and not the excerpt.
 */
export type Provenance =
  | "engine"     // computed, and checkable against something outside this code
  | "structure"  // a fact about the system's own rules, verifiable from the formula
  | "tradition"  // what the texts say — reportable, never a measurement
  | "no-arbiter" // no way to check it at all
;

export type ReadingLine = { tag: Provenance; label: string; text: string };

export type Reading = {
  lagnaRasi: number;
  lagnaText: string;
  lordNum: number;
  lordBhava: number;
  lordText: string;
  stelliums: { bhava: number; grahas: number[] }[];
  beneficCount: number;
  maleficCount: number;
  inLagna: number[];
  lines: ReadingLine[];
};

/**
 * Mechanical application of the tables above. Deliberately does not blend the lines
 * into flowing prose — a reader must be able to see which rule produced which
 * sentence, and delete the one they disagree with.
 */
export function readNatal(placements: Placement[], lagnaRasi: number): Reading {
  const lordNum = RASI_LORD[lagnaRasi];
  const lord = placements.find((p) => p.graha.num === lordNum)!;

  const byBhava = new Map<number, number[]>();
  for (const p of placements) {
    // ๙ เกตุ and ๐ มฤตยู carry no rulership; they colour a house without claiming it.
    byBhava.set(p.bhava, [...(byBhava.get(p.bhava) ?? []), p.graha.num]);
  }

  const stelliums = [...byBhava.entries()]
    .filter(([, g]) => g.length >= 3)
    .map(([bhava, grahas]) => ({ bhava, grahas }))
    .sort((a, b) => b.grahas.length - a.grahas.length);

  const nameOf = (n: number) => GRAHAS.find((g) => g.num === n)!.th;
  const inLagna = byBhava.get(1) ?? [];
  const lines: ReadingLine[] = [
    // The rising sign is computed; what it means about a person is not.
    { tag: "engine", label: "ลัคนา",
      text: `${RASI[lagnaRasi]} — คำนวณจากเวลาและพิกัดเกิด` },
    { tag: "tradition", label: "ลัคนา",
      text: LAGNA_NATURE[lagnaRasi] },
    { tag: "structure", label: "เจ้าเรือน",
      text: `ราศี${RASI[lagnaRasi]} มี ${nameOf(lordNum)} เป็นเจ้าเรือน — กฎภายในของระบบ` },
    { tag: "engine", label: "เจ้าเรือน",
      text: `${nameOf(lordNum)} สถิตภพ ${lord.bhava} ${BHAVA[lord.bhava - 1].th}` },
    { tag: "tradition", label: "เจ้าเรือน",
      text: LORD_IN_BHAVA[lord.bhava - 1] },
    inLagna.length
      ? { tag: "engine" as Provenance, label: "ในลัคนา",
          text: `${inLagna.map(nameOf).join(" · ")} ทับลัคนา` }
      : { tag: "engine" as Provenance, label: "ในลัคนา",
          text: "ไม่มีดาวทับลัคนา" },
    ...stelliums.map((s) => ({
      tag: "engine" as Provenance, label: "ดาวกระจุก",
      text: `${s.grahas.length} ดวงในภพ ${s.bhava} ${BHAVA[s.bhava - 1].th} (${s.grahas.map(nameOf).join(" ")})`,
    })),
    ...stelliums.map(() => ({
      tag: "tradition" as Provenance, label: "ดาวกระจุก",
      text: "ตำราถือว่าเรื่องของภพนั้นกินพื้นที่ชีวิตมากกว่าปกติ",
    })),
    { tag: "structure", label: "สมดุล",
      text: `ศุภเคราะห์ ${placements.filter((p) => p.graha.benefic).length} : บาปเคราะห์ ${placements.filter((p) => !p.graha.benefic).length} — นับตามการจัดประเภทของระบบ` },
    { tag: "no-arbiter", label: "ข้อจำกัด",
      text: "บรรทัดที่ติดป้าย tradition ไม่มีทางตรวจว่าตรงกับตัวเจ้าชะตาหรือไม่ ป้ายนี้ติดไว้ทุกบรรทัดเพราะคำเตือนท้ายหน้าไม่ติดไปกับข้อความที่ถูกคัดลอก" },
  ];

  return {
    lines,
    lagnaRasi,
    lagnaText: LAGNA_NATURE[lagnaRasi],
    lordNum,
    lordBhava: lord.bhava,
    lordText: LORD_IN_BHAVA[lord.bhava - 1],
    stelliums,
    beneficCount: placements.filter((p) => p.graha.benefic).length,
    maleficCount: placements.filter((p) => !p.graha.benefic).length,
    inLagna: byBhava.get(1) ?? [],
  };
}

/** Every line carries its own provenance tag, so an excerpt stays honest. */
export function renderReading(r: Reading): string {
  return r.lines
    .map((l) => `[${l.tag.padEnd(10)}] ${l.label.padEnd(10)} ${l.text}`)
    .join("\n");
}
