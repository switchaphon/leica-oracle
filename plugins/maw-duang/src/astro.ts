// Self-contained geocentric ephemeris. No dependencies, no network, no data files.
//
// Accuracy targets (1900–2050):
//   Sun    ~2"      Moon  ~30"      Mercury..Saturn ~1'      Uranus ~1'
//   Ascendant is exact given the inputs; its error is dominated by the birth time.
//
// Sources of the series: Meeus, Astronomical Algorithms 2e (ch. 22, 25, 47) and
// JPL SSD "Approximate Positions of the Planets" (elements valid 1800–2050).

const DEG = Math.PI / 180;
const norm360 = (x: number) => ((x % 360) + 360) % 360;
const sind = (d: number) => Math.sin(d * DEG);
const cosd = (d: number) => Math.cos(d * DEG);
const tand = (d: number) => Math.tan(d * DEG);

/** Julian Day from a UTC calendar date. Gregorian only — we never read charts before 1582. */
export function julianDay(y: number, m: number, d: number, hourUT: number): number {
  if (m <= 2) {
    y -= 1;
    m += 12;
  }
  const A = Math.floor(y / 100);
  const B = 2 - A + Math.floor(A / 4);
  return (
    Math.floor(365.25 * (y + 4716)) +
    Math.floor(30.6001 * (m + 1)) +
    d +
    hourUT / 24 +
    B -
    1524.5
  );
}

/**
 * TT − UT in seconds. Planets are computed in TT, sidereal time in UT; conflating
 * them costs ~0.3° of ascendant per 70s, which is a whole degree of lagna in 4 minutes.
 */
export function deltaTSeconds(year: number): number {
  const t = year - 2000;
  if (year >= 2005 && year < 2050) return 62.92 + 0.32217 * t + 0.005589 * t * t;
  if (year >= 1986 && year < 2005)
    return (
      63.86 +
      0.3345 * t -
      0.060374 * t * t +
      0.0017275 * t ** 3 +
      0.000651814 * t ** 4 +
      0.00002373599 * t ** 5
    );
  if (year >= 1961 && year < 1986) {
    const u = (year - 1975) / 1;
    return 45.45 + 1.067 * u - (u * u) / 260 - (u * u * u) / 718;
  }
  // Outside the well-fitted range the value is small next to our other error terms.
  return 64;
}

/** Mean obliquity of the ecliptic (Laskar), degrees. */
export function obliquity(T: number): number {
  const U = T / 100;
  return (
    23.43929111 -
    U * (4680.93 / 3600) -
    U ** 2 * (1.55 / 3600) +
    U ** 3 * (1999.25 / 3600) -
    U ** 4 * (51.38 / 3600) -
    U ** 5 * (249.67 / 3600)
  );
}

/** Nutation in longitude, degrees. Main terms only — the rest is below our noise floor. */
export function nutationLongitude(T: number): number {
  const om = 125.04452 - 1934.136261 * T;
  const Ls = 280.4665 + 36000.7698 * T;
  const Lm = 218.3165 + 481267.8813 * T;
  const arcsec =
    -17.2 * sind(om) - 1.32 * sind(2 * Ls) - 0.23 * sind(2 * Lm) + 0.21 * sind(2 * om);
  return arcsec / 3600;
}

/** Apparent geocentric ecliptic longitude of the Sun, degrees. */
export function sunLongitude(T: number): number {
  const L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  const M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  const C =
    (1.914602 - 0.004817 * T - 0.000014 * T * T) * sind(M) +
    (0.019993 - 0.000101 * T) * sind(2 * M) +
    0.000289 * sind(3 * M);
  const trueLong = L0 + C;
  // Aberration + the nutation shared by every body.
  const om = 125.04 - 1934.136 * T;
  return norm360(trueLong - 0.00569 - 0.00478 * sind(om));
}

