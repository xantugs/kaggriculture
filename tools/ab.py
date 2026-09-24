"""Parallel A/B of parameter variants against a fixed opponent.  usage: ab.py '{"name": {params}, ...}' [-n seeds] [--opp X]"""
import sys, json, argparse, statistics, multiprocessing as mp
def work(job):
    name, params, opp, seed, path = job
    from harness import run_match
    env, rew, st = run_match((path, params), opp, seed)
    return name, seed, rew[0], rew[1]
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("variants"); ap.add_argument("-n", type=int, default=6)
    ap.add_argument("--opp", default="starter"); ap.add_argument("--seed0", type=int, default=200); ap.add_argument("--path", default="main.py")
    a = ap.parse_args(); variants = json.loads(a.variants)
    jobs = [(nm, p, a.opp, s, a.path) for nm, p in variants.items() for s in range(a.seed0, a.seed0 + a.n)]
    with mp.Pool(min(len(jobs), mp.cpu_count())) as pool: res = pool.map(work, jobs)
    for nm in variants:
        v = [r[2] for r in res if r[0] == nm]; o = [r[3] for r in res if r[0] == nm]
        print(f"{nm:28s} mean ${statistics.mean(v):9,.0f}  min ${min(v):9,.0f}  max ${max(v):9,.0f}  sd {statistics.pstdev(v):7,.0f} | opp ${statistics.mean(o):8,.0f} | wins {sum(1 for x,y in zip(v,o) if x>y)}/{len(v)}")
