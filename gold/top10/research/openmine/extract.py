"""Opening mine: per-seat, per-day decision logs of recorded elite games (both tapes, exact replay) and of our build
in the same towns (elite_gate set-up: repaired elite tape in its recorded town vs the candidate).

usage (run from the worktree root kg/, NPROC workers, default 4):
  extract.py split                      # stream the 20-26 Sep corpora, write one-game files for games with a target
                                        #   team: openmine/games/<date>_<gid>.json.gz + games/index.jsonl
  extract.py elite [max_games]          # replay every indexed game, log every target seat
                                        #   -> elite_days.jsonl (one row per seat and day), elite_seats.jsonl
  extract.py ours cand.py [n_per_team] [tag]
                                        # cand vs repaired elite seats (balanced per team, rec_ok, latest dates first)
                                        #   -> ours_<tag>_days.jsonl / ours_<tag>_seats.jsonl (our seat, role 'ours')
                                        #      ours_<tag>_opp_days.jsonl / _opp_seats.jsonl (the repaired elite, 'elite_rep')
  extract.py verify gid [gid ...]       # replay recorded games, compare the logged cash series with the money the
                                        #   agents observe, and reconcile each day's cash change with the logged flows
env: TEAMS='A,B' overrides the target teams; NPROC.

Row of *_days.jsonl (seat s, day d; money in $, [n, $] pairs are units and total dollars):
  gid date seat team opp role cand d detail(bool, d<=16)
  m0 / m23 / mend   cash at the hour-0 observation, at the hour-23 observation, after the day's last step (= next m0;
                    day 29: m23 = mend = final money, the engine never plays step 719)
  mmin mmin_h       lowest observed cash that day and its hour
  sell{item:[n,$]} buy_prod{item:[n,$]} buy_seed{crop:[n,$]} buy_animal{kind:[n,$]} (executed market fills, hook _commit_unit)
  hires wage hire_h[hours]   (hook _do_hire; hands last one day, so hires = hands that day)
  land[{q,step,h,price,cash_before}]   (hook _do_buy_land)
  hands (max that day)  hands_h[24] (hand count at each hour's observation; detail rows)
  ops{VERB[:arg]@Q: n}  effective unit actions by verb, argument and quadrant of the acting unit (detail rows; light rows
                    carry ops without the quadrant). PLANT:crop, WATER:crop, HARVEST:product, FEED/CARE/COLLECT_FERTILIZER:
                    animal, FERTILIZE:crop, DIG:what, BUILD_COOP, BUILD_PASTURE, PLACE:animal (PLACE:shed:item),
                    PICKUP:item@shed, DROP@shed. fail{VERB:n} = no-op actions; move / pass / noact counts. hv{product: units}
  snapshot at hour 0: quads, herd{kind: placed}, crops{crop: tiles}, units{product: units standing/held on tiles},
                    struct{COOP/PASTURE: empty}, weeds, free, q{quadrant: {P:crop, A:animal, COOP, PASTURE, WEED, free}}
                    (detail), shed{item:n} and seeds{crop:n} (detail; animals bought but not placed sit in the shed)
  shops (town unlocked_shops at hour 0, i.e. shops known that day), px{item: price at hour 0} (detail)
  fills[[h, op, item, n, $]] per hour (detail; op S=sell BP=buy product BS=seed BA=animal H=hire L=land)
  riv  the rival's visible farm at hour 0: money quads herd crops struct weeds
Row of *_seats.jsonl: gid date seed seat team opp role cand rew[self, other] rec[recorded self, other] rec_ok shops
  land[...] recon_max (max over days of |mend - m0 - flows|) final{herd crops quads units} wall
"""
import sys, os, json, gzip, re, time, collections
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))
GAMES = os.path.join(HERE, 'games')
CORPORA = [('2026-09-20', os.path.join(KG, 'moon/elite/games_2026-09-20.jsonl.gz')),
           ('2026-09-21', os.path.join(KG, 'moon/elite/games_2026-09-21.jsonl.gz')),
           ('2026-09-22', os.path.join(KG, 'moon/elite/games_2026-09-22.jsonl.gz'))] + \
          [('2026-09-%d' % d, os.path.normpath(os.path.join(KG, '..', 'kaggriculture', 'moon', 'elite', 'games_2026-09-%d.jsonl' % d)))
           for d in (23, 24, 25, 26)]
