"""Market audit probe (au_market): play a candidate on pinned live games (world as pinned4.py) and record, for OUR seat
from step S on, every market order and what the engine did with it:
  orders   per step: [op, item, n, filled, why]  (why: '' full fill, 'shed' shed full, 'cash' no cash, 'stock' shed empty,
           'cut' beyond the engine's 10-order cut, 'hire_cash' HIRE with no cash)
  h0       per controller day at hour 0: shed total before the market, controller sell0/orders0/orders1/hires, reserve
  noop     per step: controller queue items popped because an input was missing (FEED without wheat, PLANT without
           seeds, FERTILIZE without fertilizer, PICKUP with an empty shed)
  end      seeds, shed and inventories left after step 718
usage: mkt_probe.py corpus.json.d S cand out.jsonl gid[,gid...] | all     (env NPROC)"""
import sys, os, json, time, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from concurrent.futures import ProcessPoolExecutor
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402


def job(t):
    path, S, cand = t
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand)
    G = A.__globals__
    C = G['GoldCtl']
    rec = dict(orders={}, h0={}, noop=collections.defaultdict(list))
    cur = {'step': -1, 'farm': None, 'commits': [], 'hires': []}
    o_useful = C._useful

    def useful(self, act, tile, inv, seeds, planting, shed, room):
        ok = o_useful(self, act, tile, inv, seeds, planting, shed, room)
        if not ok and cur['step'] >= S:
            op = act[0]; why = None
            if op == 'FEED' and isinstance(tile, dict) and 'animal' in tile and not tile.get('fed_today') and inv.get('WHEAT', 0) <= 0:
                why = 'FEED_nowheat'
            elif op == 'PLANT' and tile is None and seeds.get(act[1], 0) - planting.get(act[1], 0) <= 0:
                why = 'PLANT_noseed_' + act[1]
            elif op == 'FERTILIZE' and isinstance(tile, dict) and tile.get('kind') == 'PLANT' and inv.get('FERTILIZER', 0) <= 0:
                why = 'FERT_nofert'
            elif op == 'PICKUP' and shed.get(act[1], 0) <= 0:
                why = 'PICKUP_empty_' + act[1]
            if why:
                rec['noop'][cur['step']].append(why)
        return ok
    C._useful = useful
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        pre_total = sum(private['shed'].values()); pre_money = farm['money']
        ok = oc(op, item, price, farm, private, market, cap)
        if farm is cur['farm']:
            why = ''
            if not ok:
                if op == 'SELL':
                    why = 'stock'
                elif op in ('BUY_PRODUCT', 'BUY_ANIMAL'):
                    why = 'cash' if pre_money < price else ('shed' if pre_total >= cap else '?')
                else:
                    why = 'cash'
            cur['commits'].append((op, item, ok, why, price))
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if farm is cur['farm']:
            cur['hires'].append(farm['money'] != m0)
    opm = K._process_market
    def pm(state, env):
        st = int(state[0].observation.step)
        if st >= S:
            cur['farm'] = state[0].observation.farms[P]
            cur['commits'] = []; cur['hires'] = []
            priv = state[P].observation.private
            a = state[P].action
            q = list(a.get('market', []) or []) if isinstance(a, dict) else []
            shed0 = sum(priv['shed'].values())
            money0 = float(cur['farm']['money'])
        r = opm(state, env)
        if st >= S:
            out = []; ci = 0; hi = 0; cm = cur['commits']
            for i, o in enumerate(q):
                o = list(o) if isinstance(o, (list, tuple)) else o
                if i >= 10:
                    out.append([o[0] if o else None, o[1] if len(o) > 1 else None, int(o[2]) if len(o) > 2 else 0, 0, 'cut']); continue
                if not o:
                    continue
                if o[0] == 'HIRE':
                    ok = cur['hires'][hi] if hi < len(cur['hires']) else None; hi += 1
                    out.append(['HIRE', None, 1, 1 if ok else 0, '' if ok else 'hire_cash']); continue
                if o[0] == 'BUY_LAND':
                    out.append(['BUY_LAND', None, 1, None, '']); continue
                n = int(o[2]) if len(o) > 2 else 0
                f = 0; why = ''
                while ci < len(cm) and f < n:
                    op, item, ok, w, px = cm[ci]
                    if op != o[0] or item != o[1]:
                        break
                    ci += 1
                    if ok:
                        f += 1
                    else:
                        why = w; break
                out.append([o[0], o[1], n, f, why])
            rec['orders'][st] = dict(o=out, shed0=shed0, money0=money0)
            cur['farm'] = None
            if st == 718:
                pv = state[P].observation.private
                rec['end'] = dict(seeds={k: int(v) for k, v in dict(pv['seeds']).items() if int(v)},
                                  shed={k: int(v) for k, v in dict(pv['shed']).items() if int(v)},
                                  inv=[{k: int(v) for k, v in dict(x).items() if int(v)} for x in pv['inventories']],
                                  px={k: int(v) for k, v in dict(state[0].observation.market['prices']).items()})
        return r
    def ours(obs, cfg=None):
        cur['step'] = int(obs['step'])
        a = A(obs, cfg)
        st = int(obs['step'])
        g = G.get('_GC')
        if st >= S and st % 24 == 0 and g is not None and getattr(g, 'day_plan', None) == st // 24:
            try:
                rec['h0'][st // 24] = dict(sell0=getattr(g, 'sell0', None), orders0=getattr(g, 'orders0', None),
                                          orders1=getattr(g, 'orders1', None), hires=getattr(g, 'hires_planned', None),
                                          reserve=dict(getattr(g, 'reserve', {}) or {}), n_anim=getattr(g, 'n_animals', None),
                                          shed={k: int(v) for k, v in dict(obs['private']['shed']).items() if int(v)},
                                          seeds={k: int(v) for k, v in dict(obs['private']['seeds']).items() if int(v)},
                                          money=float(obs['farms'][P]['money']), market=a.get('market'))
            except Exception as e:
                rec['h0'][st // 24] = repr(e)
        return a
    K._commit_unit = commit; K._do_hire = hire; K._process_market = pm
    t0 = time.time()
    try:
        ag = [None, None]; ag[P] = _prefixed(ours, d['acts'], P, S); ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._do_hire = oh; K._process_market = opm; C._useful = o_useful
    rep = {k: v for k, v in (G.get('_GC_REPORT') or {}).items() if isinstance(v, (int, float, str))}
    return dict(gid=d['id'], opp=names[O], cand=cand, S=S, m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None,
                us=r['r'][P], err=r['err'], orders=rec['orders'], h0=rec['h0'], noop=dict(rec['noop']), end=rec.get('end'), rep=rep,
                wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    split, S, cand, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    want = None if sys.argv[5] == 'all' else set(int(x) for x in sys.argv[5].split(','))
    jobs = []
    for f in sorted(os.listdir(split), key=lambda s: int(s.split('.')[0])):
        with open(os.path.join(split, f), encoding='utf-8') as fh:
            head = fh.read(400)
        gid = int(head.split('"id":')[1].split(',')[0])
        if want is None or gid in want:
            jobs.append((os.path.join(split, f), S, cand))
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(r['gid'], r['opp'], r['m'], r['wall'], flush=True)
