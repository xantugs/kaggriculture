import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
fn = sys.argv[1]; cand = sys.argv[2]; steps = [int(x) for x in sys.argv[3].split(',')]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
orig = pinned.install_pinned(4, O, spawns, shops)
A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
LOG = []
def spy(obs, cfg=None):
    a = A(obs, cfg)
    if int(obs['step']) in steps or int(obs['step']) % 100 == 0:
        f = obs['farms'][obs['player']]
        LOG.append((obs['step'], 'money', f['money'], 'quads', f.get('unlocked_quadrants'), 'shops', obs['town'].get('unlocked_shops'), 'hands', len(f['hands']), 'market', a.get('market'), 'hands_cmd', a.get('hands')[-3:] if a.get('hands') else None))
    return a
ag = [None, None]; ag[P] = pinned._prefixed(spy, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
print('final', r['r'][P] - r['r'][O], A.__globals__.get('_TOM_REPORT'))
for l in LOG: print(l)
