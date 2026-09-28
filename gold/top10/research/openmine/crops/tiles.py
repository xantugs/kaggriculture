"""Tile-level crop lifecycles: every planting of a seat, with its tile, the day/hour planted, watering and fertilizer
days, every harvest (day, hour, units) and how it ended (H harvested out, D dug, W turned to weed by thirst or rot,
None still standing at the end).

usage (run from kg/, NPROC workers, default 4):
  tiles.py elite [date_min]            # recorded games in openmine/games (target seats only), date >= date_min
                                       #   (default 2026-09-23) -> crops/tiles_elite.jsonl
  tiles.py ours ours_T7_seats.jsonl    # the same games as an extract.py 'ours' run (elite_gate set-up, cand from the
                                       #   seat rows): both farms -> crops/tiles_<tag>.jsonl (roles ours / elite_rep)
Row: gid date seat team opp role shops[8] plantings[[crop, pd, ph, x, y, Q, waters[days], ferts[days],
     harvests[[d, h, units]], end, end_d]]
"""
import sys, os, json, gzip, time, collections
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
KG = os.path.normpath(os.path.join(OM, '..', '..', '..', '..'))
for p in ('arena', 'gold/harness', 'gold/elite', OM):
    sys.path.insert(0, p if os.path.isabs(p) else os.path.join(KG, p))
GAMES = os.path.join(OM, 'games')
TEAMS = os.environ.get('TEAMS', 'Boey,Fourth Quadrant,吃白饭的大肥鱼,Yizhou,THIRD FARM CLUB').split(',')


class Tracker:
    def __init__(self):
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        self.K = K
        self.FARMS = [None, None]
        self.step = 0
        self.open = [dict(), dict()]      # (x, y) -> planting record
        self.done = [[], []]
        self.orig = None

    def pid(self, farm):
        if farm is self.FARMS[0]: return 0
        if farm is self.FARMS[1]: return 1
        return None

    def _check(self, p, farm, day):
        """Close open plantings whose tile no longer holds that plant (thirst weed / rot)."""
        op = self.open[p]
        for key in list(op):
            r = op[key]
            x, y = key
            t = farm['tiles'][y][x]
            if not (isinstance(t, dict) and t.get('kind') == 'PLANT' and t.get('crop') == r[0] and t.get('planted_day') == r[1]):
                r[9] = 'W'; r[10] = day
                self.done[p].append(op.pop(key))

    def install(self):
        K = self.K; T = self
        self.orig = dict(interpreter=K.interpreter, _apply_unit_action=K._apply_unit_action,
                         _decay_plants=K._decay_plants, _daily_refresh_plants=K._daily_refresh_plants)
        oi, oa, od, orf = (self.orig[k] for k in ('interpreter', '_apply_unit_action', '_decay_plants', '_daily_refresh_plants'))

        def interp(state, env):
            o = state[0].observation
            farms = getattr(o, 'farms', None)
            if farms:
                T.step = int(K.get(o, 'step', 0))
                T.FARMS[0], T.FARMS[1] = farms[0], farms[1]
            return oi(state, env)

        def act(farm, private, idx, action, board_size, day, tpd, cap=100):
            p = T.pid(farm)
            if p is None or not isinstance(action, list) or not action or action[0] not in ('PLANT', 'WATER', 'HARVEST', 'FERTILIZE', 'DIG'):
                return oa(farm, private, idx, action, board_size, day, tpd, cap)
            pos = K._farmer_position(farm, idx)
            if pos is None:
                return oa(farm, private, idx, action, board_size, day, tpd, cap)
            x, y = pos[0], pos[1]
            t0 = farm['tiles'][y][x]
            pre = dict(t0) if isinstance(t0, dict) else t0
            r = oa(farm, private, idx, action, board_size, day, tpd, cap)
            t1 = farm['tiles'][y][x]
            h = T.step % 24
            op = action[0]
            key = (x, y)
            rec = T.open[p].get(key)
            if op == 'PLANT':
                if isinstance(t1, dict) and t1.get('kind') == 'PLANT' and pre is None:
                    if rec is not None:          # stale record (should not happen)
                        rec[9] = 'W'; rec[10] = day; T.done[p].append(T.open[p].pop(key))
                    T.open[p][key] = [t1['crop'], day, h, x, y, K._quadrant_of(x, y, board_size), [], [], [], None, None]
                return r
            if not (isinstance(pre, dict) and pre.get('kind') == 'PLANT') or rec is None:
                return r
            if op == 'WATER':
                if not pre.get('watered_today') and isinstance(t1, dict) and t1.get('watered_today'):
                    rec[6].append(day)
            elif op == 'FERTILIZE':
                if isinstance(t1, dict) and t1.get('fertilized_until_day', -1) != pre.get('fertilized_until_day', -1):
                    rec[7].append(day)
            elif op == 'HARVEST':
                u = pre.get('yield_units', 0)
                if t1 != pre and u > 0:
                    rec[8].append([day, h, u])
                    if not (isinstance(t1, dict) and t1.get('kind') == 'PLANT'):
                        rec[9] = 'H'; rec[10] = day; T.done[p].append(T.open[p].pop(key))
            elif op == 'DIG':
                if t1 is None:
                    rec[9] = 'D'; rec[10] = day; T.done[p].append(T.open[p].pop(key))
            return r

        def decay(farm, step):
            r = od(farm, step)
            p = T.pid(farm)
            if p is not None and T.open[p]:
                T._check(p, farm, step // 24)
            return r

        def refresh(farm, current_day, tpd):
            r = orf(farm, current_day, tpd)
            p = T.pid(farm)
            if p is not None and T.open[p]:
                T._check(p, farm, current_day + 1)
            return r

        K.interpreter = interp; K._apply_unit_action = act; K._decay_plants = decay; K._daily_refresh_plants = refresh

    def uninstall(self):
        for k, v in (self.orig or {}).items():
            setattr(self.K, k, v)

    def plantings(self, p):
        return sorted(self.done[p] + list(self.open[p].values()), key=lambda r: (r[1], r[2], r[4], r[3]))


def _load(path):
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        return json.load(fh)


def job_elite(t):
    import lean, pinned4
    path, date, seats = t
    d = _load(path)
    T = Tracker(); T.install()
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned4._tape(d['acts'], 0), pinned4._tape(d['acts'], 1)])
    finally:
        T.uninstall()
    names = d['info']['TeamNames']
    ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
    return [dict(gid=d['id'], date=date, seat=s, team=names[s], opp=names[1 - s], role='rec', rec_ok=ok,
                 shops=list(r['shops']), rew=[r['r'][s], r['r'][1 - s]], plantings=T.plantings(s)) for s in seats]


