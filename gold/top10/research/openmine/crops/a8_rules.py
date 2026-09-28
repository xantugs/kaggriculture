"""Rule compliance per seat (share of seats that follow each crop rule), per team (recorded 23-26 Sep) and T7, plus
per-seat distributions of the key counts. Uses crops/days.pkl (days 0..16 rows) and crops/tiles_*.jsonl.
usage: a8_rules.py"""
import sys, os, json, collections, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load import days
HERE = os.path.dirname(os.path.abspath(__file__))
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}
ORDER = ['Boey', 'FQ', 'CBF', 'TFC', 'Yiz', 'T7']
SB = {'BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET'}
TB = {'PIZZA_SHOP', 'FARMERS_MARKET'}
CB = {'PET_CAFE', 'FARMERS_MARKET'}
D = days()
TL = {}
for fn in ('tiles_elite.jsonl', 'tiles_T7.jsonl'):
    p = os.path.join(HERE, fn)
    if os.path.exists(p):
        for l in open(p, encoding='utf-8'):
            r = json.loads(l)
            if r['role'] != 'elite_rep':
                TL[(r['role'], r['gid'], r['seat'])] = r


def pl(rows, crop, a, b, Q=None):
    return sum(v for d in range(a, b + 1) for k, v in (rows[d]['ops'] or {}).items()
               if k.startswith('PLANT:' + crop + '@') and (Q is None or k.endswith('@' + Q)))


def nb(rows, d, S):
    return sum(1 for s in (rows[d]['shops'] or []) if s in S)


def landday(rows, q):
    for d in range(17):
        for e in rows[d]['land'] or []:
            if e['q'] == q:
                return d
    return None


seats = collections.defaultdict(list)
for key, rows in D['days'].items():
    role, gid, seat = key
    m = D['meta'][key]
    if role == 'rec' and m['date'] >= '2026-09-23':
        seats[AB[m['team']]].append((key, rows))
    elif role == 'ours':
        seats['T7'].append((key, rows))

feat = collections.defaultdict(list)
for g in ORDER:
    for key, rows in seats[g]:
        f = {}
        f['wheat_d0'] = pl(rows, 'WHEAT', 0, 0)
        f['melon_d0'] = pl(rows, 'MELON', 0, 0)
        f['melon_d0_3'] = pl(rows, 'MELON', 0, 3)
        f['straw_NW_d1_5'] = pl(rows, 'STRAWBERRY', 1, 5, 'NW')
        f['straw_NW_d1_4'] = pl(rows, 'STRAWBERRY', 1, 4, 'NW')
        f['wheat_NW_d1_5'] = pl(rows, 'WHEAT', 1, 5, 'NW')
        ne = landday(rows, 'NE'); sw = landday(rows, 'SW'); se = landday(rows, 'SE')
        f['ne_day'] = ne; f['sw_day'] = sw; f['se_day'] = se
        f['ne_straw'] = pl(rows, 'STRAWBERRY', ne, min(16, ne + 1), 'NE') if ne is not None else None
        f['ne_wheat'] = pl(rows, 'WHEAT', ne, min(16, ne + 1), 'NE') if ne is not None else None
        f['sb_ne'] = nb(rows, ne, SB) if ne is not None else None
        f['sw_wheat'] = pl(rows, 'WHEAT', sw, min(16, sw + 1), 'SW') if sw is not None else None
        f['sw_straw'] = pl(rows, 'STRAWBERRY', sw, min(16, sw + 3), 'SW') if sw is not None else None
        f['sb_sw'] = nb(rows, sw, SB) if sw is not None else None
        f['tom_9_15'] = pl(rows, 'TOMATO', 9, 15)
        f['tb9'] = nb(rows, 9, TB)
        f['car_8_15'] = pl(rows, 'CARROT', 8, 15)
        f['cb9'] = nb(rows, 9, CB)
        f['melon_10_15'] = pl(rows, 'MELON', 10, 15)
        f['wheat_tiles_d10'] = (rows[10]['crops'] or {}).get('WHEAT', 0)
        f['wheat_tiles_d12'] = (rows[12]['crops'] or {}).get('WHEAT', 0)
        f['straw_tiles_d12'] = (rows[12]['crops'] or {}).get('STRAWBERRY', 0)
        T = TL.get(key)
        if T:
            P = T['plantings']
            w = [p for p in P if p[0] == 'WHEAT' and p[1] <= 15 and p[8]]
            f['wheat_age_le3'] = sum(1 for p in w if p[8][0][0] - p[1] <= 3) / max(1, len(w))
            w0 = [p for p in P if p[0] == 'WHEAT' and p[1] == 0 and p[8]]
            f['w0_age'] = st.mean(p[8][0][0] for p in w0) if w0 else None
            s = [p for p in P if p[0] == 'STRAWBERRY' and p[1] <= 15]
            f['straw_fert_share'] = sum(1 for p in s if p[7]) / max(1, len(s))
            wf = [p for p in P if p[0] == 'WHEAT' and 10 <= p[1] <= 15]
            f['wheat10_fert_share'] = sum(1 for p in wf if p[7]) / max(1, len(wf)) if wf else None
            mel = [p for p in P if p[0] == 'MELON' and p[1] <= 3]
            f['melon_units'] = sum(sum(h[2] for h in p[8]) for p in mel) / max(1, len(mel)) if mel else None
            # NW tiles freed by the day-0 wheat: share replanted with strawberries within 1 day of harvest
            bt = collections.defaultdict(list)
            for p in P:
                bt[(p[3], p[4])].append(p)
            tot = strw = 0
            for ps in bt.values():
                ps.sort(key=lambda p: (p[1], p[2]))
                for i, p in enumerate(ps):
                    if p[0] == 'WHEAT' and p[1] == 0:
                        tot += 1
                        if i + 1 < len(ps) and ps[i + 1][0] == 'STRAWBERRY' and ps[i + 1][1] <= 5:
                            strw += 1
            f['w0_to_straw'] = strw / max(1, tot)
        feat[g].append(f)


