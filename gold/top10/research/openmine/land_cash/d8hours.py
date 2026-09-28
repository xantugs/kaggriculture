"""Day 8 (and 9) hour of first milk sale, of the SW buy and of the first animal buy; T7 vs elite (23-26 Sep)."""
import collections
from common import load, by_team, SHORT, TEAMS, pairs
S = load()
g = by_team(S, 'rec'); g['T7'] = [p[0] for p in pairs(S)]
def med(xs):
    xs = sorted(xs); return xs[len(xs)//2] if xs else None
for d in (8, 9):
    print('== day %d: median hour of first MILK sale / first WOOL sale / SW buy / first animal buy; units milk sold; share buying animals' % d)
    for t in TEAMS + ['T7']:
        mh, wh, sh, ah, mu, anyA = [], [], [], [], [], 0
        for s in g[t]:
            f = s['days'][d].get('fills') or []
            x = [h for h, op, it, n, v in f if op == 'S' and it == 'MILK']
            if x: mh.append(min(x))
            x = [h for h, op, it, n, v in f if op == 'S' and it == 'WOOL']
            if x: wh.append(min(x))
            x = [h for h, op, it, n, v in f if op == 'L' and it == 'SW']
            if x: sh.append(min(x))
            x = [h for h, op, it, n, v in f if op == 'BA']
            if x: ah.append(min(x)); anyA += 1
            mu.append(sum(n for h, op, it, n, v in f if op == 'S' and it == 'MILK'))
        n = len(g[t])
        print('  %-5s milk h%s (%3.0f%% of seats, %.1f units) | wool h%s | SW h%s (%3.0f%%) | animal h%s (%3.0f%%)' % (
            SHORT[t], med(mh), 100*len(mh)/n, sum(mu)/n, med(wh), med(sh), 100*len(sh)/n, med(ah), 100*anyA/n))
