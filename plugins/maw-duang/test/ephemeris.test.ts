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
} from "../src/astro";
import { lahiriAyanamsa, rasiOf, bhavaOf, RASI } from "../src/thai";

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
