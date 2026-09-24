import sys, collections
from harness import run_match
pa, pb, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
env, rew, st = run_match(pa, pb, seed)
print(f"A={pa} ${rew[0]:,.0f}   B={pb} ${rew[1]:,.0f}")
wheat_buy = [0, 0]; hire_cost = [0.0, 0.0]; fibs = [1, 1]
while len(fibs) < 40: fibs.append(fibs[-1] + fibs[-2])
for d in range(30):
    for p in (0, 1):
        for h in range(24):
            s = d * 24 + h
            if s + 1 >= len(env.steps): continue
            act = env.steps[s + 1][p].action or {}
            for od in act.get("market", []):
                if od[0] == "BUY_PRODUCT" and od[1] == "WHEAT": wheat_buy[p] += od[2]
    if d in (4, 8, 10, 12, 15, 18, 21, 24, 27, 29):
        o = env.steps[d * 24 + 23][0].observation
        line = f"d{d:2d} "
        for p in (0, 1):
            f = o.farms[p]
            c = collections.Counter()
            for row in f["tiles"]:
                for t in row:
                    if isinstance(t, dict):
                        if t.get("animal"): c[{"GOOSE": "G", "COW": "K", "SHEEP": "S"}[t["animal"]]] += 1
                        elif t.get("kind") == "PLANT": c[t["crop"][0].lower()] += 1
                    elif t is None: c["."] += 1
            line += f"| {'AB'[p]} ${f['money']/1000:6.1f}k hands={len(f['hands']):2d} {dict(sorted(c.items()))} "
        pr = o.market["prices"]
        print(line + f"| W{pr['WHEAT']} E{pr['EGG']} M{pr['MILK']} Wo{pr['WOOL']} S{pr['STRAWBERRY']} Me{pr['MELON']} F{pr['FERTILIZER']}")
print("wheat bought (orders):", wheat_buy, " shops:", [s[:5] for s in env.steps[-1][0].observation.town["unlocked_shops"]])
