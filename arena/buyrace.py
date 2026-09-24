"""Same-step wheat BUY races: our order index vs the rival's; and steps where the rival buys wheat right before (lower idx) we do."""
import json, glob, collections, sys
def idx(a, op, it):
    if not isinstance(a, dict): return None
    for i, o in enumerate(a.get('market') or []):
        if isinstance(o, list) and len(o) >= 3 and o[0] == op and o[1] == it:
            try:
                if int(o[2]) > 0: return i
            except Exception: pass
    return None
tot = collections.Counter()
for f in sorted(glob.glob(sys.argv[1])):
    for d in json.load(open(f)):
        n = d['info']['TeamNames']; P = n.index('Khantugs Gantulga'); acts = d['acts']
        c = collections.Counter()
        for s in range(3, len(acts)):
            u = idx(acts[s][P], 'BUY_PRODUCT', 'WHEAT'); t = idx(acts[s][1 - P], 'BUY_PRODUCT', 'WHEAT')
            if u is not None and t is not None:
                k = 'win' if u < t else ('lose' if u > t else 'tie'); c[k] += 1; tot[k] += 1
        if c['lose'] or c['win']:
            print('%-16s %6d  wheat-buy races win/tie/lose %d/%d/%d' % (n[1 - P][:16], d['rewards'][P] - d['rewards'][1 - P], c['win'], c['tie'], c['lose']))
print(dict(tot))
