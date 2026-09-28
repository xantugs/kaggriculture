"""au_crops audit tracer: play one live game (pinned world, our seat from S) with a candidate and log, for the days asked,
every action of our units with its engine effect, the market orders, shed stock, and the night refresh of animals/plants.
usage: au_crops_trace.py gid cand S day[,day...] [out.json]      (corpus gold/top10/gates/live191.json.d)"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402

SPLIT = '/home/user/kaggriculture/gold/top10/gates/live191.json.d'


def find(gid):
    for f in os.listdir(SPLIT):
        with open(os.path.join(SPLIT, f), encoding='utf-8') as fh:
            head = fh.read(400)
        if int(head.split('"id":')[1].split(',')[0]) == gid:
            return os.path.join(SPLIT, f)
    raise SystemExit('gid not found')


def main():
    gid, cand, S = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    days = set(int(x) for x in sys.argv[4].split(','))
    out = sys.argv[5] if len(sys.argv) > 5 else None
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(find(gid), encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand)
    G = A.__globals__
    LOG = collections.defaultdict(list)
    FARM = [None]; STEP = [0]
    o_apply = K._apply_unit_action; o_ra = K._daily_refresh_animals; o_rp = K._daily_refresh_plants
    o_commit = K._commit_unit; o_decay = K._decay_plants; o_int = K.interpreter

    def interp(state, env):
        obs0 = state[0].observation
        if FARM[0] is None and obs0.get('farms'):
            FARM[0] = obs0.farms[P]
        return o_int(state, env)

    def apply(farm, private, idx, action, bs, day, tpd, cap=100):
        if farm is not FARM[0] or day not in days:
            return o_apply(farm, private, idx, action, bs, day, tpd, cap)
        pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
        inv = dict(private['inventories'][idx]) if idx < len(private['inventories']) else {}
        t0 = None
        if pos is not None:
            t = farm['tiles'][pos[1]][pos[0]]
            t0 = json.dumps(t, sort_keys=True) if isinstance(t, dict) else t
        r = o_apply(farm, private, idx, action, bs, day, tpd, cap)
        if pos is not None and isinstance(action, list) and action and action[0] not in ('PASS', 'NORTH', 'SOUTH', 'EAST', 'WEST'):
            t = farm['tiles'][pos[1]][pos[0]]
            t1 = json.dumps(t, sort_keys=True) if isinstance(t, dict) else t
            inv2 = dict(private['inventories'][idx]) if idx < len(private['inventories']) else {}
            eff = (t0 != t1) or (inv != inv2)
            LOG[day].append(('act', STEP[0] % 24, idx, tuple(pos), action, eff, {k: v for k, v in inv.items() if v}))
        return r

    def commit(op, item, price, farm, private, market, cap=100):
        ok = o_commit(op, item, price, farm, private, market, cap)
        if farm is FARM[0] and STEP[0] // 24 in days:
            LOG[STEP[0] // 24].append(('mkt', STEP[0] % 24, op, item, price, ok))
        return ok

    def ra(farm, day):
        if farm is FARM[0] and day in days:
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and 'animal' in t:
                        LOG[day].append(('anim_night', (x, y), t['animal'], dict(fed=t['fed_today'], cared=t['cared_today'],
                                         unfed=t['consecutive_unfed'], y=t['yield_units'], pend=t.get('pending_care_bonus', 0),
                                         placed=t['placed_day'])))
        return o_ra(farm, day)

    def rp(farm, day, tpd):
        if farm is FARM[0] and day in days:
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and t.get('kind') == 'PLANT':
                        LOG[day].append(('plant_night', (x, y), t['crop'], dict(age=day - t['planted_day'], w=t['watered_today'],
                                         cu=t['consecutive_unwatered'], y=t['yield_units'], fu=t['fertilized_until_day'],
                                         mls=t['max_lifespan_step'])))
        return o_rp(farm, day, tpd)

    def decay(farm, step):
        if farm is FARM[0] and step // 24 in days:
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict) and t.get('kind') == 'PLANT':
                        m = t['max_lifespan_step']
                        if m >= 0 and step >= m and (step - m) % 2 == 0 and t['yield_units'] > 0:
                            LOG[step // 24].append(('rot', step % 24, (x, y), t['crop'], t['yield_units']))
        return o_decay(farm, step)

    def ours(obs, cfg=None):
        STEP[0] = int(obs['step'])
        a = A(obs, cfg)
        dd = STEP[0] // 24
        if dd in days and STEP[0] >= S:
            ctl = G.get('_GC')
            sh = {k: v for k, v in dict(obs['private']['shed']).items() if v}
            info = dict(shed=sh, orders=a.get('market') if isinstance(a, dict) else None)
            if ctl is not None and STEP[0] % 24 in (0, 1, 2):
                info['reserve'] = dict(getattr(ctl, 'reserve', {}) or {})
                qs = getattr(ctl, 'queues', {}) or {}
                info['q_feed'] = {u: sum(1 for _t, x, _v in q if x[0] == 'FEED') for u, q in qs.items() if q}
                info['q_pick'] = {u: [x for _t, x, _v in q if x[0] == 'PICKUP'] for u, q in qs.items() if q}
            LOG[dd].append(('obs', STEP[0] % 24, info))
        return a
    K._apply_unit_action = apply; K._daily_refresh_animals = ra; K._daily_refresh_plants = rp; K._commit_unit = commit
    K._decay_plants = decay; K.interpreter = interp
    try:
        ag = [None, None]
        ag[P] = _prefixed(ours, d['acts'], P, S)
        ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._apply_unit_action = o_apply; K._daily_refresh_animals = o_ra
        K._daily_refresh_plants = o_rp; K._commit_unit = o_commit; K._decay_plants = o_decay
        K.interpreter = o_int
    print('gid', gid, 'opp', names[O], 'm %+.0f' % (r['r'][P] - r['r'][O]))
    rep = {k: v for k, v in G['_GC_REPORT'].items() if isinstance(v, (int, float)) and v}
    print(rep)
    if out:
        json.dump({str(k): v for k, v in LOG.items()}, open(out, 'w', encoding='utf-8'), default=str)
    return LOG


if __name__ == '__main__':
    main()
