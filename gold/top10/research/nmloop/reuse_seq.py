"""reuse_seq.py CAND N : play the first N ladder-gate games (lad_v33) back to back in ONE loaded module and compare each result with
the fresh-module row of the same candidate (lad_TAPE / lad_NMp44Tr). Reports outcome flips caused by module reuse."""
import sys, os, json, io, gzip, contextlib
sys.path.insert(0, 'arena'); sys.path.insert(0, 'gold/harness'); sys.path.insert(0, 'gold/elite')
with contextlib.redirect_stdout(io.StringIO()):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
cand, n, fresh_rows = sys.argv[1], int(sys.argv[2]), sys.argv[3]
G = 'gold/top10/gates/'
refs = [json.loads(l) for l in open(G + 'lad_v33_refs.jsonl', encoding='utf-8')][:n]
want = {r['gid'] for r in refs}
games = {}
with gzip.open(G + 'lad_v33_games.jsonl.gz', 'rt', encoding='utf-8') as fh:
    for l in fh:
        g = json.loads(l)
        if g['id'] in want: games[g['id']] = g
fresh = {(x['gid'], x['seat']): x for x in (json.loads(l) for l in open(fresh_rows, encoding='utf-8') if l.startswith('{'))}
A = lean.load(cand)
diff = flips = 0
for ref in refs:
    d = games[ref['gid']]; s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = A
        with contextlib.redirect_stdout(io.StringIO()):
            r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    m = r['r'][1 - s] - r['r'][s]; f = fresh[(ref['gid'], s)]['m']
    if abs(m - f) > 0.5:
        diff += 1; fl = (m > 0) != (f > 0); flips += fl
        print('  differs %s %-16s fresh %+8.0f reused %+8.0f%s' % (ref['gid'], ref['team'][:16], f, m, '  FLIP' if fl else ''), flush=True)
print('%s: %d games in one module: %d differ from fresh, %d outcome flips' % (os.path.basename(cand), n, diff, flips))
