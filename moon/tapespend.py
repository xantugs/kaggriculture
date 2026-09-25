import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
d = json.load(open(json.load(open('g2800_list.json'))[int(sys.argv[1])], encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
A = lean.load(os.path.join('..', 'arena', 'cand', 'omw_ad_a1.py')); g = A.__globals__
SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}; ANI = {'SHEEP': 500, 'COW': 400, 'GOOSE': 300}
money = {}; plants = collections.defaultdict(list)
def f(obs, cfg=None):
    a = A(obs, cfg); s = obs['step']
    if s < 300:
        money[s] = obs['farms'][obs['player']]['money']
        for i, c in enumerate([a.get('farmer')] + list(a.get('hands') or [])):
            if c and c[0] == 'PLANT': plants[s // 24].append((s % 24, c[1]))
    return a
ag = [None, None]; ag[P] = f; ag[O] = pinned._tape(d['acts'], O)
lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=300)
route = g['_IMPL'].chassis.players[P]['route']; tape = g['_IMPL'].chassis.routes[route]
for day in range(2, 12):
    spend = collections.Counter()
    for t in range(day * 24, day * 24 + 24):
        for o in [o for o in tape[t].get('market', []) if o]:
            if o[0] == 'BUY_SEED': spend['seed_' + o[1]] += int(o[2]) * SEED.get(o[1], 100)
            elif o[0] == 'BUY_ANIMAL': spend['anim_' + o[1]] += int(o[2]) * ANI.get(o[1], 500)
            elif o[0] in ('BUY_LAND', 'HIRE'): spend[o[0]] += 1
            elif o[0] == 'BUY_PRODUCT': spend['buy_' + o[1]] += int(o[2])
    mins = min(money[t] for t in range(day * 24, day * 24 + 24) if t in money)
    wheat_pl = [h for h, c in plants[day] if c == 'WHEAT']; str_pl = [h for h, c in plants[day] if c == 'STRAWBERRY']
    print(f'd{day}: money h0 {money.get(day*24)} min {mins}  spend {dict(spend)}  wheat plants at h{wheat_pl}  straw at h{str_pl}')
