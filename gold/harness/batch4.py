"""Paired closed-loop batch in the decoupled engine, 16 processes.
usage: batch.py candA opp seeds(a-b or list) out.jsonl [seats=01]
Prints W-L, mean margin, mean money, and per-product revenue deltas."""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))

def job(t):
    import lean, decouple
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    a, b, seed, seat = t
    decouple.install(0)
    led = [collections.Counter(), collections.Counter()]
    FARMS = [None, None]
    orig_c = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = orig_c(op, item, price, farm, private, market, cap)
        if ok and op == 'SELL':
            led[0 if farm is FARMS[0] else 1][item] += price
        elif ok and op in ('BUY_PRODUCT', 'BUY_SEED', 'BUY_ANIMAL'):
            led[0 if farm is FARMS[0] else 1][item if op == 'BUY_PRODUCT' else ('seed' if op == 'BUY_SEED' else 'anim')] -= price
        return ok
    K._commit_unit = commit
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        led[0 if farm is FARMS[0] else 1]['hire'] += farm['money'] - m0
    K._do_hire = hire
    orig_pm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return orig_pm(state, env)
    K._process_market = pm
    A = lean.load(a); B = lean.load(b)
    r = lean.play(None, None, seed, agent_objs=[A, B] if seat == 0 else [B, A])
    K._commit_unit = orig_c; K._process_market = orig_pm; K._do_hire = oh
    us, them = r['r'][seat], r['r'][1 - seat]
    tel = dict(getattr(A, 'telemetry', {}) or {})
    return dict(a=a, b=b, seed=seed, seat=seat, us=us, them=them, m=(us - them) if us is not None and them is not None else None,
                err=r['err'], tmax=r['tmax'][seat], shops=r['shops'], rev_us=dict(led[seat]), rev_them=dict(led[1 - seat]), tel=tel)

def seeds_of(s):
    if '-' in s:
        a, b = s.split('-'); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(',')]

if __name__ == '__main__':
    a, b, ss, out = sys.argv[1], sys.argv[2], seeds_of(sys.argv[3]), sys.argv[4]
    seats = [int(c) for c in (sys.argv[5] if len(sys.argv) > 5 else '01')]
    jobs = [(a, b, s, st) for s in ss for st in seats]
    t = time.time(); res = []
    with ProcessPoolExecutor(4) as ex, open(out, 'w') as fh:
        for r in ex.map(job, jobs):
            res.append(r); fh.write(json.dumps(r) + '\n'); fh.flush()
    ok = [r for r in res if r['m'] is not None]
    w = sum(r['m'] > 0 for r in ok); l = sum(r['m'] < 0 for r in ok)
    n = max(1, len(ok))
    print(f"{a} vs {b}: {w}-{l}-{len(ok)-w-l} of {len(ok)}  margin {sum(r['m'] for r in ok)/n:+.0f}  us {sum(r['us'] for r in ok)/n:.0f}  them {sum(r['them'] for r in ok)/n:.0f}  errs {sum(1 for r in res if any(r['err']))}  tmax {max(r['tmax'] for r in res):.3f}  wall {time.time()-t:.0f}s")
    keys = sorted(set(k for r in ok for k in list(r['rev_us']) + list(r['rev_them'])))
    print('  net us-them:', ' '.join(f"{k[:5]} {sum(r['rev_us'].get(k,0)-r['rev_them'].get(k,0) for r in ok)/n:+.0f}" for k in keys))
    print('  rev us     :', ' '.join(f"{k[:5]} {sum(r['rev_us'].get(k,0) for r in ok)/n:.0f}" for k in keys))
    tel = collections.Counter()
    for r in ok: tel.update({k: v for k, v in r['tel'].items() if isinstance(v, (int, float))})
    print('  tel/game:', {k: round(v / n, 1) for k, v in tel.items()})
