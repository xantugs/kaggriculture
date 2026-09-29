"""preflight_timing.py FILE OUT SEEDS : per-step wall time of our agent (both seats) vs a mix of opponents, sum of time over
1 s per game (the Kaggle overage bank is 60 s per game), step index of the slowest steps."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.getcwd(), 'arena'))
import lean
f, out, seeds = sys.argv[1], sys.argv[2], sys.argv[3]
a_, b_ = seeds.split('-'); seeds = range(int(a_), int(b_) + 1)
OPPS = ['gold/submit/main_ctl_T8.py', 'gold/top10/cands/full_v29fc_FW.py', '../pubnb/x_notebooke394244546.py', '../pubnb/x_kaggriculture-v01-drip.py']
with open(out, 'w', encoding='utf-8') as fo:
    for opp in OPPS:
        for s in seeds:
            for seat in (0, 1):
                me = lean.load(f); ts = []
                def w(obs, cfg=None, _me=me, _ts=ts):
                    t0 = time.perf_counter(); a = _me(obs, cfg); _ts.append(time.perf_counter() - t0); return a
                objs = [w, lean.load(opp)] if seat == 0 else [lean.load(opp), w]
                r = lean.play(None, None, s, agent_objs=objs)
                slow = sorted(range(len(ts)), key=lambda i: -ts[i])[:5]
                rec = {'opp': os.path.basename(opp), 'seed': s, 'seat': seat, 'steps': len(ts), 'tmax': round(max(ts), 3),
                       'over': round(sum(max(0.0, t - 1.0) for t in ts), 3), 'n_over': sum(1 for t in ts if t > 1.0),
                       'tsum': round(sum(ts), 1), 'slow': [(i, round(ts[i], 3)) for i in slow],
                       'us': r['r'][seat], 'them': r['r'][1 - seat]}
                fo.write(json.dumps(rec) + '\n'); fo.flush()
