"""herd_panel.py : controller (pure form c0tp) and tape (T8fcWt, FWt) vs the 12 reacting herd-poor public agents, seeds 7500-7509,
both seats; rows research/opening/hp_<cand>.jsonl with seed, seat, opp, m."""
import sys, os, json
from concurrent.futures import ProcessPoolExecutor
HP = ['../pubnb/x_kaggriculture-%s.py' % a for a in ('findings-from-zero-to-top-meta', 'strongest-farmer-of-today', 'x544-nah-i-d-win', 'limit-breaker-agent',
      'weedproof-clone-market', 'adaptive-public-state-multi-route', 'breaking-the-tie', 'precomputed-schedule-policy', 'c01-scenario-v7-reproduction')] + \
     ['../pubnb/x_%s.py' % a for a in ('counter-cyclical-orchard', 'two-reinforcement-learning-examples-from-kaito-v27', 'v21-r1-public-state-route-portfolio')]
CANDS = {'c0tp': 'gold/top10/cands/full_OP_c0tp.py', 'T8fcWt': 'gold/top10/cands/full_T8fcWt.py', 'FWt': 'gold/top10/cands/full_FWt.py'}
def one(task):
    tag, opp, seed, seat = task
    sys.path.insert(0, os.path.join(os.getcwd(), 'arena'))
    import lean
    try:
        A = lean.load(CANDS[tag]); B = lean.load(opp)
        r = lean.play(None, None, seed, agent_objs=[A, B] if seat == 0 else [B, A])
        us, them = (r['r'][0], r['r'][1]) if seat == 0 else (r['r'][1], r['r'][0])
        tel = getattr(A, 'telemetry', {}) or {}
        return dict(tag=tag, opp=os.path.basename(opp), seed=seed, seat=seat, us=us, them=them, m=us - them, route=tel.get('gc_route'), errs=tel.get('gc_errors'))
    except Exception as e:
        return dict(tag=tag, opp=os.path.basename(opp), seed=seed, seat=seat, m=None, err=repr(e)[:120])
if __name__ == '__main__':
    tasks = [(t, o, s, st) for o in HP for s in range(7500, 7510) for st in (0, 1) for t in CANDS]
    fh = {t: open('gold/top10/research/opening/hp_%s.jsonl' % t, 'w', encoding='utf-8') for t in CANDS}
    with ProcessPoolExecutor(6) as ex:
        for row in ex.map(one, tasks, chunksize=4):
            fh[row['tag']].write(json.dumps(row) + '\n'); fh[row['tag']].flush()
    print('herd panel done')
