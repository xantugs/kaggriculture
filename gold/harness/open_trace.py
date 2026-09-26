"""Closed-loop game between two candidates with a per-day table for both farms (money, hands, land, plantings, sales, tiles).
usage: open_trace.py a.py b.py seed [days_shown]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
Q = lambda x, y: ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')

def play(a, b, seed):
    days = [[], []]
    sold = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    FARMS = [None, None]; DAY = [0]
    oc = K._commit_unit; opm = K._process_market; oeod = K._end_of_day; oh = K._do_hire
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL': sold[i][DAY[0]]['u_' + item] += 1; sold[i][DAY[0]]['$_' + item] += price
            elif op == 'BUY_PRODUCT': sold[i][DAY[0]]['buy_' + item] += 1; sold[i][DAY[0]]['$buy'] -= price
            elif op == 'BUY_SEED': sold[i][DAY[0]]['seed_' + item] += 1; sold[i][DAY[0]]['$buy'] -= price
            elif op == 'BUY_ANIMAL': sold[i][DAY[0]]['anim_' + item] += 1; sold[i][DAY[0]]['$buy'] -= price
        return ok
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None: sold[0 if farm is FARMS[0] else 1][DAY[0]]['$hire'] += farm['money'] - m0
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        DAY[0] = int(K.get(state[0].observation, 'step', 0)) // 24
        return opm(state, env)
    def eod(state, env, day):
        obs0 = state[0].observation
        for pid, farm in enumerate(obs0.farms):
            private = state[pid].observation.private
            c = collections.Counter(); planted = collections.Counter(); ripe = collections.Counter()
            for y, row in enumerate(farm['tiles']):
                for x, tile in enumerate(row):
                    if isinstance(tile, dict):
                        if tile.get('crop'):
                            c[tile['crop']] += 1
                            if tile.get('planted_day') == day: planted[tile['crop'] + '@' + Q(x, y)] += 1
                            ripe[tile['crop']] += tile.get('yield_units', 0)
                        elif tile.get('animal'):
                            c[tile['animal']] += 1; ripe[tile['animal']] += tile.get('yield_units', 0)
                        elif tile.get('kind') == 'WEED': c['WEED'] += 1
                        else: c['empty_' + str(tile.get('kind'))] += 1
                    elif tile is None: c['free'] += 1
            days[pid].append(dict(day=day, money=round(farm['money']), hands=len(farm['hands']), land=list(farm['unlocked_quadrants']),
                                  tiles=dict(c), planted=dict(planted), ripe=dict(ripe), shed={k: v for k, v in private['shed'].items() if v},
                                  seeds={k: v for k, v in private['seeds'].items() if v}, mkt=dict(sold[pid][day]),
                                  inv=sum(sum(i.values()) for i in private['inventories'])))
        return oeod(state, env, day)
    K._commit_unit = commit; K._process_market = pm; K._end_of_day = eod; K._do_hire = hire
    try:
        A = lean.load(a); B = lean.load(b)
        r = lean.play(None, None, seed, agent_objs=[A, B])
    finally:
        K._commit_unit = oc; K._process_market = opm; K._end_of_day = oeod; K._do_hire = oh
    tel = [getattr(X, 'telemetry', None) for X in (A, B)]
    return r, days, tel

def show(days, label, nd=30):
    print('==== %s' % label)
    print('day  money  hands land  planted(crop@quadrant)                                  sold units                              $sold  $buy $hire tiles')
    for rc in days[:nd]:
        pl = ' '.join('%s:%d' % (k[:5] + k[-3:], v) for k, v in sorted(rc['planted'].items(), key=lambda kv: -kv[1]))
        so = ' '.join('%s:%d' % (k[2:6], v) for k, v in sorted(rc['mkt'].items(), key=lambda kv: -kv[1]) if k.startswith('u_'))
        bu = ' '.join('%s:%d' % (k[:1] + k[-4:], v) for k, v in sorted(rc['mkt'].items()) if k.startswith(('buy_', 'anim_', 'seed_')))
        ti = ' '.join('%s:%d' % (k[:4], v) for k, v in sorted(rc['tiles'].items(), key=lambda kv: -kv[1]) if k != 'free')
        print('%3d %7d %5d %4d  %-55s %-38s %6d %5d %5d %s | %s | lost %d' % (rc['day'], rc['money'], rc['hands'], len(rc['land']), pl[:55], so[:38],
              sum(v for k, v in rc['mkt'].items() if k.startswith('$_')), rc['mkt'].get('$buy', 0), rc['mkt'].get('$hire', 0), ti[:70], bu[:60], rc['inv']))

if __name__ == '__main__':
    a, b, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    nd = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    r, days, tel = play(a, b, seed)
    print('result', r['r'], 'err', r['err'], 'shops', r['shops'])
    show(days[0], a, nd); show(days[1], b, nd)
    for X, t in zip((a, b), tel):
        if t: print(X, {k: v for k, v in t.items() if isinstance(v, (int, float, str)) and v})
