import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K
fn = sys.argv[1]; cand = sys.argv[2]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
orig = pinned.install_pinned(4, O, spawns, shops)
A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
g = A.__globals__
LOG = []; CMDS = collections.Counter(); SOLD = collections.Counter(); FARM = [None]
inner_eod = K._end_of_day
def eod(state, env, day):
    f = state[0].observation.farms[P]; pr = state[P].observation.private
    st = g['_TOM_STATE'].get(P)
    if st and st.get('plan'):
        tl = [f['tiles'][y][x] for (x, y) in st['plan']]
        tom = [t for t in tl if isinstance(t, dict) and t.get('crop') == 'TOMATO']
        LOG.append((day, 'toms', len(tom), 'yield', sum(t['yield_units'] for t in tom), 'watered', sum(t['watered_today'] for t in tom),
                    'fert', sum(t.get('fertilized_until_day', -1) >= day for t in tom), 'shedT', pr['shed'].get('TOMATO', 0),
                    'invT', sum(i.get('TOMATO', 0) for i in pr['inventories']), 'shedsum', sum(pr['shed'].values()), 'price', state[0].observation.market['prices']['TOMATO'],
                    'cmds', dict(CMDS), 'sold', dict(SOLD)))
        CMDS.clear()
    return inner_eod(state, env, day)
K._end_of_day = eod
ocu, opm = K._commit_unit, K._process_market
def cu(op, item, price, farm, private, market, cap=100):
    ok = ocu(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL' and item == 'TOMATO' and farm is FARM[0]:
        SOLD['n'] += 1; SOLD['$'] += price
    return ok
def pm(state, env):
    FARM[0] = state[0].observation.farms[P]
    return opm(state, env)
K._commit_unit, K._process_market = cu, pm
def spy(obs, cfg=None):
    a = A(obs, cfg)
    st = g['_TOM_STATE'].get(obs['player'])
    if st and st['mine']:
        hs = a.get('hands') or []
        for j in st['mine']:
            if j < len(hs): CMDS[hs[j][0]] += 1
    return a
ag = [None, None]; ag[P] = pinned._prefixed(spy, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
K._end_of_day = orig; K._commit_unit, K._process_market = ocu, opm
print('final', r['r'][P] - r['r'][O], g.get('_TOM_REPORT'))
for l in LOG: print(l)
