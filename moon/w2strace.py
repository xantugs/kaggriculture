import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
gi = int(sys.argv[1])
d = json.load(open(json.load(open('g2800_list.json'))[gi], encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
for cand in ('omw_ad_a1', 'omw_w2s_b'):
    orig = pinned.install_pinned(4, O, spawns, shops)
    A = lean.load(os.path.join('..', 'arena', 'cand', cand + '.py'))
    ev = []
    prev = {}
    def f(obs, cfg=None):
        a = A(obs, cfg); s = obs['step']
        if 96 <= s < 300:
            me = obs['farms'][obs['player']]; seeds = obs['private']['seeds'].get('STRAWBERRY', 0)
            pos = [me['farmer']] + me['hands']
            pl = [(i, tuple(pos[i])) for i, c in enumerate([a.get('farmer')] + list(a.get('hands') or [])) if c and c[:2] == ['PLANT', 'STRAWBERRY'] and i < len(pos)]
            buy = [o for o in (a.get('market') or []) if o and o[:2] == ['BUY_SEED', 'STRAWBERRY']]
            if pl or buy: ev.append((s // 24, s % 24, 'seeds', seeds, 'money', me['money'], 'plant', pl, 'buy', buy))
        return a
    ag = [None, None]; ag[P] = pinned._prefixed(f, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    pinned  # noqa
    print('==', cand, 'margin', r['r'][P] - r['r'][O], A.__globals__.get('_W2S_REPORT'))
    for e in ev: print('  ', e)
    import kaggle_environments.envs.kaggriculture.kaggriculture as K; K._end_of_day = orig
