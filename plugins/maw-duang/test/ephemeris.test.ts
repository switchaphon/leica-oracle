// Positive controls for the ephemeris.
//
// Every case here has a correct answer that exists INDEPENDENTLY of this code:
// equinoxes and solstices are *defined* as the Sun's tropical longitude hitting
// 0/90/180/270, and the lunar case is Meeus' own published worked example.
//
// A test that only compares the engine against itself would pass just as happily
// with the arithmetic inverted. These cannot.

import { expect, test, describe } from "bun:test";
import {
  julianDay, deltaTSeconds, sunLongitude, moonLongitude, gmst, ascendant, obliquity, norm360,
  sunLongitudeViaElements, precessionSinceJ2000, planetLongitude,
} from "../src/astro";
import { lahiriAyanamsa, rasiOf, bhavaOf, RASI, RASI_LORD } from "../src/thai";
import {
  kalaYoka, chulasakarat, WEEKDAY_TH, thaksa, THAKSA_WHEEL, dithi, yamOf, dignity, nakshatraOf, reukOf,
} from "../src/siam";
import { dwell, contactBaseRate, competingClaims, houseSweep, convergentYears } from "../src/weigh";
import { computeChart } from "../src/index";

/** Julian centuries TT from a UTC calendar moment. */
const centuriesTT = (y: number, m: number, d: number, h: number) =>
  (julianDay(y, m, d, h) + deltaTSeconds(y) / 86400 - 2451545.0) / 36525;

/** Signed separation in arcminutes, shortest way round the circle. */
const arcminErr = (got: number, want: number) => {
  let e = got - want;
  if (e > 180) e -= 360;
  if (e < -180) e += 360;
  return e * 60;
};

describe("solar theory — checked against the definition of the seasons", () => {
  // The instants are the published ones; each is good to about a minute, and the Sun
  // moves 2.5'/hour, so anything under ~1' of residual is the timestamp, not the code.
  const cardinals: [string, number, number, number, number, number][] = [
    ["2026 March equinox",    2026,  3, 20, 14 + 46 / 60,   0],
    ["2026 June solstice",    2026,  6, 21,  8 + 25 / 60,  90],
    ["2026 September equinox",2026,  9, 23,  0 +  6 / 60, 180],
    ["2026 December solstice",2026, 12, 21, 20 + 50 / 60, 270],
    ["2000 March equinox",    2000,  3, 20,  7 + 35 / 60,   0],
  ];

  for (const [label, y, m, d, h, want] of cardinals) {
    test(`${label}: Sun is at ${want}°`, () => {
      const err = arcminErr(sunLongitude(centuriesTT(y, m, d, h)), want);
      expect(Math.abs(err)).toBeLessThan(1.0); // arcminutes
    });
  }
});

describe("lunar theory — checked against Meeus' published worked example", () => {
  test("Example 47.a: 1992 April 12, 0h TD", () => {
    // Astronomical Algorithms 2e, ch.47: apparent lambda = 133.167265 deg
    const got = moonLongitude(-0.077221081451);
    expect(Math.abs(arcminErr(got, 133.167265))).toBeLessThan(1.0);
  });
});

describe("frame consistency — the control that was missing, and cost a wrong accusation", () => {
  // The Sun's geocentric longitude can be reached two completely separate ways:
  // Meeus' solar series, or Earth's heliocentric position from the JPL elements + 180.
  // Both must land on the same degree. They did not, because the solar series is
  // referred to the equinox OF DATE and the JPL elements to J2000 — so the planets
  // trailed the Sun by the accumulated precession. Every planet was wrong by ~22'
  // in 2026 and nothing in the old suite could see it, because every old test
  // checked the Sun, the Moon or GMST — never a planet against an outside fact.
  for (const [label, y, m, d] of [
    ["1987 (before J2000)", 1987, 9, 7],
    ["2000 (at J2000)", 2000, 1, 1],
    ["2026 (after J2000)", 2026, 8, 6],
  ] as [string, number, number, number][]) {
    test(`${label}: both paths to the Sun agree`, () => {
      const T = centuriesTT(y, m, d, 12);
      expect(Math.abs(arcminErr(sunLongitudeViaElements(T), sunLongitude(T)))).toBeLessThan(2.0);
    });
  }

  test("precession is ~0.37 deg by 2026 and negative before J2000", () => {
    expect(precessionSinceJ2000(0.266)).toBeCloseTo(0.3716, 3);
    expect(precessionSinceJ2000(-0.123)).toBeLessThan(0);
  });
});

