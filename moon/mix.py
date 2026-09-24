"""Action mix per seat over days D0..D1 (all unit turns incl. PASS and moves). usage: mix.py A B seed D0 D1"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D0, D1 = int(sys.argv[4]), int(sys.argv[5])
C = [collections.Counter(), collections.Counter()]
def wrap(ag, i):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if D0 * 24 <= obs['step'] < (D1 + 1) * 24:
            for u in [a.get('farmer')] + list(a.get('hands') or []):
                op = (u or ['PASS'])[0]
                C[i]['MOVE' if op in ('NORTH', 'SOUTH', 'EAST', 'WEST') else op] += 1
            C[i]['HANDS'] += len(obs['farms'][obs['player']]['hands'])
        return a
    return f
r = lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
print('result', r['r'])
keys = sorted(set(C[0]) | set(C[1]), key=lambda k: -(C[0][k] + C[1][k]))
for k in keys: print(f"{k:20s} {C[0][k]:6d} {C[1][k]:6d}")
print('turns', sum(v for k, v in C[0].items() if k != 'HANDS'), sum(v for k, v in C[1].items() if k != 'HANDS'))
