"""Replay a recorded game (both tapes) and print, per day, each farm's composition, hires, money, and cumulative
sales per product. usage: farmcmp.py game.json [days=6,8,10,12,15,18,21,24,27,29]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K


def comp(farm):
    c = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if t is None: c['.'] += 1
            elif t == 'LOCKED': c['#'] += 1
            elif isinstance(t, dict):
                c[t.get('crop') or t.get('animal') or t.get('kind')] += 1
    return c


def run(fn, days):
    d = json.load(open(fn, encoding='utf-8'))[0]
    names = d['info']['TeamNames']
    snaps = {}; sold = [collections.Counter(), collections.Counter()]; hires = [collections.Counter(), collections.Counter()]
    FARMS = [None, None]; STEP = [0]
    oe, ocu, opm, odh = K._end_of_day, K._commit_unit, K._process_market, K._do_hire
    def eod(state, env, day):
        if day in days:
            snaps[day] = [(comp(state[0].observation.farms[p]), state[0].observation.farms[p]['money'], len(state[0].observation.farms[p]['hands']), dict(sold[p])) for p in (0, 1)]
        return oe(state, env, day)
    def cu(op, item, price, farm, private, market, cap=100):
        ok = ocu(op, item, price, farm, private, market, cap)
        if ok and op == 'SELL':
            sold[0 if farm is FARMS[0] else 1][item] += 1
        return ok
    def pm(state, env):
        FARMS[0] = state[0].observation.farms[0]; FARMS[1] = state[0].observation.farms[1]
        return opm(state, env)
    def dh(farm, private, bs, mult=1):
        hires[0 if farm is FARMS[0] else 1][STEP[0] // 24] += 1
        return odh(farm, private, bs, mult)
    K._end_of_day, K._commit_unit, K._process_market, K._do_hire = eod, cu, pm, dh
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._end_of_day, K._commit_unit, K._process_market, K._do_hire = oe, ocu, opm, odh
    print(fn, names, 'final', r['r'], 'shops', r['shops'])
    for day in sorted(snaps):
        for p in (0, 1):
            c, m, h, s = snaps[day][p]
            cs = ' '.join(f'{k[:4]}:{v}' for k, v in sorted(c.items()) if k not in ('.', '#'))
            print(f'  d{day:2d} {names[p][:14]:14s} ${m:8.0f} empty {c["."]:2d} locked {c["#"]:2d} | {cs}')
        print(f'       sold so far: ' + ' || '.join(' '.join(f'{k[:4]}:{v}' for k, v in sorted(snaps[day][p][3].items())) for p in (0, 1)))


if __name__ == '__main__':
    days = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else '6,8,10,12,15,18,21,24,27,29').split(',')]
    run(sys.argv[1], set(days))
