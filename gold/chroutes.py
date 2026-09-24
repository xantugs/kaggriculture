"""Print each unit's path (positions+actions) for one day of a chassis game, and the day's tile-visit density."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D = int(sys.argv[4])
paths = collections.defaultdict(list)
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if seat == 0 and obs['day'] == D:
            fm = obs['farms'][0]
            pos = [fm['farmer']] + fm['hands']
            acts = [a.get('farmer')] + list(a.get('hands') or [])
            for u, (p, x) in enumerate(zip(pos, acts)):
                paths[u].append((tuple(p), x[0] if x else 'NONE'))
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)], max_steps=24 * (D + 1))
tot = collections.Counter()
for u in sorted(paths):
    p = paths[u]
    moves = sum(1 for _, a in p if a in ('NORTH', 'SOUTH', 'EAST', 'WEST'))
    work = [(pos, a) for pos, a in p if a not in ('NORTH', 'SOUTH', 'EAST', 'WEST', 'PASS')]
    tiles = len({pos for pos, a in work})
    tot['moves'] += moves; tot['work'] += len(work); tot['tiles'] += tiles
    print('unit %2d turns %2d moves %2d work %2d tiles %2d  %s' % (u, len(p), moves, len(work), tiles, ' '.join('%d%d:%s' % (pos[0], pos[1], a[:4]) for pos, a in work)))
print('total', dict(tot))