def share(g, cond):
    xs = [f for f in feat[g] if cond(f) is not None]
    ok = [cond(f) for f in xs]
    return 100 * sum(1 for o in ok if o) / max(1, len(ok)), len(ok)


def mean(g, k):
    xs = [f[k] for f in feat[g] if f.get(k) is not None]
    return st.mean(xs) if xs else float('nan'), (st.median(xs) if xs else float('nan'))


if __name__ == '__main__':
    print('seats', {g: len(feat[g]) for g in ORDER})
    print('\n== per-seat means (median) of key counts')
    for k in ('wheat_d0', 'melon_d0', 'melon_d0_3', 'straw_NW_d1_4', 'straw_NW_d1_5', 'wheat_NW_d1_5', 'w0_age', 'w0_to_straw',
              'ne_day', 'ne_straw', 'ne_wheat', 'sw_day', 'sw_wheat', 'sw_straw', 'se_day', 'wheat_tiles_d10',
              'wheat_tiles_d12', 'straw_tiles_d12', 'tom_9_15', 'car_8_15', 'melon_10_15', 'wheat_age_le3',
              'wheat10_fert_share', 'straw_fert_share', 'melon_units'):
        print(f'  {k:20s} ' + ''.join(f'{AB.get(g,g):>6s} {mean(g,k)[0]:6.2f} ({mean(g,k)[1]:5.1f})' for g in ORDER))
    R = [
        ('R1 d0: wheat>=9 and 5<=melon<=8 (NW)', lambda f: f['wheat_d0'] >= 9 and 5 <= f['melon_d0'] <= 8),
        ('R1b d0: melons>=10 on day 0', lambda f: f['melon_d0'] >= 10),
        ('R2 d1-3: >=2 more melons (total 9-12 by d3)', lambda f: f['melon_d0_3'] - f['melon_d0'] >= 2),
        ('R3 d1-4: >=3 NW strawberries', lambda f: f['straw_NW_d1_4'] >= 3),
        ('R3b d1-5: NW wheat replant <=2', lambda f: f['wheat_NW_d1_5'] <= 2),
        ('R3c d0 wheat harvested at mean age <=3', lambda f: None if f.get('w0_age') is None else f['w0_age'] <= 3.0),
        ('R4 NE bought by d6', lambda f: f['ne_day'] is not None and f['ne_day'] <= 6),
        ('R4b NE straw within 3 of 7+7*buyers(d-buy)', lambda f: None if f['ne_straw'] is None else abs(f['ne_straw'] - 7 - 7 * f['sb_ne']) <= 3),
        ('R4c NE straw 9-11 fixed', lambda f: None if f['ne_straw'] is None else 9 <= f['ne_straw'] <= 11),
        ('R5 SW bought by d9', lambda f: f['sw_day'] is not None and f['sw_day'] <= 9),
        ('R5b SW: >=10 wheat on buy day or next', lambda f: None if f['sw_wheat'] is None else f['sw_wheat'] >= 10),
        ('R5c SW straw >=4 if >=2 straw buyers', lambda f: None if (f['sb_sw'] is None or f['sb_sw'] < 2) else f['sw_straw'] >= 4),
        ('R5d SW straw <=2 if 0 straw buyers', lambda f: None if (f['sb_sw'] is None or f['sb_sw'] > 0) else f['sw_straw'] <= 2),
        ('R6 wheat tiles d10 >=14', lambda f: f['wheat_tiles_d10'] >= 14),
        ('R6b wheat tiles d12 >=18', lambda f: f['wheat_tiles_d12'] >= 18),
        ('R7 >=80% of wheat harvested by age 3', lambda f: None if f.get('wheat_age_le3') is None else f['wheat_age_le3'] >= 0.8),
        ('R7b >=40% of d10-15 wheat tiles fertilized', lambda f: None if f.get('wheat10_fert_share') is None else f['wheat10_fert_share'] >= 0.4),
        ('R8 >=90% of strawberry tiles fertilized', lambda f: None if f.get('straw_fert_share') is None else f['straw_fert_share'] >= 0.9),
        ('R9 tomatoes d9-15 >=3', lambda f: f['tom_9_15'] >= 3),
        ('R9b tomatoes >=3 | 0 tomato buyers d9', lambda f: None if f['tb9'] > 0 else f['tom_9_15'] >= 3),
        ('R9c tomatoes >=3 | 1+ tomato buyers d9', lambda f: None if f['tb9'] == 0 else f['tom_9_15'] >= 3),
        ('R10 carrots d8-15 >=10 | 1+ carrot buyers d9', lambda f: None if f['cb9'] == 0 else f['car_8_15'] >= 10),
        ('R10b carrots d8-15 >=10 | 0 carrot buyers', lambda f: None if f['cb9'] > 0 else f['car_8_15'] >= 10),
        ('R11 melon replant d10-15 >=2', lambda f: f['melon_10_15'] >= 2),
        ('R12 SE bought by d11', lambda f: f['se_day'] is not None and f['se_day'] <= 11),
    ]
    print('\n== rule compliance: % of seats (n seats where the rule applies)')
    for name, c in R:
        print(f'  {name:44s} ' + ''.join(f'{AB.get(g,g):>5s} {share(g,c)[0]:4.0f}% ({share(g,c)[1]:3d})' for g in ORDER))
