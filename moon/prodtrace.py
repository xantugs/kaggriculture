"""Count ongoing-crop productions for seat 0 and 1: fertilized+watered vs plain vs capped. usage: prodtrace.py A B seed [fromday]"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
FARMS = [None, None]; C = [collections.Counter(), collections.Counter()]
orig = K._daily_refresh_plants
def drp(farm, day, tpd):
    i = 0 if farm is FARMS[0] else 1
    if day >= D0:
        for row in farm['tiles']:
            for t in row:
                if isinstance(t, dict) and t.get('kind') == 'PLANT' and K.CROPS[t['crop']]['ongoing']:
                    cd = K.CROPS[t['crop']]; k = day + 1 - t['planted_day'] - cd['first_yield_day']
                    if k >= 0 and k % cd['interval'] == 0 and k // cd['interval'] + 1 <= cd['max_yield']:
                        f = t['watered_today'] and t.get('fertilized_until_day', -1) >= day
                        dead = (not t['watered_today']) and t['consecutive_unwatered'] >= 1
                        C[i][(t['crop'][:5], 'dead' if dead else ('FERT' if f else ('water' if t['watered_today'] else 'dry')), 'capped' if t['yield_units'] + (2 if f else 1) > 4 else '')] += 1
    orig(farm, day, tpd)
K._daily_refresh_plants = drp
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms: FARMS[0], FARMS[1] = o.farms[0], o.farms[1]
    return oi(state, env)
K.interpreter = interp
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'])
for i in range(2): print('seat', i, sorted(C[i].items()))
