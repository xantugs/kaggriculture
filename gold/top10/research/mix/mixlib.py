"""Shared helpers: shops/demand, top-30 teams, loading corpus diag rows and gate diag rows into a common seat format.
seat = dict(team, won, rew, opp_rew, shops, days=[{pl, t, su, sd, bu, h, hc, land} x 30], src)"""
import json, csv, collections
SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"], "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
         "YARN_STORE": ["WOOL"], "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
         "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
PRODS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'EGG', 'MILK', 'WOOL']
TILE_OF = {'WHEAT': 'WHEAT', 'CARROT': 'CARROT', 'TOMATO': 'TOMATO', 'STRAWBERRY': 'STRAWBERRY', 'EGG': 'GOOSE', 'MILK': 'COW', 'WOOL': 'SHEEP', 'MELON': 'MELON'}
LB = 'C:/Users/khant/AppData/Local/Temp/claude/C--Users-khant-OneDrive-Documents-ChatGPT-2027-kaggriculture-review/875e1517-4223-4d24-a8c6-423a3c7003a6/scratchpad/lb.csv'


def dem(shops, p):
    return sum((12 if len(SHOPS[s]) == 1 else 6) for s in shops if p in SHOPS[s])


def known(shops, day):
    """shops unlock at the start of days 3, 6, 9, ...: at day D the first D//3 are known."""
    return shops[:min(8, day // 3)]


def top_teams(n=30):
    out = []
    for r in csv.DictReader(open(LB, encoding='utf-8')):
        if int(r['Rank']) <= n: out.append(r['TeamName'])
    return out


def corpus_seats(paths, teams=None, winners=True):
    for p in paths:
        for l in open(p, encoding='utf-8'):
            g = json.loads(l)
            if not g.get('ok'): continue
            for s in (0, 1):
                t = g['names'][s]
                if teams is not None and t not in teams: continue
                a, b = g['rew'][s], g['rew'][1 - s]
                if a is None or b is None: continue
                won = a > b
                if winners and not won: continue
                yield dict(team=t, opp=g['names'][1 - s], won=won, rew=a, opp_rew=b, shops=g['shops'], days=g['f'][s],
                           odays=g['f'][1 - s], gid=g['id'], seat=s, src='corpus')


def _gate_days(side):
    out = []
    for r in side:
        pl = collections.Counter()
        for k, v in r['plant'].items(): pl[k.split('@')[0]] += v
        out.append(dict(pl=dict(pl), t=r['tiles'], su=r['sold'], sd=r['sold_d'], bu=r['bought'], h=r['hires'], hc=r['hire_cost'], land=r['land']))
    return out


def gate_seats(diag_paths, ref_paths):
    refs = {}
    for f in ref_paths:
        for r in map(json.loads, open(f, encoding='utf-8')): refs[(r['gid'], r['seat'])] = r
    for f in diag_paths:
        for x in map(json.loads, open(f, encoding='utf-8')):
            ref = refs[(x['gid'], x['seat'])]
            yield dict(gid=x['gid'], seat=x['seat'], team=x['team'], m=x['m'], shops=ref['shops'],
                       elite=_gate_days(x['elite']), us=_gate_days(x['other']))


def plantings(days, crop, a, b):
    return sum(days[d]['pl'].get(crop, 0) for d in range(a, min(b, 30)))


def tiles(days, d, k):
    return days[d]['t'].get(k, 0)
