import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
fn = json.load(open('g2800_list.json'))[int(sys.argv[2]) if len(sys.argv) > 2 else 0]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
orig = pinned.install_pinned(4, O, spawns, shops)
A = lean.load(os.path.join('..', 'arena', 'cand', sys.argv[1] + '.py'))
info = {}
def f(obs, cfg=None):
    a = A(obs, cfg); s = obs['step']
    if s % 24 == 22:
        me = obs['farms'][obs['player']]; op = obs['farms'][1 - obs['player']]
        tiles = me['tiles']
        empty = sum(1 for row in tiles for t in row if t is None); weed = sum(1 for row in tiles for t in row if isinstance(t, dict) and t.get('kind') == 'WEED')
        crops = collections.Counter(t.get('crop') for row in tiles for t in row if isinstance(t, dict) and t.get('kind') == 'PLANT')
        info[s // 24] = (len(me['hands']), me['hires_today'], len(op['hands']), empty, weed, dict(crops), me['unlocked_quadrants'], obs['private']['shed'].get('STRAWBERRY', 0), sum(obs['private']['shed'].values()))
    return a
ag = [None, None]; ag[P] = pinned._prefixed(f, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
lean.play(None, None, d['info']['seed'], agent_objs=ag)
for day, v in sorted(info.items()): print(day, v)
