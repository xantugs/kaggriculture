import collections, sys
from harness import run_match
seed = int(sys.argv[1]); day = int(sys.argv[2]); path = sys.argv[3] if len(sys.argv) > 3 else "main.py"
env, rew, st = run_match(path, "starter", seed)
per = collections.defaultdict(collections.Counter)
for h in range(24):
    s = day * 24 + h
    a = env.steps[s + 1][0].action
    for i, x in enumerate([a["farmer"]] + a["hands"]):
        k = x[0] if x[0] not in ("NORTH", "SOUTH", "EAST", "WEST") else "MOVE"
        per[i][k] += 1
tot = collections.Counter()
print(f"day {day}: per-unit action mix")
for i in sorted(per):
    c = per[i]; tot.update(c)
    print(f"  u{i:2d}: move={c['MOVE']:2d} pass={c['PASS']:2d} pick={c['PICKUP']} drop={c['DROP']+c['PLACE']} feed={c['FEED']:2d} care={c['CARE']:2d} coll={c['COLLECT_FERTILIZER']:2d} harv={c['HARVEST']:2d} water={c['WATER']:2d} plant={c['PLANT']} fert={c['FERTILIZE']} dig={c['DIG']} build={c['BUILD_COOP']+c['BUILD_PASTURE']}")
print("TOTAL", dict(tot))
o = env.steps[day * 24 + 12][0].observation; f = o.farms[0]
print("map at noon (K/G/S animals, w/c/m/s/t crops, x weed, . empty, o/p empty structure):")
def g(t):
    if t is None: return "."
    if t == "LOCKED": return "#"
    k = t.get("kind")
    if k == "WEED": return "x"
    if k == "PLANT": return t["crop"][0].lower()
    if t.get("animal"): return {"GOOSE": "G", "COW": "K", "SHEEP": "S"}[t["animal"]]
    return "o" if k == "COOP" else "p"
for y in range(10): print("    " + " ".join(g(t) for t in f["tiles"][y]))
