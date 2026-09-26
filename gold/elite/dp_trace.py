"""Trace the market programme's decisions on one elite-gate seat.
usage: dp_trace.py cand.py gid seat [games.jsonl.gz] [refs.jsonl]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
import lean
from eval_elite_routes import install_town, load_games
from transplant import build_agent

def load_module(path):
    g = {"__name__": "traced_agent", "__file__": path}
    sys.path.append(os.path.dirname(os.path.abspath(path)))
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), g)
    return g, [v for v in g.values() if callable(v)][-1]

def main():
    cand, gid, seat = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    path = sys.argv[4] if len(sys.argv) > 4 else 'moon/elite/games_2026-09-20.jsonl.gz'
    refs = sys.argv[5] if len(sys.argv) > 5 else 'gold/elite/elite_gate_refs.jsonl'
    ref = next(json.loads(l) for l in open(refs, encoding='utf-8') if json.loads(l)['gid'] == gid and json.loads(l)['seat'] == seat)
    d = next(g for g in load_games(path) if g['id'] == gid)
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    g, A = load_module(cand)
    cls = g['GoldCtl']; orig = cls._dp_sell; log = []
    def traced(self, obs, p, n, step, day, hour, shops, cap_night=None):
        x = orig(self, obs, p, n, step, day, hour, shops, cap_night)
        inv = int(obs['market']['inventory'][p]); px = g['_gc_price'](p, inv)
        shed = sum(int(v) for v in obs['private']['shed'].values())
        log.append((step, day, hour, p, n, x, inv, round(px), cap_night, shed, int(obs['farms'][self.me]['money'])))
        return x
    cls._dp_sell = traced
    orig_town = install_town(ref['shops'])
    try:
        ag = [None, None]; ag[seat] = build_agent(d['acts'], seat, rr, slack_min=20); ag[1 - seat] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        K._end_of_day = orig_town
    print('result: tape %.0f  us %.0f  margin %+.0f  err %s' % (r['r'][seat], r['r'][1 - seat], r['r'][1 - seat] - r['r'][seat], r['err']))
    tel = getattr(A, 'telemetry', {}) or {}
    print({k: tel.get(k) for k in ('gc_start', 'gc_dp_sold', 'gc_dp_held', 'gc_dp_wait', 'gc_dp_room_min', 'gc_held_released', 'gc_room_sells', 'gc_unserved', 'gc_mkt_dp_err')})
    print('step day hr  product     avail sold  inv  price  capN  shed  cash')
    for row in log:
        step, day, hour, p, n, x, inv, px, capn, shed, cash = row
        if x is None: continue
        print('%4d %3d %2d  %-10s %5d %4s %5d %6d %5s %5d %6d' % (step, day, hour, p, n, x, inv, px, '-' if capn is None else capn, shed, cash))
if __name__ == '__main__':
    main()
