# maw-duang — แมวดวง

A Thai (นิรายนะ / sidereal) natal chart engine as a maw CLI plugin. No dependencies,
no network, no ephemeris data files — the sky is computed from series in the source.

```bash
maw duang 1987-09-07 18:33 --tz 7
maw duang 2026-08-07 19:00 --tz 7 --lat 18.7883 --lon 98.9853   # Chiang Mai
maw duang 2026-08-07 19:00 --json
```

## Why the header prints three lines before the chart

```
ระบบ     นิรายนะ (sidereal)
อายนางศ  24.2245°  (ลาหิรี (Lahiri))
ปฏิทิน   built-in (Meeus + JPL approximate elements)
```

Thai astrology reads a **sidereal** zodiac; Western astrology reads a **tropical** one.
The gap between them — the **ayanamsa** — is currently about **24°**, which is most of a
whole sign. The same birth moment therefore produces two different charts, and the Sun
lands in a different ราศี in each:

```
2026-08-07   tropical  ๑ อาทิตย์ 15°00' สิงห์
             sidereal  ๑ อาทิตย์ 20°47' กรกฎ     ← one whole sign earlier
```

There is a third choice underneath that one: Thai practice runs on either the traditional
**สุริยยาตร์** calculation or a modern astronomical ephemeris converted to sidereal, and
the two do not agree exactly. This engine is the second kind.

So: zodiac, ayanamsa, ephemeris. If a reading does not say which three it used, a
disagreement about the reading cannot be separated from a disagreement about the setup.
That is why the header is not optional and `--ayanamsa` exists to pin the value by hand.

## What it computes

- **10 grahas, ๐–๙** — ๑ อาทิตย์ ๒ จันทร์ ๓ อังคาร ๔ พุธ ๕ พฤหัสฯ ๖ ศุกร์ ๗ เสาร์ ๘ ราหู ๙ เกตุ ๐ มฤตยู
  (๘/๙ are the lunar nodes, not bodies; ๐ is Uranus, a modern addition)
- **ลัคนา** from local sidereal time and geographic latitude
- **ภพ ๑๒** whole-sign from the lagna's *sign* — not a 30° arc from the lagna *degree*
- direct/พักร์ (retrograde) per graha

## Accuracy, and how it is checked

`bun test` — every case has an answer that exists independently of this code:

| control | residual |
|---|---|
| Sun at 4 equinoxes/solstices (2026) + 2000 equinox | < 0.4′ |
| Moon vs Meeus *Astronomical Algorithms* example 47.a | 0.15′ |
| GMST at J2000.0 | exact to 4 dp |

Planets carry roughly 1′ from the JPL approximate elements — far inside the degree-level
resolution a chart is read at. Tests that only compared the engine to itself would pass
just as happily with the arithmetic inverted; these cannot.

## Install

```bash
maw plugin install plugins/maw-duang --root ~/.maw/plugins
```

`--root` is a filesystem path, not a tier name. Passing `--root extra` reports success and
silently writes `./extra/` into the current directory instead.

## Note for anyone porting this

maw-rs runs a TS plugin as `bun <entry> <args>`. Without the `import.meta.main` block at
the bottom of `src/index.ts`, the module defines its exports, exits 0, and prints nothing —
a silent no-op that is indistinguishable from success.
