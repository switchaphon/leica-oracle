"""Registry audit of api-v3's waterlevel_load: duplicates, datums, placeholders.

Every figure quoted to rpro-ent-oracle on 2026-09-04 comes from this file. It
exists because that night produced eight retractions, and two of them were not
wrong numbers but UNRECOVERABLE ones - figures that lived only in a message and
could not be argued with because they could not be re-derived. A wrong number
gets corrected; an unrecoverable one can only be abandoned.

Three findings, in the order they should be acted on:

  1 PLACEHOLDER. ground_level == 0 means "unknown", not "sea level". Any depth
    computed on those rows silently returns raw MSL - up to 508 m presented as a
    water depth. Only the rows that happen to be duplicated are exposed; the rest
    have nothing to contradict them.

  2 DUPLICATES. The feed returns rows, not stations. Deduplicate on COORDINATE,
    never on the ridhydro_ prefix: 370 ridhydro_ rows are the sole occupant of
    their coordinate and prefix-dropping deletes them.

  3 REGISTRY DISAGREEMENT. Some duplicated coordinates carry two different
    ground_level values, so "depth" depends on which row was drawn.

Two screening lessons are built in, both learned by getting them wrong first:

  - Screen on DEPTH, not on msl. A registry fault leaves msl nearly identical
    while destroying depth, so an msl screen cannot see it by construction.
  - Screen the placeholder BEFORE computing depth, or the depth screen itself
    manufactures faults: where one row has ground 0, the pair's depth difference
    is simply the other row's ground level.

Usage:  python3 audit_registry.py
"""
import json
import urllib.request
from collections import defaultdict, Counter

V3 = "https://api-v3.thaiwater.net/api/v1/thaiwater30/public/waterlevel_load"


def rows():
    with urllib.request.urlopen(V3, timeout=90) as r:
        payload = json.load(r)
    for value in payload.values():
        if isinstance(value, dict) and isinstance(value.get("data"), list) and len(value["data"]) > 1000:
            return value["data"]
    raise SystemExit("waterlevel_load: no data block over 1000 rows")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def code(r):
    return str((r.get("station") or {}).get("tele_station_oldcode") or "")


def coord(r):
    st = r.get("station") or {}
    try:
        return (round(float(st["tele_station_lat"]), 6),
                round(float(st["tele_station_long"]), 6))
    except (TypeError, ValueError, KeyError):
        return None


def ground(r):
    return num((r.get("station") or {}).get("ground_level"))


def msl(r):
    return num(r.get("waterlevel_msl"))


def main():
    data = rows()
    by = defaultdict(list)
    for r in data:
        c = coord(r)
        if c:
            by[c].append(r)
    dups = {k: v for k, v in by.items() if len(v) > 1}

    print(f"rows {len(data)}   distinct coordinates {len(by)}   duplicated {len(dups)}")

    # --- 1 placeholder, first because it invalidates the depth screen ---
    zeros = [r for r in data if ground(r) == 0.0]
    in_dup = [r for r in zeros if len(by[coord(r)]) > 1]
    solo = [r for r in zeros if len(by[coord(r)]) == 1]
    rid_z = [r for r in zeros if code(r).startswith("ridhydro_")]
    rid_all = [r for r in data if code(r).startswith("ridhydro_")]
    print()
    print(f"[1] ground_level == 0 (placeholder, NOT an elevation): {len(zeros)} of {len(data)}")
    print(f"    exposed by duplication : {len(in_dup)}")
    print(f"    single rows, invisible : {len(solo)}   <- depth silently equals raw MSL")
    print(f"    ridhydro_ path : {len(rid_z)}/{len(rid_all)}   other: "
          f"{len(zeros) - len(rid_z)}/{len(data) - len(rid_all)}")
    worst = sorted(solo, key=lambda r: -(msl(r) or 0))[:3]
    for r in worst:
        print(f"    would report depth {msl(r)} m at {code(r)}")

    # --- 2 duplicates ---
    rid_on_dup = sum(1 for v in dups.values() for r in v if code(r).startswith("ridhydro_"))
    print()
    print(f"[2] ridhydro_ rows {len(rid_all)}: {rid_on_dup} on a duplicated coordinate, "
          f"{len(rid_all) - rid_on_dup} sole occupant")
    print(f"    dedup on COORDINATE. Dropping the prefix deletes "
          f"{len(rid_all) - rid_on_dup} stations that exist under no other name.")

    # --- 3 registry disagreement, placeholder rows excluded ---
    msl_big = depth_big = manufactured = genuine = depth_and_msl = 0
    biggest = []
    for v in dups.values():
        if len(v) != 2:
            continue
        a, b = v
        ma, mb, ga, gb = msl(a), msl(b), ground(a), ground(b)
        if None in (ma, mb, ga, gb):
            continue
        if abs(ma - mb) > 1:
            msl_big += 1
        if abs((ma - ga) - (mb - gb)) > 1:
            depth_big += 1
            # Attribute by WHICH TERM carries the fault, not by "is a ground zero".
            # A pair can have a placeholder ground and still disagree genuinely on
            # msl (X.119: grounds 0.0 / 0.21, msl 4.35 / 3.14). Classifying on the
            # zero alone mislabels those as artefacts.
            if (ga == 0.0 or gb == 0.0) and abs(ma - mb) <= 1:
                manufactured += 1        # depth gap comes from the null, not the water
            else:
                genuine += 1
                biggest.append((abs(ga - gb), code(a), ga, gb))
            if abs(ma - mb) > 1:
                depth_and_msl += 1
    print()
    # Two different splits of the same depth_big exist and are NOT the same
    # partition - one by cause, one by which screen sees it. Printed as a 2x2 so
    # they cannot be read as one fact.
    print(f"[3] duplicate pairs over 1 m: msl screen {msl_big}, DEPTH screen {depth_big}")
    print(f"    the {depth_big} depth faults, by cause and by what the msl screen sees:")
    print(f"      {'':13}{'msl-visible':>12}{'msl-blind':>11}{'total':>8}")
    print(f"      {'placeholder':13}{0:>12}{manufactured:>11}{manufactured:>8}")
    print(f"      {'genuine':13}{depth_and_msl:>12}{genuine - depth_and_msl:>11}{genuine:>8}")
    print(f"      {'total':13}{depth_and_msl:>12}{depth_big - depth_and_msl:>11}{depth_big:>8}")
    for d, c, ga, gb in sorted(biggest, reverse=True)[:5]:
        print(f"    {c:12} ground {ga} vs {gb}   {d:.3f} m apart")


if __name__ == "__main__":
    main()
