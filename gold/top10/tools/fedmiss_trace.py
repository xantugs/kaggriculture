"""Why are animals CAREd but not FED on their production night (care_fedmiss in scan.py), and how much of anim_cap is
recoverable? Instrumented S=0 replay of the live games (same world as scan.py / pinned4.py).

Per game it records, for OUR farm:
  start      first step the controller owns the farm (lean agent's _GC_RICH['taken']); 999 = never
  fm         [[day, kind, x, y, pend, px, phase, care_idx, care_hour, wheat_at_care, dropped_w_before, pick_req, pick_got,
               feeds_by_unit_before, cause]]  production nights, cared, not fed, pending bonus > 0 (the bonus is wiped)
  fmn        the same on NON-production nights (cared, unfed: the day's care is not banked, and a first strike)
  drops      [[day, hour, idx, wheat dropped, FEEDs left in its queue, fertilizer dropped, FERTILIZEs left]] controller-phase
             DROPs of a unit carrying wheat or fertilizer (the engine's DROP empties the whole inventory)
  acap       [[day, prod, k_total, k_pending_only]]  product clipped by max_held; k_pending_only = the part that a harvest
             before the night could not have saved (yield 0 + 1 + pending > max_held)
cause: 'drop' = the unit DROPped wheat earlier that day and held none when it cared; 'short' = its wheat pickups got fewer
units than asked; 'nowheat' = held none, never dropped any; 'had' = it held wheat when it cared (no FEED issued).

usage: fedmiss_trace.py games.json.d S cand out.jsonl [team]   (env NPROC, PIN_GIDS)  resumable by gid"""
import sys, os, json, time, collections, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402


