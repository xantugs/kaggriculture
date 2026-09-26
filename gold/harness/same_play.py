"""Do two builds play identically? Both play the same seeds against the same opponent; the first differing step is reported.
usage: same_play.py a.py b.py opp.py seed1,seed2,...  [elite]   (with 'elite': also 6 repaired elite seats in their towns)"""
import sys, json
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
import lean

def rec(cand, opp, seed, agent_objs=None):
    A = lean.load(cand)
    if agent_objs is None:
        B = lean.load(opp); objs = [A, B]
    else:
        objs = list(agent_objs); objs[0] = A
    r = lean.play(None, None, seed, record=True, agent_objs=objs)
    return r['r'], [a[0] for a in r['actions']]

def compare(a, b, opp, seed, agent_objs=None):
    ra, sa = rec(a, opp, seed, agent_objs); rb, sb = rec(b, opp, seed, agent_objs)
    for t, (x, y) in enumerate(zip(sa, sb)):
        if json.dumps(x, sort_keys=True) != json.dumps(y, sort_keys=True):
            return 'DIFF at step %d (money %s vs %s)' % (t, ra, rb)
    return 'identical (%s)' % (ra,)

if __name__ == '__main__':
    a, b, opp = sys.argv[1], sys.argv[2], sys.argv[3]
    seeds = [int(x) for x in sys.argv[4].split(',')]
    bad = 0
    for s in seeds:
        out = compare(a, b, opp, s); print('seed', s, out); bad += out.startswith('DIFF')
    if len(sys.argv) > 5 and sys.argv[5] == 'elite':
        from eval_elite_routes import install_town, load_games
        from transplant import build_agent
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        import os
        R = [json.loads(l) for l in open('/home/user/kaggriculture/gold/elite/elite_gate_refs.jsonl')]
        en = int(os.environ.get('ELITE_N', '6')); R = R[::max(1, len(R) // en)][:en]
        games = {g['id']: g for g in load_games('/home/user/kaggriculture/moon/elite/games_2026-09-20.jsonl.gz') if g['id'] in {r['gid'] for r in R}}
        for ref in R:
            d = games[ref['gid']]; s = ref['seat']
            rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
            outs = []
            for cand in (a, b):
                orig = install_town(ref['shops'])
                try:
                    ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = lean.load(cand)
                    r = lean.play(None, None, ref['seed'], record=True, agent_objs=ag)
                finally:
                    K._end_of_day = orig
                outs.append((r['r'], [x[1 - s] for x in r['actions']]))
            diff = next((t for t, (x, y) in enumerate(zip(outs[0][1], outs[1][1])) if json.dumps(x, sort_keys=True) != json.dumps(y, sort_keys=True)), None)
            print('elite %s seat %d: %s' % (ref['team'], s, 'identical (%s)' % (outs[0][0],) if diff is None else 'DIFF at step %d' % diff)); bad += diff is not None
    print('RESULT', 'IDENTICAL' if bad == 0 else 'DIFFERENT (%d)' % bad)
