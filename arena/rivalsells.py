import json, sys, lean, ident2
f, gi, item, lo, hi = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
d = json.load(open(f))[gi]; n = d['info']['TeamNames']; P = n.index('Khantugs Gantulga'); acts = d['acts']
log = {}
def wrap(ag, pl):
    def fn(obs, cfg=None):
        s = int(obs['step'])
        if lo <= s < hi:
            log[(pl, s)] = (int(obs['private']['shed'].get(item, 0)), sum(int(i.get(item, 0)) for i in obs['private']['inventories']), int(obs['market']['prices'][item]), int(obs['market']['inventory'][item]) - 10000)
        return ag(obs, cfg)
    return fn
ag = [wrap(ident2._tape(acts, 0), 0), wrap(ident2._tape(acts, 1), 1)]
lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=hi + 1)
def q(a):
    if not isinstance(a, dict): return 0
    return sum(int(o[2]) for o in (a.get('market') or []) if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL' and o[1] == item)
for s in range(lo, hi):
    u = log.get((P, s)); t = log.get((1 - P, s))
    if not u: continue
    qu, qt = q(acts[s + 1][P]), q(acts[s + 1][1 - P])
    if qu or qt:
        print(s, 'd%dh%02d' % (s // 24, s % 24), 'px %3d inv%+4d' % (u[2], u[3]), '| US shed %3d carry %2d sell %3s' % (u[0], u[1], qu or ''), '| THEM shed %3d carry %2d sell %3s' % (t[0], t[1], qt or ''))
