import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K
cls = json.load(open('gameclass.json'))
fn = [f for f in json.load(open('g2800_list.json')) if cls.get(os.path.basename(f)[:-5], 0) < 0.8][0]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
orig = pinned.install_pinned(4, O, spawns, shops)
A = lean.load(os.path.join('..', 'arena', 'cand', 'omw_ad_a1.py')); g = A.__globals__
chain = list(g['_AD_CFG']['chain'])
calls = collections.defaultdict(list)
def wrap(f, name):
    def w(obs, cfg=None):
        a = f(obs, cfg); s = int(obs['step'])
        if 480 <= s < 504:
            calls[s].append((name, [o for o in (a.get('market') or []) if o and o[0] == 'SELL']))
        return a
    return w
for n in chain: g[n] = wrap(g[n], n)
def top(obs, cfg=None):
    a = A(obs, cfg); s = int(obs['step'])
    if 480 <= s < 504: calls[s].append(('FINAL', [o for o in (a.get('market') or []) if o and o[0] == 'SELL']))
    return a
ag = [None, None]; ag[P] = pinned._prefixed(top, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=530)
for s in sorted(calls):
    print('step', s, 'calls', len(calls[s]))
    print('   ', [(n, m) for n, m in calls[s] if n in ('_V231_PARENT','_V233_PARENT','_R51_INPUT_PARENT','FINAL')])
