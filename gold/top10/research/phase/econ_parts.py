"""Econ-valuation gap us - elite at the start of day D split into parts: cash, goods by product, animals by kind (going
concern net of feed), standing crops by crop (pooled realized output x future price), seeds.
usage: econ_parts.py rows.jsonl[,more] 'TeamA|TeamB' D1,D2,..."""
import sys, os, json, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gapday_ana as A
paths, teams, days = sys.argv[1], sys.argv[2], [int(d) for d in sys.argv[3].split(',')]
tt = teams.split('|')
rows = [x for p in paths.split(',') for x in A.load(p) if teams == 'ALL' or any(x['team'].startswith(t) for t in tt)]
rate, per_plant = A.pooled_rates(rows)
n = len(rows)


def parts(x, side, D, P):
    s = x[side][D]['s']; out = collections.Counter()
    out['cash'] = s['money']
    for k, v in list(s['shed'].items()) + list(s.get('inv', {}).items()):
        if k in P: out['goods'] += v * P[k]
    for k, (a, u) in s['an'].items(): out['goods'] += u * P[A.AN[k][1]]
    an_p, land_p = A.purchases(x, side)
    for k, (cost, prod, fy) in A.AN.items():
        cnt = s['an'].get(k, [0, 0])[0]
        bought = sorted([d for d, kk in an_p if kk == k and d < D], reverse=True)
        for i in range(cnt):
            d0 = bought[i] if i < len(bought) else 0
            first_day = max(D, d0 + fy)
            out['an_' + k] += rate[k] * max(0, 29 - first_day) * P[prod] - (29 - D) * P['WHEAT']
    for crop, (cnt, u) in s['pl'].items():
        seed, fy, my, ong = A.CROPS[crop]
        ages = s['ages'].get(crop, {})
        if ong:
            out['goods'] += u * P[crop]
            first, iv, npr = A.ONG_LIFE[crop]
            for a, c in ages.items():
                a = int(a); done = 0 if a < first else min(npr, (a - first) // iv + 1)
                out['pl_' + crop] += c * per_plant[crop] * (npr - done) / npr * P[crop]
        else:
            for a, c in ages.items():
                out['pl_' + crop] += c * per_plant[crop] * P[crop]
    out['seeds'] = sum(v * A.CROPS[k][0] for k, v in s.get('seeds', {}).items() if k in A.CROPS)
    out['quads'] = len(s['quads'])
    return out


print('%d seats (%s); econ gap parts us - elite per seat' % (n, teams))
for D in days:
    tot = collections.Counter()
    for x in rows:
        P = {p: A.fut_price(x, min(D, 29), p) for p in A.PRODS}
        u = parts(x, 'days_us', D, P); e = parts(x, 'days_elite', D, P)
        for k in set(u) | set(e): tot[k] += (u[k] - e[k]) / n
    q = tot.pop('quads')
    print('day %2d total %+6.0f | ' % (D, sum(tot.values())) + '  '.join('%s %+.0f' % (k, v) for k, v in sorted(tot.items(), key=lambda kv: -abs(kv[1])) if abs(v) >= 100) + '  | quads %+.2f' % q)
