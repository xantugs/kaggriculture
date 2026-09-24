"""Run one match and print a daily digest of player A's farm + action mix."""
import sys, collections
from harness import run_match, load_agent
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("a"); ap.add_argument("b", nargs="?", default="starter")
ap.add_argument("--seed", type=int, default=100)
ap.add_argument("--days", type=int, default=30)
ap.add_argument("--turns", type=str, default="")   # e.g. "0:30" to dump per-turn actions
args = ap.parse_args()

env, rew, st = run_match(args.a, args.b, args.seed)
steps = env.steps
def glyph(t):
    if t is None: return "."
    if t == "LOCKED": return "#"
    k = t.get("kind")
    if k == "WEED": return "x"
    if k == "PLANT": return t["crop"][0].lower()
    if t.get("animal"): return {"GOOSE": "G", "COW": "K", "SHEEP": "S"}[t["animal"]]
    return "o" if k == "COOP" else "p"

if args.turns:
    lo, hi = [int(v) for v in args.turns.split(":")]
    for s in range(lo, hi):
        a = steps[s + 1][0].action
        o = steps[s][0].observation
        f = o.farms[0]
        print(f"t{s:3d} d{o.day} h{o.hour:2d} ${f['money']:7.0f} F@{f['farmer']} {a.get('farmer')} | hands={[(tuple(p), x) for p, x in zip(f['hands'], a.get('hands', []))]} | mkt={a.get('market')}")
        print("      shed=", {k: v for k, v in o.private['shed'].items() if v}, "seeds=", {k: v for k, v in o.private['seeds'].items() if v}, "inv=", o.private['inventories'])

act_mix = collections.Counter()
orders_day = collections.defaultdict(collections.Counter)
for s in range(len(steps) - 1):
    o = steps[s][0].observation
    a = steps[s + 1][0].action or {}
    for ua in [a.get("farmer")] + list(a.get("hands", [])):
        if ua: act_mix[(o.day, ua[0] if ua[0] not in ("NORTH","SOUTH","EAST","WEST") else "MOVE")] += 1
    for od in a.get("market", []) or []:
        if od[0] in ("BUY_ANIMAL", "BUY_PRODUCT"): orders_day[o.day][od[0][4:7] + ":" + od[1][:4]] += od[2]
        elif od[0] == "BUY_LAND": orders_day[o.day]["LAND"] += 1
    if o.hour == 23 or s == len(steps) - 2:
        if o.day >= args.days: continue
        f = o.farms[0]
        cnt = collections.Counter(glyph(t) for row in f["tiles"] for t in row)
        mix = {k[1]: v for k, v in act_mix.items() if k[0] == o.day}
        tot = sum(mix.values()) or 1
        useful = tot - mix.get("PASS", 0) - mix.get("MOVE", 0)
        print(f"day {o.day:2d} end: ${f['money']:8.0f} hands={len(f['hands']):2d} tiles={dict(cnt)} shops={len(o.town['unlocked_shops'])}"
              f" | turns={tot} act={useful} move={mix.get('MOVE',0)} pass={mix.get('PASS',0)} drop={mix.get('DROP',0)+mix.get('PLACE',0)} pick={mix.get('PICKUP',0)} | orders={dict(orders_day[o.day])}")
print("FINAL", rew, st)
print("prices:", steps[-1][0].observation.market["prices"])
