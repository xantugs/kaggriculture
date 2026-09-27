"""Log v16's strawberry/tomato seed buys and plantings (step, unit, pos) on a pinned game. usage: stbtrace.py cand gamefile"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
cand, fn = sys.argv[1], sys.argv[2]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
orig = pinned.install_pinned(4, O, spawns, shops)
A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
log = []
def f(obs, cfg=None):
    a = A(obs, cfg); s = obs['step']
    if s >= 96:
        for o in a.get('market') or []:
            if o and o[0] == 'BUY_SEED' and o[1] in ('STRAWBERRY', 'TOMATO'): log.append((s // 24, s % 24, 'BUY', o[1], o[2]))
        me = obs['farms'][obs['player']]; pos = [me['farmer']] + me['hands']
        for i, c in enumerate([a.get('farmer')] + (a.get('hands') or [])):
            if c and c[0] == 'PLANT' and c[1] in ('STRAWBERRY', 'TOMATO'): log.append((s // 24, s % 24, 'PLANT', c[1], i, tuple(pos[i]) if i < len(pos) else None))
    return a
ag = [None, None]; ag[P] = pinned._prefixed(f, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
for l in log: print(l)
print('margin', r['r'][P] - r['r'][O])
