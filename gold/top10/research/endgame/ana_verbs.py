"""Unit-turn use per day (verbs), us vs elite, from day_led.py / replay_days.py output (needs verbs_* fields).
usage: ana_verbs.py file.jsonl [...]   (the other seat is 'elite' or 'them')"""
import sys, json, collections
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p, encoding='utf-8')]
rows = [x for x in rows if x.get('verbs_us')]
oth = 'elite' if 'verbs_elite' in rows[0] else 'them'
V = ['MOVE', 'PASS', 'WATER', 'HARVEST', 'PLANT', 'FERTILIZE', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'PICKUP', 'DROP', 'DIG']
print(len(rows), 'seats; per day mean unit actions (us / %s); hires; hire $' % oth)
print('day ' + ' '.join(f"{v[:6]:>11s}" for v in ['TOTAL'] + V) + '   hires     hire$')
for d in range(12, 30):
    tot = []
    cells = []
    for v in ['TOTAL'] + V:
        a = b = 0
        for x in rows:
            vu = x['verbs_us'].get(str(d), {}); vo = x['verbs_' + oth].get(str(d), {})
            a += sum(vu.values()) if v == 'TOTAL' else vu.get(v, 0)
            b += sum(vo.values()) if v == 'TOTAL' else vo.get(v, 0)
        cells.append(f"{a/len(rows):5.0f}/{b/len(rows):<5.0f}")
    if d < 29:
        hu = sum(x['days_us'][d]['mkt'].get('hires', 0) for x in rows) / len(rows); he = sum(x['days_' + oth][d]['mkt'].get('hires', 0) for x in rows) / len(rows)
        cu = sum(x['days_us'][d]['mkt'].get('hire$', 0) for x in rows) / len(rows); ce = sum(x['days_' + oth][d]['mkt'].get('hire$', 0) for x in rows) / len(rows)
    else:
        k = [x for x in rows if 'mkt29_us' in x]
        hu = sum(x['mkt29_us'].get('hires', 0) for x in k) / max(1, len(k)); he = sum(x['mkt29_' + oth].get('hires', 0) for x in k) / max(1, len(k))
        cu = sum(x['mkt29_us'].get('hire$', 0) for x in k) / max(1, len(k)); ce = sum(x['mkt29_' + oth].get('hire$', 0) for x in k) / max(1, len(k))
    print(f"{d:3d} " + ' '.join(cells) + f"  {hu:4.1f}/{he:<4.1f} {cu:5.0f}/{ce:<5.0f}")
