"""Production audit of our ongoing crops (pinned from S): per production event whether the plant was watered and
fertilized (+2) or not (+1), units lost to the 4-unit tile cap, and units lost to decay/death. usage: prodaudit.py cand S [N]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def job(t):
    fn, cand, S = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(S // 24, O, spawns, shops)
    st = collections.Counter(); FARM = [None]
    odr, odp = K._daily_refresh_plants, K._decay_plants
    def drp(farm, day, tpd):
        mine = farm is FARM[0]
        snap = {}
        if mine:
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and t.get('kind') == 'PLANT' and K.CROPS[t['crop']]['ongoing']:
                        snap[(x, y)] = (t['crop'], t['watered_today'], t.get('fertilized_until_day', -1) >= day, t['yield_units'], t['planted_day'])
        odr(farm, day, tpd)
        if mine:
            for (x, y), (crop, w, f, y0, pd) in snap.items():
                t = farm['tiles'][y][x]
                cd = K.CROPS[crop]; ds = day + 1 - pd - cd['first_yield_day']
                event = ds >= 0 and ds % cd['interval'] == 0 and ds // cd['interval'] + 1 <= cd['max_yield']
                if not isinstance(t, dict) or t.get('kind') != 'PLANT':
                    st[(crop, 'died')] += 1
                    continue
                if event:
                    full = 2 if (w and f) else 1
                    got = t['yield_units'] - y0
                    st[(crop, 'events')] += 1; st[(crop, 'fert' if (w and f) else ('water_only' if w else 'dry'))] += 1
                    st[(crop, 'units')] += got; st[(crop, 'cap_lost')] += full - got; st[(crop, 'fert_missed')] += 0 if (w and f) else 1
        return None
    def dp(farm, step):
        if farm is FARM[0]:
            before = {(x, y): t['yield_units'] for y, row in enumerate(farm['tiles']) for x, t in enumerate(row)
                      if isinstance(t, dict) and t.get('kind') == 'PLANT' and K.CROPS[t['crop']]['ongoing']}
            odp(farm, step)
            for (x, y), yv in before.items():
                t = farm['tiles'][y][x]
                now = t['yield_units'] if isinstance(t, dict) and t.get('kind') == 'PLANT' else 0
                if yv > 0 and now < yv:
                    st[(farm['tiles'][y][x].get('crop') if isinstance(t, dict) and t.get('crop') else 'x', 'decayed')] += yv - max(0, now)
            return
        return odp(farm, step)
    opm = K._process_market
    def pm(state, env):
        FARM[0] = state[0].observation.farms[P]
        return opm(state, env)
    K._daily_refresh_plants, K._decay_plants, K._process_market = drp, dp, pm
    try:
        A = lean.load(cand)
        ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
        lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._daily_refresh_plants, K._decay_plants, K._process_market = odr, odp, opm
    return {'|'.join(k): v for k, v in st.items()}


if __name__ == '__main__':
    cand, S = sys.argv[1], int(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    files = json.load(open(os.path.join(HERE, 'g2800_list.json')))[:N]
    path = os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    tot = collections.Counter()
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '15'))) as ex:
        for r in ex.map(job, [(f, path, S) for f in files]):
            tot.update(r)
    g = len(files)
    for k in sorted(tot):
        print(f'  {k:28s} {tot[k] / g:7.1f} per game')
