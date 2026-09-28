"""Crop money by day window: units sold, $ sold, average price, seed $ and product purchases (wheat) per seat; team
(recorded, 23-26 Sep) vs T7 and the elite in the T7 games (recorded rows of those games, for pairing).
usage: a4_revenue.py"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
CR = ('WHEAT', 'STRAWBERRY', 'MELON', 'TOMATO', 'CARROT')
WIN = [(0, 9), (10, 15), (16, 21), (22, 29), (0, 29)]
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}

t7 = [json.loads(l) for l in open(os.path.join(OM, 'ours_T7_seats.jsonl'), encoding='utf-8')]
t7_el = {(s['gid'], s['elite_seat']): AB[s['opp']] for s in t7}

acc = collections.defaultdict(lambda: collections.defaultdict(float))
nseat = collections.Counter()


def add(grp, r):
    d = r['d']
    for a, b in WIN:
        if a <= d <= b:
            for c in CR:
                s = (r.get('sell') or {}).get(c)
                if s:
                    acc[grp][(c, a, b, 'n')] += s[0]; acc[grp][(c, a, b, '$')] += s[1]
                bs = (r.get('buy_seed') or {}).get(c)
                if bs:
                    acc[grp][(c, a, b, 'seed')] += bs[1]
                bp = (r.get('buy_prod') or {}).get(c)
                if bp:
                    acc[grp][(c, a, b, 'bn')] += bp[0]; acc[grp][(c, a, b, 'b$')] += bp[1]
    if d == 0:
        nseat[grp] += 1


for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    with open(os.path.join(OM, fn), encoding='utf-8') as fh:
        for line in fh:
            r = json.loads(line)
            if role == 'rec':
                if r['date'] < '2026-09-23':
                    continue
                add(AB[r['team']], r)
                k = (r['gid'], r['seat'])
                if k in t7_el:
                    add('rec@T7:' + t7_el[k], r)
            else:
                add('T7', r)
                add('T7:' + AB[r['opp']], r)

groups = ['Boey', 'FQ', 'CBF', 'TFC', 'Yiz', 'T7']
for c in CR:
    print(f'\n== {c}: per seat  sold units / $ / avg price | seed $ | bought units ($)')
    for g in groups + [x for pair in (('rec@T7:' + a, 'T7:' + a) for a in ['Boey', 'FQ', 'CBF', 'TFC', 'Yiz']) for x in pair]:
        n = nseat[g]
        if not n:
            continue
        line = f'{g:12s} n{n:4d}'
        for a, b in WIN:
            u = acc[g][(c, a, b, 'n')] / n; s = acc[g][(c, a, b, '$')] / n
            p = s / u if u else 0
            line += f' | d{a}-{b}: {u:5.0f}u ${s:6.0f} @{p:4.0f} seed${acc[g][(c, a, b, "seed")]/n:4.0f} buy{acc[g][(c, a, b, "bn")]/n:4.0f}'
        print(line)
