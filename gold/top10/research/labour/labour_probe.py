"""Labour audit: per player, per day, what every unit-turn did.

Instruments the engine (K.interpreter, K._apply_unit_action, K._do_hire) and records per day:
  ut        unit-turns available (farmer + hands present at the step)
  hut       hand-turns
  noact     units present with no action submitted (hands list shorter than the roster)
  pass      PASS actions
  mv        effective moves (position changed), mvx = move no-ops (edge)
  e:OP      effective actions by op (state changed), n:OP no-op actions by op
  wy / wm   effective waters that added yield / maintenance-only waters
  hv:P      units harvested of product P
  hire / wage   hires made / dollars paid
  q:QUAD    effective tile actions per quadrant (plant/water/harvest/feed/care/collect/fert/dig/build/place-animal)
  dist      sum of Manhattan distance (to the nearest shed-access tile) of those tile actions
  c:...     census at the start of hour 23: c:P:CROP planted tiles, c:A:ANIMAL animals, c:empty, c:weed,
            c:struct (empty coop/pasture), c:owned
Usage:
  labour_probe.py rec  corpus.jsonl[.gz] teams_csv out.jsonl [max_games]      # replay recorded games (both seats)
  labour_probe.py gate games.jsonl.gz refs.jsonl cand.py out.jsonl [gid_seat_file] # candidate vs repaired elite
"""
import sys, os, json, gzip, collections, time
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

TILE_OPS = {'PLANT', 'WATER', 'HARVEST', 'FERTILIZE', 'DIG', 'BUILD_COOP', 'BUILD_PASTURE', 'FEED',
            'COLLECT_FERTILIZER', 'CARE'}
SHED = [(4, 4), (5, 4), (4, 5), (5, 5)]


def _quad(x, y):
    return ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')


def _dist(x, y):
    return min(abs(x - a) + abs(y - b) for a, b in SHED)


