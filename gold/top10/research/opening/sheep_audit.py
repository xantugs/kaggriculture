"""sheep_audit.py CAND OUT : our animal purchases (step, item) on the elite seats whose final town has no YARN_STORE
(goldg + top10g), using elite_gate's seat runner with one extra hook; for the NY_SHEEP_CAP feasibility check."""
import sys, os, json, time, collections
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor

def _play(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    FARMS = [None, None]; STEP = [0]; buys = []
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and op == 'BUY_ANIMAL' and FARMS[0] is not None and farm is FARMS[1 - s]:
            buys.append((STEP[0], item, price))
        return ok
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]; STEP[0] = int(state[0].observation.step)
        return opm(state, env)
    K._commit_unit = commit; K._process_market = pm
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm
    return dict(gid=ref['gid'], seat=s, team=ref['team'], m=r['r'][1 - s] - r['r'][s], buys=buys, shops=ref['shops'])

if __name__ == '__main__':
    from eval_elite_routes import load_games
    cand, out = sys.argv[1], sys.argv[2]
    jobs = []
    for gz, refs in (('gold/top10/gates/goldg_games.jsonl.gz', 'gold/top10/gates/goldg_refs.jsonl'), ('gold/top10/gates/top10g_games.jsonl.gz', 'gold/top10/gates/top10g_refs.jsonl')):
        R = [json.loads(l) for l in open(refs, encoding='utf-8')]
        want = {(r['gid'], r['seat']): r for r in R if 'YARN_STORE' not in r['shops']}
        for d in load_games(gz):
            for s in (0, 1):
                if (d['id'], s) in want: jobs.append((d, want[(d['id'], s)], cand))
    print(len(jobs), 'no-yarn seats', flush=True)
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '6'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(_play, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
