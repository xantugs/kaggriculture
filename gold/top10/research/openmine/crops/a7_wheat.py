"""Wheat balance by day window (days 0..15): harvested units, FEED actions (1 wheat each), bought, sold; per team
(recorded 23-26 Sep) vs T7. Streams the day files. usage: a7_wheat.py"""
import os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}
WIN = [(0, 2), (3, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15)]
acc = collections.defaultdict(lambda: collections.defaultdict(float)); n = collections.Counter()
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    for line in open(os.path.join(OM, fn), encoding='utf-8'):
        r = json.loads(line)
        if role == 'rec' and r['date'] < '2026-09-23':
            continue
        if r['d'] > 15:
            continue
        g = AB[r['team']]
        if r['d'] == 0:
            n[g] += 1
        for a, b in WIN:
            if a <= r['d'] <= b:
                A = acc[g]
                A[(a, 'hv')] += (r.get('hv') or {}).get('WHEAT', 0)
                A[(a, 'feed')] += sum(v for k, v in (r.get('ops') or {}).items() if k.startswith('FEED'))
                A[(a, 'buy')] += ((r.get('buy_prod') or {}).get('WHEAT') or [0])[0]
                A[(a, 'sell')] += ((r.get('sell') or {}).get('WHEAT') or [0])[0]
                A[(a, 'plant')] += sum(v for k, v in (r.get('ops') or {}).items() if k.startswith('PLANT:WHEAT'))
                A[(a, 'fertW')] += sum(v for k, v in (r.get('ops') or {}).items() if k.startswith('FERTILIZE:WHEAT'))
                A[(a, 'fertS')] += sum(v for k, v in (r.get('ops') or {}).items() if k.startswith('FERTILIZE:STRAWBERRY'))
                A[(a, 'fertO')] += sum(v for k, v in (r.get('ops') or {}).items() if k.startswith('FERTILIZE:') and
                                       not k.startswith('FERTILIZE:WHEAT') and not k.startswith('FERTILIZE:STRAWBERRY'))
                A[(a, 'fsell')] += ((r.get('sell') or {}).get('FERTILIZER') or [0])[0]
                A[(a, 'fcoll')] += sum(v for k, v in (r.get('ops') or {}).items() if k.startswith('COLLECT_FERTILIZER'))
                A[(a, 'fbuy')] += ((r.get('buy_prod') or {}).get('FERTILIZER') or [0])[0]
print('per seat per window: wheat planted / harvested units / FEED / bought / sold | fertilizer collected / sold / bought '
      '/ used on wheat, strawberry, other crops')
for a, b in WIN:
    print(f'-- d{a}-{b}')
    for g in ['Boey', 'FQ', 'CBF', 'TFC', 'Yiz', 'T7']:
        A = acc[g]; k = n[g]
        print(f'   {g:5s} W plant {A[(a,"plant")]/k:5.1f} hv {A[(a,"hv")]/k:6.1f} feed {A[(a,"feed")]/k:6.1f} buy {A[(a,"buy")]/k:6.1f} '
              f'sell {A[(a,"sell")]/k:6.1f} | F coll {A[(a,"fcoll")]/k:5.1f} sell {A[(a,"fsell")]/k:5.1f} buy {A[(a,"fbuy")]/k:5.1f} '
              f'-> W {A[(a,"fertW")]/k:4.1f} S {A[(a,"fertS")]/k:4.1f} O {A[(a,"fertO")]/k:4.1f}')