class Probe:
    def __init__(self):
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        self.K = K
        self.farms = None
        self.step = 0
        self.S = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
        self.orig = {}

    def install(self):
        K = self.K
        self.orig = dict(interpreter=K.interpreter, apply=K._apply_unit_action, hire=K._do_hire)
        oi, oa, oh = self.orig['interpreter'], self.orig['apply'], self.orig['hire']
        P = self

        def interp(state, env):
            obs0 = state[0].observation
            if hasattr(obs0, 'farms') and obs0.farms and not env.done:
                P.farms = obs0.farms
                step = obs0.get('step', 0) if hasattr(obs0, 'get') else 0
                P.step = step
                day, hour = step // 24, step % 24
                for i, s in enumerate(state):
                    farm = obs0.farms[i]
                    c = P.S[i][day]
                    nh = len(farm['hands'])
                    c['ut'] += 1 + nh; c['hut'] += nh
                    a = s.action if isinstance(s.action, dict) else {}
                    ha = a.get('hands', []) if isinstance(a, dict) else []
                    ha = ha if isinstance(ha, list) else []
                    c['noact'] += max(0, nh - len(ha))
                    if hour == 23:
                        P._census(farm, c)
            return oi(state, env)

        def apply(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
            if P.farms is None:
                return oa(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
            pid = 0 if farm is P.farms[0] else 1
            c = P.S[pid][day]
            pos = K._farmer_position(farm, idx)
            if pos is None or not isinstance(action, list) or not action:
                c['noact'] += 1 if pos is not None else 0
                return oa(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
            op = action[0]
            x, y = pos[0], pos[1]
            tile = farm['tiles'][y][x]
            tb = dict(tile) if isinstance(tile, dict) else tile
            inv = K._farmer_inventory(private, idx)
            ib = dict(inv)
            sb = sum(private['shed'].values())
            yb = tile.get('yield_units', 0) if isinstance(tile, dict) else 0
            r = oa(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
            pos2 = K._farmer_position(farm, idx)
            if op in K.FARMER_MOVES:
                if tuple(pos2) != (x, y):
                    c['mv'] += 1; c['mv_h' if idx else 'mv_f'] += 1
                else:
                    c['mvx'] += 1
                return r
            if op == 'PASS':
                c['pass'] += 1
                return r
            t2 = farm['tiles'][y][x]
            ta = dict(t2) if isinstance(t2, dict) else t2
            inv2 = K._farmer_inventory(private, idx)
            eff = (ta != tb) or (dict(inv2) != ib) or (sum(private['shed'].values()) != sb)
            c[('e:' if eff else 'n:') + op] += 1
            if eff:
                c['eff_h' if idx else 'eff_f'] += 1
                crop = (tb.get('crop') if isinstance(tb, dict) else None) or (ta.get('crop') if isinstance(ta, dict) else None) \
                    or (tb.get('animal') if isinstance(tb, dict) else None)
                if crop and op in ('PLANT', 'WATER', 'HARVEST', 'FERTILIZE', 'DIG', 'FEED', 'CARE', 'COLLECT_FERTILIZER'):
                    c['k:%s:%s' % (op[:4], crop)] += 1
                    if op == 'HARVEST' and isinstance(tb, dict) and tb.get('kind') == 'PLANT':
                        c['age:%s' % crop] += day - int(tb.get('planted_day', day))
                if op == 'WATER':
                    ya = t2.get('yield_units', 0) if isinstance(t2, dict) else 0
                    c['wy' if ya > yb else 'wm'] += 1
                elif op == 'HARVEST':
                    for k, v in inv2.items():
                        d = v - ib.get(k, 0)
                        if d > 0:
                            c['hv:' + k] += d
                    if isinstance(tb, dict) and tb.get('kind') == 'PLANT' and not K.CROPS[tb['crop']]['ongoing']:
                        # units lost to over-ripeness: a one-time crop harvested after its decay began
                        mls = int(tb.get('max_lifespan_step', -1))
                        if 0 <= mls <= P.step:
                            c['late:' + tb['crop']] += 1
                if op in TILE_OPS or (op == 'PLACE' and isinstance(t2, dict) and 'animal' in t2 and not (isinstance(tb, dict) and 'animal' in tb)):
                    c['q:' + _quad(x, y)] += 1
                    c['dist'] += _dist(x, y); c['tile_acts'] += 1
            return r

        def hire(farm, private, bs, mult=1):
            m0 = farm['money']
            r = oh(farm, private, bs, mult)
            if P.farms is not None and farm['money'] != m0:
                pid = 0 if farm is P.farms[0] else 1
                c = P.S[pid][P.step // 24]
                c['hire'] += 1; c['wage'] += m0 - farm['money']
            return r

        od = K._drop_inventories_to_shed
        self.orig['drop'] = od
        P.privs = []

        def drop(private, capacity):
            # night drop: count units discarded for want of shed room, by product and by carrying unit index
            before = collections.Counter()
            for inv in private['inventories']:
                for k, v in inv.items():
                    if v > 0:
                        before[k] += v
            shed0 = collections.Counter({k: v for k, v in private['shed'].items() if v})
            r = od(private, capacity)
            if P.farms is not None:
                pid = next((i for i, pv in enumerate(P.privs) if pv is private), None)
                if pid is not None:
                    c = P.S[pid][P.step // 24]
                    for k, v in before.items():
                        lost = shed0[k] + v - private['shed'].get(k, 0)
                        if lost > 0:
                            c['lost:' + k] += lost
                    c['carry_night'] += sum(before.values()); c['shed_eve'] += sum(shed0.values())
            return r

        oi2 = interp

        def interp2(state, env):
            try:
                P.privs = [s.observation.private for s in state]
            except Exception:
                pass
            return oi2(state, env)

        K.interpreter = interp2; K._apply_unit_action = apply; K._do_hire = hire; K._drop_inventories_to_shed = drop

    def uninstall(self):
        K = self.K
        K.interpreter = self.orig['interpreter']; K._apply_unit_action = self.orig['apply']; K._do_hire = self.orig['hire']
        K._drop_inventories_to_shed = self.orig['drop']

    def _census(self, farm, c):
        owned = set(farm['unlocked_quadrants'])
        for y in range(10):
            for x in range(10):
                if _quad(x, y) not in owned:
                    continue
                t = farm['tiles'][y][x]
                c['c:owned'] += 1
                if t is None:
                    c['c:empty'] += 1
                elif isinstance(t, dict):
                    k = t.get('kind')
                    if k == 'PLANT':
                        c['c:P:' + t['crop']] += 1
                        c['c:Pq:' + _quad(x, y)] += 1
                    elif 'animal' in t:
                        c['c:A:' + t['animal']] += 1
                        c['c:Aq:' + _quad(x, y)] += 1
                    elif k == 'WEED':
                        c['c:weed'] += 1
                    else:
                        c['c:struct'] += 1

    def result(self):
        return [{str(d): dict(c) for d, c in sorted(self.S[i].items())} for i in range(2)]


def _rec_job(d):
    import lean, pinned4
    P = Probe(); P.install()
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned4._tape(d['acts'], 0), pinned4._tape(d['acts'], 1)])
    finally:
        P.uninstall()
    return dict(gid=d['id'], teams=d['info']['TeamNames'], rec=d['rewards'], r=r['r'], days=P.result())


def _gate_job(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    P = Probe(); P.install()
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        P.uninstall(); K._end_of_day = orig
    days = P.result()
    return dict(gid=ref['gid'], seat=s, team=ref['team'], cand=cand, elite=r['r'][s], us=r['r'][1 - s],
                m=r['r'][1 - s] - r['r'][s], err=r['err'], wall=round(time.time() - t0, 1),
                days_us=days[1 - s], days_elite=days[s])


def _iter_corpus(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as fh:
        for l in fh:
            if l.strip():
                yield l


if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor
    mode = sys.argv[1]
    nproc = int(os.environ.get('NPROC', '2'))
    if mode == 'rec':
        paths, teams, out = sys.argv[2].split(','), set(sys.argv[3].split(',')), sys.argv[4]
        maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6

        def gen():
            n = 0
            for p in paths:
                for l in _iter_corpus(p):
                    # cheap prefilter on the header before decoding the whole game
                    head = l[:400]
                    if not any(t in head for t in teams):
                        continue
                    d = json.loads(l)
                    if len(d.get('acts', [])) != 720 or not (set(d['info']['TeamNames']) & teams):
                        continue
                    yield d
                    n += 1
                    if n >= maxg:
                        return
        t0 = time.time(); k = 0
        with ProcessPoolExecutor(nproc) as ex, open(out, 'w', encoding='utf-8') as fh:
            for x in ex.map(_rec_job, gen(), chunksize=1):
                fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush(); k += 1
        print('rec games', k, 'wall', round(time.time() - t0))
    else:
        from eval_elite_routes import load_games
        gpath, refs, cand, out = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        want = None
        if len(sys.argv) > 6:
            want = {tuple(map(int, l.split())) for l in open(sys.argv[6]) if l.strip()}
        R = []
        for l in open(refs, encoding='utf-8'):
            r = json.loads(l)
            if want is None or (r['gid'], r['seat']) in want:
                R.append(r)
        gids = {r['gid'] for r in R}
        games = {g['id']: g for g in load_games(gpath) if g['id'] in gids}
        jobs = [(games[r['gid']], r, cand) for r in R]
        t0 = time.time()
        with ProcessPoolExecutor(nproc) as ex, open(out, 'w', encoding='utf-8') as fh:
            for x in ex.map(_gate_job, jobs):
                fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
        print('gate seats', len(jobs), 'wall', round(time.time() - t0))
