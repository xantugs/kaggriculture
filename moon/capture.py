"""Capture v12's observation at a given step (seat 0) for offline development."""
import sys, json, pickle, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'arena'))
import lean, decouple
S = int(sys.argv[1]); seed = int(sys.argv[2]); out = sys.argv[3]
A = lean.load('cand/omw_v12.py'); B = lean.load('cand/omw_v12.py')
cap = {}
def wrap(obs, cfg=None):
    if obs['step'] == S: cap['obs'] = json.loads(json.dumps(obs))
    return A(obs, cfg)
decouple.install(0)
r = lean.play(None, None, seed, agent_objs=[wrap, B], max_steps=S + 1)
json.dump(cap['obs'], open(out, 'w'))
o = cap['obs']; me = o['farms'][o['player']]
print('money', me['money'], 'hands', len(me['hands']), 'quads', me['unlocked_quadrants'])
print('private', json.dumps(o['private'])[:600])
for row in me['tiles']:
    print(' '.join('#' if t == 'LOCKED' else '.' if t is None else (t.get('crop') or t.get('animal') or t['kind'])[:2] for t in row))
print('market', o['market']['prices'], o['town'])
print(json.dumps([t for row in me['tiles'] for t in row if isinstance(t, dict)][:3]))
