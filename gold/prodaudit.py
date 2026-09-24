"""Count ongoing-crop productions per seat (from day 12): doubled (fertilized+watered) vs single, and units lost to the held cap."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
FARMS = [None, None]
st = [collections.Counter(), collections.Counter()]
orig = K._daily_refresh_plants
def refresh(farm, current_day, tpd):
    i = 0 if farm is FARMS[0] else 1
    if current_day >= 12:
        for row in farm['tiles']:
            for t in row:
                if isinstance(t, dict) and t.get('kind') == 'PLANT' and t['crop'] in ('STRAWBERRY', 'TOMATO'):
                    cd = K.CROPS[t['crop']]
                    dsf = current_day + 1 - t['planted_day'] - cd['first_yield_day']
                    if dsf >= 0 and dsf % cd['interval'] == 0 and dsf // cd['interval'] + 1 <= cd['max_yield']:
                        if t['consecutive_unwatered'] + (0 if t['watered_today'] else 1) >= 2:
                            st[i][t['crop'][:5] + '_dies'] += 1; continue
                        fert = t['watered_today'] and t.get('fertilized_until_day', -1) >= current_day
                        gain = 2 if fert else 1
                        room = cd['max_yield'] - t['yield_units']
                        st[i][t['crop'][:5] + ('_double' if fert else '_single')] += 1
                        st[i][t['crop'][:5] + '_capped'] += max(0, gain - room)
                        if not t['watered_today']: st[i][t['crop'][:5] + '_unwatered_eve'] += 1
                        elif t.get('fertilized_until_day', -1) < current_day: st[i][t['crop'][:5] + '_unfert_eve'] += 1
    return orig(farm, current_day, tpd)
K._daily_refresh_plants = refresh
oe = K._end_of_day
def eod(state, env, day):
    FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
    return oe(state, env, day)
K._end_of_day = eod
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'])
for i in (0, 1): print('seat', i, dict(sorted(st[i].items())))
