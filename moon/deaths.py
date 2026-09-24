"""Log seat-0 plants that turn to weeds overnight (and animals that escape). usage: deaths.py A B seed"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
orig = K._daily_refresh_plants; orig_a = K._daily_refresh_animals
log = []; FARM0 = [None]
def drp(farm, day, tpd):
    before = {(x, y): dict(t) for y, row in enumerate(farm['tiles']) for x, t in enumerate(row) if isinstance(t, dict) and t.get('kind') == 'PLANT'}
    orig(farm, day, tpd)
    if farm is FARM0[0]:
        for (x, y), t in before.items():
            n = farm['tiles'][y][x]
            if isinstance(n, dict) and n.get('kind') == 'WEED':
                log.append(('DRY', day, (x, y), t['crop'], 'age', day - t['planted_day'], 'cu', t['consecutive_unwatered'], 'w', t['watered_today'], 'yu', t['yield_units']))
def dra(farm, day):
    before = {(x, y): dict(t) for y, row in enumerate(farm['tiles']) for x, t in enumerate(row) if isinstance(t, dict) and 'animal' in t}
    orig_a(farm, day)
    if farm is FARM0[0]:
        for (x, y), t in before.items():
            n = farm['tiles'][y][x]
            if not (isinstance(n, dict) and 'animal' in n):
                log.append(('ESC', day, (x, y), t['animal'], 'unfed', t['consecutive_unfed'], 'fed', t['fed_today'], 'yu', t['yield_units']))
K._daily_refresh_plants = drp; K._daily_refresh_animals = dra
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms: FARM0[0] = o.farms[0]
    return oi(state, env)
K.interpreter = interp
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'])
c = collections.Counter((e[0], e[3]) for e in log); print(c)
for e in log[:40]: print(e)
