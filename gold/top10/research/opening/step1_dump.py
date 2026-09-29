"""step1_dump.py : public state of each tape-copy herd-poor agent at steps 1-6 (seat 1) vs c0tp, seeds 7500 and 7501."""
import sys, os, json
sys.path.insert(0, os.path.join(os.getcwd(), 'arena'))
import lean
AG = ['kaggriculture-adaptive-public-state-multi-route', 'kaggriculture-breaking-the-tie', 'kaggriculture-strongest-farmer-of-today',
      'kaggriculture-precomputed-schedule-policy', 'kaggriculture-x544-nah-i-d-win']
def tiles_of(f):
    out = []
    for y, row in enumerate(f['tiles']):
        for x, t in enumerate(row):
            if isinstance(t, dict):
                d = t.get('animal') or t.get('crop') or t.get('kind')
                out.append('%s@%d,%d' % (str(d)[:5], x, y))
    return out
for seed in (7500, 7501):
    for a in AG:
        A = lean.load('gold/top10/cands/full_OP_c0tp.py'); B = lean.load('../pubnb/x_%s.py' % a)
        rec = []
        def wa(obs, cfg=None):
            st = int(obs['step'])
            if 1 <= st <= 6:
                f = obs['farms'][1]; inv = obs['market']['inventory']
                rec.append('s%d $%d h%d F%s H%s q%d T%s wheatInv%+d fertInv%+d' % (st, float(f['money']), len(f['hands']), tuple(f['farmer']), [tuple(h) for h in f['hands']], len(f['unlocked_quadrants']), tiles_of(f), int(inv['WHEAT']) - 10000, int(inv['FERTILIZER']) - 10000))
            return A(obs, cfg)
        lean.play(None, None, seed, agent_objs=[wa, B], max_steps=7)
        print('== seed %d %s' % (seed, a[14:] if a.startswith('kaggriculture-') else a))
        for line in rec: print('   ' + line)
