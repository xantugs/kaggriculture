"""Days 16-29 behaviour of sf8 vs the elite (day_led.py output): plantings, hires, tiles, holdings, day-29 hourly sales.
usage: ana_late.py dl.jsonl [...]"""
import sys, json, collections, statistics as st
PR = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
AN = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}
rows = []
for p in sys.argv[1:]:
    for l in open(p, encoding='utf-8'):
        x = json.loads(l)
        if x['m'] is not None and len(x['days_us']) >= 29: rows.append(x)
def grp(m):
    return 'W' if m > 0 else ('L<3k' if m > -3000 else 'L>3k')
G = collections.defaultdict(list)
for x in rows: G[grp(x['m'])].append(x); G['ALL'].append(x)
mean = lambda v: sum(v) / max(1, len(v))
for gname in ('ALL', 'W', 'L<3k', 'L>3k'):
    xs = G[gname]
    print(f"\n===== {gname}: {len(xs)} seats, mean margin {mean([x['m'] for x in xs]):+.0f}")
    print('day | plantings us (W C T S M)        elite            | hires us/el  $us/$el | tiles us W/C/T/S/geese  el')
    for d in range(14, 29):
        def pl(who):
            c = collections.Counter()
            for x in xs: c.update(x['days_' + who][d]['planted'])
            return ' '.join(f"{c[k]/len(xs):4.1f}" for k in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON'))
        def ti(who):
            c = collections.Counter()
            for x in xs: c.update(x['days_' + who][d]['tiles'])
            return '/'.join(f"{c[k]/len(xs):.0f}" for k in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'GOOSE'))
        h = lambda who, k: mean([x['days_' + who][d]['mkt'].get(k, 0) for x in xs])
        print(f"{d:3d} | {pl('us')} | {pl('elite')} | {h('us','hires'):4.1f}/{h('elite','hires'):4.1f} {h('us','hire$'):5.0f}/{h('elite','hire$'):5.0f} | {ti('us'):16s} {ti('elite')}")
    # holdings at end of day 28 (before drop) + ripe after the night refresh, valued at the day-28 end price
    print('end of d28: held (shed+carried) | ripe on tiles after refresh  [units us / elite]')
    for p in PR:
        hu = mean([x['days_us'][28]['held'].get(p, 0) for x in xs]); he = mean([x['days_elite'][28]['held'].get(p, 0) for x in xs])
        rk = [k for k, v in AN.items() if v == p] + [p]
        ru = mean([sum(x['days_us'][28].get('ripe_post', x['days_us'][28]['ripe']).get(k, 0) for k in rk) for x in xs])
        re_ = mean([sum(x['days_elite'][28].get('ripe_post', x['days_elite'][28]['ripe']).get(k, 0) for k in rk) for x in xs])
        # day-29 units sold and $
        u29 = lambda who: mean([sum(v.get('u_' + p, 0) for s, v in x['steps_' + who].items() if int(s) // 24 == 29) for x in xs])
        r29 = lambda who: mean([sum(v.get('$_' + p, 0) for s, v in x['steps_' + who].items() if int(s) // 24 == 29) for x in xs])
        fl = [x for x in xs if x.get('final_us')]
        lu = mean([x['final_us']['held'].get(p, 0) + sum(x['final_us']['ripe'].get(k, 0) for k in rk) for x in fl]) if fl else float('nan')
        le = mean([x['final_elite']['held'].get(p, 0) + sum(x['final_elite']['ripe'].get(k, 0) for k in rk) for x in fl]) if fl else float('nan')
        print(f"  {p[:6]:6s} held {hu:5.1f}/{he:5.1f}  ripe {ru:5.1f}/{re_:5.1f}  | d29 sold {u29('us'):5.1f}/{u29('elite'):5.1f} units ${r29('us'):6.0f}/${r29('elite'):6.0f} | left at end {lu:4.1f}/{le:4.1f}")
    # day-29 sales by hour (all products, $)
    hrs = collections.defaultdict(lambda: [0, 0])
    for x in xs:
        for i, who in enumerate(('us', 'elite')):
            for s, v in x['steps_' + who].items():
                s = int(s)
                if s // 24 == 29:
                    hrs[s % 24][i] += sum(val for k, val in v.items() if k.startswith('$_'))
    print('day-29 $ by hour us/elite: ' + ' '.join(f"h{h}:{hrs[h][0]/len(xs):.0f}/{hrs[h][1]/len(xs):.0f}" for h in sorted(hrs)))
    hrs = collections.defaultdict(lambda: [0, 0])
    for x in xs:
        for i, who in enumerate(('us', 'elite')):
            for s, v in x['steps_' + who].items():
                s = int(s)
                if s // 24 == 28:
                    hrs[s % 24][i] += sum(val for k, val in v.items() if k.startswith('$_'))
    print('day-28 $ by hour us/elite: ' + ' '.join(f"h{h}:{hrs[h][0]/len(xs):.0f}/{hrs[h][1]/len(xs):.0f}" for h in sorted(hrs)))
