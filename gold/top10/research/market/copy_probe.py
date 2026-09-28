"""pinned4.py job (S = 0, full game) + both farms' fills + an evening snapshot for the h23 pre-drop question:
at steps 24d+20..23 (before that step's market), for each farm: every unit's position, its carried premium goods
(MILK, WOOL, STRAWBERRY, MELON, EGG) and its walking distance to the nearest shed-access tile; plus the premium units
each farm carries into the night drop.
usage: copy_probe.py games.json S cand out.jsonl [team] ; env PIN_GIDS, NPROC (default 2)"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.path.insert(0, '/home/user/kaggriculture/arena')
import pinned4 as PN

PREM = ("MILK", "WOOL", "STRAWBERRY", "MELON", "EGG")
ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]


def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, idx, team, cand, S = t
    d = json.load(open(path, encoding='utf-8'))[idx]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, rref = PN.reference(d)
    orig = PN.install_pinned(S // 24, O, spawns, shops)
    FILLS = []; STEP = [0]; FARMS = [None, None]; SNAP = []; NIGHT = []
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None and op in ('SELL', 'BUY_PRODUCT'):
            i = 0 if farm is FARMS[0] else 1
            FILLS.append((STEP[0], op[0] if i == P else 'r' + op[0], item, price))
        return ok
    opm = K._process_market
    def pm(state, env):
        st = int(state[0].observation.step)
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = st
        if st % 24 >= 20 and 144 <= st < 528:
            row = [st]
            for side, pid in ((0, P), (1, O)):
                farm = state[0].observation.farms[pid]
                invs = state[pid].observation.private['inventories']
                pos = [farm['farmer']] + list(farm['hands'] or [])
                units = []
                for u, p_ in enumerate(pos):
                    inv = invs[u] if u < len(invs) else {}
                    c = {k: int(inv.get(k, 0)) for k in PREM if int(inv.get(k, 0)) > 0}
                    if c:
                        dist = min(abs(p_[0] - a) + abs(p_[1] - b) for a, b in ACCESS)
                        units.append([u, dist, c])
                shed = {k: int(state[pid].observation.private['shed'].get(k, 0)) for k in PREM}
                row.append([units, shed])
            SNAP.append(row)
        return opm(state, env)
    odr = K._drop_inventories_to_shed
    def drop(private, cap):
        c = collections.Counter()
        for inv in private['inventories']:
            for k in PREM:
                c[k] += int(inv.get(k, 0))
        k_ = sum(1 for x in NIGHT if x[0] == STEP[0])   # engine order: farm 0 then farm 1
        NIGHT.append([STEP[0], 0 if k_ == P else 1, dict(c)])
        return odr(private, cap)
    K._commit_unit = commit; K._process_market = pm; K._drop_inventories_to_shed = drop
    try:
        A = lean.load(cand)
        ag = [None, None]
        ag[P] = PN._prefixed(A, d['acts'], P, S)
        ag[O] = PN._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._drop_inventories_to_shed = odr
    return dict(gid=d['id'], opp=names[O], cand=cand, S=S, us=r['r'][P], them=r['r'][O],
                m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None, err=r['err'], fills=FILLS, snap=SNAP, night=NIGHT, P=P)


if __name__ == '__main__':
    f, S, cand, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    want = set(int(x) for x in open(os.environ["PIN_GIDS"]).read().split()) if os.environ.get("PIN_GIDS") else None
    split = f + '.d'
    games = []
    for i, d in enumerate(json.load(open(f, encoding='utf-8'))):
        if team in d['info']['TeamNames'] and (want is None or d['id'] in want):
            one = os.path.join(split, '%d.json' % i)
            if not os.path.exists(one):
                os.makedirs(split, exist_ok=True); json.dump([d], open(one, 'w', encoding='utf-8'))
            games.append((one, 0))
    jobs = [(g, i, team, cand, S) for g, i in games]
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get("NPROC", "2"))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for k, r in enumerate(ex.map(job, jobs)):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(k + 1, r['gid'], r['m'], round(time.time() - t0), flush=True)
