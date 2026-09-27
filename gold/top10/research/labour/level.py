"""Wage convexity on controller days: actual wage vs flat roster vs local leveling (work moved at most `win` days)."""
import sys, json, statistics as st
FIB = [1, 1]
while len(FIB) < 40: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(40)]
paths = sys.argv[1].split(','); d0 = int(sys.argv[2]) if len(sys.argv) > 2 else 16; d1 = int(sys.argv[3]) if len(sys.argv) > 3 else 28
win = int(sys.argv[4]) if len(sys.argv) > 4 else 1
rows = [json.loads(l) for p in paths for l in open(p, encoding='utf-8')]

def level(hs, win):
    hs = list(hs)
    improved = True
    while improved:
        improved = False
        for i in range(len(hs)):
            for j in range(max(0, i - win), min(len(hs), i + win + 1)):
                if hs[i] - hs[j] >= 2:
                    hs[i] -= 1; hs[j] += 1; improved = True
    return hs

def stats(days):
    hs = [days.get(str(d), {}).get('hire', 0) for d in range(d0, d1 + 1)]
    w = sum(CUM[h] for h in hs)
    tot = sum(hs); n = len(hs); lo = tot // n; k = tot - lo * n
    flat = k * CUM[lo + 1] + (n - k) * CUM[lo]
    lv = sum(CUM[h] for h in level(hs, win))
    b12 = sum(CUM[h] - CUM[12] for h in hs if h > 12)
    return dict(hd=tot, w=w, flat=flat, lv=lv, b12=b12, n13=sum(h >= 13 for h in hs), mx=max(hs))

by = {}
for r in rows:
    by.setdefault(r['team'], []).append(r)
print(f"days {d0}-{d1}, leveling window {win}")
print(f"{'team':14s} {'n':>3} {'win%':>5} {'marg':>7} | {'hd_us':>6} {'w_us':>6} {'flat':>6} {'lvl':>6} {'>12':>6} {'n13':>4} | {'hd_el':>6} {'w_el':>6} {'flat':>6} {'lvl':>6} {'n13':>4}")
def line(name, xs):
    n = len(xs)
    U = [stats(r['days_us']) for r in xs]; E = [stats(r['days_elite']) for r in xs]
    m = lambda L, k: sum(x[k] for x in L) / n
    print(f"{name[:14]:14s} {n:3d} {100*sum(r['m']>0 for r in xs)/n:5.0f} {sum(r['m'] for r in xs)/n:+7.0f} | {m(U,'hd'):6.1f} {m(U,'w'):6.0f} {m(U,'flat'):6.0f} {m(U,'lv'):6.0f} {m(U,'b12'):6.0f} {m(U,'n13'):4.1f} | {m(E,'hd'):6.1f} {m(E,'w'):6.0f} {m(E,'flat'):6.0f} {m(E,'lv'):6.0f} {m(E,'n13'):4.1f}")
for t, xs in sorted(by.items(), key=lambda kv: -len(kv[1])):
    line(t, xs)
line('ALL', rows)
# how many losses would flip if we saved (w - lv) dollars
sav = [(r['m'], stats(r['days_us'])['w'] - stats(r['days_us'])['lv']) for r in rows]
print('flips if the local-leveling saving were banked:', sum(1 for m, s in sav if m <= 0 and m + s > 0), 'of', len(rows),
      ' mean saving', round(sum(s for _, s in sav) / len(sav)))
sav2 = [(r['m'], stats(r['days_us'])['w'] - stats(r['days_us'])['flat']) for r in rows]
print('flips with the flat-roster saving:', sum(1 for m, s in sav2 if m <= 0 and m + s > 0), ' mean', round(sum(s for _, s in sav2) / len(sav2)))
