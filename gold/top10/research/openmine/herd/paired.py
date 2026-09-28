"""T7 vs the recorded elite seat of the same game (same town, same shop sequence): herd by day, herd-product revenue,
feed wheat bought, by opponent team. Also T7 vs the repaired elite it actually played (elite_rep)."""
import collections
from lib import *

rows = load()
rec = {(r['gid'], r['seat']): r for r in rows if r['role'] == 'rec'}
rep = {r['gid']: r for r in rows if r['role'] == 'elite_rep'}
ours = [r for r in rows if r['role'] == 'ours']
PR = ('FERTILIZER', 'EGG', 'MILK', 'WOOL')


def rev(r, a0, a1, p):
    return sum((r['days'][d]['sell'].get(p) or [0, 0])[1] for d in range(a0, a1 + 1))


def fbuy(r, a0, a1):
    return sum((r['days'][d]['bp'].get('FERTILIZER') or [0, 0])[1] for d in range(a0, a1 + 1))


def herdv(r, d):
    o = owned(r['days'][d])
    return tuple(o.get(a, 0) for a in AN)


def wheat_net(r, a0, a1):
    b = sum((r['days'][d]['bp'].get('WHEAT') or [0, 0])[1] for d in range(a0, a1 + 1))
    s = sum((r['days'][d]['sell'].get('WHEAT') or [0, 0])[1] for d in range(a0, a1 + 1))
    return b - s


by = collections.defaultdict(list)
for o in ours:
    e = rec.get((o['gid'], o['elite_seat']))
    p = rep.get(o['gid'])
    if e is None:
        continue
    t = SHORT[e['team']]
    by[t].append((o, e, p))
    by['ALL'].append((o, e, p))

for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'ALL']:
    L = by[t]
    print('=====', t, len(L), 'T7 wins %.0f%%, margin vs rep %.0f' % (100 * mean(o['rew'][0] > o['rew'][1] for o, e, p in L), mean(o['m'] for o, e, p in L)))
    for d in (3, 6, 9, 12, 16):
        print('  d%-2d herd G/C/S  T7 %4.1f/%4.1f/%4.1f  rec %4.1f/%4.1f/%4.1f  rep %4.1f/%4.1f/%4.1f' % ((d,) + tuple(mean(herdv(o, d)[i] for o, e, p in L) for i in range(3))
              + tuple(mean(herdv(e, d)[i] for o, e, p in L) for i in range(3)) + tuple(mean(herdv(p, d)[i] for o, e, p in L) for i in range(3))))
    for a0, a1 in ((0, 7), (8, 15), (16, 29)):
        s = []
        for pr in PR:
            s.append('%s %5.0f/%5.0f/%5.0f' % (pr[:4], mean(rev(o, a0, a1, pr) for o, e, p in L), mean(rev(e, a0, a1, pr) for o, e, p in L), mean(rev(p, a0, a1, pr) for o, e, p in L)))
        s.append('fertbuy %4.0f/%4.0f/%4.0f' % (mean(fbuy(o, a0, a1) for o, e, p in L), mean(fbuy(e, a0, a1) for o, e, p in L), mean(fbuy(p, a0, a1) for o, e, p in L)))
        s.append('wheat net buy %5.0f/%5.0f/%5.0f' % (mean(wheat_net(o, a0, a1) for o, e, p in L), mean(wheat_net(e, a0, a1) for o, e, p in L), mean(wheat_net(p, a0, a1) for o, e, p in L)))
        print('  d%d-%d rev T7/rec/rep: ' % (a0, a1) + '  '.join(s))
