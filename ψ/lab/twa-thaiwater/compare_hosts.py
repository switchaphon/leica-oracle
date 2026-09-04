"""Cross-host value comparison, the test rpro-ent is waiting on.

The coordinate join proved the two hosts share a station registry. It said
nothing about whether the same station reports the same VALUE, at the same
cadence, with the same freshness - and rain_today vs rain_24h on api-v3 already
showed that two feeds over one station set can disagree completely about whether
a station is even alive.

So: for stations matched across hosts, compare the reading and the timestamp.
"""
import json
import math
import urllib.request
from collections import Counter

KEY = "TPSXrHRvTHeVT2Lygq6YeTqqAm4xZ72x"


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())


v3raw = get("https://api-v3.thaiwater.net/api/v1/thaiwater30/public/waterlevel_load")
v3 = []
for r in v3raw["waterlevel_data"]["data"]:
    st = r.get("station") or {}
    try:
        v3.append({
            "la": float(st["tele_station_lat"]), "lo": float(st["tele_station_long"]),
            "name": (st.get("tele_station_name") or {}).get("th"),
            "msl": None if r.get("waterlevel_msl") in (None, "") else float(r["waterlevel_msl"]),
            "ts": r.get("waterlevel_datetime"),
        })
    except Exception:
        pass

twaraw = get("https://twa-api-public.thaiwater.net/v2/waterlevel",
             {"x-api-key": KEY, "Accept-Language": "th"})
tw = []
for fc in twaraw["data"].values():
    if not (isinstance(fc, dict) and "features" in fc):
        continue
    for f in fc["features"]:
        p = f["properties"]
        lo, la = f["geometry"]["coordinates"][:2]
        tw.append({
            "la": float(la), "lo": float(lo),
            "name": (p.get("station") or {}).get("station"),
            "msl": p.get("waterlevelMsl"),
            "ts": p.get("waterlevelDatetime"),
        })

# match on coordinates, the key that survived trap 9
index = {}
for v in v3:
    index.setdefault((round(v["la"], 4), round(v["lo"], 4)), v)

pairs = []
for t in tw:
    v = index.get((round(t["la"], 4), round(t["lo"], 4)))
    if v:
        pairs.append((t, v))

print(f"matched pairs compared: {len(pairs)}\n")

both_val = [(t, v) for t, v in pairs if t["msl"] is not None and v["msl"] is not None]
diffs = [abs(float(t["msl"]) - float(v["msl"])) for t, v in both_val]
exact = sum(1 for d in diffs if d < 1e-9)
mm = sum(1 for d in diffs if d < 0.001)
cm = sum(1 for d in diffs if d < 0.01)

print("VALUE  (waterlevel msl, both sides numeric)")
print(f"  comparable          {len(both_val)}")
print(f"  identical exactly   {exact}  ({100*exact/len(both_val):.1f}%)")
print(f"  agree within 1 mm   {mm}  ({100*mm/len(both_val):.1f}%)")
print(f"  agree within 1 cm   {cm}  ({100*cm/len(both_val):.1f}%)")
if diffs:
    ds = sorted(diffs)
    print(f"  median / p95 / max  {ds[len(ds)//2]:.4f} / {ds[int(len(ds)*.95)]:.4f} / {ds[-1]:.4f} m")

print("\nTIMESTAMP  (is the same station equally fresh on both hosts?)")
same_ts = 0
tw_newer = 0
v3_newer = 0
for t, v in pairs:
    a = (t["ts"] or "")[:16].replace("T", " ")
    b = (v["ts"] or "")[:16].replace("T", " ")
    if not a or not b:
        continue
    if a == b:
        same_ts += 1
    elif a > b:
        tw_newer += 1
    else:
        v3_newer += 1
tot = same_ts + tw_newer + v3_newer
print(f"  comparable          {tot}")
print(f"  identical timestamp {same_ts}  ({100*same_ts/tot:.1f}%)")
print(f"  twa fresher         {tw_newer}")
print(f"  api-v3 fresher      {v3_newer}")

print("\nCOVERAGE OF THE VALUE ITSELF")
print(f"  twa null msl        {sum(1 for t,_ in pairs if t['msl'] is None)}")
print(f"  api-v3 null msl     {sum(1 for _,v in pairs if v['msl'] is None)}")

worst = sorted(both_val, key=lambda p: -abs(float(p[0]["msl"]) - float(p[1]["msl"])))[:5]
print("\nlargest disagreements")
for t, v in worst:
    d = abs(float(t["msl"]) - float(v["msl"]))
    print(f"  {d:8.3f} m  {str(t['name'])[:30]:<30} twa {t['msl']} @ {(t['ts'] or '')[:16]}"
          f"   v3 {v['msl']} @ {(v['ts'] or '')[:16]}")
