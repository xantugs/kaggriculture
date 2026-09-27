"""Missed-fertilizer audit (pinned from S). A missed event = a yield gain that got +1 where +2 was possible:
an ongoing crop's end-of-day production (watered, not fertilized) or a non-ongoing crop's in-window WATER
(not fertilized), with the tile cap not binding. For each miss on day d we look at the unit-steps spent standing on
that tile on days d-2..d (before the event) and classify the cheapest fix:
  free    - a unit was there with a no-op command (PASS or a command that changed nothing) and carried fertilizer
  pickup  - a no-op visit, no fertilizer carried, but the shed held fertilizer that day
  buy     - a no-op visit, no fertilizer anywhere (would need a market buy)
  busy    - only productive commands on that tile in the window
  none    - no unit stood on that tile in the window
Also reports our fertilizer flows: collected, used, sold, bought, left in shed at the end.
usage: fertaudit.py cand S [N]"""
import sys, os, json, collections, copy
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
    FARM = [None]; PRIV = [None]
    visits = collections.defaultdict(list)   # (x, y) -> [(day, step, idx, kind, carried, shed)]
    misses = []                               # (crop, day, x, y, when) ; when = 'eod' or step
    flows = collections.Counter()
    STEP = [0]
    oau, odr, opm = K._apply_unit_action, K._daily_refresh_plants, K._process_market

    def au(farm, private, idx, action, board_size, day, tpd, cap=100):
        if farm is not FARM[0] or not isinstance(action, list) or not action:
            return oau(farm, private, idx, action, board_size, day, tpd, cap)
        op = action[0]
        pos = K._farmer_position(farm, idx)
        if op in K.FARMER_MOVES or pos is None:
            return oau(farm, private, idx, action, board_size, day, tpd, cap)
        x, y = pos
        tile = farm['tiles'][y][x]
        inv = K._farmer_inventory(private, idx)
        before = (copy.deepcopy(tile), dict(inv), dict(private['shed']))
        carried = inv.get('FERTILIZER', 0); shed = private['shed'].get('FERTILIZER', 0)
        plant = isinstance(tile, dict) and tile.get('kind') == 'PLANT'
        pre = None
        if plant and op == 'WATER' and not tile['watered_today']:
            cd = K.CROPS[tile['crop']]
            if not cd['ongoing']:
                age = day - tile['planted_day']
                if (cd['max_yield_day'] + 1) // 2 <= age <= cd['max_yield_day'] and tile['yield_units'] + 1 < cd['max_yield']:
                    pre = tile.get('fertilized_until_day', -1) >= day
        r = oau(farm, private, idx, action, board_size, day, tpd, cap)
        after = farm['tiles'][y][x]
        noop = op == 'PASS' or (after == before[0] and inv == before[1] and private['shed'] == before[2])
        if op == 'COLLECT_FERTILIZER' and inv.get('FERTILIZER', 0) > before[1].get('FERTILIZER', 0):
            flows['collected'] += 1
        if op == 'FERTILIZE' and inv.get('FERTILIZER', 0) < carried:
            flows['used'] += 1
            flows['used_' + tile['crop']] += 1
        if plant:
            visits[(x, y)].append((day, STEP[0], idx, 'noop' if noop else op, carried, shed))
        if pre is False:
            misses.append((tile['crop'], day, x, y, STEP[0]))
        if pre is True:
            flows['fert_' + tile['crop']] += 1
        return r

    def drp(farm, day, tpd):
        if farm is FARM[0]:
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if not (isinstance(t, dict) and t.get('kind') == 'PLANT'):
                        continue
                    cd = K.CROPS[t['crop']]
                    if not cd['ongoing'] or not t['watered_today'] or t['consecutive_unwatered'] >= 1 and False:
                        continue
                    ds = day + 1 - t['planted_day'] - cd['first_yield_day']
                    if ds < 0 or ds % cd['interval'] or ds // cd['interval'] + 1 > cd['max_yield']:
                        continue
                    if t['yield_units'] + 1 >= cd['max_yield']:
                        continue
                    if t.get('fertilized_until_day', -1) >= day:
                        flows['fert_' + t['crop']] += 1
                    else:
                        misses.append((t['crop'], day, x, y, 10 ** 6))
        return odr(farm, day, tpd)

    def pm(state, env):
        FARM[0] = state[0].observation.farms[P]; PRIV[0] = state[P].observation.private
        STEP[0] = int(state[0].observation.step)
        a = state[P].action if isinstance(state[P].action, dict) else {}
        for o in a.get('market') or []:
            if o and len(o) >= 3 and o[1] == 'FERTILIZER' and STEP[0] >= S:
                flows[('sold' if o[0] == 'SELL' else 'bought') + '_ordered'] += int(o[2])
        return opm(state, env)

    K._apply_unit_action, K._daily_refresh_plants, K._process_market = au, drp, pm
    try:
        A = lean.load(cand)
        ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
        lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._apply_unit_action, K._daily_refresh_plants, K._process_market = oau, odr, opm
    flows['shed_left'] = PRIV[0]['shed'].get('FERTILIZER', 0) if PRIV[0] else 0
    cls = collections.Counter()
    for crop, day, x, y, when in misses:
        if day * 24 < S:
            continue
        vs = [v for v in visits[(x, y)] if day - 2 <= v[0] <= day and v[1] < when]
        no = [v for v in vs if v[3] == 'noop']
        if any(v[4] > 0 for v in no):
            k = 'free'
        elif any(v[5] > 0 for v in no):
            k = 'pickup'
        elif no:
            k = 'buy'
        elif vs:
            k = 'busy'
        else:
            k = 'none'
        cls[(crop, k)] += 1
        cls[(crop, 'missed')] += 1
    return {'|'.join(k): v for k, v in cls.items()}, dict(flows)


if __name__ == '__main__':
    cand, S = sys.argv[1], int(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    files = json.load(open(os.path.join(HERE, os.environ.get('GLIST', 'g2800_list.json'))))[:N]
    path = os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    tot = collections.Counter(); fl = collections.Counter()
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '15'))) as ex:
        for r, f in ex.map(job, [(f, path, S) for f in files]):
            tot.update(r); fl.update(f)
    g = len(files)
    for k in sorted(tot):
        print(f'  {k:28s} {tot[k] / g:7.2f} per game')
    print('flows:')
    for k in sorted(fl):
        print(f'  {k:28s} {fl[k] / g:7.2f} per game')
