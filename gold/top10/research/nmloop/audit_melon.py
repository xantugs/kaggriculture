"""audit_melon.py CAND N_EACH OUT : short-cohort forensic (ChatGPT L20). On fresh29 band seats, the 12-melon rule 'fired' (NMp26
differs from NMp13: full cohort) or not (short cohort). Replays N_EACH seats of each kind with CAND and the extract_t Logger and
writes, per seat, our days 0-7: cash at dawn / minimum, melon plants standing, seeds bought (melon/wheat/strawberry), animals
bought, hires and wages, land, free tiles; plus the elite's step-1 money."""
import sys, os, json, io, gzip, contextlib, random
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness'))
sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite')); sys.path.insert(0, 'gold/top10/research/temporal')
with contextlib.redirect_stdout(io.StringIO()):
    import lean, extract_t as X
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
cand, n_each, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
N = 'gold/top10/research/nmloop/'; G = 'gold/top10/gates/'
refs = {}
for l in open(G + 'fresh29_refs.jsonl', encoding='utf-8'):
    r = json.loads(l); refs[(r['gid'], r['seat'])] = r
def band(r):
    m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
    return 940 <= m <= 980 and h == 0
def rows(p): return {(x['gid'], x['seat']): x for x in (json.loads(l) for l in open(p, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None}
A, B = rows(N + 'f29_NMp13.jsonl'), rows(N + 'f29_NMp26.jsonl')
ks = [k for k in B if k in A and band(refs[k])]
fired = sorted(k for k in ks if abs(B[k]['m'] - A[k]['m']) > 1); short = sorted(k for k in ks if abs(B[k]['m'] - A[k]['m']) <= 1)
rnd = random.Random(7)
pick = [('full', k) for k in rnd.sample(fired, min(n_each, len(fired)))] + [('short', k) for k in rnd.sample(short, min(n_each, len(short)))]
want = {k[0] for _, k in pick}
games = {}
with gzip.open(G + 'fresh29_games.jsonl.gz', 'rt', encoding='utf-8') as fh:
    for l in fh:
        g = json.loads(l)
        if g['id'] in want: games[g['id']] = g
fo = open(out, 'w', encoding='utf-8')
for kind, (gid, s) in pick:
    ref = refs[(gid, s)]; d = games[gid]
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops']); L = X.Logger(); L.install()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
        with contextlib.redirect_stdout(io.StringIO()):
            r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        L.uninstall(); K._end_of_day = orig
    p = 1 - s
    days, _ = L.rows(p, dict(gid=gid, seat=p, team='us', opp='', role='x', cand=None), r['r'][p])
    rec = dict(kind=kind, gid=gid, seat=s, team=ref['team'], m=r['r'][p] - r['r'][s], shops=ref['shops'][:3], days=[])
    for x in days[:8]:
        rec['days'].append(dict(d=x['d'], m0=x['m0'], mmin=x['mmin'], mmin_h=x['mmin_h'], melons=(x.get('crops') or {}).get('MELON', 0),
                                crops=x.get('crops'), seeds=x.get('buy_seed'), anim=x.get('buy_animal'), prod=x.get('buy_prod'), hires=x['hires'],
                                wage=x['wage'], land=[(e['q'], e['h'], e['price']) for e in x.get('land') or []], free=x.get('free'), sell=x.get('sell'),
                                herd=x.get('herd')))
    fo.write(json.dumps(rec) + '\n'); fo.flush()
    print(kind, gid, s, ref['team'][:10], 'melons by day', [y['melons'] for y in rec['days']], 'margin %+.0f' % rec['m'], flush=True)
