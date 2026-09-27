import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K
for gi in map(int, sys.argv[1].split(',')):
    d = json.load(open(json.load(open('g2800_list.json'))[gi], encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand')
    rows = {}
    opm = K._process_market
    def pm(state, env):
        o = state[0].observation
        if o.step % 24 in (0, 12) and o.step < 312:
            f = o.farms[P]; pr = state[P].observation.private
            rows[o.step] = (f['money'], len(f['hands']), sum(pr['seeds'].values()), o.market['prices']['STRAWBERRY'], o.market['prices']['WHEAT'])
        return opm(state, env)
    K._process_market = pm
    try: lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally: K._process_market = opm
    print('game', gi, ' '.join(f'd{s//24}h{s%24}:${v[0]}' for s, v in sorted(rows.items())))
