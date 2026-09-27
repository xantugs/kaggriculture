"""gold/harness/pinned4.py with the candidate's worst step time (tmax, seconds) and its telemetry in every row, plus resume.
Same pinned world and row fields (gid, m, led_us, led_them, tel, ...). One-game files <corpus>.d/<i>.json are written by
the main process; each worker loads only its own game. (Night-drop track; named apart from the other agents' tools.)
Rows also carry disc {item: units} and disc_v ($ at the evening price): goods our farm lost at the night drops.
usage: shed_gate.py games.json S cand1[,cand2] out.jsonl [team=offhand]   (env NPROC, PIN_GIDS)"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor, as_completed
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402


def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, idx, team, cand, S = t
    t0 = time.time()
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)[idx]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, rref = reference(d)
    rec_ok = [int(x) for x in rref] == [int(x) for x in d['rewards']]
    orig = install_pinned(S // 24, O, spawns, shops)
    led = [collections.Counter(), collections.Counter()]
    FARMS = [None, None]
    oc = K._commit_unit

    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL': led[i][item] += price
            elif op == 'BUY_PRODUCT': led[i][item] -= price
            elif op == 'BUY_SEED': led[i]['seed'] -= price
            elif op == 'BUY_ANIMAL': led[i]['anim'] -= price
        return ok
    opm = K._process_market

    def pm(state, env):
        if state[0].observation.step >= S:
            FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    oh = K._do_hire

    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            led[i]['hire'] += farm['money'] - m0
    # night-drop discards of our farm (units and $ at the evening price), measured at the engine's drop
    DISC = collections.Counter(); DV = [0.0]; OURS = {}
    o_int = K.interpreter; o_drop = K._drop_inventories_to_shed

    def interp(state, env):
        out = o_int(state, env)
        if 'priv' not in OURS and state[0].observation.get('farms'):
            OURS['priv'] = state[P].observation.private; OURS['mkt'] = state[0].observation.market
        return out

    def drop(private, cap):
        if private is not OURS.get('priv'):
            return o_drop(private, cap)
        shed = private['shed']; s0 = dict(shed); tot = collections.Counter()
        for inv in private['inventories']:
            for k_, v_ in inv.items():
                if v_ > 0:
                    tot[k_] += v_
        out = o_drop(private, cap)
        for k_, n_ in tot.items():
            lost = n_ - (shed.get(k_, 0) - s0.get(k_, 0))
            if lost > 0:
                DISC[k_] += lost; DV[0] += lost * float(OURS['mkt']['prices'].get(k_, 0))
        return out
    K._commit_unit = commit; K._process_market = pm; K._do_hire = hire
    K.interpreter = interp; K._drop_inventories_to_shed = drop
    try:
        A = lean.load(cand)
        ag = [None, None]
        ag[P] = _prefixed(A, d['acts'], P, S)
        ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh
        K.interpreter = o_int; K._drop_inventories_to_shed = o_drop
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    return dict(led_us=dict(led[P]), led_them=dict(led[O]), gid=d['id'], opp=names[O], cand=cand, S=S,
                rec=d['rewards'][P] - d['rewards'][O], rec_ok=rec_ok, us=r['r'][P], them=r['r'][O],
                m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None, err=r['err'], tel=tel,
                tmax=r['tmax'][P], tsum=r['tsum'][P], disc=dict(DISC), disc_v=round(DV[0], 1), wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    f = sys.argv[1]; S = int(sys.argv[2]); cands = sys.argv[3].split(','); out = sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    want = set(int(x) for x in open(os.environ["PIN_GIDS"]).read().split()) if os.environ.get("PIN_GIDS") else None
    split = f + '.d'
    games = []
    corpus = json.load(open(f, encoding='utf-8'))
    for i, d in enumerate(corpus):
        if team in d['info']['TeamNames'] and (want is None or d['id'] in want):
            one = os.path.join(split, '%d.json' % i)
            if not os.path.exists(one):
                os.makedirs(split, exist_ok=True)
                json.dump([d], open(one, 'w', encoding='utf-8'))
            games.append((one, d['id']))
    del corpus
    import gc; gc.collect()
    done = set()
    if os.path.exists(out):
        for line in open(out, encoding='utf-8'):
            try:
                rr = json.loads(line)
                if rr.get('m') is not None:
                    done.add((rr['gid'], rr['cand']))
            except ValueError:
                pass
    jobs = [(p, 0, team, c, S) for p, g in games for c in cands if (g, c) not in done]
    print('games %d  done %d  jobs %d  NPROC %s' % (len(games), len(done), len(jobs), os.environ.get('NPROC', '3')), flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        futs = {ex.submit(job, j): j for j in jobs}
        for k, fu in enumerate(as_completed(futs)):
            try:
                rr = fu.result()
            except Exception as e:
                print('JOB FAILED', futs[fu][0], repr(e)[:200], flush=True)
                continue
            fh.write(json.dumps(rr, ensure_ascii=False) + '\n'); fh.flush()
            print('%s %s %s m %s tmax %.3f [%d/%d %.0fs]' % (rr['gid'], rr['opp'], rr['cand'].split('/')[-1], rr['m'], rr['tmax'],
                                                          k + 1, len(jobs), time.time() - t0), flush=True)
    print('done %.0fs' % (time.time() - t0))
