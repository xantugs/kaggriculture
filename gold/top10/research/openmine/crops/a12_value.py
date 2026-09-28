"""Unit economics per tile by cohort: units/tile, fertilizer applications/tile, waters+harvests/tile (labour), and the
gross value of the harvested units at the team's own average strawberry/tomato/wheat sale price on the harvest day.
usage: a12_value.py"""
import os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); OM = os.path.dirname(HERE)
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}
ORDER = ['Boey', 'FQ', 'CBF', 'TFC', 'Yiz', 'T7']
# price by (group, item, day): the group's own average sale price that day (fallback: the all-group mean)
P = collections.defaultdict(lambda: [0, 0.0])
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    for line in open(os.path.join(OM, fn), encoding='utf-8'):
        r = json.loads(line)
        if role == 'rec' and r['date'] < '2026-09-23': continue
        g = AB[r['team']]
        for it in ('STRAWBERRY', 'TOMATO', 'WHEAT', 'MELON', 'CARROT'):
            s = (r.get('sell') or {}).get(it)
            if s:
                for k in ((g, it, r['d']), ('*', it, r['d'])):
                    P[k][0] += s[0]; P[k][1] += s[1]
def price(g, it, d):
    for k in ((g, it, d), ('*', it, d)):
        n, v = P[k]
        if n >= 20: return v / n
    n, v = P[('*', it, d)]
    return v / n if n else 0
SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
COH = [('STRAWBERRY', 0, 5), ('STRAWBERRY', 6, 7), ('STRAWBERRY', 8, 11), ('STRAWBERRY', 12, 15), ('MELON', 0, 0), ('MELON', 1, 3), ('MELON', 4, 9), ('MELON', 10, 15),
       ('TOMATO', 8, 15), ('WHEAT', 0, 0), ('WHEAT', 1, 5), ('WHEAT', 6, 9), ('WHEAT', 10, 15), ('CARROT', 8, 15)]
acc = collections.defaultdict(lambda: collections.defaultdict(float)); nseat = collections.Counter()
for fn in ('tiles_elite.jsonl', 'tiles_T7.jsonl'):
    for l in open(os.path.join(HERE, fn), encoding='utf-8'):
        r = json.loads(l)
        if r['role'] == 'elite_rep': continue
        g = AB[r['team']]; nseat[g] += 1
        for p in r['plantings']:
            for c, a, b in COH:
                if p[0] == c and a <= p[1] <= b:
                    A = acc[(g, c, a)]
                    A['n'] += 1; A['u'] += sum(h[2] for h in p[8]); A['f'] += len(p[7]); A['lab'] += 1 + len(p[6]) + len(p[8])
                    A['val'] += sum(h[2] * price(g, c, h[0]) for h in p[8])
                    A['days'] += ((p[10] if p[10] is not None else 30) - p[1])
                    A['hd'] += sum(h[0] * h[2] for h in p[8])
print('per tile: units | fertilizer uses | labour actions (plant+water+harvest) | tile-days held | unit-weighted harvest day |'
      ' gross $ at own sale price that day | net of seed | net $ per tile-day')
for c, a, b in COH:
    print(f'-- {c} planted d{a}-{b}')
    for g in ORDER:
        A = acc[(g, c, a)]
        if not A['n']: continue
        n = A['n']
        net = (A['val'] - SEED[c] * n) / n
        print(f'   {g:5s} tiles/seat {n/nseat[g]:5.1f} | {A["u"]/n:4.2f}u | fert {A["f"]/n:4.2f} | lab {A["lab"]/n:5.1f} | days {A["days"]/n:4.1f} |'
              f' hday {A["hd"]/max(1,A["u"]):4.1f} | ${A["val"]/n:6.0f} | net ${net:6.0f} | ${net/max(0.1,A["days"]/n):4.0f}/tile-day')