describe("sidereal time", () => {
  test("GMST at J2000.0 is 280.46061837 deg", () => {
    expect(gmst(2451545.0)).toBeCloseTo(280.46061837, 4);
  });
});

describe("ayanamsa", () => {
  test("Lahiri is ~23.85 deg at J2000 and grows ~1.4 deg per century", () => {
    expect(lahiriAyanamsa(0)).toBeCloseTo(23.853, 2);
    expect(lahiriAyanamsa(1) - lahiriAyanamsa(0)).toBeCloseTo(1.396, 2);
  });

  test("2026 sits near 24.2 deg — the value Thai practice quotes as 'about 24'", () => {
    const T = (julianDay(2026, 8, 7, 12) - 2451545.0) / 36525;
    expect(lahiriAyanamsa(T)).toBeGreaterThan(24.0);
    expect(lahiriAyanamsa(T)).toBeLessThan(24.5);
  });
});

describe("the nirayana shift is the whole difference between the two systems", () => {
  test("2026-08-07: tropical Sun in Leo, sidereal Sun in Cancer", () => {
    const T = centuriesTT(2026, 8, 7, 12);
    const trop = sunLongitude(T);
    const sid = norm360(trop - lahiriAyanamsa(T));
    expect(RASI[rasiOf(trop)]).toBe("สิงห์");  // Leo
    expect(RASI[rasiOf(sid)]).toBe("กรกฎ");   // Cancer — one whole sign earlier
  });
});

describe("ascendant", () => {
  test("with the vernal point on the meridian at the equator, lagna is 90 deg", () => {
    // RAMC = 0 puts 0 Aries on the MC; the rising degree is then the solstitial point.
    expect(ascendant(0, 0, obliquity(0))).toBeCloseTo(90, 6);
  });

  test("lagna advances through all twelve signs over one sidereal day", () => {
    const seen = new Set<number>();
    for (let lst = 0; lst < 360; lst += 1) seen.add(rasiOf(ascendant(lst, 13.7563, obliquity(0))));
    expect(seen.size).toBe(12);
  });
});

describe("กาลโยค — checked against a published จุลศักราช year", () => {
  // จ.ศ. 1387 (16 Apr 2025 – 15 Apr 2026) is published as:
  //   ธงชัย=ศุกร์  อธิบดี=ศุกร์  อุบาทว์=พฤหัสบดี  โลกาวินาศ=อาทิตย์
  // Four independent formulas, four independent published answers. Nothing here is
  // compared against my own arithmetic.
  test("all four day-qualities reproduce for จ.ศ. 1387", () => {
    const k = kalaYoka(2025, 8, 1); // any date inside that Songkran year
    expect(k.chulasakarat).toBe(1387);
    expect(WEEKDAY_TH[k.thongchai]).toBe("ศุกร์");
    expect(WEEKDAY_TH[k.athibodi]).toBe("ศุกร์");
    expect(WEEKDAY_TH[k.ubat]).toBe("พฤหัสบดี");
    expect(WEEKDAY_TH[k.lokawinat]).toBe("อาทิตย์");
  });

  test("the จุลศักราช year turns at Songkran, not at New Year", () => {
    expect(chulasakarat(2026, 4, 15)).toBe(1387); // still the old year
    expect(chulasakarat(2026, 4, 16)).toBe(1388); // turned
    expect(chulasakarat(2026, 8, 6)).toBe(1388);  // the event day
  });
});

