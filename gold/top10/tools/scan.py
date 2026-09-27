"""Instrumented full-game scan: where does a candidate lose money to mechanics (not strategy)?

Same world as gold/harness/pinned4.py (rival replays its recorded tape, town shops and rival weeds pinned from
day S//24, our weeds from a private stream). Use S=0: the candidate plays our seat for all 720 steps.
Engine functions on module K are wrapped (restored in finally) to record, for OUR farm only, per day:

  m0            money at hour 0                         hires, hire_c   hands hired, wage paid
  hands23       hands alive at hour 23                  px              evening prices (PRODUCTS order), at _end_of_day
  px12          prices at hour 12 (before that step)    sold            {item: [units, $]} market sales
  esc           [[kind, placed_day, held, fut, x, y, $]]  animals escaped at the night refresh
                (engine rule: consecutive_unfed reaches 2 = unfed on two consecutive days; held product is lost with
                 the animal; fut = base production events it would still have had, end of day d..28; $ = (held+fut) x px)
  unfed         {kind: n} animals unfed today that did NOT escape (first strike)
  anim          {kind: n} animals on tiles after the night refresh; anim_shed {kind: n} animals sitting in the shed
  thirst        [[crop, age, planted_day, yield, pot, $]] plants turned to weeds by 2 unwatered days
                (pot = units it could still have been harvested for by day 29 at one unit per remaining watered
                 window day / production event, capped at max_yield; $ = pot x px)
  mww           {crop: units} non-ongoing crops left unwatered on a yield-window day (the water bonus lost), mww_v $
                (per-night count, capped only by the yield on the tile that night: an upper bound)
  mwwh          {crop: units} the same misses realised at HARVEST, cap-aware: min(max_yield, y + bonuses missed) - y,
                mwwh_v $ at the price of the harvest step (plants that never get harvested are left to thirst / rot)
  pcap / acap   {item: units} ongoing-crop / animal production clipped by max_yield / max_held, pcap_v / acap_v $
  carel         {product: units} pending care bonus wiped by an unfed production day, carel_v $
                carelc / carelc_v: the part where the animal WAS cared that day (a unit reached it but did not feed)
  rot / rotw    {crop: units} units lost to _decay_plants (finished plant left in the field), {crop: plants} that
                rotted into weeds with yield still on them, rot_v $
  drop          {item: units} discarded at the night drop (hands + farmer inventories vs shed room, capacity 100),
                drop_v = units x evening price (animals at purchase cost), drop_vw = the same units walked down the
                evening book (market_price at inventory+k), room23 = shed room before the drop,
                carry = [[unit idx (0 farmer), {item: n}]] non-empty inventories at hour 23, shed23 = shed before the drop
                (only on days with a discard)
  ddrop         {item: units} overflow discarded by a daytime DROP action into a full shed, ddrop_v $ (current price)
  pass          PASS unit-turns (explicit)             blocked  PLANT turned into PASS by the atomic seed check
  idle          hands alive but given no action        noop     {op: n} non-PASS actions that changed nothing
  mfail         {"OP:ITEM": n} market unit commits that failed (SELL with empty shed stock, BUY with no cash/room)
Per game: end = stock left at the end (shed, inventories, harvestable yield on tiles, seeds) valued at the final book.

usage: scan.py games.json[,more.json] S cand1[,cand2] out.jsonl [team=offhand] [maxgames]   (env NPROC, PIN_GIDS)
Resumable: rows already in out.jsonl with a result (same gid and candidate) are kept and skipped; failed rows rerun."""
import sys, os, json, random, time, collections, traceback
from concurrent.futures import ProcessPoolExecutor
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
sys.path.insert(0, os.path.join(HERE, '..', 'gold', 'harness'))
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402

LAST_DAY = 29        # last day with actions (last processed step 718 = day 29 hour 22); no night refresh on day 29


class Rec:
    def __init__(self, P):
        self.P = P
        self.farm = None; self.priv = None; self.mkt = None
        self.step = 0; self.day = 0
        self.days = collections.defaultdict(dict)
        self.intent = []
        self.px = {}
        self.mw = {}        # id(plant tile) -> [tile, water bonus missed on window days]

    def ev(self, d=None):
        return self.days[self.day if d is None else d]


