"""Pinned single-game smoke test of candidates with telemetry. usage: sestest.py game.json cand1,cand2 [S=96]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K
fn = sys.argv[1]; cands = sys.argv[2].split(','); S = int(sys.argv[3]) if len(sys.argv) > 3 else 96
d = json.load(open(fn, encoding='utf-8'))[0]
names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
for cand in cands:
    orig = pinned.install_pinned(S // 24, O, spawns, shops)
    snaps = []
    pe = K._end_of_day
    def eod(state, env, day):
        f = state[0].observation.farms[P]
        c = collections.Counter()
        for (x, y) in [(x, y) for y in range(5, 10) for x in range(5, 10)]:
            t = f['tiles'][y][x]
            c['#' if t == 'LOCKED' else '.' if t is None else (t.get('crop') or t.get('kind')) if isinstance(t, dict) else '?'] += 1
        snaps.append((day, int(f['money']), dict(c), len(f['hands']), state[0].observation.market['prices']['STRAWBERRY']))
        return pe(state, env, day)
    K._end_of_day = eod
    try:
        A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
        ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    g = A.__globals__
    print(cand, 'us', r['r'][P], 'them', r['r'][O], 'm', r['r'][P] - r['r'][O], 'err', r['err'])
    print('  SES', g.get('_SES_REPORT'), 'AD', g.get('_AD_REPORT'), 'GC start', g.get('_GC_REPORT', {}).get('gc_start'))
    for s in snaps:
        if s[0] in (11, 12, 13, 14, 16, 18, 20, 21, 22, 23, 24, 26, 28):
            print('  ', s)
