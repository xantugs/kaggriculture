"""Print an agent's market orders over a step range. usage: orders.py A B seed seat s0 s1"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); seat = int(sys.argv[4])
s0, s1 = int(sys.argv[5]), int(sys.argv[6])
LOG = []
def wrap(obs, cfg=None):
    a = A(obs, cfg)
    s = obs['step']
    if s0 <= s <= s1:
        m = [o for o in (a.get('market') or []) if o[0] != 'SELL']
        sells = [o for o in (a.get('market') or []) if o[0] == 'SELL']
        if m or sells:
            LOG.append((s, 'd%d h%d' % (s // 24, s % 24), '$%d' % obs['farms'][seat]['money'], 'hands', len(a.get('hands') or []), m, 'SELL', [(o[1][:4], o[2]) for o in sells]))
    return a
lean.play(None, None, seed, agent_objs=[wrap, B] if seat == 0 else [B, wrap], max_steps=s1 + 1)
for l in LOG: print(*l)
