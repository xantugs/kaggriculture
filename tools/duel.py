"""A vs B over seeds, both seats, params for each side.  usage: duel.py '{A params}' '{B params}' -n 4"""
import sys, json, argparse, statistics
from harness import run_match
ap = argparse.ArgumentParser(); ap.add_argument("pa"); ap.add_argument("pb"); ap.add_argument("-n", type=int, default=3)
ap.add_argument("--seed0", type=int, default=300); ap.add_argument("--patha", default="main.py"); ap.add_argument("--pathb", default="main.py")
a = ap.parse_args(); PA, PB = json.loads(a.pa), json.loads(a.pb)
res = []
for seed in range(a.seed0, a.seed0 + a.n):
    for seatA in (0, 1):
        specs = [(a.patha, PA), (a.pathb, PB)]
        if seatA == 1: specs.reverse()
        env, rew, st = run_match(specs[0], specs[1], seed)
        mA, mB = (rew[0], rew[1]) if seatA == 0 else (rew[1], rew[0])
        res.append((mA, mB)); print(f"  seed {seed} seatA={seatA}: A ${mA:9,.0f}  B ${mB:9,.0f}  {st}", flush=True)
w = sum(1 for x, y in res if x > y)
print(f"A mean ${statistics.mean(x for x,_ in res):,.0f} | B mean ${statistics.mean(y for _,y in res):,.0f} | A wins {w}/{len(res)}")
