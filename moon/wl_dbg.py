import sys; sys.path.insert(0, '../arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load('../arena/cand/omw_v15b.py')
sold = []
def wrap(obs, cfg=None):
    a = A(obs, cfg); s = int(obs['step'])
    for o in a.get('market') or []:
        if o[:2] == ['SELL', 'WHEAT'] and 16 <= s // 24 <= 18: sold.append((s // 24, s % 24, o[2], obs['private']['shed'].get('WHEAT', 0)))
    return a
lean.play(None, None, 3, agent_objs=[wrap, B])
for w in A.__globals__['_M_REPORT']['wheatlog']: print(w)
print('wheat sell orders d16-18 (day, hour, qty, shed):', sold)