TEAMS = os.environ.get('TEAMS', 'Boey,Fourth Quadrant,吃白饭的大肥鱼,Yizhou,THIRD FARM CLUB').split(',')
DETAIL_DAYS = 17          # days 0..16 carry the full detail
NDAYS = 30


# ---------------------------------------------------------------------------------------------------------- logger
def _acc(dct, key, price):
    v = dct.get(key)
    if v is None:
        v = dct[key] = [0, 0.0]
    v[0] += 1; v[1] += price


def _new_day():
    return dict(m0=None, m23=None, mmin=None, mmin_h=None, hands_h=[0] * 24, shops=None, px=None,
                hires=0, wage=0.0, hire_h=[], land=[], sell={}, buy_prod={}, buy_seed={}, buy_animal={},
                fills={}, ops=collections.Counter(), fail=collections.Counter(), move=0, pas=0, noact=0,
                hv=collections.Counter(), snap=None)


class Logger:
    """Hooks the engine (interpreter, _apply_unit_action, _commit_unit, _do_hire, _do_buy_land) and logs both farms."""
    OPC = {'SELL': 'S', 'BUY_PRODUCT': 'BP', 'BUY_SEED': 'BS', 'BUY_ANIMAL': 'BA'}

    def __init__(self):
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        self.K = K
        self.bs = 10
        self.QM = [[K._quadrant_of(x, y, self.bs) for x in range(self.bs)] for y in range(self.bs)]
        self.FARMS = [None, None]; self.PRIV = [None, None]
        self.step = 0
        self.days = [collections.defaultdict(_new_day), collections.defaultdict(_new_day)]
        self.landlog = [[], []]
        self.orig = None

    def pid(self, farm):
        if farm is self.FARMS[0]: return 0
        if farm is self.FARMS[1]: return 1
        return None

    def snap(self, farm, private):
        herd = collections.Counter(); crops = collections.Counter(); units = collections.Counter()
        struct = collections.Counter(); q = {}; weeds = 0; free = 0
        for y, row in enumerate(farm['tiles']):
            for x, t in enumerate(row):
                if t == 'LOCKED':
                    continue
                c = q.get(self.QM[y][x])
                if c is None:
                    c = q[self.QM[y][x]] = collections.Counter()
                if t is None:
                    c['free'] += 1; free += 1
                elif 'animal' in t:
                    a = t['animal']; c['A:' + a] += 1; herd[a] += 1
                    units[self.K.ANIMALS[a]['product']] += t.get('yield_units', 0)
                elif t.get('kind') == 'PLANT':
                    cr = t['crop']; c['P:' + cr] += 1; crops[cr] += 1; units[cr] += t.get('yield_units', 0)
                else:
                    k = t.get('kind'); c[k] += 1
                    if k == 'WEED': weeds += 1
                    else: struct[k] += 1
        out = dict(quads=list(farm['unlocked_quadrants']), herd=dict(herd), crops=dict(crops),
                   units={k: v for k, v in units.items() if v}, struct=dict(struct), weeds=weeds, free=free,
                   q={k: dict(v) for k, v in sorted(q.items())})
        if private is not None:
            out['shed'] = {k: v for k, v in private['shed'].items() if v}
            out['seeds'] = {k: v for k, v in private['seeds'].items() if v}
        return out

    def fill(self, pid, op, item, price):
        t = self.step; d, h = divmod(t, 24); D = self.days[pid][d]
        if op == 'SELL': _acc(D['sell'], item, price)
        elif op == 'BUY_PRODUCT': _acc(D['buy_prod'], item, price)
        elif op == 'BUY_SEED': _acc(D['buy_seed'], item, price)
        elif op == 'BUY_ANIMAL': _acc(D['buy_animal'], item, price)
        _acc(D['fills'], (h, self.OPC.get(op, op), item or ''), price)

    # --- hooks
    def install(self):
        K = self.K; L = self
        self.orig = dict(interpreter=K.interpreter, _apply_unit_action=K._apply_unit_action, _commit_unit=K._commit_unit,
                         _do_hire=K._do_hire, _do_buy_land=K._do_buy_land)
        oi, oa, oc, oh, ol = (self.orig[k] for k in ('interpreter', '_apply_unit_action', '_commit_unit', '_do_hire', '_do_buy_land'))

        def interp(state, env):
            o = state[0].observation
            farms = getattr(o, 'farms', None)
            if farms:
                t = int(K.get(o, 'step', 0)); d, h = divmod(t, 24)
                L.step = t
                L.FARMS[0], L.FARMS[1] = farms[0], farms[1]
                L.PRIV[0], L.PRIV[1] = state[0].observation.private, state[1].observation.private
                for p in (0, 1):
                    f = farms[p]; D = L.days[p][d]; m = float(f['money'])
                    if h == 0:
                        D['m0'] = m
                        D['snap'] = L.snap(f, L.PRIV[p])
                        D['shops'] = list(o.town['unlocked_shops'])
                        D['px'] = {k: round(float(v), 1) for k, v in o.market['prices'].items()}
                    if h == 23:
                        D['m23'] = m
                    if D['mmin'] is None or m < D['mmin']:
                        D['mmin'], D['mmin_h'] = m, h
                    D['hands_h'][h] = len(f['hands'])
            return oi(state, env)

        def act(farm, private, idx, action, board_size, day, tpd, cap=100):
            p = L.pid(farm)
            if p is None:
                return oa(farm, private, idx, action, board_size, day, tpd, cap)
            D = L.days[p][day]
            if not isinstance(action, list) or not action:
                D['noact'] += 1
                return oa(farm, private, idx, action, board_size, day, tpd, cap)
            op = action[0]
            pos = K._farmer_position(farm, idx)
            if pos is None:
                D['fail']['NOHAND'] += 1
                return oa(farm, private, idx, action, board_size, day, tpd, cap)
            if op == 'PASS':
                D['pas'] += 1
                return oa(farm, private, idx, action, board_size, day, tpd, cap)
            x, y = pos[0], pos[1]
            if op in K.FARMER_MOVES:
                r = oa(farm, private, idx, action, board_size, day, tpd, cap)
                p1 = K._farmer_position(farm, idx)
                if (p1[0], p1[1]) != (x, y): D['move'] += 1
                else: D['fail']['MOVE'] += 1
                return r
            t0 = farm['tiles'][y][x]
            pre = dict(t0) if isinstance(t0, dict) else t0
            invs = private['inventories']
            inv0 = dict(invs[idx]) if idx < len(invs) else {}
            shed_op = op in ('DROP', 'PICKUP', 'PLACE')
            shed0 = dict(private['shed']) if shed_op else None
            r = oa(farm, private, idx, action, board_size, day, tpd, cap)
            t1 = farm['tiles'][y][x]
            inv1 = invs[idx] if idx < len(invs) else {}
            ch = (pre != t1) or ({k: v for k, v in inv0.items() if v} != {k: v for k, v in inv1.items() if v}) or \
                 (shed_op and shed0 != private['shed'])
            if not ch:
                D['fail'][op] += 1
                return r
            Q = L.QM[y][x]
            arg = None
            if op == 'PLANT':
                arg = t1.get('crop') if isinstance(t1, dict) else None
            elif op in ('WATER', 'FERTILIZE'):
                arg = pre.get('crop') if isinstance(pre, dict) else None
            elif op == 'HARVEST':
                if isinstance(pre, dict):
                    arg = pre['crop'] if pre.get('kind') == 'PLANT' else K.ANIMALS[pre['animal']]['product'] if 'animal' in pre else None
                    if arg: D['hv'][arg] += pre.get('yield_units', 0)
            elif op in ('FEED', 'CARE', 'COLLECT_FERTILIZER'):
                arg = pre.get('animal') if isinstance(pre, dict) else None
            elif op == 'DIG':
                if isinstance(pre, dict):
                    arg = pre['crop'] if pre.get('kind') == 'PLANT' else pre.get('kind')
            elif op == 'PLACE':
                it = action[1] if len(action) > 1 else None
                arg = it if (isinstance(t1, dict) and 'animal' in t1 and pre != t1) else 'shed:%s' % it
            elif op == 'PICKUP':
                arg = action[1] if len(action) > 1 else None
            if op in ('DROP', 'PICKUP') or (op == 'PLACE' and arg and arg.startswith('shed:')):
                Q = 'shed'
            D['ops'][op + ((':' + str(arg)) if arg else '') + '@' + Q] += 1
            return r

        def commit(op, item, price, farm, private, market, cap=100):
            ok = oc(op, item, price, farm, private, market, cap)
            if ok:
                p = L.pid(farm)
                if p is not None: L.fill(p, op, item, float(price))
            return ok

        def hire(farm, private, bs, mult=1):
            m0 = farm['money']; n0 = len(farm['hands'])
            oh(farm, private, bs, mult)
            p = L.pid(farm)
            if p is not None and len(farm['hands']) > n0:
                cost = float(m0 - farm['money']); d, h = divmod(L.step, 24); D = L.days[p][d]
                D['hires'] += 1; D['wage'] += cost; D['hire_h'].append(h)
                _acc(D['fills'], (h, 'H', ''), cost)

        def land(farm, bs):
            m0 = float(farm['money']); nq = len(farm['unlocked_quadrants'])
            ol(farm, bs)
            p = L.pid(farm)
            if p is not None and len(farm['unlocked_quadrants']) > nq:
                d, h = divmod(L.step, 24)
                ev = dict(q=farm['unlocked_quadrants'][-1], step=L.step, d=d, h=h, price=round(m0 - float(farm['money']), 1),
                          cash_before=round(m0, 1))
                L.days[p][d]['land'].append(ev); L.landlog[p].append(ev)
                _acc(L.days[p][d]['fills'], (h, 'L', ev['q']), m0 - float(farm['money']))

        K.interpreter = interp; K._apply_unit_action = act; K._commit_unit = commit; K._do_hire = hire; K._do_buy_land = land

    def uninstall(self):
        for k, v in (self.orig or {}).items():
            setattr(self.K, k, v)

    # --- output
    def rows(self, p, head, final_money):
        """Per-day rows of farm p (head: dict of seat-level fields copied into each row) and the seat summary."""
        days = self.days[p]; other = self.days[1 - p]
        fin = self.snap(self.FARMS[p], self.PRIV[p])
        out = []; recon = 0.0
        for d in range(NDAYS):
            D = days.get(d) or _new_day()
            O = other.get(d)
            mend = days[d + 1]['m0'] if (d + 1 < NDAYS and (d + 1) in days) else final_money
            m23 = D['m23'] if D['m23'] is not None else final_money
            s = D['snap'] or {}
            flows = sum(v[1] for v in D['sell'].values()) - sum(v[1] for v in D['buy_prod'].values()) - \
                sum(v[1] for v in D['buy_seed'].values()) - sum(v[1] for v in D['buy_animal'].values()) - \
                D['wage'] - sum(e['price'] for e in D['land'])
            if D['m0'] is not None and mend is not None:
                recon = max(recon, abs((mend - D['m0']) - flows))
            det = d < DETAIL_DAYS
            rs = (O or {}).get('snap') or {}
            row = dict(head, d=d, detail=det, m0=D['m0'], m23=m23, mend=mend, mmin=D['mmin'], mmin_h=D['mmin_h'],
                       sell=_r(D['sell']), buy_prod=_r(D['buy_prod']), buy_seed=_r(D['buy_seed']), buy_animal=_r(D['buy_animal']),
                       hires=D['hires'], wage=D['wage'], hire_h=D['hire_h'], land=D['land'],
                       hands=max(D['hands_h']), quads=s.get('quads'), herd=s.get('herd'), crops=s.get('crops'),
                       units=s.get('units'), struct=s.get('struct'), weeds=s.get('weeds'), free=s.get('free'),
                       shops=D['shops'], hv=dict(D['hv']), fail=dict(D['fail']), move=D['move'], pas=D['pas'], noact=D['noact'],
                       riv=dict(money=(O or {}).get('m0'), quads=rs.get('quads'), herd=rs.get('herd'), crops=rs.get('crops'),
                                struct=rs.get('struct'), weeds=rs.get('weeds')))
            if det:
                row.update(q=s.get('q'), shed=s.get('shed'), seeds=s.get('seeds'), px=D['px'], hands_h=D['hands_h'],
                           ops=dict(D['ops']),
                           fills=[[h, op, it, n, round(v, 1)] for (h, op, it), (n, v) in sorted(D['fills'].items())])
            else:
                ops = collections.Counter()
                for k, v in D['ops'].items(): ops[k.split('@')[0]] += v
                row['ops'] = dict(ops)
            out.append(row)
        seat = dict(head, land=self.landlog[p], recon_max=round(recon, 6),
                    final=dict(herd=fin['herd'], crops=fin['crops'], quads=fin['quads'], units=fin['units'], money=final_money))
        return out, seat


