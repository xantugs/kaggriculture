import json, os, collections, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
AN = ('GOOSE', 'COW', 'SHEEP')
EGGB = {'BAKERY', 'BRUNCH_SPOT'}
MILKB = {'PIZZA_SHOP', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'}
YARN = {'YARN_STORE'}
TEAMS = ['Boey', 'Fourth Quadrant', '吃白饭的大肥鱼', 'Yizhou', 'THIRD FARM CLUB']
SHORT = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'Yizhou': 'Yiz', 'THIRD FARM CLUB': 'TFC',
         'T7': 'T7'}


def load(role=None, dates=None):
    rows = []
    with open(os.path.join(HERE, 'compact.jsonl'), encoding='utf-8') as f:
        for l in f:
            r = json.loads(l)
            if role and r['role'] not in role:
                continue
            if dates and r['date'] not in dates:
                continue
            rows.append(r)
    return rows


def late(r):
    return r['date'] >= '2026-09-23'


def owned(day):
    """animals owned at hour 0: placed + waiting in the shed (shed only on detail rows)"""
    h = dict(day['herd'])
    for a in AN:
        h[a] = h.get(a, 0) + (day.get('shed') or {}).get(a, 0)
    return h


def nbuy(day, a):
    v = day['ba'].get(a)
    return v[0] if v else 0


def shopset(day):
    return set(day['shops'] or [])


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float('nan')


def pct(xs):
    xs = list(xs)
    return 100.0 * sum(1 for x in xs if x) / len(xs) if xs else float('nan')


def med(xs):
    xs = list(xs)
    return st.median(xs) if xs else float('nan')


def boey_old(r):
    """Boey's 23-24 Sep variant (2C3S day 0, no early geese; 29 seats, 0 wins, margin -$77k): excluded from Boey rules."""
    return r['team'] == 'Boey' and r['role'] in ('rec', 'elite_rep') and nbuy(r['days'][0], 'COW') == 2 and \
        not sum(nbuy(r['days'][d], 'GOOSE') for d in range(4))