def job_ours(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent, reference_log
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, date, s, cand, tag = t
    d = _load(path)
    ref = reference_log(d, s)
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
    orig_eod = install_town(ref['shops'])
    T = Tracker(); T.install()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        T.uninstall(); K._end_of_day = orig_eod
    names = d['info']['TeamNames']
    out = []
    for p, role in ((1 - s, 'ours'), (s, 'elite_rep')):
        out.append(dict(gid=d['id'], date=date, seat=p, team=(tag if role == 'ours' else names[s]),
                        opp=(names[s] if role == 'ours' else tag), role=role, shops=list(r['shops']),
                        rew=[r['r'][p], r['r'][1 - p]], plantings=T.plantings(p)))
    return out


def _index():
    return [json.loads(l) for l in open(os.path.join(GAMES, 'index.jsonl'), encoding='utf-8') if l.strip()]


def run_elite(dmin):
    idx = [r for r in _index() if r['date'] >= dmin]
    jobs = [(os.path.join(GAMES, r['file']), r['date'], r['seats']) for r in idx]
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, \
            open(os.path.join(HERE, 'tiles_elite.jsonl'), 'w', encoding='utf-8') as fo:
        for i, res in enumerate(ex.map(job_elite, jobs, chunksize=2)):
            for row in res:
                fo.write(json.dumps(row, ensure_ascii=False) + '\n'); n += 1
            if i % 50 == 0:
                fo.flush(); print(i, 'games', n, 'seats', 'T', round(time.time() - t0), flush=True)
    print('ALLDONE elite', n, 'seats', round(time.time() - t0), 's', flush=True)


def run_ours(seats_file):
    seats = [json.loads(l) for l in open(os.path.join(OM, seats_file), encoding='utf-8') if l.strip()]
    files = {r['gid']: (os.path.join(GAMES, r['file']), r['date']) for r in _index()}
    cand = None
    for c in ('gold/top10/cands', 'gold/top10'):
        f = os.path.join(KG, c, seats[0]['cand'])
        if os.path.exists(f): cand = f; break
    tag = seats[0]['team']
    jobs = [(files[s['gid']][0], files[s['gid']][1], s['elite_seat'], cand, tag) for s in seats]
    print(len(jobs), 'games cand', cand, flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, \
            open(os.path.join(HERE, 'tiles_%s.jsonl' % tag), 'w', encoding='utf-8') as fo:
        for i, res in enumerate(ex.map(job_ours, jobs)):
            for row in res:
                fo.write(json.dumps(row, ensure_ascii=False) + '\n')
            fo.flush()
            print(i, res[0]['opp'], res[0]['gid'], 'rew', res[0]['rew'], 'T', round(time.time() - t0), flush=True)
    print('ALLDONE ours', round(time.time() - t0), 's', flush=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'elite':
        run_elite(sys.argv[2] if len(sys.argv) > 2 else '2026-09-23')
    elif mode == 'ours':
        run_ours(sys.argv[2])
    elif mode == 'one':        # quick check: tiles.py one <gid>
        idx = {r['gid']: r for r in _index()}
        r = idx[int(sys.argv[2])]
        res = job_elite((os.path.join(GAMES, r['file']), r['date'], r['seats']))
        for row in res:
            print(row['team'], row['rec_ok'], len(row['plantings']))
            for p in row['plantings'][:400]:
                if p[1] <= 15: print('  ', p)
