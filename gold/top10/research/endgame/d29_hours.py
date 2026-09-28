"""Day-29 (and day-28) sales by product and hour block, us vs rival, from day_led.py / pin_days.py output.
usage: d29_hours.py file.jsonl [...] [--close K]  (--close: only seats with |m| < K)"""
import sys, json, collections
args = [a for a in sys.argv[1:] if not a.startswith('--')]
K = None
for a in sys.argv[1:]:
    if a.startswith('--close='): K = float(a.split('=')[1])
rows = []
for p in args:
    for l in open(p, encoding='utf-8'):
        x = json.loads(l)
        if x.get('m') is None: continue
        if K is not None and abs(x['m']) >= K: continue
        rows.append(x)
n = len(rows); print(n, 'seats')
PR = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
BL = [(0, 1), (2, 7), (8, 15), (16, 19), (20, 21), (22, 23)]
for day in (28, 29):
    print(f'\nday {day}: units (avg $/u) by hour block, us | rival')
    print('product    ' + ''.join(f"h{a}-{b}".rjust(18) for a, b in BL))
    for p in PR:
        cells = []
        for a, b in BL:
            uu = ue = du = de = 0
            for x in rows:
                for who in ('us', 'elite'):
                    for st, v in x['steps_' + who].items():
                        st = int(st)
                        if st // 24 == day and a <= st % 24 <= b:
                            if who == 'us': uu += v.get('u_' + p, 0); du += v.get('$_' + p, 0)
                            else: ue += v.get('u_' + p, 0); de += v.get('$_' + p, 0)
            cells.append(f"{uu/n:4.1f}({du/max(uu,1):3.0f})|{ue/n:4.1f}({de/max(ue,1):3.0f})")
        print(f"{p[:10]:10s} " + ''.join(c.rjust(18) for c in cells))