def _r(dct):
    return {k: [n, round(v, 1)] for k, (n, v) in dct.items()}


# ---------------------------------------------------------------------------------------------------------- jobs
def _load(path):
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        return json.load(fh)


def job_elite(t):
    import lean, pinned4
    path, date, seats = t
    d = _load(path)
    L = Logger(); L.install(); t0 = time.time()
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned4._tape(d['acts'], 0), pinned4._tape(d['acts'], 1)])
    finally:
        L.uninstall()
    names = d['info']['TeamNames']
    rec_ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
    res = []
    for s in seats:
        head = dict(gid=d['id'], date=date, seat=s, team=names[s], opp=names[1 - s], role='rec', cand=None)
        rows, seat = L.rows(s, head, r['r'][s])
        seat.update(seed=d['info']['seed'], rew=[r['r'][s], r['r'][1 - s]], rec=[d['rewards'][s], d['rewards'][1 - s]],
                    rec_ok=rec_ok, shops=list(r['shops']), err=r['err'], wall=round(time.time() - t0, 1))
        res.append((rows, seat))
    return res


def job_ours(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent, reference_log
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, date, s, cand, tag = t
    d = _load(path)
    t0 = time.time()
    ref = reference_log(d, s)
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
    orig_eod = install_town(ref['shops'])
    L = Logger(); L.install()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        L.uninstall(); K._end_of_day = orig_eod
    names = d['info']['TeamNames']
    u, e = r['r'][1 - s], r['r'][s]
    out = []
    for p, role in ((1 - s, 'ours'), (s, 'elite_rep')):
        head = dict(gid=d['id'], date=date, seat=p, team=(tag if role == 'ours' else names[s]),
                    opp=(names[s] if role == 'ours' else tag), role=role, cand=os.path.basename(cand))
        rows, seat = L.rows(p, head, r['r'][p])
        seat.update(seed=d['info']['seed'], rew=[r['r'][p], r['r'][1 - p]], rec=[d['rewards'][s], d['rewards'][1 - s]],
                    rec_ok=ref['ok'], shops=list(r['shops']), err=r['err'], elite_seat=s,
                    m=(u - e) if (u is not None and e is not None) else None, wall=round(time.time() - t0, 1))
        out.append((rows, seat))
    return out


# ---------------------------------------------------------------------------------------------------------- modes
def split():
    os.makedirs(GAMES, exist_ok=True)
    rx = re.compile(r'"TeamNames": (\[[^\]]*\])')
    idx = []
    for date, path in CORPORA:
        op = gzip.open if path.endswith('.gz') else open
        n = k = 0
        with op(path, 'rt', encoding='utf-8') as fh:
            for line in fh:
                if not line.strip(): continue
                n += 1
                names = json.loads(rx.search(line[:1000]).group(1))
                seats = [s for s in (0, 1) if names[s] in TEAMS]
                if not seats: continue
                d = json.loads(line)
                if len(d['acts']) != 720: continue
                f = os.path.join(GAMES, '%s_%d.json.gz' % (date, d['id']))
                if not os.path.exists(f):
                    with gzip.open(f, 'wt', encoding='utf-8') as g:
                        json.dump(d, g, ensure_ascii=False)
                idx.append(dict(gid=d['id'], date=date, file=os.path.basename(f), names=names, seats=seats,
                                seed=d['info']['seed'], rewards=d['rewards']))
                k += 1; del d
        print(date, 'games', n, 'kept', k, flush=True)
    with open(os.path.join(GAMES, 'index.jsonl'), 'w', encoding='utf-8') as fh:
        for r in idx: fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    c = collections.Counter(r['names'][s] for r in idx for s in r['seats'])
    print('index', len(idx), 'games', dict(c))


def _index():
    return [json.loads(l) for l in open(os.path.join(GAMES, 'index.jsonl'), encoding='utf-8') if l.strip()]


def _write(results, fd, fs):
    nrows = 0
    for rows, seat in results:
        for r in rows: fd.write(json.dumps(r, ensure_ascii=False) + '\n')
        fs.write(json.dumps(seat, ensure_ascii=False) + '\n'); nrows += 1
    fd.flush(); fs.flush()
    return nrows


def run_elite(maxg):
    idx = _index()[:maxg]
    jobs = [(os.path.join(GAMES, r['file']), r['date'], r['seats']) for r in idx]
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, \
            open(os.path.join(HERE, 'elite_days.jsonl'), 'w', encoding='utf-8') as fd, \
            open(os.path.join(HERE, 'elite_seats.jsonl'), 'w', encoding='utf-8') as fs:
        for i, res in enumerate(ex.map(job_elite, jobs, chunksize=2)):
            n += _write(res, fd, fs)
            if i % 50 == 0:
                print(i, 'games', n, 'seats', 'T', round(time.time() - t0), flush=True)
    print('ALLDONE elite', n, 'seats', round(time.time() - t0), 's', flush=True)


def run_ours(cand, per_team, tag):
    seats = [json.loads(l) for l in open(os.path.join(HERE, 'elite_seats.jsonl'), encoding='utf-8') if l.strip()]
    files = {r['gid']: (os.path.join(GAMES, r['file']), r['date']) for r in _index()}
    by = collections.defaultdict(list)
    for s in seats:
        if s['rec_ok'] and not any(s['err']):
            by[s['team']].append(s)
    sel = []
    for team, xs in sorted(by.items()):
        xs.sort(key=lambda s: (s['date'], s['gid'], s['seat']), reverse=True)   # latest first
        recent = [s for s in xs if s['date'] >= '2026-09-23'] or xs
        step = max(1, len(recent) // per_team)
        sel += recent[::step][:per_team]
    print(len(sel), 'seats', dict(collections.Counter(s['team'] for s in sel)), flush=True)
    jobs = [(files[s['gid']][0], files[s['gid']][1], s['seat'], cand, tag) for s in sel]
    t0 = time.time(); w = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, \
            open(os.path.join(HERE, 'ours_%s_days.jsonl' % tag), 'w', encoding='utf-8') as fd, \
            open(os.path.join(HERE, 'ours_%s_seats.jsonl' % tag), 'w', encoding='utf-8') as fs, \
            open(os.path.join(HERE, 'ours_%s_opp_days.jsonl' % tag), 'w', encoding='utf-8') as fd2, \
            open(os.path.join(HERE, 'ours_%s_opp_seats.jsonl' % tag), 'w', encoding='utf-8') as fs2:
        for i, res in enumerate(ex.map(job_ours, jobs)):
            _write(res[:1], fd, fs); _write(res[1:], fd2, fs2)
            seat = res[0][1]; w.append(seat['m'])
            print(i, seat['opp'], seat['gid'], 'm', seat['m'], 'wall', seat['wall'], 'T', round(time.time() - t0), flush=True)
    ok = [m for m in w if m is not None]
    print('ALLDONE ours', len(ok), 'wins', sum(m > 0 for m in ok), 'margin', round(sum(ok) / max(1, len(ok))), flush=True)


def verify(gids):
    """Replay recorded games with the logger and an observing wrapper; compare cash series and reconcile flows."""
    import lean, pinned4
    files = {r['gid']: (os.path.join(GAMES, r['file']), r['date'], r['seats']) for r in _index()}
    for gid in gids:
        path, date, seats = files[gid]
        d = _load(path)
        seen = [dict(), dict()]      # (day, hour) -> money as observed by each agent
        def obs_tape(p):
            inner = pinned4._tape(d['acts'], p)
            def f(obs, cfg=None):
                t = obs['step']
                if t % 24 in (0, 23): seen[p][(t // 24, t % 24)] = float(obs['farms'][p]['money'])
                return inner(obs, cfg)
            return f
        L = Logger(); L.install()
        try:
            r = lean.play(None, None, d['info']['seed'], agent_objs=[obs_tape(0), obs_tape(1)])
        finally:
            L.uninstall()
        print('game', gid, d['info']['TeamNames'], 'rewards rec', d['rewards'], 'replay', r['r'])
        for s in (0, 1):
            rows, seat = L.rows(s, dict(gid=gid, seat=s), r['r'][s])
            bad = 0
            print(f" seat {s} {d['info']['TeamNames'][s]}  recon_max {seat['recon_max']}  land {[(e['q'], e['d'], e['h'], e['cash_before']) for e in seat['land']]}")
            print('   d      m0     m23    mend   sell$   seed$   anim$   prod$   wage  land$   flows  resid  obs0==m0 obs23==m23')
            for row in rows:
                dd = row['d']
                sell = sum(v[1] for v in row['sell'].values()); seed = sum(v[1] for v in row['buy_seed'].values())
                an = sum(v[1] for v in row['buy_animal'].values()); pr = sum(v[1] for v in row['buy_prod'].values())
                ld = sum(e['price'] for e in row['land'])
                flows = sell - seed - an - pr - row['wage'] - ld
                resid = row['mend'] - row['m0'] - flows
                o0 = seen[s].get((dd, 0)); o23 = seen[s].get((dd, 23), r['r'][s] if dd == 29 else None)
                ok0 = o0 is not None and abs(o0 - row['m0']) < 1e-6; ok23 = o23 is not None and abs(o23 - row['m23']) < 1e-6
                bad += (not ok0) + (not ok23) + (abs(resid) > 1e-6)
                if dd <= 16 or dd == 29 or not (ok0 and ok23):
                    print(f"  {dd:2d} {row['m0']:8.1f} {row['m23']:8.1f} {row['mend']:8.1f} {sell:7.1f} {seed:7.1f} {an:7.1f} {pr:7.1f} {row['wage']:6.1f} {ld:6.1f} {flows:8.1f} {resid:6.2f}  {ok0} {ok23}")
            print(f'   mismatches: {bad}   final money {rows[-1]["mend"]} vs reward {r["r"][s]}')


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'split':
        split()
    elif mode == 'elite':
        run_elite(int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 6)
    elif mode == 'ours':
        cand = sys.argv[2]
        run_ours(cand, int(sys.argv[3]) if len(sys.argv) > 3 else 20,
                 sys.argv[4] if len(sys.argv) > 4 else os.path.splitext(os.path.basename(cand))[0].replace('full_', ''))
    elif mode == 'verify':
        verify([int(x) for x in sys.argv[2:]])
