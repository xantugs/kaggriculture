"""Per-day action counts for both seats from a start day (closed loop)."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D0 = int(sys.argv[4])
cnt = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        d = obs['day']
        if d >= D0:
            for u in [a.get('farmer')] + list(a.get('hands') or []):
                op = u[0] if isinstance(u, list) and u else 'NONE'
                if op in ('NORTH', 'SOUTH', 'EAST', 'WEST'): op = 'MOVE'
                cnt[seat][d][op] += 1
            if obs['hour'] == 12:
                cnt[seat][d]['_units'] = 1 + len(obs['farms'][seat]['hands'])
        return a
    return f
r = lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
print('result', r['r'])
keys = ['_units', 'MOVE', 'PASS', 'WATER', 'HARVEST', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'FERTILIZE', 'PLANT', 'PICKUP', 'DROP', 'PLACE', 'DIG']
tot = [collections.Counter(), collections.Counter()]
print('day   ' + ' '.join('%9s' % k[:9] for k in keys))
for d in sorted(cnt[0]):
    for s in (0, 1):
        c = cnt[s][d]; tot[s].update({k: c[k] for k in keys if k != '_units'})
    print('%3d   ' % d + ' '.join('%4d/%-4d' % (cnt[0][d][k], cnt[1][d][k]) for k in keys))
print('tot   ' + ' '.join('%4d/%-4d' % (tot[0][k], tot[1][k]) for k in keys))
