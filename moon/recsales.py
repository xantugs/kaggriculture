"""Daily sales (units@avg price) per seat for recorded games. usage: recsales.py games.json name_filter PRODUCT[,P2]"""
import sys, os, json, collections
sys.path.insert(0, '.'); sys.path.insert(0, '../arena')
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K
f, who, prods = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
for d in json.load(open(f, encoding='utf-8')):
    names = d['info']['TeamNames']
    if who not in ' '.join(names): continue
    P = names.index('offhand'); O = 1 - P
    FARMS = [None, None]; STEP = [0]; L = collections.defaultdict(lambda: [0, 0]); INV = {}
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and op == 'SELL' and item in prods:
            e = L[(STEP[0] // 24, 'us' if farm is FARMS[P] else 'them', item)]; e[0] += 1; e[1] += price
        return ok
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]; STEP[0] = state[0].observation.step
        if STEP[0] % 24 == 0: INV[STEP[0] // 24] = {p: state[0].observation.market['prices'][p] for p in prods}
        return opm(state, env)
    K._commit_unit = commit; K._process_market = pm
    lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    K._commit_unit = oc; K._process_market = opm
    print('==', names[O], 'margin(us-them)', d['rewards'][P] - d['rewards'][O])
    for day in range(10, 30):
        row = []
        for p in prods:
            a = L.get((day, 'us', p)); b = L.get((day, 'them', p))
            row.append(f"{p[:5]} px{INV.get(day, {}).get(p, 0):>4} {(str(a[0])+'@'+str(a[1]//a[0])) if a else '-':>8}|{(str(b[0])+'@'+str(b[1]//b[0])) if b else '-':<8}")
        print(day, '  '.join(row))
