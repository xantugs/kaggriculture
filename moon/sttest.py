import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
cand, fn = sys.argv[1], sys.argv[2]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
orig = pinned.install_pinned(4, O, spawns, shops)
A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
g = A.__globals__
print(cand, 'margin', r['r'][P] - r['r'][O], 'us', r['r'][P], g.get('_TOM_REPORT') or g.get('_FH_REPORT') or g.get('_ST_REPORT') or g.get('_SN_REPORT') or g.get('_W2S_REPORT'), g.get('_AD_REPORT'), 'V219', g['_V219_REPORT']['confirmed_plants'])
