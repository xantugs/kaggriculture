"""Each variant (params on main.py) plays the champion file, both seats.  usage: sweep.py champion.py '{"name": {...}}' -n 3"""
import sys, json, argparse, statistics
from harness import run_match
ap = argparse.ArgumentParser(); ap.add_argument("champ"); ap.add_argument("variants"); ap.add_argument("-n", type=int, default=3); ap.add_argument("--seed0", type=int, default=400)
a = ap.parse_args(); V = json.loads(a.variants)
for nm, p in V.items():
    res = []
    for seed in range(a.seed0, a.seed0 + a.n):
        for seat in (0, 1):
            specs = [("main.py", p), (a.champ, {})]
            if seat: specs.reverse()
            env, rew, st = run_match(specs[0], specs[1], seed)
            res.append((rew[seat], rew[1 - seat]))
    w = sum(1 for x, y in res if x > y)
    print(f"{nm:26s} wins {w}/{len(res)} | me ${statistics.mean(x for x,_ in res):8,.0f} vs champ ${statistics.mean(y for _,y in res):8,.0f} | margin ${statistics.mean(x-y for x,y in res):+9,.0f}", flush=True)