R = None


def _inc(dct, key, n=1):
    dct[key] = dct.get(key, 0) + n


def _walk(K, item, n, mkt):
    """Revenue of selling n units one by one into the current book (sales at $1 add no supply)."""
    if item in K.ANIMALS:
        return n * K.ANIMALS[item]['cost']
    inv = mkt['inventory'][item]; params = mkt.get('params'); tot = 0
    for _ in range(int(n)):
        p = K.market_price(item, inv, params); tot += p
        if p > 1:
            inv += 1
    return tot


def _price(K, item, px):
    if item in K.ANIMALS:
        return K.ANIMALS[item]['cost']
    return px.get(item, 0)


def _anim_fut(K, kind, placed, day):
    a = K.ANIMALS[kind]; n = 0
    for e in range(day, LAST_DAY):          # productions at the end of days day..28 are sellable by day 29
        dsf = e + 1 - placed - a['first_yield_day']
        if dsf >= 0 and dsf % a['interval'] == 0:
            n += 1
    return n


def _plant_pot(K, t, day):
    cd = K.CROPS[t['crop']]; pl = t['planted_day']; y = max(0, t.get('yield_units', 0))
    if not cd['ongoing']:
        if pl + cd['first_yield_day'] > LAST_DAY:
            return 0
        ws = (cd['max_yield_day'] + 1) // 2; c = 0
        for d in range(day + 1, min(pl + cd['max_yield_day'], LAST_DAY) + 1):
            if d - pl >= ws:
                c += 1
        return min(cd['max_yield'], y + c)
    c = 0
    for e in range(day, LAST_DAY):
        dsf = e + 1 - pl - cd['first_yield_day']
        if dsf >= 0 and dsf % cd['interval'] == 0 and dsf // cd['interval'] + 1 <= cd['max_yield']:
            c += 1
    return y + c


