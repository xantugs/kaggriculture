"""Tape-plus smoke runner: the gate game set-ups (elite_gate / pinned4 at S=0) plus per-game diagnostics.
usage:
  tp_diag.py elite goldg|top10g cand.py out.jsonl [teams=OW] [max]    # repaired elite seats in their towns
  tp_diag.py live  games.json cand.py out.jsonl [gids_file] [max]      # our live games from step 0 (pinned opp tape)
Rows carry the gate fields (gid seat team cand us them m led_us led_them tel) so paircmp.py works on them, plus
diag = {bounce {day: {HIRE, ANIMAL, SEED, LAND, PRODUCT: units ordered but not filled}}, cap {day: orders beyond 10},
        esc {day: animals escaped overnight}, land [[step, quads_before, cash_before]], anim {day: {kind: n}},
        seed {day: {crop: n}}, hires {day: n}, m0 {day: cash at hour 0} (days 0-16), d16 {snapshot at step 384}}.
OW = the five opening-winner teams. NPROC workers (default 4)."""
import sys, os, json, gzip, time, collections
from concurrent.futures import ProcessPoolExecutor
KG = '/home/user/kaggriculture'
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))
OW = ('Boey', 'Fourth Quadrant', '吃白饭的大肥鱼', 'Yizhou', 'THIRD FARM CLUB')


def _snap16(obs, me):
    farm = obs['farms'][me]
    c = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict):
                if t.get('kind') == 'PLANT':
                    c['P_' + t.get('crop', '?')] += 1
                elif t.get('animal'):
                    c['A_' + t['animal']] += 1
                elif t.get('kind') in ('COOP', 'PASTURE'):
                    c['E_' + t['kind']] += 1
                elif t.get('kind') == 'WEED':
                    c['WEED'] += 1
    c['money'] = int(farm['money'])
    c['quads'] = len(list(farm['unlocked_quadrants']))
    return dict(c)


