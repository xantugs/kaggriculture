"""herd_screen.py : one game of T8fcWt vs each herd-type public agent (seed 7400, both seats), margin and wall time."""
import sys, os, time, json
from concurrent.futures import ProcessPoolExecutor
AG = ['findings-from-zero-to-top-meta', 'strongest-farmer-of-today', 'x544-nah-i-d-win', 'limit-breaker-agent', 'weedproof-clone-market',
      'adaptive-public-state-multi-route', 'breaking-the-tie', 'precomputed-schedule-policy', 'c01-scenario-v7-reproduction']
AG = ['../pubnb/x_kaggriculture-%s.py' % a for a in AG] + ['../pubnb/x_%s.py' % a for a in (
      'counter-cyclical-orchard', 'two-reinforcement-learning-examples-from-kaito-v27', 'v21-r1-public-state-route-portfolio',
      'wide-sigma-cma-tuned-scenario-aware-submitted', 'king-v4e-rc4', 'titan-kaggriculture-frontier-source', 'shabby-farm', 'notebooke394244546')] + [
      '../pubnb/x_kaggriculture-%s.py' % a for a in ('v01-drip', 'c02-core-3-cow-1-sheep', 'c07-public-v12-tape', 'hamburger')]
def one(path):
    sys.path.insert(0, os.path.join(os.getcwd(), 'arena'))
    import lean
    out = []
    for seat in (0, 1):
        t = time.time()
        try:
            A = lean.load('gold/top10/cands/full_T8fcWt.py'); B = lean.load(path)
            objs = [A, B] if seat == 0 else [B, A]
            r = lean.play(None, None, 7400, agent_objs=objs)
            us, them = (r['r'][0], r['r'][1]) if seat == 0 else (r['r'][1], r['r'][0])
            out.append((seat, us, them, round(time.time() - t)))
        except Exception as e:
            out.append((seat, None, repr(e)[:80], round(time.time() - t)))
    return path, out
if __name__ == '__main__':
    with ProcessPoolExecutor(4) as ex:
        for path, out in ex.map(one, AG):
            print('%-62s %s' % (os.path.basename(path)[2:64], '  '.join(('seat%d us %6.0f them %6.0f (%+6.0f) %ds' % (s, u, th, u - th, w)) if u is not None else ('seat%d ERR %s' % (s, th)) for s, u, th, w in out)), flush=True)