def install_hooks(K):
    """Wrap engine functions; returns a restore() callable."""
    saved = {n: getattr(K, n) for n in ('interpreter', '_apply_unit_action', '_commit_unit', '_do_hire', '_decay_plants',
                                         '_daily_refresh_plants', '_daily_refresh_animals', '_drop_inventories_to_shed',
                                         '_end_of_day')}
    o_int = saved['interpreter']; o_apply = saved['_apply_unit_action']; o_commit = saved['_commit_unit']
    o_hire = saved['_do_hire']; o_decay = saved['_decay_plants']; o_rp = saved['_daily_refresh_plants']
    o_ra = saved['_daily_refresh_animals']; o_drop = saved['_drop_inventories_to_shed']; o_eod = saved['_end_of_day']
    PRODUCTS = K.PRODUCTS

    def interp(state, env):
        r = R
        obs0 = state[0].observation
        if r.farm is not None:
            st = int(obs0.get('step', 0)); r.step = st; r.day = st // 24
            h = st % 24
            if h == 0:
                r.ev()['m0'] = round(float(r.farm['money']), 1)
            elif h == 12:
                r.ev()['px12'] = [int(r.mkt['prices'][p]) for p in PRODUCTS]
        out = o_int(state, env)
        if r.farm is None and obs0.get('farms'):
            r.farm = obs0.farms[r.P]; r.priv = state[r.P].observation.private; r.mkt = obs0.market
        return out

    def apply(farm, private, idx, action, board_size, day, tpd, cap=100):
        r = R
        if farm is not r.farm:
            return o_apply(farm, private, idx, action, board_size, day, tpd, cap)
        ev = r.ev()
        op = action[0] if isinstance(action, list) and action else None
        if op is None or op == 'PASS':
            it = r.intent[idx] if idx < len(r.intent) else None
            if isinstance(it, list) and it and it[0] == 'PLANT':
                _inc(ev, 'blocked')
            else:
                _inc(ev, 'pass')
            return o_apply(farm, private, idx, action, board_size, day, tpd, cap)
        pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
        if pos is None:
            _inc(ev.setdefault('noop', {}), 'NOHAND')
            return o_apply(farm, private, idx, action, board_size, day, tpd, cap)
        x, y = pos[0], pos[1]
        invs = private['inventories']; inv = invs[idx] if idx < len(invs) else {}
        shed = private['shed']; seeds = private['seeds']
        t = farm['tiles'][y][x]
        if op == 'HARVEST' and isinstance(t, dict) and t.get('kind') == 'PLANT' and id(t) in r.mw and r.mw[id(t)][0] is t:
            cd = K.CROPS[t['crop']]
            if t['yield_units'] > 0 and day - t['planted_day'] >= cd['first_yield_day']:
                y0 = t['yield_units']; k = min(cd['max_yield'], y0 + r.mw.pop(id(t))[1]) - y0
                if k > 0:
                    _inc(ev.setdefault('mwwh', {}), t['crop'], k); _inc(ev, 'mwwh_v', k * r.mkt['prices'][t['crop']])
        sig = (x, y, tuple(sorted(inv.items())), id(t), tuple(t.items()) if isinstance(t, dict) else t,
               sum(shed.values()), sum(seeds.values()))
        if op == 'DROP':
            inv0 = dict(inv); shed0 = dict(shed)
        out = o_apply(farm, private, idx, action, board_size, day, tpd, cap)
        pos2 = farm['farmer'] if idx == 0 else farm['hands'][idx - 1]
        inv2 = invs[idx] if idx < len(invs) else {}
        t2 = farm['tiles'][y][x]
        sig2 = (pos2[0], pos2[1], tuple(sorted(inv2.items())), id(t2), tuple(t2.items()) if isinstance(t2, dict) else t2,
                sum(shed.values()), sum(seeds.values()))
        if sig == sig2:
            _inc(ev.setdefault('noop', {}), str(op))
        if op == 'DROP':
            lost = {}
            for it_, n in inv0.items():
                if n > 0:
                    k = n - (shed.get(it_, 0) - shed0.get(it_, 0))
                    if k > 0:
                        lost[it_] = k
            if lost:
                dd = ev.setdefault('ddrop', {})
                for it_, k in lost.items():
                    _inc(dd, it_, k)
                    _inc(ev, 'ddrop_v', k * _price(K, it_, r.mkt['prices']))
        return out

    def commit(op, item, price, farm, private, market, cap=100):
        ok = o_commit(op, item, price, farm, private, market, cap)
        r = R
        if farm is r.farm:
            ev = r.ev()
            if not ok:
                _inc(ev.setdefault('mfail', {}), '%s:%s' % (op, item))
            elif op == 'SELL':
                s = ev.setdefault('sold', {}).setdefault(item, [0, 0])
                s[0] += 1; s[1] += price
            else:
                s = ev.setdefault('bought', {}).setdefault('%s:%s' % (op, item), [0, 0])
                s[0] += 1; s[1] += price
        return ok

    def hire(farm, private, board_size, mult=1):
        m0 = farm['money']; n0 = len(farm['hands'])
        out = o_hire(farm, private, board_size, mult)
        r = R
        if farm is r.farm and len(farm['hands']) > n0:
            ev = r.ev(); _inc(ev, 'hires'); _inc(ev, 'hire_c', round(m0 - farm['money'], 1))
        return out

    def decay(farm, step):
        r = R
        if farm is r.farm:
            ev = None
            for row in farm['tiles']:
                for t in row:
                    if not isinstance(t, dict) or t.get('kind') != 'PLANT':
                        continue
                    mls = t['max_lifespan_step']
                    if mls < 0 or step < mls or (step - mls) % 2:
                        continue
                    if t['yield_units'] >= 1:
                        if ev is None:
                            ev = r.ev(step // 24)
                        c = t['crop']
                        _inc(ev.setdefault('rot', {}), c)
                        _inc(ev, 'rot_v', r.mkt['prices'][c])
                        if t['yield_units'] == 1:
                            _inc(ev.setdefault('rotw', {}), c)
        return o_decay(farm, step)

    def refresh_plants(farm, day, tpd):
        r = R
        if farm is r.farm:
            ev = r.ev(day); px = r.px
            for row in farm['tiles']:
                for t in row:
                    if not isinstance(t, dict) or t.get('kind') != 'PLANT':
                        continue
                    cd = K.CROPS[t['crop']]; w = t['watered_today']; age = day - t['planted_day']
                    if not w and t['consecutive_unwatered'] + 1 >= 2:
                        pot = _plant_pot(K, t, day)
                        ev.setdefault('thirst', []).append([t['crop'], age, t['planted_day'], t['yield_units'], pot,
                                                            pot * px.get(t['crop'], 0)])
                        continue
                    if not cd['ongoing']:
                        ws = (cd['max_yield_day'] + 1) // 2
                        if (not w and ws <= age <= cd['max_yield_day'] and t['yield_units'] < cd['max_yield']
                                and t['planted_day'] + cd['first_yield_day'] <= LAST_DAY):
                            b = 2 if t['fertilized_until_day'] >= day else 1
                            k = min(b, cd['max_yield'] - t['yield_units'])
                            _inc(ev.setdefault('mww', {}), t['crop'], k); _inc(ev, 'mww_v', k * px.get(t['crop'], 0))
                            m_ = r.mw.setdefault(id(t), [t, 0])
                            if m_[0] is not t:
                                r.mw[id(t)] = m_ = [t, 0]
                            m_[1] += b
                        continue
                    dsf = day + 1 - t['planted_day'] - cd['first_yield_day']
                    if dsf >= 0 and dsf % cd['interval'] == 0 and dsf // cd['interval'] + 1 <= cd['max_yield']:
                        add = 2 if (w and t.get('fertilized_until_day', -1) >= day) else 1
                        k = max(0, t['yield_units'] + add - cd['max_yield'])
                        if k:
                            _inc(ev.setdefault('pcap', {}), t['crop'], k); _inc(ev, 'pcap_v', k * px.get(t['crop'], 0))
        return o_rp(farm, day, tpd)

    def refresh_animals(farm, day):
        r = R
        if farm is not r.farm:
            return o_ra(farm, day)
        ev = r.ev(day); px = r.px
        for y, row in enumerate(farm['tiles']):
            for x, t in enumerate(row):
                if not (isinstance(t, dict) and 'animal' in t):
                    continue
                kind = t['animal']; a = K.ANIMALS[kind]; prod = a['product']; fed = t['fed_today']
                if not fed and t['consecutive_unfed'] + 1 >= 2:
                    held = t['yield_units']; fut = _anim_fut(K, kind, t['placed_day'], day)
                    ev.setdefault('esc', []).append([kind, t['placed_day'], held, fut, x, y, (held + fut) * px.get(prod, 0)])
                    continue
                if not fed:
                    _inc(ev.setdefault('unfed', {}), kind)
                dsf = day + 1 - t['placed_day'] - a['first_yield_day']
                if dsf >= 0 and dsf % a['interval'] == 0:
                    pend = t.get('pending_care_bonus', 0)
                    add = 1 + (pend if fed else 0)
                    k = max(0, t['yield_units'] + add - a['max_held'])
                    if k:
                        _inc(ev.setdefault('acap', {}), prod, k); _inc(ev, 'acap_v', k * px.get(prod, 0))
                    if not fed and pend:
                        _inc(ev.setdefault('carel', {}), prod, pend); _inc(ev, 'carel_v', pend * px.get(prod, 0))
                        if t['cared_today']:
                            _inc(ev.setdefault('carelc', {}), prod, pend); _inc(ev, 'carelc_v', pend * px.get(prod, 0))
        out = o_ra(farm, day)
        an = {}
        for row in farm['tiles']:
            for t in row:
                if isinstance(t, dict) and 'animal' in t:
                    _inc(an, t['animal'])
        ev['anim'] = an
        return out

    def drop(private, capacity):
        r = R
        if private is not r.priv:
            return o_drop(private, capacity)
        ev = r.ev(); shed = private['shed']
        shed0 = {k: v for k, v in shed.items() if v}
        carry = [[i, {k: v for k, v in inv.items() if v > 0}] for i, inv in enumerate(private['inventories'])]
        carry = [c for c in carry if c[1]]
        ev['room23'] = max(0, capacity - sum(shed.values()))
        ash = {k: v for k, v in shed0.items() if k in K.ANIMALS}
        if ash:
            ev['anim_shed'] = ash
        out = o_drop(private, capacity)
        if carry:
            ev['carry'] = carry
            tot = collections.Counter()
            for _, d in carry:
                tot.update(d)
            lost = {}
            for it_, n in tot.items():
                k = n - (shed.get(it_, 0) - shed0.get(it_, 0))
                if k > 0:
                    lost[it_] = k
            if lost:
                ev['drop'] = lost
                ev['drop_v'] = sum(k * _price(K, it_, r.px) for it_, k in lost.items())
                ev['drop_vw'] = sum(_walk(K, it_, k, r.mkt) for it_, k in lost.items())
                ev['shed23'] = shed0
        return out

    def eod(state, env, day):
        r = R
        if r.farm is not None:
            r.day = day
            r.px = {p: int(r.mkt['prices'][p]) for p in PRODUCTS}
            ev = r.ev(day)
            ev['px'] = [r.px[p] for p in PRODUCTS]
            ev['hands23'] = len(r.farm['hands'])
        return o_eod(state, env, day)

    K.interpreter = interp; K._apply_unit_action = apply; K._commit_unit = commit; K._do_hire = hire
    K._decay_plants = decay; K._daily_refresh_plants = refresh_plants; K._daily_refresh_animals = refresh_animals
    K._drop_inventories_to_shed = drop; K._end_of_day = eod

    def restore():
        for n, f in saved.items():
            setattr(K, n, f)
    return restore


def _recorder(inner, P):
    def f(obs, cfg=None):
        a = inner(obs, cfg)
        r = R
        if isinstance(a, dict):
            hs = a.get('hands', []) or []
            r.intent = [a.get('farmer')] + (list(hs) if isinstance(hs, list) else [])
            try:
                nh = len(obs['farms'][P]['hands'])
                idle = nh - (len(hs) if isinstance(hs, list) else 0)
                if idle > 0:
                    _inc(r.ev(int(obs['step']) // 24), 'idle', idle)
            except Exception:
                pass
        else:
            r.intent = []
        return a
    return f


def end_stock(K, rec):
    farm, priv, mkt = rec.farm, rec.priv, rec.mkt
    shed = {k: v for k, v in priv['shed'].items() if v > 0}
    inv = collections.Counter()
    for d in priv['inventories']:
        for k, v in d.items():
            if v > 0:
                inv[k] += v
    tiles = collections.Counter()
    for row in farm['tiles']:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get('kind') == 'PLANT' and t.get('yield_units', 0) > 0:
                if LAST_DAY - t['planted_day'] >= K.CROPS[t['crop']]['first_yield_day']:
                    tiles[t['crop']] += t['yield_units']
            elif 'animal' in t and t.get('yield_units', 0) > 0:
                tiles[K.ANIMALS[t['animal']]['product']] += t['yield_units']
    seeds = {k: v for k, v in priv['seeds'].items() if v > 0}
    return dict(shed=shed, inv=dict(inv), tiles=dict(tiles), seeds=seeds,
                v_shed=sum(_walk(K, k, v, mkt) for k, v in shed.items()),
                v_inv=sum(_walk(K, k, v, mkt) for k, v in inv.items()),
                v_tiles=sum(_walk(K, k, v, mkt) for k, v in tiles.items()),
                v_seeds=sum(v * K.CROPS[k]['seed'] for k, v in seeds.items()),
                px=[int(mkt['prices'][p]) for p in K.PRODUCTS])


def job(t):
    global R
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, idx, team, cand, S = t
    t0 = time.time()
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)[idx]          # a one-game file written by the main process (never the whole corpus)
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    try:
        spawns, shops, rref = reference(d)
        rec_ok = [int(x) for x in rref] == [int(x) for x in d['rewards']]
        orig = install_pinned(S // 24, O, spawns, shops)
        R = Rec(P)
        restore = install_hooks(K)
        try:
            A = lean.load(cand)
            ag = [None, None]
            ag[P] = _recorder(_prefixed(A, d['acts'], P, S), P)
            ag[O] = _tape(d['acts'], O)
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            restore()
            K._end_of_day = orig
        end = end_stock(K, R) if R.farm is not None else None
        days = {str(k): v for k, v in sorted(R.days.items())}
        tel = getattr(A, 'telemetry', None)
        tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
        m = (r['r'][P] - r['r'][O]) if r['r'][P] is not None and r['r'][O] is not None else None
        return dict(gid=d['id'], opp=names[O], cand=cand, S=S, seat=P, rec=d['rewards'][P] - d['rewards'][O], rec_ok=rec_ok,
                    us=r['r'][P], them=r['r'][O], m=m, margin=m, err=r['err'], tmax=r['tmax'][P],
                    wall=round(time.time() - t0, 1), days=days, end=end, tel=tel)
    except Exception:
        return dict(gid=d['id'], opp=names[O], cand=cand, S=S, seat=P, m=None, margin=None, us=None, them=None,
                    err=['scan exception', None], exc=traceback.format_exc()[-2000:], wall=round(time.time() - t0, 1))


def _load_rows(out):
    rows = []
    if os.path.exists(out):
        with open(out, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass            # a torn last line from an interrupted run
    return rows


if __name__ == '__main__':
    from concurrent.futures import as_completed
    files = sys.argv[1].split(','); S = int(sys.argv[2]); cands = sys.argv[3].split(','); out = sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    maxg = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
    games = []
    want = set(int(x) for x in open(os.environ["PIN_GIDS"]).read().split()) if os.environ.get("PIN_GIDS") else None
    for f in files:
        # same split as gold/harness/pinned4.py: one small file per game (<f>.d/<i>.json, a one-element list), written
        # here in the main process, so each worker loads only its own game (loading the whole corpus in every worker
        # ran the machine out of memory)
        split = f + '.d'
        os.makedirs(split, exist_ok=True)
        corpus = json.load(open(f, encoding='utf-8'))
        for i, d in enumerate(corpus):
            if team in d['info']['TeamNames'] and (want is None or d['id'] in want):
                one = os.path.join(split, '%d.json' % i)
                if not os.path.exists(one):
                    json.dump([d], open(one, 'w', encoding='utf-8'))
                games.append((one, 0, d['id']))
        del corpus, d
    import gc; gc.collect()
    games = games[:maxg]
    # resume: keep good rows already in `out` (same gid and candidate), drop failed ones, run the rest
    old = _load_rows(out)
    done = {(r['gid'], r.get('cand')) for r in old if r.get('m') is not None and not r.get('exc')}
    keep = [r for r in old if (r['gid'], r.get('cand')) in done]
    jobs = [(f, i, team, c, S) for f, i, g in games for c in cands if (g, c) not in done]
    print('games %d  rows kept %d  dropped %d  jobs to run %d  NPROC %s' % (
        len(games), len(keep), len(old) - len(keep), len(jobs), os.environ.get("NPROC", "4")), flush=True)
    with open(out, 'w', encoding='utf-8') as fh:
        for r in keep:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    t0 = time.time(); res = list(keep)
    if jobs:
        with ProcessPoolExecutor(int(os.environ.get("NPROC", "4"))) as ex, open(out, 'a', encoding='utf-8') as fh:
            futs = {ex.submit(job, j): j for j in jobs}
            for fu in as_completed(futs):
                try:
                    r = fu.result()
                except Exception as e:      # worker died; leave the game out so a rerun picks it up
                    print('JOB FAILED', futs[fu][0], repr(e)[:200], flush=True)
                    continue
                res.append(r); fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
                print('%s %s m %s wall %.0fs%s  [%d/%d, %.0fs]' % (r['gid'], r['opp'], r['m'], r['wall'],
                      ' EXC' if r.get('exc') else '', len(res), len(games) * len(cands), time.time() - t0), flush=True)
    for c in cands:
        rs = [r for r in res if r.get('cand') == c and r['m'] is not None]
        w = sum(r['m'] > 0 for r in rs); n = max(1, len(rs))
        print(f"{c}: {w}-{len(rs)-w} of {len(rs)}  margin {sum(r['m'] for r in rs)/n:+.0f}  us {sum(r['us'] for r in rs)/n:.0f}"
              f"  them {sum(r['them'] for r in rs)/n:.0f}  rec {sum(r['rec'] for r in rs)/n:+.0f}  wall {time.time()-t0:.0f}s"
              f"  failed {sum(1 for r in res if r.get('cand') == c and r['m'] is None)}")
