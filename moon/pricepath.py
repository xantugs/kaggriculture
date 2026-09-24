import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[1]); items = sys.argv[3].split(','); LOG = {}
def w(obs, cfg=None):
    s = int(obs['step'])
    if s % 24 == 12: LOG[s // 24] = {it: obs['market']['prices'][it] for it in items}
    return A(obs, cfg)
lean.play(None, None, int(sys.argv[2]), agent_objs=[w, B])
for it in items: print(it, ' '.join(f"d{d}:{LOG[d][it]}" for d in sorted(LOG) if d >= 8))