// Meeus table 47.A, the terms that matter at our tolerance. [D, M, M', F, coefficient×1e-6 deg]
const MOON_TERMS: [number, number, number, number, number][] = [
  [0, 0, 1, 0, 6288774], [2, 0, -1, 0, 1274027], [2, 0, 0, 0, 658314],
  [0, 0, 2, 0, 213618], [0, 1, 0, 0, -185116], [0, 0, 0, 2, -114332],
  [2, 0, -2, 0, 58793], [2, -1, -1, 0, 57066], [2, 0, 1, 0, 53322],
  [2, -1, 0, 0, 45758], [0, 1, -1, 0, -40923], [1, 0, 0, 0, -34720],
  [0, 1, 1, 0, -30383], [2, 0, 0, -2, 15327], [0, 0, 1, 2, -12528],
  [0, 0, 1, -2, 10980], [4, 0, -1, 0, 10675], [0, 0, 3, 0, 10034],
  [4, 0, -2, 0, 8548], [2, 1, -1, 0, -7888], [2, 1, 0, 0, -6766],
  [1, 0, -1, 0, -5163], [1, 1, 0, 0, 4987], [2, -1, 1, 0, 4036],
  [2, 0, 2, 0, 3994], [4, 0, 0, 0, 3861], [2, 0, -3, 0, 3665],
  [0, 1, -2, 0, -2689], [2, 0, -1, 2, -2602], [2, -1, -2, 0, 2390],
  [1, 0, 1, 0, -2348], [2, -2, 0, 0, 2236], [0, 1, 2, 0, -2120],
  [0, 2, 0, 0, -2069], [2, -2, -1, 0, 2048],
];

/** Apparent geocentric ecliptic longitude of the Moon, degrees. */
export function moonLongitude(T: number): number {
  const Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T * T + T ** 3 / 538841;
  const D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T * T + T ** 3 / 545868;
  const M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T * T;
  const Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T * T + T ** 3 / 69699;
  const F = 93.272095 + 483202.0175233 * T - 0.0036539 * T * T - T ** 3 / 3526000;
  const E = 1 - 0.002516 * T - 0.0000074 * T * T;

  let sigma = 0;
  for (const [cD, cM, cMp, cF, coef] of MOON_TERMS) {
    const arg = cD * D + cM * M + cMp * Mp + cF * F;
    // Terms in the solar anomaly shrink as Earth's eccentricity does.
    const damp = cM === 0 ? 1 : Math.abs(cM) === 1 ? E : E * E;
    sigma += coef * damp * sind(arg);
  }
  return norm360(Lp + sigma / 1e6 + nutationLongitude(T));
}

/** Mean ascending lunar node (Rahu), degrees. Retrograde by construction. */
export function rahuLongitude(T: number): number {
  return norm360(
    125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + T ** 3 / 467441 - T ** 4 / 60616000
  );
}

// JPL approximate elements, valid 1800–2050. Row 1 = value at J2000, row 2 = rate per century.
// [a, e, I, L, longPeri, longNode]
type Elem = [number, number, number, number, number, number];
const PLANETS: Record<string, { e0: Elem; rate: Elem }> = {
  mercury: {
    e0: [0.38709927, 0.20563593, 7.00497902, 252.2503235, 77.45779628, 48.33076593],
    rate: [0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081],
  },
  venus: {
    e0: [0.72333566, 0.00677672, 3.39467605, 181.9790995, 131.60246718, 76.67984255],
    rate: [0.0000039, -0.00004107, -0.0007889, 58517.81538729, 0.00268329, -0.27769418],
  },
  earth: {
    e0: [1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0],
    rate: [0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0],
  },
  mars: {
    e0: [1.52371034, 0.0933941, 1.84969142, -4.55343205, -23.94362959, 49.55953891],
    rate: [0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343],
  },
  jupiter: {
    e0: [5.202887, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909],
    rate: [-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106],
  },
  saturn: {
    e0: [9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448],
    rate: [-0.0012506, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794],
  },
  uranus: {
    e0: [19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.9542763, 74.01692503],
    rate: [-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589],
  },
};

type Vec3 = [number, number, number];

