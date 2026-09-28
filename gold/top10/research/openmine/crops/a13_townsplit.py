"""Strawberry outcome by town type: # strawberry buyers known on day 6 (b6) and on day 12 (b12). Per seat: strawberry
tiles planted d0-15, units sold d10-29, $ sold, avg price; recorded elite (23-26 Sep) vs T7 (and the recorded elite
in the T7 games). usage: a13_townsplit.py"""
import os, sys, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); OM = os.path.dirname(HERE)
sys.path.insert(0, HERE)
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}
SB = {'BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET'}
t7 = [json.loads(l) for l in open(os.path.join(OM, 'ours_T7_seats.jsonl'), encoding='utf-8')]
t7el = {(s['gid'], s['elite_seat']) for s in t7}
seat = collections.defaultdict(lambda: dict(pl=0, u=0, v=0.0, b6=None, b12=None, win=None))
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    for line in open(os.path.join(OM, fn), encoding='utf-8'):
        r = json.loads(line)
        if role == 'rec' and r['date'] < '2026-09-23': continue
        k = (role, r['gid'], r['seat'])
        S = seat[k]; S['g'] = AB[r['team']]; S['t7game'] = role == 'rec' and (r['gid'], r['seat']) in t7el
        if r['d'] <= 15:
            S['pl'] += sum(v for kk, v in (r.get('ops') or {}).items() if kk.startswith('PLANT:STRAWBERRY'))
        if r['d'] == 6: S['b6'] = sum(1 for s in r['shops'] if s in SB)
        if r['d'] == 12: S['b12'] = sum(1 for s in r['shops'] if s in SB)
        s = (r.get('sell') or {}).get('STRAWBERRY')
        if s: S['u'] += s[0]; S['v'] += s[1]
print('b6 = strawberry buyers known on day 6 | per seat: strawberries planted d0-15, units sold, $ sold, avg price  (n)')
for key in ('b6', 'b12'):
    print(f'\n== split by {key}')
    for g in ('Boey', 'FQ', 'CBF', 'TFC', 'Yiz', 'rec@T7', 'T7'):
        line = f'  {g:7s}'
        for b in (0, 1, 2, 3):
            xs = [S for kk, S in seat.items() if S.get(key) is not None and (S[key] == b if b < 3 else S[key] >= 3) and
                  ((g == 'T7' and kk[0] == 'ours') or (g == 'rec@T7' and S.get('t7game')) or (kk[0] == 'rec' and S['g'] == g and g not in ('T7',)))]
            if not xs: line += ' ' * 40; continue
            n = len(xs)
            pl = sum(S['pl'] for S in xs) / n; u = sum(S['u'] for S in xs) / n; v = sum(S['v'] for S in xs) / n
            line += f' | b={b}{"+" if b == 3 else " "} {pl:4.1f}t {u:5.0f}u ${v/1000:5.1f}k @{v/max(1,u*1):4.0f} ({n:3d})'
        print(line)