describe("ทักษา", () => {
  test("a Monday-born carries อาทิตย์ as กาลกิณี", () => {
    const t = thaksa(1);
    expect(t.byBhava["บริวาร"]).toBe(2); // จันทร์ at the start
    expect(t.kalakini).toBe(1);          // อาทิตย์ lands on กาลกิณี
  });

  test("the wheel is อ จ ภ ว ส ช ร ศ — เสาร์ before พฤหัส, not ๑..๘", () => {
    expect(THAKSA_WHEEL).toEqual([1, 2, 3, 4, 7, 5, 8, 6]);
  });

  test("every weekday assigns all eight grahas exactly once", () => {
    for (let wd = 0; wd < 7; wd++) {
      expect(new Set(Object.values(thaksa(wd).byBhava)).size).toBe(8);
    }
  });
});

describe("ดิถี and ยาม", () => {
  test("new moon is ขึ้น 1 ค่ำ, full moon is ขึ้น 15 ค่ำ", () => {
    expect(dithi(100, 100).kam).toBe(1);              // conjunction
    expect(dithi(100, 100 + 179).phase).toBe("ขึ้น"); // just short of opposition
    expect(dithi(100, 100 + 181).phase).toBe("แรม");  // just past it
  });

  test("watches are 1h30 from 06:00 and 18:00", () => {
    expect(yamOf(6)).toEqual({ half: "กลางวัน", n: 1 });
    expect(yamOf(17.9)).toEqual({ half: "กลางวัน", n: 8 });
    expect(yamOf(18)).toEqual({ half: "กลางคืน", n: 1 });
    expect(yamOf(19.5)).toEqual({ half: "กลางคืน", n: 2 });
  });
});

describe("มาตรฐานดาว", () => {
  test("มหาอุจ is a degree, not a sign — อุจ by sign alone is not มหาอุจ", () => {
    // พุธ exalts in กันย์ at 15°. Virgo starts at 150°.
    expect(dignity(4, 150 + 15, RASI_LORD).label).toBe("มหาอุจ");
    expect(dignity(4, 150 + 6.34, RASI_LORD).label).toBe("อุจ"); // 8.66° off the point
    expect(dignity(6, 150 + 5, RASI_LORD).label).toBe("นิจ");    // ศุกร์ falls in กันย์
  });
});

describe("whole-sign houses", () => {
  test("the lagna's own sign is bhava 1, and houses run forward from it", () => {
    const lagna = 200;                    // 20° ตุล (Libra spans 180–210)
    expect(bhavaOf(200, lagna)).toBe(1);
    expect(bhavaOf(205, lagna)).toBe(1);  // 25° Libra — same sign, still bhava 1
    expect(bhavaOf(185, lagna)).toBe(1);  // 5° Libra — BEHIND the lagna degree, still bhava 1
    expect(bhavaOf(215, lagna)).toBe(2);  // 5° Scorpio — next sign, next bhava
    expect(bhavaOf(170, lagna)).toBe(12); // 20° Virgo — previous sign wraps to 12
  });
});

describe("weighing a mechanism — the checks the 6 Aug case forced", () => {
  const base = { tz: 7, lat: 18.7883, lon: 98.9853 };
  const NATAL_LAGNA = 10; // กุมภ์

  test("the Moon is the only day-scale mechanism; the slow grahas are climate", () => {
    // Timescale of the mechanism must match timescale of the question. A condition
    // true for a year cannot explain one Thursday — including MY OWN second answer,
    // which leaned on the Sun in ภพ ๖ and is a 31-day condition.
    const moon = dwell(2, "2026-08-06", NATAL_LAGNA, base);
    expect(moon.daysHeld).toBeLessThanOrEqual(3);
    expect(moon.verdict).toBe("เฉพาะวัน");

    for (const slow of [5, 7, 9]) {           // พฤหัส, เสาร์, เกตุ
      expect(dwell(slow, "2026-08-06", NATAL_LAGNA, base).verdict).toBe("ภูมิอากาศ");
    }

    const sun = dwell(1, "2026-08-06", NATAL_LAGNA, base);
    expect(sun.daysHeld).toBeGreaterThan(14);  // my กาลกิณี argument was never day-scale
  });

  test("a sub-1° contact is near a coin flip, so it is not evidence on its own", () => {
    const br = contactBaseRate("2026-08-06", "18:00", base, { orbDeg: 1.0, samples: 24 });
    expect(br.rate).toBeGreaterThan(0.2);
    expect(br.rate).toBeLessThan(0.7);
  });

  test("the competing-claim scan reaches every occupied bhava, not just the question's", () => {
    const ev = computeChart({ date: "2026-08-06", time: "18:00", sidereal: true, ...base });
    const claims = competingClaims(ev, NATAL_LAGNA, 3);
    expect(claims.find((c) => c.isQuestion)?.bhava).toBe(3);
    // ภพ ๗ ปัตนิ — the spouse — is the house the real cause came from, and it is
    // occupied. Scanning only the question's house never surfaces it.
    expect(claims.some((c) => c.bhava === 7 && c.grahas.length > 0)).toBe(true);
  });
});

