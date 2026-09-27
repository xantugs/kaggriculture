"""Marginal value of one extra unit of supply (margin = us - elite), on the recorded fill paths of fills_gate.py rows.
For a unit sold at step t: price now, minus the drop it causes on OUR later sales (self), plus the drop on the ELITE's
later sales (denial). The book is a stock (town drain is fixed), so a unit shifts every later quote until the floor.
usage: ana_marg.py rows.jsonl[,more] [team_filter]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P, MP, price, load

REF_DAYS = [4, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]


def main():
    rows = list(load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
    n = len(rows)
    acc = collections.defaultdict(float)  # (prod, day, key)
    grp = collections.defaultdict(float)
    for r in rows:
        inv = r['inv']
        sells = collections.defaultdict(list)  # prod -> [(t, side, units, dollars)]
        for t, sd, op, it, k, d in r['fills']:
            if op == 'S': sells[it].append((t, sd, k, d))
        for it in P:
            pi = P.index(it)
            ev = sells.get(it, [])
            for day in REF_DAYS:
                t0 = day * 24
                x0 = inv[t0 - 1][pi] if t0 >= 1 else 0
                den = slf = 0.0
                for t, sd, k, d in ev:
                    if t < t0: continue
                    if d <= k: continue  # floor units: a shift does not move them
                    x = inv[t - 1][pi] if t >= 1 else 0
                    s = price(it, x) - price(it, x + 1)
                    if sd == 1: den += k * s
                    else: slf += k * s
                acc[(it, day, 'p')] += price(it, x0)
                acc[(it, day, 'den')] += den
                acc[(it, day, 'self')] += slf
                lose = r['m'] < -5000
                grp[(it, day, lose, 'den')] += den; grp[(it, day, lose, 'self')] += slf; grp[(it, day, lose, 'n')] += 1
    print(f"{n} seats. per product and day (hour 0): quote p, denial (drop on the elite's later sales per extra unit now),")
    print("self (drop on our later sales), net = p - self + den")
    for it in P:
        print(f"{it}")
        print("   day  " + " ".join(f"{d:6d}" for d in REF_DAYS))
        for key in ('p', 'den', 'self'):
            print(f"   {key:5s}" + " ".join(f"{acc[(it,d,key)]/n:6.1f}" for d in REF_DAYS))
        print(f"   {'net':5s}" + " ".join(f"{(acc[(it,d,'p')]-acc[(it,d,'self')]+acc[(it,d,'den')])/n:6.1f}" for d in REF_DAYS))
        for lose in (True, False):
            m = grp[(it, 12, lose, 'n')]
            if m:
                print(f"   {'L>5k' if lose else 'rest'} den-self " + " ".join(f"{(grp[(it,d,lose,'den')]-grp[(it,d,lose,'self')])/max(1,grp[(it,d,lose,'n')]):6.1f}" for d in REF_DAYS))


if __name__ == '__main__':
    main()
