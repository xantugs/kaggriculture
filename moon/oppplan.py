"""Season plan of our opponents in a games file, split by class (gameclass.json): plantings per crop per 3-day block,
land purchase days, animal purchases. usage: oppplan.py games.json [thr]"""
import sys, json, collections
games = json.load(open(sys.argv[1], encoding='utf-8')); cls = json.load(open('gameclass.json')); thr = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
for name, test in (('DIVERGENT opponents', lambda s: s < thr), ('MIRROR opponents', lambda s: s >= thr), ('US (offhand)', None)):
    G = 0; plant = collections.defaultdict(collections.Counter); land = collections.Counter(); anim = collections.defaultdict(collections.Counter); hires = collections.Counter()
    for d in games:
        s = cls.get(str(d['id']))
        if s is None: continue
        n = d['info']['TeamNames']; P = n.index('offhand')
        if test is None:
            if s >= thr: continue
            p = P
        else:
            if not test(s): continue
            p = 1 - P
        G += 1; q = 0
        for t in range(len(d['acts']) - 1):
            a = d['acts'][t + 1][p]
            if not isinstance(a, dict): continue
            day = t // 24
            for o in a.get('market') or []:
                if not o: continue
                if o[0] == 'BUY_LAND': q += 1; land[(q, day)] += 1
                elif o[0] == 'BUY_ANIMAL': anim[o[1]][day // 3] += int(o[2]) if len(o) > 2 else 1
                elif o[0] == 'HIRE': hires[day] += 1
            for c in [a.get('farmer') or ['PASS']] + list(a.get('hands') or []):
                if c and c[0] == 'PLANT' and len(c) > 1: plant[c[1]][day // 3] += 1
    g = max(1, G)
    print(f"{name}: games {G}" + ('  (our side in divergent games)' if test is None else ''))
    for crop in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON'):
        c = plant[crop]; print(f"   {crop:10s} {sum(c.values()) / g:6.1f}/game  by 3-day block: " + ' '.join(f"{c[b] / g:4.1f}" for b in range(10)))
    for an in ('GOOSE', 'COW', 'SHEEP'):
        c = anim[an]; print(f"   {an:6s} {sum(c.values()) / g:4.1f}/game  by 3-day block: " + ' '.join(f"{c[b] / g:3.1f}" for b in range(10)))
    lk = collections.defaultdict(list)
    for (k, day), v in land.items(): lk[k] += [day] * v
    print('   land purchase (nth: median day, share of games):', {k: (sorted(v)[len(v) // 2], round(len(v) / g, 2)) for k, v in sorted(lk.items())})
    print('   hires/day:', ' '.join(f"{hires[d] / g:.0f}" for d in range(30)))
