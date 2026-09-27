"""Timing vs volume on fills_gate.py rows.
- same-day price gap: for (seat, product, day) where both sides sell, our $/unit minus the elite's, weighted by our units
  (isolates who sells first within a day from which days each side sells on);
- order within the post-drain windows: share of units each side sells before the other in the same window;
- census: animals and plants by day for both sides, split by outcome.
usage: ana_timing.py rows.jsonl[,more] [team_filter]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P, MP, price, load, phase, PH


def main():
    rows = list(load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
    n = len(rows)
    gap = collections.defaultdict(float); wts = collections.defaultdict(float)
    first = collections.defaultdict(float)
    dayrev = collections.defaultdict(float)
    for r in rows:
        dd = collections.defaultdict(lambda: [[0, 0], [0, 0]])  # (it, day) -> side -> [units, $]
        win = collections.defaultdict(lambda: [None, None])  # (it, window) -> first step per side
        wu = collections.defaultdict(lambda: [0, 0])
        for t, sd, op, it, k, d in r['fills']:
            if op != 'S': continue
            day = t // 24
            e = dd[(it, day)][sd]; e[0] += k; e[1] += d
            # window id: drains happen after the market at steps 0 mod 4, so steps 4w+1 .. 4w+4 face one book
            w = (t - 1) // 4
            f = win[(it, w)]
            if f[sd] is None or t < f[sd]: f[sd] = t
            wu[(it, w)][sd] += k
        for (it, day), s in dd.items():
            (uu, du), (ue, de) = s
            if uu and ue:
                ph = phase(day)
                gap[(it, ph)] += uu * (du / uu - de / ue); wts[(it, ph)] += uu
        for (it, w), f in win.items():
            if f[0] is None or f[1] is None: continue
            u0, u1 = wu[(it, w)]
            ph = phase(w * 4 // 24)
            if f[0] < f[1]: first[(it, ph, 'us_first')] += 1
            elif f[1] < f[0]: first[(it, ph, 'el_first')] += 1
            else: first[(it, ph, 'same')] += 1
    print(f"{n} seats. same-day $/unit gap (us - elite), weighted by our units; units in both-sell days per seat")
    for it in P:
        print(f"  {it:10s} " + "  ".join(f"{PH[ph]} {gap[(it,ph)]/wts[(it,ph)] if wts[(it,ph)] else 0:+6.1f} ({wts[(it,ph)]/n:5.1f}u)" for ph in range(4)))
    print("\nwindows where both sell: who sells first (count per seat: us / elite / same step)")
    for it in P:
        print(f"  {it:10s} " + "  ".join(f"{PH[ph]} {first[(it,ph,'us_first')]/n:4.1f}/{first[(it,ph,'el_first')]/n:4.1f}/{first[(it,ph,'same')]/n:4.1f}" for ph in range(4)))
    # census
    print("\ncensus at the end of day D (per seat, us | elite): animals, strawberry/tomato/wheat/carrot/melon tiles, hands, money")
    keys = ['COW', 'SHEEP', 'GOOSE', 'STRAWBERRY', 'TOMATO', 'WHEAT', 'CARROT', 'MELON', 'hands', 'money', 'quads']
    for lab, sub in [('all', rows), ('loss>5k', [r for r in rows if r['m'] < -5000]), ('other', [r for r in rows if r['m'] >= -5000])]:
        m = len(sub)
        if not m: continue
        print(f" {lab} ({m})")
        for D in (5, 8, 11, 15, 19, 23, 27):
            print(f"   d{D:2d} " + " ".join(f"{k[:5]} {sum(r['census'][D][0].get(k,0) for r in sub if len(r['census'])>D)/m:5.1f}|{sum(r['census'][D][1].get(k,0) for r in sub if len(r['census'])>D)/m:5.1f}" for k in keys))


if __name__ == '__main__':
    main()
