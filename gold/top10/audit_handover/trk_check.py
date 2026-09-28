"""Tracker check: play a game with a candidate, record the rival's true SELL fills per market step (engine hook) and
compare them with the controller's inferred rival_sales (lots >= rival_min_lot) on the 2 days before the takeover and
the takeover day; also log the market programme's rival forecast on the first controller day.
usage: trk_check.py cand gid[,gid...] out.jsonl"""
import sys, os, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402
from concurrent.futures import ProcessPoolExecutor
IDX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gid_index.json')))


def job(t):
    cand, gid, S = t
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(IDX[str(gid)], encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    STEP = [0]; FARMS = [None, None]; true = {}
    oc = K._commit_unit; opm = K._process_market

    def pm(state, env):
        STEP[0] = int(state[0].observation.step)
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)

    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and op == 'SELL' and price > 1 and farm is FARMS[O]:
            k = '%d:%s' % (STEP[0], item)
            true[k] = true.get(k, 0) + 1
        return ok
    K._commit_unit = commit; K._process_market = pm
    A = lean.load(cand)
    G = A.__globals__; C = G['GoldCtl']; GC = G['_GC']; REP = G['_GC_REPORT']
    fc = {}
    o_dp = C._dp_sell

    def dp(self, obs, p, n, step, day, hour, shops, cap_night=None):
        out = o_dp(self, obs, p, n, step, day, hour, shops, cap_night)
        if day == int(REP.get('gc_start', 528)) // 24 and hour < 24:
            fc.setdefault(p, []).append((step, n, out, round(self._dp_rv_now.get(p, 0.0), 2) if hasattr(self, '_dp_rv_now') else None))
        return out
    C._dp_sell = dp
    try:
        ag = [None, None]; ag[P] = _prefixed(A, d['acts'], P, S); ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm
    start = int(REP.get('gc_start', 528))
    inf = {}
    for p, lst in GC.rival_sales.items():
        for dd, hh, q in lst:
            inf['%d:%s' % (dd * 24 + hh, p)] = q
    best = None
    for sh in (-2, -1, 0, 1):
        tr = {}
        for k, v in true.items():
            s_, p_ = k.split(':')
            tr['%d:%s' % (int(s_) + sh, p_)] = v
        win = lambda k: start - 48 <= int(k.split(':')[0]) < start + 24
        tw = {k: v for k, v in tr.items() if win(k) and v >= 2}
        iw = {k: v for k, v in inf.items() if win(k)}
        match = sum(1 for k in tw if k in iw and iw[k] == tw[k])
        if best is None or match > best[0]:
            best = (match, sh, tw, iw)
    match, shift, tw, iw = best
    days = {}
    for k, v in tw.items():
        dd_ = int(k.split(':')[0]) // 24 - start // 24; days.setdefault('true%+d' % dd_, 0); days['true%+d' % dd_] += v
    for k, v in iw.items():
        dd_ = int(k.split(':')[0]) // 24 - start // 24; days.setdefault('inf%+d' % dd_, 0); days['inf%+d' % dd_] += v
    return dict(gid=gid, m=r['r'][P] - r['r'][O], start=start, shift=shift, days=days, true_lots=len(tw), inf_lots=len(iw), exact=match,
                true_units=sum(tw.values()), inf_units=sum(iw.values()),
                miss=sorted(set(tw) - set(iw))[:12], extra=sorted(set(iw) - set(tw))[:12],
                diffq=[(k, tw[k], iw[k]) for k in tw if k in iw and iw[k] != tw[k]][:12],
                fc={p: v[:30] for p, v in fc.items()}, hfix=REP.get('gc_hfix1'))


if __name__ == '__main__':
    cand = sys.argv[1]; gids = [int(x) for x in sys.argv[2].split(',')]; out = sys.argv[3]
    S = int(os.environ.get('S', '288'))
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, [(cand, g, S) for g in gids]):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(json.dumps({k: v for k, v in r.items() if k != 'fc'}), flush=True)
