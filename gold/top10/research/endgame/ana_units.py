"""Units sold/bought per product and window, us vs elite (day_led.py output), by outcome group."""
import sys, json, collections
PR = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
WIN = [(12, 15), (16, 19), (20, 23), (24, 26), (27, 28), (29, 29)]
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p, encoding='utf-8')]
rows = [x for x in rows if x['m'] is not None and len(x['days_us']) >= 29]
def val(x, who, a, b, key):
    s = 0
    for d in range(a, min(b, 28) + 1): s += x['days_' + who][d]['mkt'].get(key, 0)
    if b == 29:
        for stp, v in x['steps_' + who].items():
            if int(stp) // 24 == 29: s += v.get(key, 0)
    return s
for name, sel in (('ALL', rows), ('L<5k', [x for x in rows if -5000 < x['m'] < 0]), ('W<5k', [x for x in rows if 0 < x['m'] < 5000])):
    n = len(sel); print(f'== {name} {n} seats: units sold us/elite (avg price us/elite)')
    print('         ' + ' '.join(f"{'d%d-%d' % w:>19s}" for w in WIN))
    for p in PR:
        cells = []
        for a, b in WIN:
            uu = sum(val(x, 'us', a, b, 'u_' + p) for x in sel) / n; ue = sum(val(x, 'elite', a, b, 'u_' + p) for x in sel) / n
            ru = sum(val(x, 'us', a, b, '$_' + p) for x in sel) / n; re_ = sum(val(x, 'elite', a, b, '$_' + p) for x in sel) / n
            cells.append(f"{uu:4.0f}/{ue:4.0f} ${ru/max(uu,1e-9):3.0f}/{re_/max(ue,1e-9):3.0f}")
        print(f"{p[:8]:8s} " + ' '.join(f"{c:>19s}" for c in cells))
    for p in ('WHEAT', 'FERTILIZER'):
        print(f"buy {p[:5]:5s} " + ' '.join(f"{sum(val(x, 'us', a, b, 'bu_' + p) for x in sel)/n:9.1f}/{sum(val(x, 'elite', a, b, 'bu_' + p) for x in sel)/n:<9.1f}" for a, b in WIN))
