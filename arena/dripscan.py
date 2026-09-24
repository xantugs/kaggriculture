import json, glob, collections, sys
def lots(acts, pl, item):
    out = []
    for s in range(1, len(acts)):
        a = acts[s][pl]
        if not isinstance(a, dict): continue
        q = 0
        for o in a.get('market') or []:
            if isinstance(o, list) and len(o) >= 3 and o[0] == 'SELL' and o[1] == item:
                try: q += int(o[2])
                except Exception: pass
        if q > 0 and s < 690: out.append(q)
    return out
for item in sys.argv[2].split(','):
    print('==', item)
    for f in sorted(glob.glob(sys.argv[1])):
        for d in json.load(open(f)):
            n = d['info']['TeamNames']; P = n.index('Khantugs Gantulga'); acts = d['acts']
            u = lots(acts, P, item); t = lots(acts, 1 - P, item)
            if not u and not t: continue
            su = sum(1 for q in u if q <= 2); st = sum(1 for q in t if q <= 2)
            if st >= 8 or su >= 8:
                print('%-16s %6d  us lots %3d (<=2: %3d, avg %.1f) | them lots %3d (<=2: %3d, avg %.1f)' % (n[1 - P][:16], d['rewards'][P] - d['rewards'][1 - P], len(u), su, sum(u) / max(1, len(u)), len(t), st, sum(t) / max(1, len(t))))