def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, team, cand, S = t
    t0 = time.time()
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    st = dict(farm=None, priv=None, mkt=None, step=0, start=999)
    unit = collections.defaultdict(lambda: dict(dropw=0, preq=0, pgot=0, feeds=0))   # (day, idx) -> counters
    care = {}          # (day, x, y) -> (idx, hour, wheat held, dropped before, pick req, pick got, feeds before)
    fm = []; fmn = []; acap = []; drops = []; G_ = {}
    o_int = K.interpreter; o_apply = K._apply_unit_action; o_ra = K._daily_refresh_animals

    def interp(state, env):
        obs0 = state[0].observation
        if st['farm'] is not None:
            st['step'] = int(obs0.get('step', 0))
        out = o_int(state, env)
        if st['farm'] is None and obs0.get('farms'):
            st['farm'] = obs0.farms[P]; st['priv'] = state[P].observation.private; st['mkt'] = obs0.market
        return out

    def apply(farm, private, idx, action, bs, day, tpd, cap=100):
        if farm is not st['farm'] or not isinstance(action, list) or not action:
            return o_apply(farm, private, idx, action, bs, day, tpd, cap)
        op = action[0]
        invs = private['inventories']; inv = invs[idx] if idx < len(invs) else {}
        u = unit[(day, idx)]
        pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
        if op == 'DROP':
            u['dropw'] += int(inv.get('WHEAT', 0))
            w_, f_ = int(inv.get('WHEAT', 0)), int(inv.get('FERTILIZER', 0))
            if w_ or f_:
                gc = G_.get('_GC') if G_ else None
                q = (getattr(gc, 'queues', {}) or {}).get(idx) or [] if (gc is not None and day * 24 >= st['start']) else None
                if q is not None:
                    drops.append([day, st['step'] % 24, idx, w_, sum(1 for it in q if it[1][0] == 'FEED'), f_,
                                  sum(1 for it in q if it[1][0] == 'FERTILIZE')])
        elif op == 'PICKUP' and len(action) >= 2 and action[1] == 'WHEAT':
            w0 = int(inv.get('WHEAT', 0))
            out = o_apply(farm, private, idx, action, bs, day, tpd, cap)
            inv = private['inventories'][idx]
            u['preq'] += int(action[2]) if len(action) >= 3 else 1; u['pgot'] += int(inv.get('WHEAT', 0)) - w0
            return out
        elif op in ('CARE', 'FEED') and pos is not None:
            t = farm['tiles'][pos[1]][pos[0]]
            if isinstance(t, dict) and 'animal' in t:
                if op == 'CARE' and not t['cared_today']:
                    care[(day, pos[0], pos[1])] = (idx, st['step'] % 24, int(inv.get('WHEAT', 0)), u['dropw'], u['preq'],
                                                   u['pgot'], u['feeds'])
                if op == 'FEED' and not t['fed_today'] and int(inv.get('WHEAT', 0)) > 0:
                    u['feeds'] += 1
        return o_apply(farm, private, idx, action, bs, day, tpd, cap)

    def ra(farm, day):
        if farm is st['farm']:
            px = st['mkt']['prices']
            phase = 'ctl' if day * 24 >= st['start'] else 'chs'
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if not (isinstance(t, dict) and 'animal' in t):
                        continue
                    kind = t['animal']; a = K.ANIMALS[kind]; prod = a['product']; fed = t['fed_today']
                    if not fed and t['consecutive_unfed'] + 1 >= 2:
                        continue                         # escapes: scan.py's category
                    dsf = day + 1 - t['placed_day'] - a['first_yield_day']
                    prodn = dsf >= 0 and dsf % a['interval'] == 0
                    pend = int(t.get('pending_care_bonus', 0) or 0)
                    if prodn:
                        add = 1 + (pend if fed else 0)
                        k = max(0, t['yield_units'] + add - a['max_held'])
                        if k:
                            acap.append([day, prod, k, min(k, max(0, add - a['max_held'])), int(px[prod]), phase])
                    if t['cared_today'] and not fed:
                        c = care.get((day, x, y))
                        if c:
                            idx, hr, w, dw, pr, pg, fd = c
                            cause = 'had' if w > 0 else ('drop' if dw > 0 else ('short' if pg < pr else 'nowheat'))
                        else:
                            idx = hr = w = dw = pr = pg = fd = -1; cause = '?'
                        rec = [day, kind, x, y, pend, int(px[prod]), phase, idx, hr, w, dw, pr, pg, fd, cause]
                        if prodn and pend > 0:
                            fm.append(rec)
                        elif not prodn:
                            fmn.append(rec)
        return o_ra(farm, day)

    try:
        spawns, shops, rref = reference(d)
        orig = install_pinned(S // 24, O, spawns, shops)
        K.interpreter = interp; K._apply_unit_action = apply; K._daily_refresh_animals = ra
        try:
            A = lean.load(cand)
            G = A.__globals__; G_.update(G)

            def ours(obs, cfg=None):
                a = A(obs, cfg)
                gr = G.get('_GC_RICH')
                if st['start'] == 999 and isinstance(gr, dict) and gr.get('taken'):
                    st['start'] = int(obs['step'])
                return a
            ag = [None, None]
            ag[P] = _prefixed(ours, d['acts'], P, S)
            ag[O] = _tape(d['acts'], O)
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            K.interpreter = o_int; K._apply_unit_action = o_apply; K._daily_refresh_animals = o_ra
            K._end_of_day = orig
        m = (r['r'][P] - r['r'][O]) if r['r'][P] is not None and r['r'][O] is not None else None
        return dict(gid=d['id'], opp=names[O], cand=cand, S=S, m=m, start=st['start'], fm=fm, fmn=fmn, acap=acap, drops=drops,
                    err=r['err'], tmax=r['tmax'][P], wall=round(time.time() - t0, 1))
    except Exception:
        return dict(gid=d['id'], opp=names[O], cand=cand, S=S, m=None, exc=traceback.format_exc()[-1500:],
                    wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    split, S, cand, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    want = set(int(x) for x in open(os.environ['PIN_GIDS']).read().split()) if os.environ.get('PIN_GIDS') else None
    done = set()
    if os.path.exists(out):
        for line in open(out, encoding='utf-8'):
            try:
                r = json.loads(line)
                if r.get('m') is not None:
                    done.add(r['gid'])
            except ValueError:
                pass
    jobs = []
    for f in sorted(os.listdir(split), key=lambda s: int(s.split('.')[0])):
        p = os.path.join(split, f)
        with open(p, encoding='utf-8') as fh:
            head = fh.read(400)
        gid = int(head.split('"id":')[1].split(',')[0]) if '"id":' in head else None
        if gid is None:
            gid = json.load(open(p, encoding='utf-8'))[0]['id']
        if (want is None or gid in want) and gid not in done:
            jobs.append((p, team, cand, S))
    print('jobs', len(jobs), 'done', len(done), flush=True)
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        futs = [ex.submit(job, j) for j in jobs]
        for fu in as_completed(futs):
            r = fu.result(); n += 1
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(r['gid'], r.get('opp'), 'm', r.get('m'), 'start', r.get('start'), 'fm', len(r.get('fm', [])),
                  'EXC' if r.get('exc') else '', '[%d/%d %.0fs]' % (n, len(jobs), time.time() - t0), flush=True)
