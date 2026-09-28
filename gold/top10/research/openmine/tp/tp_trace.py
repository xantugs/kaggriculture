"""Per-step trace of our seat in one gate game (tape-plus development).
usage: tp_trace.py goldg|top10g gid seat cand.py out.jsonl [last_step]
       tp_trace.py live FILE.json gid cand.py out.jsonl [last_step]      (pinned from step 0)
Row per step: step money route raw(tape action) act(final action) pos(units) tiles(at unit positions) seeds shed
fills(our market fills that step) hires land."""
import sys, os, json, gzip, collections
KG = '/home/user/kaggriculture'
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))
from kaggle_environments.envs.kaggriculture import kaggriculture as K
import lean


def ctile(t):
    if t is None:
        return None
    if not isinstance(t, dict):
        return str(t)
    k = t.get('kind')
    if k == 'PLANT':
        return 'P:%s:%s:%s%s' % (t.get('crop'), t.get('planted_day'), t.get('yield_units', 0), 'w' if t.get('watered_today') else '')
    if k in ('COOP', 'PASTURE'):
        return '%s:%s' % (k, t.get('animal') or '-')
    return str(k)


WATCH = [tuple(int(v) for v in q.split(',')) for q in os.environ.get('TP_WATCH', '').split(';') if q]


def main():
    gate = sys.argv[1]
    last = None
    if gate in ('goldg', 'top10g'):
        gid, seat, cand, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
        last = int(sys.argv[6]) if len(sys.argv) > 6 else None
        base = os.path.join(KG, 'gold/top10/gates/%s' % gate)
        ref = None
        for l in open(base + '_refs.jsonl', encoding='utf-8'):
            r = json.loads(l)
            if r['gid'] == gid and r['seat'] == seat:
                ref = r; break
        d = None
        with gzip.open(base + '_games.jsonl.gz', 'rt', encoding='utf-8') as fh:
            for l in fh:
                if ('"id": %d' % gid) in l or ('"id":%d' % gid) in l:
                    x = json.loads(l)
                    if x['id'] == gid:
                        d = x; break
        from eval_elite_routes import install_town
        from transplant import build_agent
        s = ref['seat']
        rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
        orig = install_town(ref['shops'])
        me = 1 - s
        opp = build_agent(d['acts'], s, rr, slack_min=20)
        seed = ref['seed']
    else:
        path, gid, cand, out = sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
        last = int(sys.argv[6]) if len(sys.argv) > 6 else None
        import pinned4
        d = None
        for f in os.listdir(path + '.d'):
            x = json.load(open(os.path.join(path + '.d', f), encoding='utf-8'))[0]
            if x['id'] == gid:
                d = x; break
        names = d['info']['TeamNames']; me = names.index('offhand'); O = 1 - me
        spawns, shops, rref = pinned4.reference(d)
        orig = pinned4.install_pinned(0, O, spawns, shops)
        opp = pinned4._tape(d['acts'], O)
        seed = d['info']['seed']
    A = lean.load(cand)
    G = A.__globals__
    rows = []
    FARMS = [None, None]; STEP = [0]
    fills = collections.defaultdict(list)
    led = [collections.Counter(), collections.Counter()]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[me] is not None and farm is FARMS[me]:
            fills[STEP[0]].append([op, item, price])
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL':
                led[i][item] += price; led[i]['n' + item] += 1
                if item == 'STRAWBERRY': led[i]['sd%02d' % (STEP[0] // 24)] += 1
            elif op == 'BUY_PRODUCT': led[i]['b' + item] -= price
            elif op == 'BUY_SEED': led[i]['seed'] -= price
            elif op == 'BUY_ANIMAL': led[i]['anim'] -= price
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[me] is not None and farm is FARMS[me] and farm['money'] != m0:
            fills[STEP[0]].append(['HIRE', None, m0 - farm['money']])
    ol = K._do_buy_land
    def land(farm, bs):
        m0 = farm['money']; ol(farm, bs)
        if FARMS[me] is not None and farm is FARMS[me] and farm['money'] != m0:
            fills[STEP[0]].append(['LAND', None, m0 - farm['money']])
    opm = K._process_market
    def pm(state, env):
        STEP[0] = state[0].observation.step
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    K._commit_unit = commit; K._do_hire = hire; K._do_buy_land = land; K._process_market = pm

    def ours(obs, cfg=None):
        a = A(obs, cfg)
        st = int(obs['step'])
        if last is None or st <= last:
            farm = obs['farms'][me]
            pos = [list(farm['farmer'])] + [list(h) for h in farm['hands']]
            ch = G['_IMPL'].chassis
            pl = ch.players.get(me) or {}
            rt = pl.get('route')
            raw = ch.routes[rt][st] if rt in ch.routes and st < len(ch.routes[rt]) else None
            tiles = [ctile(farm['tiles'][p[1]][p[0]]) for p in pos]
            if WATCH and st % 24 in (0, 23):
                wt = {'%d,%d' % q: (dict(farm['tiles'][q[1]][q[0]]) if isinstance(farm['tiles'][q[1]][q[0]], dict) else farm['tiles'][q[1]][q[0]]) for q in WATCH}
            else:
                wt = None
            rows.append(dict(step=st, money=float(farm['money']), route=rt, raw=raw, act=json.loads(json.dumps(a)), pos=pos,
                             tiles=tiles, seeds={k: int(v) for k, v in dict(obs['private']['seeds']).items() if int(v)},
                             shed={k: int(v) for k, v in dict(obs['private']['shed']).items() if int(v)},
                             inv=[{k: int(v) for k, v in dict(i).items() if int(v)} for i in obs['private']['inventories']],
                             shops=list(obs['town']['unlocked_shops']), watch=wt))
        return a
    ag = [None, None]; ag[me] = ours; ag[1 - me] = opp
    try:
        r = lean.play(None, None, seed, agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh; K._do_buy_land = ol
    for row in rows:
        row['fills'] = fills.get(row['step'], [])
    with open(out, 'w', encoding='utf-8') as fh:
        for row in rows:
            fh.write(json.dumps(row) + '\n')
        tel = getattr(A, 'telemetry', None)
        tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
        fh.write(json.dumps(dict(final=r['r'], me=me, err=r['err'], tel=tel, led_us=dict(led[me]), led_them=dict(led[1 - me]))) + '\n')
    print('rewards', r['r'], 'me', me, 'm', (r['r'][me] or 0) - (r['r'][1 - me] or 0), r['err'])


if __name__ == '__main__':
    main()
