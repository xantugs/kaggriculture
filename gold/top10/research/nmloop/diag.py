"""diag.py CAND [GID ...] : milestones for ChatGPT: first day our herd/crops reach COW 5/7, GOOSE 2/5/7, MELON 12, quadrants
2/3, and minimum cash on days 5-10, for us and for the (repaired) rival, in ladder games (default: pangzi, RS Turley, Y&G)."""
import sys, os, json, io, contextlib
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite')); sys.path.insert(0, 'gold/top10/research/temporal')
with contextlib.redirect_stdout(io.StringIO()):
    import lean, extract_t as X
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
sys.stdout.reconfigure(encoding='utf-8')
cand = sys.argv[1]; gids = [int(x) for x in sys.argv[2:]] or [115336805, 115335380, 115333932]
D = 'gold/top10/research/v33loss/'
games = {r['id']: r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{'))}
refs = {json.loads(l)['gid']: json.loads(l) for l in open(D + 'ladder_refs.jsonl', encoding='utf-8')}
def first(byd, f):
    for d in range(30):
        x = byd.get(d)
        if x and f(x): return d
    return '-'
for gid in gids:
    ref = refs[gid]; d = games[gid]; s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops']); L = X.Logger(); L.install()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
        with contextlib.redirect_stdout(io.StringIO()):
            r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        L.uninstall(); K._end_of_day = orig
    out = []
    for who, p in (('us', 1 - s), ('rival', s)):
        rows, _ = L.rows(p, dict(gid=gid, seat=p, team=who, opp='', role='x', cand=None), r['r'][p])
        byd = {x['d']: x for x in rows}
        h = lambda k, n: first(byd, lambda x: (x.get('herd') or {}).get(k, 0) >= n)
        c = lambda k, n: first(byd, lambda x: (x.get('crops') or {}).get(k, 0) >= n)
        q = lambda n: first(byd, lambda x: len(x.get('quads') or []) >= n)
        mc = min(int(byd[dd]['mmin']) for dd in range(5, 11) if dd in byd and byd[dd].get('mmin') is not None)
        wages = sum(float(byd[dd].get('wage') or 0) for dd in range(0, 11) if dd in byd)
        hands = '/'.join(str(byd[dd].get('hands')) for dd in (1, 3, 5, 7, 9) if dd in byd)
        spend = {k: sum(v[1] for dd in range(0, 11) if dd in byd for kk, v in (byd[dd].get(k2) or {}).items() for k2 in [k] if True) for k in ()}
        seeds = sum(v[1] for dd in range(0, 11) if dd in byd for v in (byd[dd].get('buy_seed') or {}).values())
        anim = sum(v[1] for dd in range(0, 11) if dd in byd for v in (byd[dd].get('buy_animal') or {}).values())
        sold = sum(v[1] for dd in range(0, 11) if dd in byd for v in (byd[dd].get('sell') or {}).values())
        out.append('%s: d0-10 wages $%d seeds $%d animals $%d sold $%d hands d1/3/5/7/9 %s' % (who, wages, seeds, anim, sold, hands))
        out.append('%s: cow5 d%s cow7 d%s goose2 d%s goose5 d%s goose7 d%s melon12 d%s quad2 d%s quad3 d%s mincash5-10 $%d final %.0f' % (
            who, h('COW', 5), h('COW', 7), h('GOOSE', 2), h('GOOSE', 5), h('GOOSE', 7), c('MELON', 12), q(2), q(3), mc, r['r'][p]))
    print('%d %s | %s' % (gid, str(d['meta']['opp'])[:10], ' || '.join(out)))
