"""Independently re-derive Trap 9's numbers before committing them under my name.

Checks the claims: 780 twa / 1,406 v3, zero without coordinates, 768 matched at
110 m, 12 unmatched, no v3 station claimed twice, max match distance ~0.1 m.
"""
import json
import math
import urllib.request

KEY = "TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x"


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


v3 = get("https://api-v3.thaiwater.net/api/v1/thaiwater30/public/waterlevel_load")
v3st = []
v3nocoord = 0
for r in v3["waterlevel_data"]["data"]:
    st = r.get("station") or {}
    try:
        v3st.append((float(st["tele_station_lat"]), float(st["tele_station_long"]),
                     st.get("tele_station_oldcode")))
    except Exception:
        v3nocoord += 1

twa = get("https://twa-api-public.thaiwater.net/v2/waterlevel",
          {"x-api-key": KEY, "Accept-Language": "th"})
tw = []
twnocoord = 0
for fc in twa["data"].values():
    if not (isinstance(fc, dict) and "features" in fc):
        continue
    for f in fc["features"]:
        try:
            lo, la = f["geometry"]["coordinates"][:2]
            tw.append((float(la), float(lo),
                       (f["properties"].get("station") or {}).get("station")))
        except Exception:
            twnocoord += 1

print(f"twa stations   {len(tw):>5}   without coordinates {twnocoord}")
print(f"v3  stations   {len(v3st):>5}   without coordinates {v3nocoord}")


def metres(a, b):
    dla = (a[0] - b[0]) * 111_320
    dlo = (a[1] - b[1]) * 111_320 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dla, dlo)


matched, unmatched, dists = 0, [], []
claimed = {}
for t in tw:
    best, bestd = None, 1e18
    for i, v in enumerate(v3st):
        if abs(t[0] - v[0]) > 0.002 or abs(t[1] - v[1]) > 0.002:
            continue
        d = metres(t, v)
        if d < bestd:
            best, bestd = i, d
    if best is not None and bestd <= 110:
        matched += 1
        dists.append(bestd)
        claimed[best] = claimed.get(best, 0) + 1
    else:
        unmatched.append(t)

dists.sort()
print(f"\nmatched at 110 m      {matched}  ({100*matched/len(tw):.1f}%)")
print(f"unmatched             {len(unmatched)}")
print(f"v3 claimed twice+     {sum(1 for c in claimed.values() if c > 1)}")
if dists:
    p90 = dists[int(len(dists) * 0.9)]
    print(f"distance med/p90/max  {dists[len(dists)//2]:.1f} / {p90:.1f} / {dists[-1]:.1f} m")
    print(f"within 10 m           {sum(1 for d in dists if d <= 10)} of {len(dists)}")
    print(f"same answer at 1 m    {sum(1 for d in dists if d <= 1)} matched")

print("\nthe unmatched twa stations:")
for t in unmatched:
    near = min(metres(t, v) for v in v3st) / 1000
    print(f"  {str(t[2])[:34]:<34} nearest v3 {near:6.2f} km")