def _run(ag_other, me, cand, seed, install, uninstall):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    led = [collections.Counter(), collections.Counter()]
    FARMS = [None, None]; STEP = [0]
    fills = collections.defaultdict(collections.Counter)      # step -> Counter of filled units by key
    lands = []; esc = collections.Counter()
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL': led[i][item] += price
            elif op == 'BUY_PRODUCT': led[i][item] -= price
            elif op == 'BUY_SEED': led[i]['seed'] -= price
            elif op == 'BUY_ANIMAL': led[i]['anim'] -= price
            if i == me and op != 'SELL':
                fills[STEP[0]][(op, item)] += 1
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            led[i]['hire'] += farm['money'] - m0
            if i == me and farm['money'] != m0:
                fills[STEP[0]][('HIRE', None)] += 1
    ol = K._do_buy_land
    def land(farm, bs):
        m0 = farm['money']; q0 = len(list(farm['unlocked_quadrants']))
        ol(farm, bs)
        if FARMS[me] is not None and farm is FARMS[me] and farm['money'] != m0:
            fills[STEP[0]][('BUY_LAND', None)] += 1
            lands.append([STEP[0], q0, round(m0)])
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = state[0].observation.step
        return opm(state, env)
    ora = K._daily_refresh_animals
    def rfa(farm, day):
        mine = FARMS[me] is not None and farm is FARMS[me]
        if mine:
            n0 = sum(1 for row in farm['tiles'] for t in row if isinstance(t, dict) and t.get('animal'))
        ora(farm, day)
        if mine:
            n1 = sum(1 for row in farm['tiles'] for t in row if isinstance(t, dict) and t.get('animal'))
            if n1 < n0:
                esc[day] += n0 - n1
    K._commit_unit = commit; K._process_market = pm; K._do_hire = hire; K._do_buy_land = land; K._daily_refresh_animals = rfa
    A = lean.load(cand)
    orders = {}; m0 = {}; d16 = {}
    def ours(obs, cfg=None):
        a = A(obs, cfg)
        st = int(obs['step'])
        if st % 24 == 0 and st < 17 * 24:
            m0[st // 24] = round(float(obs['farms'][me]['money']))
        if st == 384:
            d16.update(_snap16(obs, me))
        if st < 17 * 24 and isinstance(a, dict):
            orders[st] = [list(o) for o in (a.get('market') or []) if isinstance(o, (list, tuple))]
        return a
    ag = [None, None]; ag[me] = ours; ag[1 - me] = ag_other
    try:
        install()
        r = lean.play(None, None, seed, agent_objs=ag)
    finally:
        uninstall()
        K._commit_unit = oc; K._process_market = opm; K._do_hire = oh; K._do_buy_land = ol; K._daily_refresh_animals = ora
    bounce = collections.defaultdict(collections.Counter); cap = collections.Counter()
    anim = collections.defaultdict(collections.Counter); seedc = collections.defaultdict(collections.Counter)
    hires = collections.Counter()
    for st, ol_ in orders.items():
        d = st // 24
        if len(ol_) > 10:
            cap[d] += len(ol_) - 10
        want = collections.Counter()
        for o in ol_[:10]:
            if not o:
                continue
            if o[0] in ('HIRE', 'BUY_LAND'):
                want[(o[0], None)] += 1
            elif o[0] in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT') and len(o) >= 3:
                try:
                    n = int(o[2])
                except Exception:
                    continue
                if n > 0:
                    want[(o[0], o[1])] += n
        got = fills.get(st, collections.Counter())
        for k, n in want.items():
            miss = n - got.get(k, 0)
            if miss > 0:
                lab = {'HIRE': 'HIRE', 'BUY_LAND': 'LAND', 'BUY_ANIMAL': 'ANIMAL', 'BUY_SEED': 'SEED', 'BUY_PRODUCT': 'PRODUCT'}[k[0]]
                bounce[d][lab] += miss
                if k[0] == 'BUY_ANIMAL':
                    bounce[d]['ANIMAL_' + k[1]] += miss
        for k, n in got.items():
            if k[0] == 'BUY_ANIMAL':
                anim[d][k[1]] += n
            elif k[0] == 'BUY_SEED':
                seedc[d][k[1]] += n
            elif k[0] == 'HIRE':
                hires[d] += n
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    diag = dict(bounce={d: dict(c) for d, c in sorted(bounce.items())}, cap=dict(cap), esc=dict(esc), land=lands,
                anim={d: dict(c) for d, c in sorted(anim.items())}, seed={d: dict(c) for d, c in sorted(seedc.items())},
                hires=dict(hires), m0=m0, d16=d16)
    return r, led, tel, diag


def job_elite(t):
    d, ref, cand = t
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    saved = {}
    def inst():
        saved['eod'] = install_town(ref['shops'])
    def uninst():
        K._end_of_day = saved['eod']
    t0 = time.time()
    opp = build_agent(d['acts'], s, rr, slack_min=20)
    r, led, tel, diag = _run(opp, 1 - s, cand, ref['seed'], inst, uninst)
    tape, cd = r['r'][s], r['r'][1 - s]
    return dict(gid=ref['gid'], seat=s, team=ref['team'], cand=cand, tape=tape, us=cd,
                m=(cd - tape) if tape is not None and cd is not None else None, err=r['err'], wall=round(time.time() - t0, 1),
                led_us=dict(led[1 - s]), led_elite=dict(led[s]), tel=tel, diag=diag)


def job_live(t):
    path, cand = t
    import pinned4
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, rref = pinned4.reference(d)
    saved = {}
    def inst():
        saved['eod'] = pinned4.install_pinned(0, O, spawns, shops)
    def uninst():
        K._end_of_day = saved['eod']
    t0 = time.time()
    r, led, tel, diag = _run(pinned4._tape(d['acts'], O), P, cand, d['info']['seed'], inst, uninst)
    return dict(gid=d['id'], seat=P, opp=names[O], cand=cand, S=0, rec=d['rewards'][P] - d['rewards'][O],
                rec_ok=[int(x) for x in rref] == [int(x) for x in d['rewards']], us=r['r'][P], them=r['r'][O],
                m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None, err=r['err'], wall=round(time.time() - t0, 1),
                led_us=dict(led[P]), led_them=dict(led[O]), tel=tel, diag=diag,
                opp_before=(d.get('meta') or {}).get('opp_before'))


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'elite':
        gate, cand, out = sys.argv[2], sys.argv[3], sys.argv[4]
        teams = OW if len(sys.argv) <= 5 or sys.argv[5] == 'OW' else tuple(sys.argv[5].split(','))
        maxg = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
        base = os.path.join(KG, 'gold/top10/gates/%s' % gate)
        R = []
        for l in open(base + '_refs.jsonl', encoding='utf-8'):
            if any(('"team": "%s"' % tm) in l or ('"team": %s' % json.dumps(tm)) in l for tm in teams):
                r = json.loads(l)
                if r['team'] in teams:
                    R.append(r)
        R = R[:maxg]
        want = set(r['gid'] for r in R)
        games = {}
        with gzip.open(base + '_games.jsonl.gz', 'rt', encoding='utf-8') as fh:
            for l in fh:
                x = json.loads(l)
                if x['id'] in want:
                    games[x['id']] = x
        jobs = [(games[r['gid']], r, cand) for r in R]
        fn = job_elite
    else:
        path, cand, out = sys.argv[2], sys.argv[3], sys.argv[4]
        gids = set(int(x) for x in open(sys.argv[5]).read().split()) if len(sys.argv) > 5 and sys.argv[5] != '-' else None
        maxg = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
        split = path + '.d'
        jobs = []
        for f in sorted(os.listdir(split), key=lambda s: (len(s), s)):
            fp = os.path.join(split, f)
            if gids is not None:
                with open(fp, encoding='utf-8') as fh:
                    head = fh.read(200)
                import re
                mm = re.search(r'"id":\s*(\d+)', head)
                if not mm or int(mm.group(1)) not in gids:
                    continue
            jobs.append((fp, cand))
        jobs = jobs[:maxg]
        fn = job_live
    t0 = time.time(); n = 0; w = 0; ms = 0.0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(fn, jobs):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
            if x['m'] is not None:
                n += 1; w += x['m'] > 0; ms += x['m']
    print('%s: %d-%d of %d  margin %+.0f  wall %.0fs' % (cand, w, n - w, n, ms / max(1, n), time.time() - t0))
