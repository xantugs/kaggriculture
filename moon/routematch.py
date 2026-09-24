"""Fraction of each elite team's recorded actions that equal our chassis route tape (best route per game), by phase.
usage: routematch.py [teams]"""
import sys, os, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean
A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'))
R = A.__globals__['_ROUTES']
PH = [(0, 144), (144, 360), (360, 504), (504, 720)]
def norm(a):
    if not isinstance(a, dict): return None
    return (tuple(a.get('farmer') or ['PASS']), tuple(tuple(h) for h in (a.get('hands') or [])))
def score(acts, p, tape, lo, hi):
    n = s = 0
    for t in range(lo, min(hi, len(acts) - 1, len(tape))):
        a = acts[t + 1][p] if t + 1 < len(acts) else None   # replay step t+1 holds the action taken at t
        if a is None: continue
        n += 1; s += norm(a) == norm(tape[t])
    return s / max(1, n)
res = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(HERE, 'elite', 'games_*.jsonl'))):
    for line in open(f, encoding='utf-8'):
        d = json.loads(line); n = d['info']['TeamNames']
        if not n: continue
        for p in (0, 1):
            best = max(R, key=lambda k: score(d['acts'], p, R[k], 0, 144))
            res[n[p]].append([score(d['acts'], p, R[best], lo, hi) for lo, hi in PH])
for t, xs in sorted(res.items(), key=lambda kv: -len(kv[1])):
    m = [sum(x[i] for x in xs) / len(xs) for i in range(4)]
    print(f"{t[:24]:24s} n {len(xs):4d}  match d0-5 {m[0]:.2f}  d6-14 {m[1]:.2f}  d15-20 {m[2]:.2f}  d21-29 {m[3]:.2f}")
