"""SF clone diagnostics: elite_gate play (candidate vs repaired elite recording in its town, cached refs) with the
openmine Logger on, so one run gives the gate row and the per-day logs of both farms.
usage (from kg/): diag.py games.jsonl.gz refs.jsonl cand.py tag [teams] [max]
  -> sf/out/<tag>_gate.jsonl (elite_gate row format + 'gate'), sf/out/<tag>_days.jsonl (both seats, role ours/elite_rep)
"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '..'))
for p in ('arena', 'gold/harness', 'gold/elite', 'gold/top10/research/openmine'):
    sys.path.insert(0, os.path.join(KG, p))
OUT = os.path.join(HERE, 'out')


def _play(t):
    import lean, extract
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand, tag = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    L = extract.Logger(); L.install()
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        L.uninstall(); K._end_of_day = orig
    tape, cd = r['r'][s], r['r'][1 - s]
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    led = [collections.Counter(), collections.Counter()]
    for p in (0, 1):
        for dd, D in L.days[p].items():
            for it, (n, v) in D['sell'].items(): led[p][it] += v
            for it, (n, v) in D['buy_prod'].items(): led[p][it] -= v
            for it, (n, v) in D['buy_seed'].items(): led[p]['seed'] -= v
            for it, (n, v) in D['buy_animal'].items(): led[p]['anim'] -= v
            led[p]['hire'] -= D['wage']
            led[p]['land'] -= sum(e['price'] for e in D['land'])
    gate = dict(gid=ref['gid'], seat=s, team=ref['team'], cand=tag, tape=tape, us=cd, m=(cd - tape) if tape is not None and cd is not None else None,
                err=r['err'], tmax=r['tmax'], rec_tape=ref['rec_tape'], wall=round(time.time() - t0, 1),
                led_us={k: round(v, 1) for k, v in led[1 - s].items()}, led_elite={k: round(v, 1) for k, v in led[s].items()}, tel=tel)
    rows = []
    for p, role in ((1 - s, 'ours'), (s, 'elite_rep')):
        head = dict(gid=ref['gid'], seat=p, team=(tag if role == 'ours' else ref['team']), opp=(ref['team'] if role == 'ours' else tag),
                    role=role, cand=tag)
        rs, seat = L.rows(p, head, r['r'][p])
        rows += [x for x in rs if x['d'] <= 17]
    return gate, rows


if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, cand, tag = sys.argv[1:5]
    teams = sys.argv[5].split(',') if len(sys.argv) > 5 and sys.argv[5] not in ('', 'all') else None
    maxg = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
    R = [json.loads(l) for l in open(refs, encoding='utf-8')]
    if teams:
        R = [r for r in R if r['team'] in teams]
    ids = os.environ.get('GIDS')
    if ids:
        keep = set(int(x) for x in open(ids).read().split())
        R = [r for r in R if r['gid'] in keep]
    R = R[:maxg]
    need = set(r['gid'] for r in R)
    games = {}
    for g in load_games(path):
        if g['id'] in need:
            games[g['id']] = g
    jobs = [(games[r['gid']], r, os.path.abspath(cand), tag) for r in R]
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time(); res = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, \
            open(os.path.join(OUT, tag + '_gate.jsonl'), 'w', encoding='utf-8') as fg, \
            open(os.path.join(OUT, tag + '_days.jsonl'), 'w', encoding='utf-8') as fd:
        for gate, rows in ex.map(_play, jobs):
            res.append(gate); fg.write(json.dumps(gate, ensure_ascii=False) + '\n'); fg.flush()
            for x in rows: fd.write(json.dumps(x, ensure_ascii=False) + '\n')
            fd.flush()
            print(len(res), gate['team'], gate['gid'], 'm', gate['m'], 'us', gate['us'], 'el', gate['tape'], 'wall', gate['wall'],
                  'err', [e for e in gate['err'] if e][:1], flush=True)
    ok = [x for x in res if x['m'] is not None]
    by = collections.defaultdict(list)
    for x in ok: by[x['team']].append(x)
    for team, xs in sorted(by.items()):
        n = len(xs)
        print(f"{team[:22]:22s} {n:4d} W{sum(x['m'] > 0 for x in xs):3d} m {sum(x['m'] for x in xs)/n:+8.0f} us {sum(x['us'] for x in xs)/n:7.0f} el {sum(x['tape'] for x in xs)/n:7.0f}")
    print('ALLDONE', tag, len(ok), 'W', sum(x['m'] > 0 for x in ok), 'm', round(sum(x['m'] for x in ok) / max(1, len(ok))), 'wall', round(time.time() - t0))
