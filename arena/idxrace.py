"""Same-step sale races between us and the rival: who had the lower order index for the contested product."""
import json, glob, collections, sys
def sells(a):
    out = {}
    if not isinstance(a, dict): return out
    for i, o in enumerate(a.get('market') or []):
        if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL':
            try: q = int(o[2])
            except Exception: continue
            if q > 0 and o[1] not in out: out[o[1]] = i
    return out
tot = collections.Counter()
for f in sorted(glob.glob(sys.argv[1])):
    for gi, d in enumerate(json.load(open(f))):
        names = d['info']['TeamNames']; P = names.index('Khantugs Gantulga'); acts = d['acts']
        c = collections.Counter()
        for s in range(1, len(acts)):
            u = sells(acts[s][P]); t = sells(acts[s][1 - P])
            for it in set(u) & set(t):
                k = 'win' if u[it] < t[it] else ('lose' if u[it] > t[it] else 'tie')
                c[(it, k)] += 1; tot[(it, k)] += 1
        m = d['rewards'][P] - d['rewards'][1 - P]
        print('%-16s %6d ' % (names[1 - P][:16], m), ' '.join('%s:%d/%d/%d' % (it[:4], c[(it, 'win')], c[(it, 'tie')], c[(it, 'lose')]) for it in ('STRAWBERRY', 'MILK', 'WOOL', 'EGG', 'TOMATO', 'CARROT', 'MELON') if c[(it, 'win')] + c[(it, 'lose')] + c[(it, 'tie')]))
print({k: v for k, v in sorted(tot.items())})
