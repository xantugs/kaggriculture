"""OLS of the day's hires on the day's workload, per team (days 2-16):
   A) on hour-0 state: crop tiles, placed animals, animals waiting in the shed, same-day plantings+builds (the plan)
   B) on the day's effective actions (eff)  -> actions per extra hand
Reports coefficients, R^2, and the share of seat-days predicted within +-1 hire."""
import collections
from common import *

rec, ours, rep = load()
rows = rec + ours
teams = TEAMS + ['T7']


def feats(r):
    ops = r['ops'] or {}
    plant = sum(v for k, v in ops.items() if k.startswith('PLANT'))
    build = sum(v for k, v in ops.items() if k.startswith('BUILD'))
    water = sum(v for k, v in ops.items() if k.startswith('WATER'))
    shedanim = sum((r['shed'] or {}).get(a, 0) for a in ('GOOSE', 'COW', 'SHEEP'))
    return [1.0, ntiles(r), nanim(r), shedanim, plant + build, water]


for lo, hi in ((2, 16), (6, 16)):
    print('\n== days %d-%d' % (lo, hi))
    print('team      n   const  tiles  anim  shedA  plant+bld | R2  within1 || B: hires = a + eff/k : a      k    R2  within1')
    for t in teams:
        X = []; y = []; E = []
        for r in rows:
            if team_of(r) != t or not (lo <= r['d'] <= hi): continue
            f = feats(r); X.append(f[:5]); y.append(r['hires']); E.append(labour(r)['eff'])
        b = lstsq(X, y); p = predict(X, b); R2 = r2(y, p)
        w1 = mean([abs(round(a) - c) <= 1 for a, c in zip(p, y)])
        XB = [[1.0, e] for e in E]
        bb = lstsq(XB, y); pb = predict(XB, bb); r2b = r2(y, pb)
        w1b = mean([abs(round(a) - c) <= 1 for a, c in zip(pb, y)])
        print('%5s %6d  %6.2f %6.3f %5.3f %6.3f %6.3f   | %4.2f  %3.0f%%   ||  %6.2f %6.1f  %4.2f  %3.0f%%' % (
            t, len(y), b[0], b[1], b[2], b[3], b[4], R2, 100 * w1, bb[0], 1 / bb[1], r2b, 100 * w1b))

# pooled elite (FQ, Boey, TFC) model on days 2-16, applied to T7's own state -> hires T7 "should" run on its own farm
print('\n== pooled FQ+Boey+TFC model (days 2-16) applied to T7 farms: predicted vs actual T7 hires by day')
X = []; y = []
for r in rows:
    if team_of(r) in ('FQ', 'Boey', 'TFC') and 2 <= r['d'] <= 16:
        X.append(feats(r)[:5]); y.append(r['hires'])
b = lstsq(X, [float(v) for v in y])
print('coef const %.2f tiles %.3f anim %.3f shedA %.3f plant+build %.3f' % tuple(b))
G = collections.defaultdict(list)
for r in rows:
    if team_of(r) == 'T7' and 2 <= r['d'] <= 16:
        G[r['d']].append((sum(a * c for a, c in zip(feats(r)[:5], b)), r['hires']))
print('day  pred  actual')
for d in sorted(G):
    print('%3d  %5.1f  %5.1f' % (d, mean([a for a, _ in G[d]]), mean([c for _, c in G[d]])))
