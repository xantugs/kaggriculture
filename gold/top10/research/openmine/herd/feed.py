"""Feeding, care, fertilizer collection, escapes and herd income per team by day window.
feed rate = FEED ops / placed animal-days (herd at hour 0 + placed that day), wheat sources: own harvest (hv), bought (BP),
wheat sold; herd income = sells of EGG/MILK/WOOL/FERTILIZER."""
import collections
from lib import *

rows = load(role={'rec', 'ours', 'elite_rep'})
G = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec':
        if late(r):
            G[SHORT[r['team']]].append(r)
    elif r['role'] == 'ours':
        G['T7'].append(r)
order = ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']
WIN = [(0, 3), (4, 7), (8, 11), (12, 15), (16, 22), (23, 29)]


def s_(day, k, i=0):
    v = day['sell'].get(k)
    return v[i] if v else 0


def bp_(day, k, i=0):
    v = day['bp'].get(k)
    return v[i] if v else 0


print('== per-seat totals by window; feed%/care%/coll% = ops per placed animal-day; esc = animals lost')
for g in order:
    rs = G[g]
    print('---', g, len(rs))
    for a0, a1 in WIN:
        ad = feed = care = coll = esc = 0
        wh_h = wh_b = wh_bd = wh_s = wh_sd = wpl = 0
        inc = collections.Counter()
        for r in rs:
            D = r['days']
            for d in range(a0, a1 + 1):
                day = D[d]
                n_an = sum(day['herd'].get(a, 0) for a in AN)
                ad += n_an
                feed += sum(day['feed'].values())
                care += sum(day['care'].values())
                coll += sum(day['coll'].values())
                if d < 29:
                    nxt = D[d + 1]
                    for a in AN:
                        lost = day['herd'].get(a, 0) + day['placed'][a] - nxt['herd'].get(a, 0)
                        esc += max(0, lost)
                wh_h += day['hv'].get('WHEAT', 0)
                wh_b += bp_(day, 'WHEAT'); wh_bd += bp_(day, 'WHEAT', 1)
                wh_s += s_(day, 'WHEAT'); wh_sd += s_(day, 'WHEAT', 1)
                wpl += day['plant_wheat']
                for p in ('EGG', 'MILK', 'WOOL', 'FERTILIZER'):
                    inc[p] += s_(day, p, 1)
                inc['FERTbuy'] += bp_(day, 'FERTILIZER', 1)
        n = len(rs)
        print('  d%2d-%2d anim-days %5.1f feed %4.0f%% care %4.0f%% coll %4.0f%% esc %.2f | wheat plant %5.1f harv %5.1f buy %5.1f ($%4.0f) sell %5.1f ($%4.0f) feed %5.1f | $ egg %5.0f milk %5.0f wool %5.0f fert %5.0f (fert bought $%4.0f)' % (
            a0, a1, ad / n, 100 * feed / max(ad, 1), 100 * care / max(ad, 1), 100 * coll / max(ad, 1), esc / n,
            wpl / n, wh_h / n, wh_b / n, wh_bd / n, wh_s / n, wh_sd / n, feed / n,
            inc['EGG'] / n, inc['MILK'] / n, inc['WOOL'] / n, inc['FERTILIZER'] / n, inc['FERTbuy'] / n))
