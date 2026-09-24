import sys, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
SP = '/home/user/kaggriculture/gold/harness'
def sig(farm):
    out = []
    for row in farm['tiles']:
        for t in row:
            if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED'): out.append('.')
            elif t == 'LOCKED': out.append('#')
            elif isinstance(t, dict): out.append(str(t.get('crop') or t.get('animal') or t.get('kind')))
            else: out.append('?')
    return out
games = json.load(open(SP + '/pin_all.json'))
res = {}
for d in games:
    acts = d['acts']; P = d['info']['TeamNames'].index('offhand')
    sims = {}
    def tape(p):
        def f(obs, cfg=None):
            t = obs['step']
            if p == 0 and t in (143, 359):
                a = sig(obs['farms'][P]); b = sig(obs['farms'][1 - P])
                sims[t] = round(sum(x == y for x, y in zip(a, b)) / len(a), 3)
            a = acts[t + 1][p] if t + 1 < len(acts) else None
            return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        return f
    lean.play(None, None, d['info']['seed'], agent_objs=[tape(0), tape(1)], max_steps=360)
    res[d['id']] = sims
json.dump(res, open(SP + '/simclass.json', 'w'))
div = sum(1 for s in res.values() if s.get(143, 1) < 0.9 or s.get(359, 1) < 0.8)
print('games', len(res), 'divergent', div)