describe("BLIND-02 post-mortem — the significator, not the mechanism, was wrong", () => {
  const CM = { tz: 7, lat: 18.7883, lon: 98.9853 };
  const natal = computeChart({
    date: "1987-09-07", time: "18:33", tz: 7, lat: 14.6167, lon: 100.3333, sidereal: true,
  });
  const jupiterBhavaOn = (date: string) => {
    const c = computeChart({ date, time: "12:00", sidereal: true, ...CM });
    const j = c.placements.find((p) => p.graha.num === 5)!;
    return ((j.rasi - natal.lagna.rasi + 12) % 12) + 1;
  };

  test("Jupiter's house at each real event — the instrument worked 3/3", () => {
    expect(jupiterBhavaOn("2018-08-15")).toBe(9);   // entered master's — I named ๙  ✓
    expect(jupiterBhavaOn("2020-08-15")).toBe(11);  // finished       — I named ๑๐ ✗
    expect(jupiterBhavaOn("2024-08-15")).toBe(4);   // started PhD    — I named ๔  ✓
  });

  test("at graduation the house I chose was empty and the one I omitted was loaded", () => {
    const ev = computeChart({ date: "2020-08-15", time: "12:00", sidereal: true, ...CM });
    const sweep = houseSweep(ev, natal.lagna.rasi);
    const slow = (b: number) => sweep[b - 1].grahas.filter((g) => [5, 7, 8, 9].includes(g));

    expect(sweep[10].primary).toContain("ลาภ");  // ภพ ๑๑ is the house of attainment
    expect(slow(11).sort()).toEqual([5, 9]);      // พฤหัส + เกตุ both sitting in it
    expect(sweep[9].grahas).toHaveLength(0);      // ภพ ๑๐ — my pick — entirely empty
  });

  test("the sweep covers all twelve, because a shortlist is where the answer was lost", () => {
    const ev = computeChart({ date: "2020-08-15", time: "12:00", sidereal: true, ...CM });
    expect(houseSweep(ev, natal.lagna.rasi)).toHaveLength(12);
  });
});

describe("convergence — adopted from Atom and Ting, and measurably better than mine", () => {
  const CM = { tz: 7, lat: 18.7883, lon: 98.9853 };
  const natal = computeChart({
    date: "1987-09-07", time: "18:33", tz: 7, lat: 14.6167, lon: 100.3333, sidereal: true,
  });

  test("requiring two independent mechanisms collapses the base rate", () => {
    const loose = convergentYears([4, 12], 2010, 2026, natal.lagna.rasi, CM, 1);
    const tight = convergentYears([4, 12], 2010, 2026, natal.lagna.rasi, CM, 2);

    expect(loose.baseRate).toBeGreaterThan(0.4);   // ~47% — explains nothing
    expect(tight.baseRate).toBeLessThan(0.1);      // ~6%  — actually discriminating
    expect(tight.years).toHaveLength(1);
    expect(tight.years[0].year).toBe(2020);
    expect(tight.years[0].count).toBeGreaterThanOrEqual(3); // พฤหัส + เสาร์ + ราหู
  });
});

