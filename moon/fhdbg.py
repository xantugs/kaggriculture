import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned


def run(cand, d, P, O):
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(4, O, spawns, shops)
    A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
    g = A.__globals__
    log = {}
    par = g.get('_FH_PARENT')
    if par:
        def spy(obs, cfg=None):
            f = obs['farms'][obs['player']]
            a = par(obs, cfg)
            log[int(obs['step'])] = ([tuple(f['farmer'])] + [tuple(h) for h in f['hands']], json.dumps(a, sort_keys=True), f['money'])
            return a
        g['_FH_PARENT'] = spy; inner = A
    else:
        def inner(obs, cfg=None):
            f = obs['farms'][obs['player']]
            a = A(obs, cfg)
            log[int(obs['step'])] = ([tuple(f['farmer'])] + [tuple(h) for h in f['hands']], json.dumps(a, sort_keys=True), f['money'])
            return a
    ag = [None, None]; ag[P] = pinned._prefixed(inner, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    return log, r


fn = sys.argv[1]
d = json.load(open(fn, encoding='utf-8'))[0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
la, ra = run('omw_ad_a2', d, P, O)
lb, rb = run('omw_fh_a', d, P, O)
n = 0
for t in sorted(la):
    if t not in lb:
        continue
    if la[t][0] != lb[t][0] or la[t][1] != lb[t][1]:
        print('step', t, 'day', t // 24, 'hour', t % 24, 'money', la[t][2], lb[t][2])
        print('  pos A', la[t][0]); print('  pos B', lb[t][0])
        print('  act A', la[t][1][:400]); print('  act B', lb[t][1][:400])
        n += 1
        if n >= int(sys.argv[2]) if len(sys.argv) > 2 else 3:
            break
