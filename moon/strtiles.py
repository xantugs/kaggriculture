import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
import kaggle_environments.envs.kaggriculture.kaggriculture as K
gi = int(sys.argv[1])
d = json.load(open(json.load(open('g2800_list.json'))[gi], encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
res = {}
for cand in ('omw_ad_a1', sys.argv[2] if len(sys.argv) > 2 else 'omw_w2s_b'):
    orig = pinned.install_pinned(4, O, spawns, shops)
    A = lean.load(os.path.join('..', 'arena', 'cand', cand + '.py'))
    snap = {}
    def f(obs, cfg=None):
        a = A(obs, cfg); s = obs['step']
        if s in (9 * 24, 12 * 24, 16 * 24, 20 * 24):
            me = obs['farms'][obs['player']]
            snap[s // 24] = {(x, y): (t['crop'], t['planted_day']) for y, row in enumerate(me['tiles']) for x, t in enumerate(row) if isinstance(t, dict) and t.get('kind') == 'PLANT'}
        return a
    ag = [None, None]; ag[P] = pinned._prefixed(f, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
    lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=20 * 24 + 2)
    K._end_of_day = orig
    res[cand] = snap
for day in (9, 12, 16, 20):
    a, b = res['omw_ad_a1'][day], res[list(res)[1]][day]
    diff = sorted(set(a.items()) ^ set(b.items()))
    sa = sum(1 for v in a.values() if v[0] == 'STRAWBERRY'); sb = sum(1 for v in b.values() if v[0] == 'STRAWBERRY')
    print('day', day, 'strawberry tiles v16', sa, 'w2s', sb, ' diff:', [(k, v, 'v16' if (k, v) in a.items() else 'w2s') for k, v in diff][:12])
