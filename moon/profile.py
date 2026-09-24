"""Season profile of a team from recorded actions: land, plantings per crop, animals, hires/day, fertilizer buys,
wheat buys, sell requests, command mix. usage: profile.py team [files...]"""
import sys, os, json, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
team = sys.argv[1]
files = sys.argv[2:] or sorted(glob.glob(os.path.join(HERE, 'elite', 'games_*.jsonl')))
def games():
    for f in files:
        if f.endswith('.jsonl'):
            for line in open(f, encoding='utf-8'): yield json.loads(line)
        else:
            yield from json.load(open(f, encoding='utf-8'))
G = 0; seen = set()
land = collections.Counter(); plant = collections.defaultdict(collections.Counter); anim = collections.defaultdict(collections.Counter)
hires = collections.Counter(); fert = collections.Counter(); wheatbuy = collections.Counter(); ops = collections.Counter()
sells = collections.defaultdict(collections.Counter); cash = []; wins = 0; build = collections.Counter(); fertop = collections.defaultdict(collections.Counter)
for d in games():
    n = d['info'].get('TeamNames') or []
    if team not in n or d['id'] in seen: continue
    seen.add(d['id']); p = n.index(team); G += 1
    r = d['rewards']; cash.append(r[p]); wins += r[p] > r[1 - p]
    q = 0
    for t in range(len(d['acts']) - 1):
        a = d['acts'][t + 1][p]
        if not isinstance(a, dict): continue
        day = t // 24
        for o in a.get('market') or []:
            if not o: continue
            if o[0] == 'BUY_LAND': q += 1; land[(q, day)] += 1
            elif o[0] == 'BUY_ANIMAL': anim[o[1]][day] += int(o[2]) if len(o) > 2 else 1
            elif o[0] == 'HIRE': hires[day] += 1
            elif o[0] == 'BUY_PRODUCT' and o[1] == 'FERTILIZER': fert[day] += int(o[2]) if len(o) > 2 else 1
            elif o[0] == 'BUY_PRODUCT' and o[1] == 'WHEAT': wheatbuy[day] += int(o[2]) if len(o) > 2 else 1
            elif o[0] == 'SELL': sells[o[1]][day // 5] += int(o[2]) if len(o) > 2 else 1
        for c in [a.get('farmer') or ['PASS']] + list(a.get('hands') or []):
            if not c: continue
            ops[c[0]] += 1
            if c[0] == 'PLANT' and len(c) > 1: plant[c[1]][day] += 1
            if c[0] in ('BUILD_COOP', 'BUILD_PASTURE'): build[(c[0], day)] += 1
g = max(1, G)
print(f"{team}: games {G} wins {wins} median cash {sorted(cash)[len(cash)//2] if cash else 0:.0f}")
print(' land (nth quadrant, day): ' + ', '.join(f"{k[0]}@d{k[1]}:{v}" for k, v in sorted(land.items()) if v >= max(2, G // 20)))
for crop in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON'):
    c = plant[crop]; tot = sum(c.values()) / g
    print(f" plant {crop:10s} {tot:6.1f}/game  by day: " + ' '.join(f"{sum(c[x] for x in range(d0, d0 + 3)) / g:4.1f}" for d0 in range(0, 30, 3)))
for an in ('GOOSE', 'COW', 'SHEEP'):
    c = anim[an]; print(f" animal {an:6s} {sum(c.values()) / g:4.1f}/game  first days: " + ' '.join(f"d{k}:{v / g:.1f}" for k, v in sorted(c.items()) if v / g >= 0.2))
print(' hires/day: ' + ' '.join(f"{hires[d] / g:.0f}" for d in range(30)))
print(f" fertilizer bought {sum(fert.values()) / g:.0f}/game; wheat bought {sum(wheatbuy.values()) / g:.0f}/game")
print(' sell requests per 5-day block: ' + '; '.join(f"{it[:5]} " + ','.join(f"{c[b] / g:.0f}" for b in range(6)) for it, c in sorted(sells.items())))
tot = sum(ops.values()) / g
print(' unit ops/game: ' + ', '.join(f"{k} {v / g:.0f}" for k, v in ops.most_common(16)) + f"  (total {tot:.0f})")