describe("JPL Horizons — the external planetary control I should have had from the start", () => {
  // Apparent geocentric ecliptic longitude of date, geocentre (500@399),
  // 2026-08-06 12:00 UT, fetched from ssd.jpl.nasa.gov/api/horizons.api.
  // Frozen here as fixtures so the suite stays offline and deterministic.
  //
  // Every earlier control in this file tests the Sun, the Moon or sidereal time.
  // Not one tested a PLANET against an outside authority — which is precisely where
  // the J2000-frame bug lived, undetected, while 21 tests passed. The idea to check
  // against Horizons came from mahamodo-engine, who published their own bound first.
  const JPL: Record<string, number> = {
    mercury: 115.3815775,
    venus:   179.6963245,
    mars:     86.7665682,
    jupiter: 128.1778582,
    saturn:   14.6529740,
  };
  const T = centuriesTT(2026, 8, 6, 12);

  test("no planet is off by more than 5 arcmin — and the frame fix is confirmed", () => {
    // Before the precession fix every one of these was ~22' out. Passing at this
    // tolerance is independent proof the frame is now right.
    for (const body of Object.keys(JPL)) {
      expect(Math.abs(arcminErr(planetLongitude(body, T), JPL[body]))).toBeLessThan(5);
    }
  });

  test("the inner planets and Jupiter hold under 1.5 arcmin", () => {
    for (const body of ["mercury", "venus", "mars", "jupiter"]) {
      expect(Math.abs(arcminErr(planetLongitude(body, T), JPL[body]))).toBeLessThan(1.5);
    }
  });

  test("Saturn is the weakest body and its error is declared, not hidden", () => {
    // 4.5' — three times worse than anything else here, and outside the 0.04°
    // bound mahamodo declared for their engine. Within JPL's stated tolerance for
    // the approximate elements, but it is a real limit and the page says so.
    const e = Math.abs(arcminErr(planetLongitude("saturn", T), JPL.saturn));
    expect(e).toBeGreaterThan(2);
    expect(e).toBeLessThan(6);
  });
});

describe("สุริยยาตร์ vs modern ephemeris — the fork, measured", () => {
  // maw-suriyayart implemented the traditional คัมภีร์สุริยยาตร์ against Eade (2000)
  // and printed 1910/1948 calendars, and published these for 1987-09-07:
  const SURIYAYART = { sun: 4 * 30 + 24.33, moon: 10 * 30 + 22.73 };

  const natal = computeChart({
    date: "1987-09-07", time: "18:33", tz: 7, lat: 14.6167, lon: 100.3333, sidereal: true,
  });
  const lon = (n: number) => natal.placements.find((p) => p.graha.num === n)!.lon;

  test("the two systems differ by DEGREES, not by the arcminutes we spent the day arguing over", () => {
    expect(SURIYAYART.sun - lon(1)).toBeGreaterThan(3);   // ~3.7°
    expect(SURIYAYART.moon - lon(2)).toBeGreaterThan(5);  // ~5.9°
  });

  test("the gap is not a different ayanamsa — it is a different algorithm", () => {
    // If สุริยยาตร์ were merely modern positions minus some other ayanamsa, the value
    // implied by the Sun and by the Moon would agree. They differ by more than 2°,
    // so no single constant reconciles the two systems.
    const trop = computeChart({
      date: "1987-09-07", time: "18:33", tz: 7, lat: 14.6167, lon: 100.3333, sidereal: false,
    });
    const tl = (n: number) => trop.placements.find((p) => p.graha.num === n)!.lon;
    const impliedFromSun = tl(1) - SURIYAYART.sun;
    const impliedFromMoon = tl(2) - SURIYAYART.moon;
    expect(Math.abs(impliedFromSun - impliedFromMoon)).toBeGreaterThan(2);
  });

  test("it lands on a different ฤกษ์ — which seeds the whole dasha chain", () => {
    expect(nakshatraOf(lon(2))).not.toBe(nakshatraOf(SURIYAYART.moon));
  });

  test("but both systems agree on ดิถี — a real convergence, worth as much as the gaps", () => {
    const mine = dithi(lon(1), lon(2));
    expect(mine.phase).toBe("ขึ้น");
    expect(mine.kam).toBe(15);
  });
});

