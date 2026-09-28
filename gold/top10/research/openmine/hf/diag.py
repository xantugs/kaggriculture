"""Herd-first clone diagnostics: candidate vs the repaired elite recording in its own town (elite_gate set-up),
with per-day farm logs of both sides (extract.py Logger) and our telemetry.

usage (from kg/):
  diag.py run cand.py tag [teams] [n_per_team] [gate]   -> hf/out_<tag>.jsonl (one row per seat)
        teams: comma list of short names (FQ,Boey,TFC,CBF,Yiz or 'hf' = FQ,Boey,TFC; 'all' = every gate seat)
        gate: goldg / top10g / both (default both). Seats are the gate refs in file order (first n per team).
  diag.py cmp tag [tag2 ...] [--team X] [--days 0-16]   -> day-by-day table ours vs elite (means)
  diag.py gate tag [base_rows...]                       -> margin/wins vs T8 rows on the same seats (+ product ledger)
env NPROC (default 3).
"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.dirname(HERE)
KG = os.path.normpath(os.path.join(OM, '..', '..', '..', '..'))
sys.path.insert(0, OM)
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))
GATES = os.path.join(KG, 'gold', 'top10', 'gates')
SHORT = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'Yizhou': 'Yiz', 'THIRD FARM CLUB': 'TFC'}
T8ROWS = [os.path.join(GATES, 'kout', 'kagg-gate-r14c', 'rows_goldg.jsonl'),
          os.path.join(GATES, 'kout', 'kagg-gate-r14c', 'rows_top10g.jsonl')]
ANIM = ('GOOSE', 'COW', 'SHEEP')


def short(team):
    return SHORT.get(team, team[:6])


def seats(teams, n, gate):
    out = []
    files = []
    if gate in ('goldg', 'both'): files.append(('goldg', os.path.join(GATES, 'goldg_refs.jsonl')))
    if gate in ('top10g', 'both'): files.append(('top10g', os.path.join(GATES, 'top10g_refs.jsonl')))
    cnt = collections.Counter()
    for g, f in files:
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            t = short(r['team'])
            if teams == 'nothf':
                if t in ('FQ', 'Boey', 'TFC'):
                    continue
            elif teams != 'all' and t not in teams:
                continue
            if cnt[t] >= n:
                continue
            cnt[t] += 1
            out.append((g, r['gid'], r['seat'], r['team']))
    return out


def compact(rows):
    """days 0..29 compact: m0 mend quads herd crops struct hires wage land sell$ buy$ hv shed free weeds"""
    out = []
    for r in rows:
        sell = {k: [v[0], v[1]] for k, v in (r.get('sell') or {}).items()}
        x = dict(d=r['d'], m0=r['m0'], mend=r['mend'], mmin=r['mmin'], quads=r.get('quads'), herd=r.get('herd') or {},
                 crops=r.get('crops') or {}, struct=r.get('struct') or {}, hires=r['hires'], wage=r['wage'],
                 hire_h=r.get('hire_h'), land=[(e['q'], e['h'], e['cash_before']) for e in r.get('land', [])],
                 sell=sell, ba=r.get('buy_animal') or {}, bs=r.get('buy_seed') or {}, bp=r.get('buy_prod') or {},
                 hv=r.get('hv') or {}, free=r.get('free'), weeds=r.get('weeds'), fail=r.get('fail') or {},
                 shops=r.get('shops'), move=r.get('move'), pas=r.get('pas'))
        if r.get('detail'):
            x['shed'] = r.get('shed') or {}
            ops = collections.Counter()
            for k, v in (r.get('ops') or {}).items():
                ops[k.split('@')[0]] += v
            x['ops'] = dict(ops)
            x['q'] = r.get('q')
            x['fills'] = r.get('fills')
            x['seeds'] = r.get('seeds') or {}
        out.append(x)
    return out


def job(t):
    import lean, extract
    from eval_elite_routes import install_town
    from transplant import build_agent, reference_log
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    g, gid, s, team, cand, path = t
    d = extract._load(path)
    t0 = time.time()
    ref = reference_log(d, s)
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
    orig_eod = install_town(ref['shops'])
    L = extract.Logger(); L.install()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        L.uninstall(); K._end_of_day = orig_eod
    u, e = r['r'][1 - s], r['r'][s]
    rows_u, _ = L.rows(1 - s, dict(), u)
    rows_e, _ = L.rows(s, dict(), e)
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    led = []
    for rows in (rows_u, rows_e):
        c = collections.Counter()
        for r_ in rows:
            for k, v in (r_.get('sell') or {}).items(): c[k] += v[1]
            for k, v in (r_.get('buy_prod') or {}).items(): c[k] -= v[1]
            for k, v in (r_.get('buy_seed') or {}).items(): c['seed'] -= v[1]
            for k, v in (r_.get('buy_animal') or {}).items(): c['anim'] -= v[1]
            c['hire'] -= r_['wage']
            for ev in r_.get('land', []): c['land'] -= ev['price']
        led.append({k: round(v, 1) for k, v in c.items()})
    return dict(gate=g, gid=gid, seat=s, team=team, cand=os.path.basename(cand), us=u, tape=e,
                m=(u - e) if (u is not None and e is not None) else None, err=r['err'], tmax=r['tmax'],
                wall=round(time.time() - t0, 1), led_us=led[0], led_elite=led[1], tel=tel,
                ours=compact(rows_u), elite=compact(rows_e))


def run(cand, tag, teams, n, gate):
    import extract
    files = {r['gid']: os.path.join(extract.GAMES, r['file']) for r in extract._index()}
    S = seats(teams, n, gate)
    jobs = [(g, gid, s, team, os.path.abspath(cand), files[gid]) for g, gid, s, team in S if gid in files]
    print(len(jobs), 'seats', dict(collections.Counter(short(j[3]) for j in jobs)), flush=True)
    out = os.path.join(HERE, 'out_%s.jsonl' % tag)
    t0 = time.time(); ms = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(job, jobs):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
            ms.append(x['m'])
            print(short(x['team']), x['gid'], 'm', x['m'], 'us', x['us'], 'el', x['tape'], 'wall', x['wall'],
                  'err', (x['tel'] or {}).get('gc_errors'), (x['tel'] or {}).get('gc_last_error', '')[:80], 'T', round(time.time() - t0), flush=True)
    ok = [m for m in ms if m is not None]
    print('ALLDONE', tag, len(ok), 'wins', sum(m > 0 for m in ok), 'margin', round(sum(ok) / max(1, len(ok))), flush=True)


def load(tag):
    f = tag if tag.endswith('.jsonl') else os.path.join(HERE, 'out_%s.jsonl' % tag)
    return [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]


def t8rows():
    R = {}
    for f in T8ROWS:
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            R[(r['gid'], r['seat'])] = r
    return R


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float('nan')


def sellsum(day, items=None):
    return sum(v[1] for k, v in day['sell'].items() if items is None or k in items)


def cmp(tags, team=None, d0=0, d1=16):
    for tag in tags:
        X = load(tag)
        if team:
            X = [x for x in X if short(x['team']) in team.split(',')]
        print('==', tag, len(X), 'seats', dict(collections.Counter(short(x['team']) for x in X)))
        ms = [x['m'] for x in X]
        print('   margin %+.0f  wins %d/%d  us %.0f  elite %.0f' % (mean(ms), sum(m > 0 for m in ms), len(ms),
                                                                    mean(x['us'] for x in X), mean(x['tape'] for x in X)))
        hdr = ' d | side  m0     mend  quads  G    C    S   | Str  Wht  Mel  Tom Car | hire wage | sell$  fert milk wool egg  | seed$ anim$ land'
        print(hdr)
        for d in range(d0, d1 + 1):
            for side in ('ours', 'elite'):
                D = [x[side][d] for x in X]
                q = mean(len(dd['quads'] or []) for dd in D)
                h = {a: mean(dd['herd'].get(a, 0) for dd in D) for a in ANIM}
                c = {k: mean(dd['crops'].get(k, 0) for dd in D) for k in ('STRAWBERRY', 'WHEAT', 'MELON', 'TOMATO', 'CARROT')}
                print('%2d | %-5s %6.0f %6.0f %4.2f %4.1f %4.1f %4.1f | %4.1f %4.1f %4.1f %4.1f %4.1f | %4.1f %5.0f | %6.0f %4.0f %4.0f %4.0f %4.0f | %5.0f %5.0f %s' % (
                    d, side[:5], mean(dd['m0'] for dd in D), mean(dd['mend'] for dd in D), q, h['GOOSE'], h['COW'], h['SHEEP'],
                    c['STRAWBERRY'], c['WHEAT'], c['MELON'], c['TOMATO'], c['CARROT'],
                    mean(dd['hires'] for dd in D), mean(dd['wage'] for dd in D),
                    mean(sellsum(dd) for dd in D), mean(sellsum(dd, ('FERTILIZER',)) for dd in D),
                    mean(sellsum(dd, ('MILK',)) for dd in D), mean(sellsum(dd, ('WOOL',)) for dd in D), mean(sellsum(dd, ('EGG',)) for dd in D),
                    mean(sum(v[1] for v in dd['bs'].values()) for dd in D), mean(sum(v[1] for v in dd['ba'].values()) for dd in D),
                    ' '.join('%s%.0f' % (k, 100.0 * sum(1 for dd in D if any(l[0] == k for l in dd['land'])) / len(D)) for k in ('NE', 'SW', 'SE')
                             if any(any(l[0] == k for l in dd['land']) for dd in D))))
        # product ledger
        keys = sorted({k for x in X for k in list(x['led_us']) + list(x['led_elite'])})
        print('   ledger (mean $): ' + '  '.join('%s us %.0f el %.0f' % (k, mean(x['led_us'].get(k, 0) for x in X), mean(x['led_elite'].get(k, 0) for x in X)) for k in keys))


def gate(tag, base=None):
    X = load(tag)
    B = t8rows() if base is None else {(r['gid'], r['seat']): r for f in base for r in load(f)}
    by = collections.defaultdict(list)
    for x in X:
        b = B.get((x['gid'], x['seat']))
        if b is None or x['m'] is None:
            continue
        by[short(x['team'])].append((x, b))
        by['ALL'].append((x, b))
    import statistics
    col = [(x, b) for x, b in by['ALL'] if x['tape'] < 0.6 * b['tape']]
    if col:
        print('   elite tape collapses (elite final < 60%% of base): %d  %s' % (len(col), [(x['gid'], int(x['tape']), int(b['tape'])) for x, b in col]))
    for t in list(by):
        by[t + '*'] = [(x, b) for x, b in by[t] if x['tape'] >= 0.6 * b['tape']]
    for t, xs in sorted(by.items()):
        n = len(xs)
        if not n:
            continue
        dm = [x['m'] - b['m'] for x, b in xs]
        mu = mean(dm); sd = (sum((v - mu) ** 2 for v in dm) / max(1, n - 1)) ** 0.5
        print('%-5s n %3d  delta %+7.0f +- %5.0f  wins %2d -> %2d   m base %+7.0f new %+7.0f' % (
            t, n, mu, sd / max(1, n) ** 0.5, sum(b['m'] > 0 for x, b in xs), sum(x['m'] > 0 for x, b in xs),
            mean(b['m'] for x, b in xs), mean(x['m'] for x, b in xs)) + '  median %+.0f' % statistics.median(dm))
        if t == 'ALL':
            keys = sorted({k for x, b in xs for k in list(x['led_elite']) + list(b.get('led_elite', {}))})
            print('   elite ledger delta (new - base): ' + '  '.join('%s %+.0f' % (k, mean(x['led_elite'].get(k, 0) - b.get('led_elite', {}).get(k, 0) for x, b in xs)) for k in keys))
            keys = sorted({k for x, b in xs for k in list(x['led_us']) + list(b.get('led_us', {}))})
            print('   our ledger delta (new - base):   ' + '  '.join('%s %+.0f' % (k, mean(x['led_us'].get(k, 0) - b.get('led_us', {}).get(k, 0) for x, b in xs)) for k in keys))


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'run':
        cand, tag = sys.argv[2], sys.argv[3]
        teams = sys.argv[4] if len(sys.argv) > 4 else 'hf'
        teams = teams if teams in ('all', 'nothf') else (['FQ', 'Boey', 'TFC'] if teams == 'hf' else teams.split(','))
        n = int(sys.argv[5]) if len(sys.argv) > 5 else 5
        g = sys.argv[6] if len(sys.argv) > 6 else 'both'
        run(cand, tag, teams, n, g)
    elif mode == 'cmp':
        args = sys.argv[2:]
        team = None; d0, d1 = 0, 16
        if '--team' in args:
            i = args.index('--team'); team = args[i + 1]; args = args[:i] + args[i + 2:]
        if '--days' in args:
            i = args.index('--days'); d0, d1 = (int(v) for v in args[i + 1].split('-')); args = args[:i] + args[i + 2:]
        cmp(args, team, d0, d1)
    elif mode == 'trace':
        # trace tag gid [side] [d0-d1]: per-day fills and ops of one seat
        X = [x for x in load(sys.argv[2]) if str(x['gid']) == sys.argv[3]]
        side = sys.argv[4] if len(sys.argv) > 4 else 'ours'
        d0, d1 = (int(v) for v in (sys.argv[5] if len(sys.argv) > 5 else '0-9').split('-'))
        for x in X:
            print(x['team'], x['gid'], 'm', x['m'], 'tel', {k: v for k, v in (x['tel'] or {}).items() if k.startswith('gc_open')})
            for D in x[side][d0:d1 + 1]:
                print('d', D['d'], 'm0', D['m0'], 'mmin', D['mmin'], 'hires', D['hires'], D.get('hire_h'), 'herd', D['herd'], 'crops', D['crops'],
                      'shed', D.get('shed'), 'seeds', D.get('seeds'), 'shops', D['shops'], 'free', D['free'], 'weeds', D['weeds'])
                print('   fills', D.get('fills'))
                print('   ops', dict(sorted((D.get('ops') or {}).items())), 'fail', D['fail'], 'move', D['move'], 'pass', D['pas'])
    elif mode == 'gate':
        gate(sys.argv[2], sys.argv[3:] or None)