/** Heliocentric ecliptic rectangular coordinates in AU. */
function heliocentric(name: string, T: number): Vec3 {
  const p = PLANETS[name];
  const [a, e, I, L, wbar, Om] = p.e0.map((v, i) => v + p.rate[i] * T) as Elem;

  const omega = wbar - Om;
  let M = norm360(L - wbar);
  if (M > 180) M -= 360;

  // Kepler's equation, Newton–Raphson in degrees.
  const eStar = (180 / Math.PI) * e;
  let E = M + eStar * sind(M);
  for (let i = 0; i < 12; i++) {
    const dM = M - (E - eStar * sind(E));
    const dE = dM / (1 - e * cosd(E));
    E += dE;
    if (Math.abs(dE) < 1e-10) break;
  }

  const xp = a * (cosd(E) - e);
  const yp = a * Math.sqrt(1 - e * e) * sind(E);

  const cw = cosd(omega), sw = sind(omega);
  const cO = cosd(Om), sO = sind(Om);
  const cI = cosd(I), sI = sind(I);

  return [
    (cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp,
    (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp,
    sw * sI * xp + cw * sI * yp,
  ];
}

const LIGHT_DAYS_PER_AU = 0.0057755183;

/**
 * General precession in longitude since J2000, degrees.
 *
 * The JPL elements above are referred to the ecliptic and equinox of **J2000**.
 * sunLongitude/moonLongitude/rahuLongitude are all referred to the equinox **of date**.
 * Mixing the two frames leaves the planets trailing everything else by ~0.37° in 2026 —
 * which is 22', enough to move a conjunction by a day and a half. Everything must be
 * expressed in one frame before anything is subtracted from anything.
 */
export function precessionSinceJ2000(T: number): number {
  return (5029.0966 * T + 1.11161 * T * T - 0.000006 * T * T * T) / 3600;
}

/** Apparent geocentric ecliptic longitude of a planet, degrees, equinox of date. */
export function planetLongitude(name: string, T: number): number {
  const earth = heliocentric("earth", T);
  let body = heliocentric(name, T);

  // One light-time iteration: we see where it was, not where it is.
  for (let i = 0; i < 2; i++) {
    const dx = body[0] - earth[0], dy = body[1] - earth[1], dz = body[2] - earth[2];
    const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
    body = heliocentric(name, T - (dist * LIGHT_DAYS_PER_AU) / 36525);
  }

  const x = body[0] - earth[0];
  const y = body[1] - earth[1];
  const lonJ2000 = (Math.atan2(y, x) * 180) / Math.PI;
  return norm360(lonJ2000 + precessionSinceJ2000(T) + nutationLongitude(T));
}

/**
 * The Sun's geocentric longitude derived from the PLANETARY code path
 * (Earth's heliocentric direction, reversed). Exists so a test can hold it against
 * sunLongitude(), which comes from an entirely separate series. The two paths must
 * agree; when they do not, the frames have drifted apart.
 */
export function sunLongitudeViaElements(T: number): number {
  const e = heliocentric("earth", T);
  const lonJ2000 = (Math.atan2(e[1], e[0]) * 180) / Math.PI;
  return norm360(lonJ2000 + 180 + precessionSinceJ2000(T) + nutationLongitude(T));
}

/** Greenwich mean sidereal time in degrees, from JD(UT). */
export function gmst(jdUT: number): number {
  const T = (jdUT - 2451545.0) / 36525;
  return norm360(
    280.46061837 +
      360.98564736629 * (jdUT - 2451545.0) +
      0.000387933 * T * T -
      (T * T * T) / 38710000
  );
}

/**
 * Tropical ascendant in degrees — the ecliptic degree rising on the eastern horizon.
 * lstDeg is local sidereal time (RAMC) in degrees; latitude in degrees north.
 */
export function ascendant(lstDeg: number, latDeg: number, eps: number): number {
  const y = -cosd(lstDeg);
  const x = sind(lstDeg) * cosd(eps) + tand(latDeg) * sind(eps);
  return norm360((Math.atan2(y, x) * 180) / Math.PI + 180);
}

export { norm360 };
