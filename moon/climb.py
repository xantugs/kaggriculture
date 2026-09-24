import sys, json
eps = json.load(open(sys.argv[1], encoding='utf-8')); subs = [int(x) for x in sys.argv[2].split(',')]
for sb in subs:
    rows = []
    for e in eps:
        for k, s in enumerate(e['sub']):
            if s == sb and e['teams'][k] == 'offhand' and None not in e['r']:
                rows.append((e['t'], e['score'][k], e['r'][k] - e['r'][1 - k], e['teams'][1 - k], e['score'][1 - k], e['id']))
    rows.sort()
    pts = [rows[i][1] for i in (0, 9, 19, 39, 59, 79, 95, 119) if i < len(rows)]
    print(sb, 'rating at games 1/10/20/40/60/80/96/120:', [round(p) if p else None for p in pts])
    losses = [r for r in rows if r[2] <= 0]
    for r in losses[:10]:
        if sb == subs[0]: print('   loss', r[0][:16], 'margin', r[2], 'vs', r[3][:20], 'opp rating', round(r[4] or 0), 'episode', r[5])
