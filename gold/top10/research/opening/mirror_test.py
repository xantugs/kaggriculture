"""mirror_test.py: oracle mirror test. Our seat replays the elite rival's RECORDED actions one step behind (the transplant
repairs on top) through day 15, then T8's controller takes over at step 384 ('d16' mode); 'whole' mode mirrors the entire
game (tie check). Elite seats: the same repaired replay in their own town (elite_gate set-up).
usage: mirror_test.py mode out.jsonl [NPROC]   mode = whole | d16 | d12 | d20"""
import sys, os, json, gzip, time, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))
G = os.path.join(KG, 'gold', 'top10', 'gates')
WANT = {'goldg': {'THIRD FARM CLUB': 8, 'mtmr_s1': 4, 'TheEggman': 4, 'Yizhou': 4, '吃白饭的大肥鱼': 6},
        'top10g': {'Boey': 8, 'Fourth Quadrant': 8, 'DECEM': 4, 'Unknown Mother-Goose': 4, 'Azat Akhtyamov': 4, 'DSM': 4}}
OFF = dict(es_days=None, es_waves=None, s2t_days=[], w2t_days=[], tie_blk=None, lead2=False, sells_first_chassis=False,
           cash_guard_min=0, chassis_unit_floor=0.0, straw_cap=None, fert_idle=False, arb_chassis=False, v219x=False, v219e=None,
           start_div=None, start_div2=None, start_div143=None, rich_start=None, rich_steps=None, chassis_globals=None, ad_thresh=None)

def seats():
    out = []
    for g, want in WANT.items():
        cnt = collections.Counter()
        for l in open(os.path.join(G, g + '_refs.jsonl'), encoding='utf-8'):
            r = json.loads(l)
            if r['team'] in want and cnt[r['team']] < want[r['team']]:
                cnt[r['team']] += 1; out.append((g, r))
    return out

