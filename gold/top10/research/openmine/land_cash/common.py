"""Shared loader for the land/cash-flow study. Streams the openmine day files once, keeps days 0..MAXD and caches
compact rows to land_cash/cache_days.pkl (a few tens of MB), so the analysis scripts never re-read the 98 MB file.

seats: dict key (role, gid, seat) -> {'team','opp','date','role','days': [row d=0..MAXD]}
role 'rec' = recorded elite, 'ours' = T7 in the elite's town, 'elite_rep' = repaired elite playing T7.
"""
import os, json, pickle, collections

HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
MAXD = 16
CACHE = os.path.join(HERE, 'cache_days.pkl')
KEEP = ('d', 'm0', 'm23', 'mend', 'mmin', 'mmin_h', 'sell', 'buy_prod', 'buy_seed', 'buy_animal', 'hires', 'wage',
        'hire_h', 'land', 'hands', 'quads', 'herd', 'crops', 'units', 'struct', 'weeds', 'free', 'shops', 'hv', 'ops',
        'q', 'shed', 'seeds', 'px', 'fills', 'riv')
TEAMS = ['Boey', 'Fourth Quadrant', '吃白饭的大肥鱼', 'Yizhou', 'THIRD FARM CLUB']
SHORT = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'Yizhou': 'Yiz', 'THIRD FARM CLUB': 'TFC',
         'T7': 'T7'}
RECENT = ('2026-09-23', '2026-09-24', '2026-09-25', '2026-09-26')


def _stream(path, seats):
    with open(path, encoding='utf-8') as f:
        for line in f:
            # cheap day filter before json parsing
            i = line.find('"d": ')
            if i >= 0:
                j = line.find(',', i)
                try:
                    d = int(line[i + 5:j])
                except ValueError:
                    d = 99
                if d > MAXD:
                    continue
            r = json.loads(line)
            if r['d'] > MAXD:
                continue
            k = (r['role'], r['gid'], r['seat'])
            s = seats.get(k)
            if s is None:
                s = seats[k] = {'team': r['team'], 'opp': r['opp'], 'date': r['date'], 'role': r['role'],
                                'gid': r['gid'], 'seat': r['seat'], 'days': [None] * (MAXD + 1)}
            s['days'][r['d']] = {x: r.get(x) for x in KEEP}


def load():
    if os.path.exists(CACHE):
        with open(CACHE, 'rb') as f:
            return pickle.load(f)
    seats = {}
    for fn in ('elite_days.jsonl', 'ours_T7_days.jsonl', 'ours_T7_opp_days.jsonl'):
        _stream(os.path.join(OM, fn), seats)
    seatrows = {}
    for fn in ('elite_seats.jsonl', 'ours_T7_seats.jsonl', 'ours_T7_opp_seats.jsonl'):
        with open(os.path.join(OM, fn), encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                seatrows[(r['role'], r['gid'], r['seat'])] = r
    for k, s in seats.items():
        sr = seatrows.get(k, {})
        s['seat_row'] = {x: sr.get(x) for x in ('rew', 'rec', 'shops', 'land', 'final', 'elite_seat', 'm', 'seed')}
    with open(CACHE, 'wb') as f:
        pickle.dump(seats, f, protocol=pickle.HIGHEST_PROTOCOL)
    return seats


def by_team(seats, role='rec', recent=True):
    out = collections.defaultdict(list)
    for k, s in seats.items():
        if s['role'] != role:
            continue
        if recent and s['date'] not in RECENT:
            continue
        out[s['team']].append(s)
    return out


def win(s):
    r = s['seat_row'].get('rew') or [0, 0]
    return r[0] > r[1]


if __name__ == '__main__':
    import time
    t = time.time()
    S = load()
    c = collections.Counter((s['role'], s['team'], s['date'] in RECENT) for s in S.values())
    for k, v in sorted(c.items()):
        print(k, v)
    print('rows', len(S), 'time', round(time.time() - t, 1))


def pairs(S):
    """[(t7_seat, recorded_elite_seat, repaired_elite_seat)] for the 96 T7 games; team = t7['opp']"""
    rec = {(s['gid'], s['seat']): s for s in S.values() if s['role'] == 'rec'}
    rep = {(s['gid'], s['seat']): s for s in S.values() if s['role'] == 'elite_rep'}
    out = []
    for s in S.values():
        if s['role'] != 'ours':
            continue
        es = s['seat_row']['elite_seat']
        out.append((s, rec[(s['gid'], es)], rep.get((s['gid'], es))))
    return out
