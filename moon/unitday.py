"""Per-day labor profile of seat 0: hands, wage bill, and per-unit turn use (moves / useful ops / pickups+drops / pass),
from day D0. usage: unitday.py agent.py seed [D0] [opp]"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); seed = int(sys.argv[2]); D0 = int(sys.argv[3]) if len(sys.argv) > 3 else 15
B = lean.load(sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'))
MOVES = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
USEFUL = {'WATER', 'HARVEST', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'PLANT', 'FERTILIZE', 'DIG', 'BUILD_COOP', 'BUILD_PASTURE', 'PLACE'}
day_stat = collections.defaultdict(lambda: collections.Counter())
wage = collections.Counter(); PASSH = collections.Counter(); FARM0 = [None]; STEP = [0]
oh, opm = K._do_hire, K._process_market
def hire(farm, private, bs, mult=1):
    m0 = farm['money']; oh(farm, private, bs, mult)
    if farm is FARM0[0]: wage[STEP[0] // 24] += m0 - farm['money']
def pm(state, env):
    FARM0[0] = state[0].observation.farms[0]; STEP[0] = state[0].observation.step
    return opm(state, env)
K._do_hire, K._process_market = hire, pm
def wrap(obs, cfg=None):
    a = A(obs, cfg); s = int(obs['step']); d = s // 24
    cmds = [a.get('farmer') or ['PASS']] + list(a.get('hands') or [])
    n = 1 + len(obs['farms'][int(obs['player'])]['hands'])
    st = day_stat[d]; st['units_max'] = max(st['units_max'], n)
    for c in cmds[:n]:
        op = (c or ['PASS'])[0]
        st['turns'] += 1
        if op in MOVES: st['move'] += 1
        elif op in USEFUL: st['useful'] += 1
        elif op in ('PICKUP', 'DROP'): st['shed'] += 1
        else:
            st['pass'] += 1; PASSH[s % 24] += 1
    return a
r = lean.play(None, None, seed, agent_objs=[wrap, B])
print(os.path.basename(sys.argv[1]), r['r'])
tot = collections.Counter()
for d in range(D0, 30):
    st = day_stat[d]; tot.update(st); tot['wage'] += wage[d]
    print(f"day {d:2d} units {st['units_max']:2d} wage {wage[d]:5.0f}  turns {st['turns']:3d} move {st['move']:3d} useful {st['useful']:3d} shed {st['shed']:3d} pass {st['pass']:3d}")
print(f"TOTAL wage {tot['wage']:.0f} turns {tot['turns']} move {tot['move']} useful {tot['useful']} shed {tot['shed']} pass {tot['pass']}")
print('PASS by hour:', ' '.join(f"{h}:{PASSH[h]}" for h in range(24)))