describe("cross-validated against mawdo's reference chapters", () => {
  // mawdo published nine chapters tracing their engine back to the original
  // program. Their derivations are independent of mine — different source, different
  // route — so agreement is worth more than my own tests agreeing with each other.
  // This is the layer I twice named as my weakest, so it is the layer that most
  // needed an outside check.

  test("ฤกษ์ 27→9 folding is identical for all 27, formula traced to the original", () => {
    const theirs = (n: number) => ((((n - 1) % 27) % 9 + 9) % 9) + 1;
    for (let n = 1; n <= 27; n++) expect(reukOf(n)).toBe(theirs(n));
  });

  test("one ฤกษ์ spans 800 arcmin — 13°20' exactly", () => {
    expect((360 / 27) * 60).toBeCloseTo(800, 9);
  });

  test("กาลโยค formulas match theirs symbolically, not just on one year", () => {
    // theirs: ธงชัย = cs×10+3 · อธิบดี = cs mod 498 · อุบาทว์ = cs×10+2
    const day = (r: number) => (r === 0 ? 7 : r) - 1;
    for (let cs = 1300; cs <= 1400; cs++) {
      const k = kalaYoka(cs + 638, 8, 1);
      expect(k.chulasakarat).toBe(cs);
      expect(k.thongchai).toBe(day((cs * 10 + 3) % 7));
      expect(k.athibodi).toBe(day((cs % 498) % 7));
      expect(k.ubat).toBe(day((cs * 10 + 2) % 7));
    }
  });

  test("กาลกิณี is the graha one step BEFORE the birth-day graha on the wheel", () => {
    // Their rule, stated differently from mine — I walk forward to the 8th position.
    // The two phrasings must agree on every weekday, and they do.
    for (let wd = 0; wd < 7; wd++) {
      const i = THAKSA_WHEEL.indexOf([1, 2, 3, 4, 5, 6, 7][wd]);
      expect(thaksa(wd).kalakini).toBe(THAKSA_WHEEL[(i - 1 + 8) % 8]);
    }
  });

  test("Lahiri agrees with their recovered value to about an arcsecond", () => {
    // Their reference epoch 2001-02-03 04:05 +07 gives 23.868723°.
    const T = (julianDay(2001, 2, 2, 21 + 5 / 60) - 2451545.0) / 36525;
    expect(Math.abs(lahiriAyanamsa(T) - 23.868723) * 3600).toBeLessThan(3);
  });
});

describe("1782 — the engine outside its nominal range, checked rather than assumed", () => {
  // Casting a ดวงเมือง means working centuries before the JPL elements' 1800–2050
  // window. Rather than assume the Sun and Moon still hold there, I asked Horizons.
  // Values below are from ssd.jpl.nasa.gov for 1782-04-21 00:12 UT, geocentre.
  const JPL_1782 = { sun: 30.9800980, moon: 122.6046645 };
  const T = centuriesTT(1782, 4, 21, 12 / 60);

  test("Sun and Moon still agree with JPL in 1782", () => {
    expect(Math.abs(arcminErr(sunLongitude(T), JPL_1782.sun))).toBeLessThan(0.5);
    expect(Math.abs(arcminErr(moonLongitude(T), JPL_1782.moon))).toBeLessThan(0.5);
  });

  test("historical ΔT is used, not the flat fallback", () => {
    // The fallback of 64s was wrong by ~48s for 1782 — 0.2° of lagna.
    expect(deltaTSeconds(1782)).toBeGreaterThan(10);
    expect(deltaTSeconds(1782)).toBeLessThan(25);
    expect(deltaTSeconds(1900)).toBeLessThan(0); // genuinely negative around 1900
  });

  test("ดิถี at the Bangkok founding moment is ๘, and JPL's own elongation agrees", () => {
    // A source summary gave ขึ้น ๑๐ ค่ำ. Both my engine and JPL give the 8th, so the
    // mismatch is in the record or its date conversion, not in the arithmetic.
    const elong = ((JPL_1782.moon - JPL_1782.sun) % 360 + 360) % 360;
    expect(Math.floor(elong / 12) + 1).toBe(8);
    expect(dithi(sunLongitude(T), moonLongitude(T)).kam).toBe(8);
  });
});
