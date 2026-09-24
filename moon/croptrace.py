"""How each plant of a crop ends on seat 0's farm: (tile, planted_day, last seen age, next state, harvested units).
usage: croptrace.py agent.py seed CROP [D0]"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); seed = int(sys.argv[2]); CROP = sys.argv[3]; D0 = int(sys.argv[4]) if len(sys.argv) > 4 else 15
B = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'))
prev = {}; ends = []; harv = collections.Counter(); FARM0 = [None]; STEP = [0]
oa, opm = K._apply_unit_action, K._process_market
def hook(farm, private, actor, command, *a, **k):
    if farm is FARM0[0] and command and command[0] == 'HARVEST':
        x, y = (farm['farmer'] if actor == 0 else farm['hands'][actor - 1])
        t = farm['tiles'][y][x]
        if isinstance(t, dict) and t.get('crop') == CROP:
            harv[(x, y, t['planted_day'])] += t.get('yield_units', 0)
    return oa(farm, private, actor, command, *a, **k)
def pm(state, env):
    FARM0[0] = state[0].observation.farms[0]; STEP[0] = state[0].observation.step
    return opm(state, env)
K._apply_unit_action, K._process_market = hook, pm
def wrap(obs, cfg=None):
    s = int(obs['step'])
    if s % 24 == 0 and s // 24 >= D0:
        tiles = obs['farms'][int(obs['player'])]['tiles']; cur = {}
        for y in range(10):
            for x in range(10):
                t = tiles[y][x]
                if isinstance(t, dict) and t.get('crop') == CROP:
                    cur[(x, y)] = t['planted_day']
        for xy, pd in prev.items():
            if cur.get(xy) != pd:
                t = tiles[xy[1]][xy[0]]
                nxt = 'EMPTY' if t is None else (t.get('kind') + ':' + str(t.get('crop', '')) if isinstance(t, dict) else str(t))
                ends.append((xy, pd, s // 24 - pd, nxt))
        prev.clear(); prev.update(cur)
    return A(obs, cfg)
r = lean.play(None, None, seed, agent_objs=[wrap, B])
print(os.path.basename(sys.argv[1]), r['r'])
by = collections.Counter(e[3] for e in ends)
print(' endings:', dict(by))
for xy, pd, age, nxt in sorted(ends, key=lambda e: e[1]):
    print(f"  {xy} planted d{pd} ended at age {age:2d} -> {nxt:18s} harvested {harv[(xy[0], xy[1], pd)]}")
print(' total harvested', sum(harv.values()), 'plants', len(harv))
