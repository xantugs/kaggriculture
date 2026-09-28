"""Race and floor analysis on fills_gate.py rows (exact re-pricing, both schedules fixed).
race: for each (product, drain window) where both sides sell, move our units to the first step either side sells in that
      window, ahead of the elite (index 0). Margin change per seat by phase = the in-window timing prize (upper bound).
late: the opposite: our units moved behind the elite's in the window (what the elite's lead costs us today).
floor: units sold at <= $2 by day and hour, per side.
usage: race.py rows.jsonl[,more] [team]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P, load, phase, PH
from reprice import events, reprice


def window(t):
    return (t - 1) // 4   # drains after the market of steps 0 mod 4: steps 4w+1..4w+4 face one book


def move(ev_p, mode, t_lo=0, t_hi=720):
    """mode 'strict': windows where the elite's first sale is at an earlier step than ours: our units in that window go to
    the elite's first step at index 0; 'tie': windows where both first sell at the same step: our units at that step go to
    index 0 (ahead of the lockstep); 'first': every shared window, our units to the earliest step at index 0."""
    wins = collections.defaultdict(lambda: [set(), set()])
    for t, es in ev_p.items():
        for sd, op, n, d in es:
            if op == 'S' and d > n: wins[window(t)][sd].add(t)
    out = {t: [list(e) for e in es] for t, es in ev_p.items()}
    moved = 0
    for w, (a, b) in wins.items():
        if not a or not b: continue
        if not (t_lo <= min(a | b) < t_hi): continue
        fa, fb = min(a), min(b)
        if mode == 'strict' and not fb < fa: continue
        if mode == 'tie' and fa != fb: continue
        tgt = min(a | b)
        src = [fa] if mode == 'tie' else list(a)
        k = 0
        for t in src:
            keep = []
            for e in out[t]:
                if e[0] == 0 and e[1] == 'S' and e[3] != -1: k += e[2]
                else: keep.append(e)
            out[t] = keep
        out.setdefault(tgt, []).insert(0, [0, 'S', k, -1])
        moved += k
    return out, moved


def reprice_ordered(ev_p, prod, shops):
    """Like reprice() but honours list order within a step: an entry at index 0 of side 0 sells entirely first."""
    from ana_fills import price
    from reprice import drain_at
    x = 0; rev = [0.0, 0.0]
    for t in range(719):
        es = ev_p.get(t)
        if es:
            first = [e for e in es if e[3] == -1]
            rest = [e for e in es if e[3] != -1]
            for e in first:
                for _ in range(e[2]):
                    q = price(prod, x); rev[0] += q
                    if q > 1: x += 1
            buys = [0, 0]; sells = [0, 0]
            for sd, op, n, d in rest:
                if op == 'B': buys[sd] += n
                else: sells[sd] += n
            for sd in (0, 1):
                for _ in range(buys[sd]):
                    rev[sd] -= price(prod, x - 1); x -= 1
            while sells[0] > 0 or sells[1] > 0:
                q = price(prod, x)
                for sd in (0, 1):
                    if sells[sd] > 0:
                        rev[sd] += q; sells[sd] -= 1
                        if q > 1: x += 1
        x -= drain_at(shops, prod, t)
    return rev


def main():
    rows = list(load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
    n = len(rows)
    acc = collections.defaultdict(float)
    fl = collections.defaultdict(float)
    for r in rows:
        ev = events(r)
        for p in P:
            evp = ev.get(p, {})
            if not evp: continue
            a0, b0 = reprice_ordered(evp, p, r['shops'])
            for ph, (lo, hi) in enumerate([(0, 288), (288, 384), (384, 576), (576, 720)]):
                for mode in ('first', 'strict', 'tie'):
                    e2, mv = move(evp, mode, lo, hi)
                    a, b = reprice_ordered(e2, p, r['shops'])
                    acc[(p, ph, mode)] += (a - b) - (a0 - b0)
                    acc[(p, ph, mode, 'u')] += mv
        for t, sd, op, it, k, d in r['fills']:
            if op == 'S' and d <= 2 * k:
                fl[(it, sd, t // 24)] += k
    print(f"{n} seats. in-window race, margin change per seat: all shared windows first / elite-earlier windows (units) / same-step ties (units)")
    for p in P:
        print(f"  {p:10s} " + "  ".join(f"{PH[ph]} {acc[(p,ph,'first')]/n:+5.0f} {acc[(p,ph,'strict')]/n:+5.0f}({acc[(p,ph,'strict','u')]/n:4.1f}) {acc[(p,ph,'tie')]/n:+5.0f}({acc[(p,ph,'tie','u')]/n:4.1f})" for ph in range(4)))
    for m in ('first', 'strict', 'tie'):
        print(f"  total {m:6s}: " + "  ".join(f"{PH[ph]} {sum(acc[(p, ph, m)] for p in P)/n:+.0f}" for ph in range(4)))
    print("\nfloor sales (<= $2 a unit) per seat by day, us | elite")
    for p in ("STRAWBERRY", "MILK", "WOOL", "FERTILIZER", "MELON"):
        s = []
        for d in range(30):
            u0, u1 = fl[(p, 0, d)] / n, fl[(p, 1, d)] / n
            if u0 + u1 >= 0.05: s.append(f"d{d} {u0:.1f}|{u1:.1f}")
        print(f"  {p:10s} " + "  ".join(s))


if __name__ == '__main__':
    main()
