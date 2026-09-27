"""Analyse day_led.py output: where (which days / products) the margin is made, by outcome group.
usage: ana_days.py dl.jsonl [dl2.jsonl ...]
"""
import sys, json, collections, statistics as st
PR = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
rows = []
for p in sys.argv[1:]:
    for l in open(p, encoding='utf-8'):
        x = json.loads(l)
        if x['m'] is None or len(x['days_us']) < 29: continue
        rows.append(x)
print(len(rows), 'seats')
def grp(m):
    if m > 5000: return 'W>5k'
    if m > 0: return 'W<5k'
    if m > -2000: return 'L<2k'
    if m > -5000: return 'L2-5k'
    return 'L>5k'
WIN = [(0, 11), (12, 15), (16, 19), (20, 23), (24, 26), (27, 28), (29, 29)]
def day29(x, who):
    # day 29 cash flow = final - money at end of day 28
    return x[who] - x['days_' + who][28]['money']
def flow(x, who, d):
    D = x['days_' + who]
    if d == 29: return day29(x, 'us' if who == 'us' else 'elite')
    prev = 3000 if d == 0 else D[d - 1]['money']
    return D[d]['money'] - prev
G = collections.defaultdict(list)
for x in rows: G[grp(x['m'])].append(x)
order = ['W>5k', 'W<5k', 'L<2k', 'L2-5k', 'L>5k']
print('\nMargin made per window (us - elite net cash flow), mean per seat; lead at end of d23 and d28 (cash)')
print('group   n   ' + ' '.join(f"d{a}-{b}".rjust(8) for a, b in WIN) + '   lead23   lead28   final')
for g in order:
    xs = G[g]
    if not xs: continue
    vals = []
    for a, b in WIN:
        vals.append(st.mean(sum(flow(x, 'us', d) - flow(x, 'elite', d) for d in range(a, b + 1)) for x in xs))
    l23 = st.mean(x['days_us'][23]['money'] - x['days_elite'][23]['money'] for x in xs)
    l28 = st.mean(x['days_us'][28]['money'] - x['days_elite'][28]['money'] for x in xs)
    print(f"{g:6s} {len(xs):3d}  " + ' '.join(f"{v:+8.0f}" for v in vals) + f" {l23:+8.0f} {l28:+8.0f} {st.mean(x['m'] for x in xs):+7.0f}")
# led at d23/d28 and lost
n = len(rows)
print('\nled at end of d23 and lost:', sum(1 for x in rows if x['days_us'][23]['money'] > x['days_elite'][23]['money'] and x['m'] < 0),
      ' trailed at d23 and won:', sum(1 for x in rows if x['days_us'][23]['money'] < x['days_elite'][23]['money'] and x['m'] > 0))
print('led at end of d28 and lost:', sum(1 for x in rows if x['days_us'][28]['money'] > x['days_elite'][28]['money'] and x['m'] < 0),
      ' trailed at d28 and won:', sum(1 for x in rows if x['days_us'][28]['money'] < x['days_elite'][28]['money'] and x['m'] > 0))
# product revenue by window, us - elite
def rev(x, who, a, b, key):
    s = 0
    for d in range(a, min(b, 28) + 1):
        s += x['days_' + who][d]['mkt'].get(key, 0)
    if b == 29:
        for stp, v in x['steps_' + who].items():
            if int(stp) // 24 == 29: s += v.get(key, 0)
    return s
print('\nRevenue gap us - elite by product and window (mean per seat, all seats; then close losses L<2k + L2-5k)')
for sel_name, xs in (('ALL', rows), ('L<5k', G['L<2k'] + G['L2-5k']), ('L>5k', G['L>5k']), ('W<5k', G['W<5k'])):
    print(' --', sel_name, len(xs))
    for p in PR:
        vals = [st.mean(rev(x, 'us', a, b, '$_' + p) - rev(x, 'elite', a, b, '$_' + p) for x in xs) for a, b in WIN]
        print(f"   {p[:6]:6s} " + ' '.join(f"{v:+8.0f}" for v in vals))
    for key in ('hire$', 'seed$', 'anim$'):
        vals = [st.mean(-(rev(x, 'us', a, min(b, 28), key) - rev(x, 'elite', a, min(b, 28), key)) for x in xs) for a, b in WIN]
        print(f"   {key[:6]:6s} " + ' '.join(f"{v:+8.0f}" for v in vals))
    vals = [st.mean(-(sum(rev(x, 'us', a, min(b, 28), 'b$_' + p) for p in PR) - sum(rev(x, 'elite', a, min(b, 28), 'b$_' + p) for p in PR)) for x in xs) for a, b in WIN]
    print(f"   {'buys':6s} " + ' '.join(f"{v:+8.0f}" for v in vals))
