"""Verbs by day per team (mean effective actions), idle breakdown, watering coverage, hire caps and hour-0 funding."""
import sys, collections
from common import *

rec, ours, rep = load()
rows = rec + ours
G = collections.defaultdict(list)
for r in rows:
    G[(team_of(r), r['d'])].append(r)
teams = TEAMS + ['T7']
CATS = ['water', 'harv', 'feed', 'care', 'cfert', 'plant', 'fertz', 'pick', 'drop', 'place', 'build', 'dig']

print('== verbs by day: mean effective actions (days 0-16)')
for t in teams:
    print('\n' + t)
    print('day ' + ''.join('%7s' % c for c in CATS) + '   tiles  anim  hires')
    for d in range(17):
        rs = G.get((t, d), [])
        if not rs: continue
        vc = collections.Counter()
        for r in rs: vc.update(verbcats(r['ops']))
        n = len(rs)
        print('%3d ' % d + ''.join('%7.1f' % (vc[c] / n) for c in CATS) +
              '  %6.1f %5.1f %6.1f' % (mean([ntiles(r) for r in rs]), mean([nanim(r) for r in rs]), mean([r['hires'] for r in rs])))

print('\n== idle breakdown per unit-turn (%): pass+noact / fail(no-op verbs) / unsent (hands with no action sent)')
print('day ' + ''.join('%16s' % t for t in teams))
for d in range(17):
    line = '%3d ' % d
    for t in teams:
        rs = G.get((t, d), [])
        L = [labour(r) for r in rs]
        ut = sum(x['ut'] for x in L)
        line += '   %4.1f/%4.1f/%4.1f' % (100 * sum(x['pas'] for x in L) / ut, 100 * sum(x['fail'] for x in L) / ut,
                                         100 * sum(max(0, x['unsent']) for x in L) / ut)
    print(line)

print('\n== watering coverage: WATER ops / crop tiles at h0 (%)')
print('day ' + ''.join('%7s' % t for t in teams))
for d in range(1, 17):
    line = '%3d ' % d
    for t in teams:
        rs = G.get((t, d), [])
        w = sum(verbcats(r['ops'])['water'] for r in rs); p = sum(verbcats(r['ops'])['plant'] for r in rs)
        tl = sum(ntiles(r) for r in rs)
        line += ' %6.0f' % (100 * (w - p) / max(1, tl))
    print(line)

print('\n== hires distribution days 6-16 (% of seat-days): <=8 / 9-10 / 11-12 / 13+ ; max')
for t in teams:
    hs = [r['hires'] for d in range(6, 17) for r in G.get((t, d), [])]
    n = len(hs)
    print('%5s  %5.1f %5.1f %5.1f %5.1f  max %d' % (t, 100 * sum(h <= 8 for h in hs) / n, 100 * sum(9 <= h <= 10 for h in hs) / n,
                                                 100 * sum(11 <= h <= 12 for h in hs) / n, 100 * sum(h >= 13 for h in hs) / n, max(hs)))

print('\n== hour-0 funding: share of seat-days where the hour-0 hires cost more than m0 (sells at h0 fund them), days 1-10')
print('day ' + ''.join('%7s' % t for t in teams))
for d in range(1, 11):
    line = '%3d ' % d
    for t in teams:
        rs = G.get((t, d), [])
        k = 0
        for r in rs:
            n0 = sum(1 for h in r['hire_h'] if h == 0)
            if fib_sum(n0) > (r['m0'] or 0) + 1e-9: k += 1
        line += ' %6.0f' % (100 * k / max(1, len(rs)))
    print(line)
print('\n== hires at hour 0 / hour 1 / hour 2+ (mean per seat-day)')
print('day ' + ''.join('%16s' % t for t in teams))
for d in range(0, 17):
    line = '%3d ' % d
    for t in teams:
        rs = G.get((t, d), [])
        a = mean([sum(h == 0 for h in r['hire_h']) for r in rs]); b = mean([sum(h == 1 for h in r['hire_h']) for r in rs])
        c = mean([sum(h >= 2 for h in r['hire_h']) for r in rs])
        line += '   %4.1f/%4.1f/%4.1f' % (a, b, c)
    print(line)
print('\n== hour-0 market orders used (hires at h0 + distinct non-hire fills at h0), mean; share of seat-days at 10')
print('day ' + ''.join('%12s' % t for t in teams))
for d in range(0, 17):
    line = '%3d ' % d
    for t in teams:
        rs = G.get((t, d), [])
        u = []
        for r in rs:
            n0 = sum(1 for h in r['hire_h'] if h == 0)
            nf = sum(1 for f in (r['fills'] or []) if f[0] == 0 and f[1] not in ('H',))
            u.append(n0 + nf)
        line += '   %4.1f/%3.0f%%' % (mean(u), 100 * sum(x >= 10 for x in u) / max(1, len(u)))
    print(line)
