"""Daily land use of seat 0 at hour 12: empty / weed / crop counts / animals. usage: tileuse.py agent.py seed [D0]"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); seed = int(sys.argv[2]); D0 = int(sys.argv[3]) if len(sys.argv) > 3 else 15
B = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py')); LOG = {}
def wrap(obs, cfg=None):
    s = int(obs['step'])
    if s % 24 == 12 and s // 24 >= D0:
        c = collections.Counter()
        for row in obs['farms'][int(obs['player'])]['tiles']:
            for t in row:
                if t == 'LOCKED': continue
                if t is None: c['empty'] += 1
                elif t.get('kind') == 'WEED': c['weed'] += 1
                elif t.get('kind') == 'PLANT': c[t['crop'][:5]] += 1
                elif 'animal' in t and t.get('animal'): c['anim'] += 1
                else: c['struct'] += 1
        LOG[s // 24] = c
    return A(obs, cfg)
lean.play(None, None, seed, agent_objs=[wrap, B])
keys = ['empty', 'weed', 'WHEAT', 'CARRO', 'STRAW', 'TOMAT', 'MELON', 'anim', 'struct']
print(os.path.basename(sys.argv[1]), ' '.join(f"{k:>5s}" for k in keys))
tot = collections.Counter()
for d in sorted(LOG):
    tot.update(LOG[d]); print(f"  d{d:2d}  " + ' '.join(f"{LOG[d][k]:5d}" for k in keys))
print('  sum  ' + ' '.join(f"{tot[k]:5d}" for k in keys))
