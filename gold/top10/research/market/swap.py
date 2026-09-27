"""Static swap evaluation on recorded fill paths (both sides' schedules fixed, exact book re-pricing):
remove `units` of our sales of product A in days [a0, a1) (our lots in the window scaled down), add `m` units of B sold by
us at hour 1 of day D (split over `spread` consecutive days). Prints margin change per seat by team.
usage: swap.py rows.jsonl A a0 a1 units B D m [spread]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import load
from reprice import events, reprice


def cut(ev_p, units, t0, t1):
    tot = sum(n for t, es in ev_p.items() if t0 <= t < t1 for sd, op, n, d in es if sd == 0 and op == 'S')
    if tot <= 0: return ev_p, 0
    f = max(0.0, 1.0 - units / tot)
    out = {}; kept = 0.0; want = tot * f; acc = 0.0
    for t in sorted(ev_p):
        nl = []
        for sd, op, n, d in ev_p[t]:
            if sd == 0 and op == 'S' and t0 <= t < t1:
                acc += n * f
                n2 = int(round(acc - kept))
                kept += n2
                if n2 > 0: nl.append([sd, op, n2, d])
            else:
                nl.append([sd, op, n, d])
        out[t] = nl
    return out, tot - kept


def add(ev_p, m, D, spread):
    out = {t: [list(e) for e in es] for t, es in ev_p.items()}
    per = [m // spread + (1 if i < m % spread else 0) for i in range(spread)]
    for i, k in enumerate(per):
        if k > 0: out.setdefault((D + i) * 24 + 1, []).insert(0, [0, 'S', k, 0])
    return out


def main():
    path, A, a0, a1, units, B, D, m = sys.argv[1:9]
    spread = int(sys.argv[9]) if len(sys.argv) > 9 else 1
    a0, a1, units, D, m = int(a0), int(a1), int(units), int(D), int(m)
    rows = list(load(path))
    by = collections.defaultdict(list)
    for r in rows:
        ev = events(r)
        dm = 0.0; parts = {}
        for p in set([A, B]):
            evp = ev.get(p, {})
            a_0, b_0, _, _ = reprice(evp, p, r['shops'])
            e2 = evp
            removed = 0
            if p == A and units > 0:
                e2, removed = cut(e2, units, a0 * 24, a1 * 24)
            if p == B and m > 0:
                e2 = add(e2, m, D, spread)
            a, b, _, _ = reprice(e2, p, r['shops'])
            parts[p] = ((a - a_0), (b - b_0))
            dm += (a - a_0) - (b - b_0)
        by[r['team']].append((dm, parts, r['m']))
    allv = [x for v in by.values() for x in v]
    def line(name, xs):
        n = len(xs)
        dm = sum(x[0] for x in xs) / n
        pa = {p: (sum(x[1][p][0] for x in xs) / n, sum(x[1][p][1] for x in xs) / n) for p in xs[0][1]}
        near = sum(1 for x in xs if x[2] < 0 and x[2] + x[0] > 0) - sum(1 for x in xs if x[2] > 0 and x[2] + x[0] < 0)
        print(f"  {name[:22]:22s} n={n:3d} dmargin {dm:+7.0f}  " + "  ".join(f"{p[:5]} us {v[0]:+6.0f} el {v[1]:+6.0f}" for p, v in pa.items()) + f"  static flips {near:+d}")
    print(f"swap: -{units} {A} (days {a0}-{a1-1}) +{m} {B} (day {D}, spread {spread})")
    for team, xs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        line(team, xs)
    line('ALL', allv)


if __name__ == '__main__':
    main()
