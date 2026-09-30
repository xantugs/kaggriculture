"""azrs.py GID CAND_A CAND_B : side-by-side daily trace of two candidates in one ladder game (vs the repaired rival): our cash,
the rival's cash and the margin (ours - rival) per day from day 5, the margin-gap B - A, product revenue that day, herd, hires
and crop tiles; reports the first day the gap exceeds $1k."""
import sys, os, json, io, contextlib, collections
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite')); sys.path.insert(0, 'gold/top10/research/temporal')
with contextlib.redirect_stdout(io.StringIO()):
    import lean, extract_t as X
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
sys.stdout.reconfigure(encoding='utf-8')
gid, ca, cb = int(sys.argv[1]), sys.argv[2], sys.argv[3]
X.DETAIL_DAYS = 30
D = 'gold/top10/research/v33loss/'
games = {r['id']: r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{'))}
ref = {json.loads(l)['gid']: json.loads(l) for l in open(D + 'ladder_refs.jsonl', encoding='utf-8')}[gid]
def run(cand):
    d = games[gid]; s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops']); L = X.Logger(); L.install()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
        with contextlib.redirect_stdout(io.StringIO()):
            r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        L.uninstall(); K._end_of_day = orig
    out = {}
    for who, p in (('us', 1 - s), ('riv', s)):
        rows, _ = L.rows(p, dict(gid=gid, seat=p, team=who, opp='', role='x', cand=None), r['r'][p])
        out[who] = {x['d']: x for x in rows}
    return out, r['r'][1 - s], r['r'][s]
A, fa, ra = run(ca); B, fb, rb = run(cb)
if len(sys.argv) > 4:
    json.dump(dict(A=A, B=B, fa=fa, ra=ra, fb=fb, rb=rb), open(sys.argv[4], 'w'), default=str)
print('%d %s: A final %.0f vs rival %.0f (%+.0f) | B final %.0f vs rival %.0f (%+.0f)' % (gid, games[gid]['meta']['opp'], fa, ra, fa - ra, fb, rb, fb - rb))
first = None
for d in range(5, 30):
    a, b = A['us'].get(d), B['us'].get(d); ar, br = A['riv'].get(d), B['riv'].get(d)
    if not (a and b and ar and br): continue
    ma = (a.get('mend') or 0) - (ar.get('mend') or 0); mb = (b.get('mend') or 0) - (br.get('mend') or 0)
    gap = mb - ma
    if first is None and abs(gap) > 1000: first = d
    sa = sum(v[1] for v in (a.get('sell') or {}).values()); sb = sum(v[1] for v in (b.get('sell') or {}).values())
    fmt = lambda x: ' '.join('%s%d' % (k[:2], v[0]) for k, v in sorted((x.get('sell') or {}).items()))
    ha, hb = a.get('herd') or {}, b.get('herd') or {}
    print('d%-2d A us $%6.0f riv $%6.0f m %+6.0f | B us $%6.0f riv $%6.0f m %+6.0f | gap %+6.0f | sold A $%5.0f [%s] B $%5.0f [%s] | herd A C%dS%dG%d B C%dS%dG%d | hires %s/%s' % (
        d, a.get('mend') or 0, ar.get('mend') or 0, ma, b.get('mend') or 0, br.get('mend') or 0, mb, gap, sa, fmt(a), sb, fmt(b),
        ha.get('COW', 0), ha.get('SHEEP', 0), ha.get('GOOSE', 0), hb.get('COW', 0), hb.get('SHEEP', 0), hb.get('GOOSE', 0), a.get('hires'), b.get('hires')))
print('first day |gap| > $1k:', first)
