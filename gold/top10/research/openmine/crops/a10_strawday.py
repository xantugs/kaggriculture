"""Strawberry (and wheat, tomato) units sold and average sale price by day (days 10..29), team (recorded 23-26 Sep)
vs T7; plus harvested units by day from the tile lifecycles. usage: a10_strawday.py"""
import os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); OM = os.path.dirname(HERE)
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}
ORDER = ['Boey', 'FQ', 'CBF', 'TFC', 'Yiz', 'T7']
S = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0.0])); N = collections.Counter()
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    for line in open(os.path.join(OM, fn), encoding='utf-8'):
        r = json.loads(line)
        if role == 'rec' and r['date'] < '2026-09-23':
            continue
        g = AB[r['team']]
        if r['d'] == 0: N[g] += 1
        for it in ('STRAWBERRY', 'TOMATO', 'MELON'):
            s = (r.get('sell') or {}).get(it)
            if s:
                S[(g, it)][r['d']][0] += s[0]; S[(g, it)][r['d']][1] += s[1]
H = collections.defaultdict(lambda: collections.Counter())
for fn in ('tiles_elite.jsonl', 'tiles_T7.jsonl'):
    for l in open(os.path.join(HERE, fn), encoding='utf-8'):
        r = json.loads(l)
        if r['role'] == 'elite_rep': continue
        g = AB[r['team']]
        for p in r['plantings']:
            if p[0] == 'STRAWBERRY':
                for h in p[8]:
                    H[g][h[0]] += h[2]
for it in ('STRAWBERRY', 'TOMATO', 'MELON'):
    print(f'\n== {it}: per seat per day  sold units @ avg price' + (' | harvested units' if it == 'STRAWBERRY' else ''))
    for d in range(10, 30):
        line = f'd{d:2d} '
        for g in ORDER:
            n, v = S[(g, it)][d]
            line += f'| {g:4s} {n/N[g]:5.1f} @{(v/n if n else 0):4.0f}' + (f' hv {H[g][d]/N[g]:5.1f} ' if it == 'STRAWBERRY' else '')
        print(line)
