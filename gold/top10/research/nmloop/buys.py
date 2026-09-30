"""buys.py CAND GID : per day (0-11) purchases, sales, hires and cash for us and the repaired rival in one ladder game."""
import sys, os, json, io, contextlib
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite')); sys.path.insert(0, 'gold/top10/research/temporal')
with contextlib.redirect_stdout(io.StringIO()):
    import lean, extract_t as X
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
sys.stdout.reconfigure(encoding='utf-8')
cand, gid = sys.argv[1], int(sys.argv[2])
D = 'gold/top10/research/v33loss/'
games = {r['id']: r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{'))}
ref = {json.loads(l)['gid']: json.loads(l) for l in open(D + 'ladder_refs.jsonl', encoding='utf-8')}[gid]
d = games[gid]; s = ref['seat']
rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
orig = install_town(ref['shops']); L = X.Logger(); L.install()
try:
    ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
    with contextlib.redirect_stdout(io.StringIO()):
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
finally:
    L.uninstall(); K._end_of_day = orig
f = lambda dct: ' '.join('%s%d' % (k[:2], v[0]) for k, v in sorted((dct or {}).items()))
for who, p in (('US', 1 - s), ('RIV', s)):
    rows, _ = L.rows(p, dict(gid=gid, seat=p, team=who, opp='', role='x', cand=None), r['r'][p])
    byd = {x['d']: x for x in rows}
    for dd in range(0, 12):
        x = byd.get(dd)
        if not x: continue
        sold = sum(v[1] for v in (x.get('sell') or {}).values())
        print('%-3s d%-2d m0 $%5.0f min $%4.0f | anim %-14s seeds %-24s land %s | hires %d wage %3.0f | sold $%5.0f %s' % (
            who, dd, x.get('m0') or 0, x.get('mmin') or 0, f(x.get('buy_animal')), f(x.get('buy_seed')), [e.get('q') for e in x.get('land') or []],
            x.get('hires') or 0, x.get('wage') or 0, sold, f(x.get('sell'))))