def play(t):
    import lean
    from eval_elite_routes import install_town, load_games
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    g, ref, mode = t
    gid, s = ref['gid'], ref['seat']
    d = None
    for x in load_games(os.path.join(G, g + '_games.jsonl.gz')):
        if x['id'] == gid:
            d = x; break
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    # the mirror: the rival's actions and successful market orders, shifted one step later
    SH = int(os.environ.get('MSHIFT', '1'))   # 0 = same-step copy (not playable live; bounds the second-mover cost)
    acts_shift = [None] * SH + list(d['acts'])
    outs = {k + SH: [list(o) for o in v] for k, v in rr['outcomes'].items()}
    mskip = int(os.environ.get('MSKIPMEL', '0'))
    if mskip:
        for k in sorted(outs):
            if k > 3: break
            for o in outs[k]:
                if o[0] == 'BUY_SEED' and o[1] == 'MELON' and mskip > 0:
                    take = min(mskip, int(o[2])); o[2] = int(o[2]) - take; mskip -= take
            outs[k] = [o for o in outs[k] if not (o[0] in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT', 'SELL') and int(o[2]) <= 0)]
    mbuf = int(os.environ.get('MBUF', '0'))   # cash buffer: skip this many of the rival's day-0 sheep (the rest of the plan stays)
    if mbuf:
        for k in sorted(outs):
            if k > 3: break
            for o in outs[k]:
                if o[0] == 'BUY_ANIMAL' and o[1] == 'SHEEP' and mbuf > 0:
                    take = min(mbuf, int(o[2])); o[2] = int(o[2]) - take; mbuf -= take
            outs[k] = [o for o in outs[k] if not (o[0] in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT', 'SELL') and int(o[2]) <= 0)]
    rr_shift = dict(hands=([rr['hands'][0]] * SH + list(rr['hands'][:len(rr['hands']) - SH])) if rr['hands'] else rr['hands'],
                    money=([rr['money'][0]] * SH + list(rr['money'][:len(rr['money']) - SH])) if rr['money'] else rr['money'],
                    outcomes=outs, shops=rr['shops'])
    mirror0 = build_agent(acts_shift, s, rr_shift, slack_min=int(os.environ.get('MSLACK', '20')), emergency=os.environ.get('MEMERG', '1') == '1')
    # Unit actions are replayed from the recording per unit with a per-unit cursor. MSHIFT=1: a unit runs one step behind
    # the rival (its hour-23 action is lost: units reset to the spawn at the day boundary); MLEAD=1 lets a unit catch up
    # at its first PASS of the day (an ideal predictor); MSHIFT=0 is the same-step copy. PLANT/BUILD on a weed tile:
    # DIG first (the unit falls one step behind and catches up at its next PASS).
    LEAD = int(os.environ.get('MLEAD', '0'))
    acts_rec = d['acts']
    def rec_act(step, u):
        if step < 0 or step + 1 >= len(acts_rec): return None
        a = acts_rec[step + 1][s]
        if not isinstance(a, dict): return None
        if u == 0: return a.get('farmer') or ['PASS']
        hs = a.get('hands') or []
        return hs[u - 1] if u - 1 < len(hs) else None
    idx = {}
    def mirror(obs, cfg=None):
        a = mirror0(obs, cfg)
        st = int(obs['step']); day, hour = divmod(st, 24)
        me = int(obs['player']); farm = obs['farms'][me]; tiles = farm['tiles']; priv = obs['private']
        units = [farm['farmer']] + [list(h) for h in farm['hands']]
        if hour == 0: idx.clear()
        bound = st if (SH == 0 or LEAD) else st - 1
        out = []
        for u, pos in enumerate(units):
            i = idx.get(u)
            if i is None: i = 24 * day if hour == 0 else st - SH
            act = rec_act(i, u)
            while i < bound and (act is None or act[0] == 'PASS'):
                i += 1; act = rec_act(i, u)
            if i > bound or act is None: act = ['PASS']
            x, y = int(pos[0]), int(pos[1]); t = tiles[y][x]
            if act[0] in ('PLANT', 'BUILD_COOP', 'BUILD_PASTURE') and isinstance(t, dict) and t.get('kind') == 'WEED':
                out.append(['DIG']); idx[u] = i; continue
            out.append(list(act)); idx[u] = i + 1
        seeds = priv.get('seeds') or {}
        demand = collections.Counter(o[1] for o in out if len(o) >= 2 and o[0] == 'PLANT')
        for crop, n in demand.items():
            surplus = n - int(seeds.get(crop, 0))
            for k in range(len(out) - 1, -1, -1):
                if surplus > 0 and len(out[k]) >= 2 and out[k][0] == 'PLANT' and out[k][1] == crop:
                    out[k] = ['PASS']; surplus -= 1
        a = dict(a); a['farmer'] = out[0]; a['hands'] = out[1:]
        last['a'] = out; last['m'] = a.get('market')
        return a
    last = {}
    TRACE = os.environ.get('MTRACE')
    tf = open(TRACE, 'a', encoding='utf-8') if TRACE else None
    def summ(f):
        c = collections.Counter()
        for row in f['tiles']:
            for t in row:
                if t is None: c['.'] += 1
                elif t == 'LOCKED': pass
                elif isinstance(t, dict):
                    if 'animal' in t: c[t['animal'][0]] += 1
                    elif t.get('kind') == 'PLANT': c[t['crop'][0].lower()] += 1
                    elif t.get('kind') == 'WEED': c['x'] += 1
                    else: c[t.get('kind', '?')[0]] += 1
        return '$%6.0f h%2d %s' % (float(f['money']), len(f.get('hands') or []), ' '.join('%s%d' % (k, v) for k, v in sorted(c.items())))
    start = {'whole': 720, 'd16': 384, 'd12': 288, 'd20': 480}[mode]
    A = lean.load(os.path.join(KG, 'gold', 'submit', 'main_ctl_T8.py'))
    GL = A.__globals__
    GL['_GC_PARENT'] = mirror
    GL['GC_P'].update(OFF); GL['GC_P']['start'] = start
    GL['GC_P'].update(GL['GC_P'].get('div_over') or {})   # elite rivals are divergent: the controller's div_over rules
    snap = {}
    def ours(obs, cfg=None):
        st = int(obs['step'])
        if tf:
            me = int(obs['player']); fu, fe = obs['farms'][me], obs['farms'][1 - me]
            pu = [list(fu['farmer'])] + [list(h) for h in fu.get('hands') or []]
            pe = [list(fe['farmer'])] + [list(h) for h in fe.get('hands') or []]
            if st < 120 and (pu != pe or st % 24 in (0, 23)):
                tf.write('s%3d us %s el %s | last %s %s\n' % (st, pu, pe, last.get('a'), last.get('m')))
            mu, ml = float(fu['money']), float(fe['money'])
            if 144 <= st < 240 and (last.get('m') or abs((mu - ml) - last.get('dm', 0)) > 30):
                tf.write('m%3d us $%.0f el $%.0f d %.0f | ord %s | shed %s | rec %s' % (st, mu, ml, mu - ml, last.get('m'), {k: v for k, v in (obs['private'].get('shed') or {}).items() if v}, rr['outcomes'].get(st)) + chr(10))
            last['dm'] = mu - ml
            if st % 24 == 23:
                tf.write('d%2d | us %s | el %s\n' % (st // 24, summ(fu), summ(fe)))
            tf.flush()
        if st in (144, 216, 288, 384, 480):
            me = int(obs['player']); snap[st] = (float(obs['farms'][me]['money']), float(obs['farms'][1 - me]['money']))
        return A(obs, cfg)
    orig = install_town(ref['shops'])
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = ours
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    tape, cd = r['r'][s], r['r'][1 - s]
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    return dict(gate=g, gid=gid, seat=s, team=ref['team'], mode=mode, tape=tape, us=cd, m=(cd - tape) if (tape is not None and cd is not None) else None,
                err=r['err'], tmax=r['tmax'], wall=round(time.time() - t0, 1), snap={str(k): v for k, v in snap.items()},
                errs=(tel or {}).get('gc_errors'), last_err=(tel or {}).get('gc_last_error', '')[:100])

if __name__ == '__main__':
    mode, out = sys.argv[1], sys.argv[2]
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    jobs = [(g, r, mode) for g, r in seats()]
    if os.environ.get('MTEAMS'):
        want = set(os.environ['MTEAMS'].split(','))
        jobs = [j for j in jobs if j[1]['team'] in want]
    if os.environ.get('MAXSEATS'):
        jobs = jobs[:int(os.environ['MAXSEATS'])]
    print(len(jobs), 'seats', dict(collections.Counter(r['team'][:8] for g, r in seats())), 'mode', mode, flush=True)
    T = {}
    for g in ('goldg', 'top10g'):
        for l in open(os.path.join(G, 'kout', 'kagg-gate-r14c', 'rows_%s.jsonl' % g), encoding='utf-8'):
            r = json.loads(l); T[(r['gid'], r['seat'])] = r
    rows = []
    with ProcessPoolExecutor(nproc) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(play, jobs):
            rows.append(x); fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
            b = T.get((x['gid'], x['seat']))
            print('%-10s %d m %+7.0f (T8 %+7.0f) us %6.0f el %6.0f snap384 %s err %s %s' % (x['team'][:10], x['gid'], x['m'] or 0, (b['m'] if b else 0), x['us'] or 0, x['tape'] or 0, x['snap'].get('384'), x['errs'], x['last_err'][:50]), flush=True)
    by = collections.defaultdict(list)
    for x in rows:
        b = T.get((x['gid'], x['seat']))
        if b and x['m'] is not None: by[x['team']].append((x, b)); by['ALL'].append((x, b))
    for t, ps in sorted(by.items(), key=lambda kv: -len(kv[1])):
        n = len(ps)
        print('%-22s n %2d  mirror %+7.0f wins %2d | T8 %+7.0f wins %2d | delta %+7.0f' % (t[:22], n, sum(x['m'] for x, b in ps) / n, sum(x['m'] > 0 for x, b in ps), sum(b['m'] for x, b in ps) / n, sum(b['m'] > 0 for x, b in ps), sum(x['m'] - b['m'] for x, b in ps) / n))
