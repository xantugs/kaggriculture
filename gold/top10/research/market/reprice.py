"""Re-price a recorded fill path under a changed supply schedule (both sides' sale steps fixed, non-reactive).
The book is a stock: x(t) = x(t-1) + units sold above $1 - units bought - town drain (fixed by the shop list).
Within a step both sides' units of one product are quoted in lockstep (pairs at the same book), as in the engine.

Library: drain_schedule(shops), events(row), reprice(events, prod, shops) -> (rev_us, rev_el, units_us, units_el).
CLI: reprice.py rows.jsonl validate          (recorded revenue vs re-priced revenue per product)
     reprice.py rows.jsonl supply            (value of +/-k units of our supply per product, by day window)"""
import sys, json, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P, MP, price, load

SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"], "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
         "YARN_STORE": ["WOOL"], "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
         "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}


def drain_at(shops, prod, t):
    """Units the town removes after the market of step t."""
    d = 0
    day = t // 24
    if t % 4 == 0:
        k = day // 3  # shop i unlocks at the end of day 3i+2, active from day 3(i+1)
        for s in shops[:min(k, 8)]:
            if prod in SHOPS[s]:
                d += 2 if len(SHOPS[s]) == 1 else 1
    if t % 24 == 0 and prod != "FERTILIZER":
        d += 1
    return d


def events(row):
    ev = collections.defaultdict(lambda: collections.defaultdict(list))  # prod -> t -> [(side, op, n, $)]
    for t, sd, op, it, k, d in row['fills']:
        ev[it][t].append([sd, op, k, d])
    return ev


def reprice(ev_p, prod, shops, T=719, x0=0, trace=None):
    x = x0
    rev = [0.0, 0.0]; units = [0, 0]
    for t in range(T):
        es = ev_p.get(t)
        if es:
            buys = [0, 0]; sells = [0, 0]
            for sd, op, n, d in es:
                if op == 'B': buys[sd] += n
                else: sells[sd] += n
            for sd in (0, 1):
                for _ in range(buys[sd]):
                    rev[sd] -= price(prod, x - 1); x -= 1
            while sells[0] > 0 or sells[1] > 0:
                q = price(prod, x)
                for sd in (0, 1):
                    if sells[sd] > 0:
                        rev[sd] += q; units[sd] += 1; sells[sd] -= 1
                        if q > 1: x += 1
        x -= drain_at(shops, prod, t)
        if trace is not None: trace.append(x)
    return rev[0], rev[1], units[0], units[1]


def recorded(row, prod):
    r = [0.0, 0.0]
    for t, sd, op, it, k, d in row['fills']:
        if it == prod: r[sd] += d if op == 'S' else -d
    return r


def validate(rows):
    err = collections.defaultdict(float); tot = collections.defaultdict(float); xe = collections.defaultdict(float)
    for r in rows:
        ev = events(r)
        for p in P:
            tr = []
            a, b, _, _ = reprice(ev.get(p, {}), p, r['shops'], trace=tr)
            ra, rb = recorded(r, p)
            err[p] += abs(a - ra) + abs(b - rb); tot[p] += abs(ra) + abs(rb)
            pi = P.index(p)
            xe[p] += sum(abs(tr[t] - r['inv'][t][pi]) for t in range(min(len(tr), len(r['inv'])))) / 719
    for p in P:
        print(f"{p:10s} revenue abs err {err[p]/len(rows):8.1f} of {tot[p]/len(rows):8.0f} per seat;  mean |x - x_rec| {xe[p]/len(rows):6.2f}")


def scale_ours(ev_p, f, t0, t1, side=0):
    """Scale side's sales in [t0, t1) by f (rounding each lot); f > 1 adds units to existing lots."""
    out = {}
    for t, es in ev_p.items():
        nl = []
        for sd, op, n, d in es:
            if sd == side and op == 'S' and t0 <= t < t1:
                n2 = int(round(n * f))
                if n2 > 0: nl.append([sd, op, n2, d])
            else:
                nl.append([sd, op, n, d])
        out[t] = nl
    return out


def add_ours(ev_p, k, t, side=0):
    out = {tt: [list(e) for e in es] for tt, es in ev_p.items()}
    out.setdefault(t, []).insert(0, [side, 'S', k, 0])
    return out


def supply(rows):
    """Margin value (us - elite) of k extra units sold by us at hour 1 of day D (after the midnight drain),
    and of removing 10% of our sales in a window, per product."""
    DAYS = [6, 10, 13, 16, 19, 22, 25, 28]
    K = 5
    acc = collections.defaultdict(float)
    for r in rows:
        ev = events(r)
        for p in P:
            evp = ev.get(p, {})
            a0, b0, _, _ = reprice(evp, p, r['shops'])
            for D in DAYS:
                a, b, _, _ = reprice(add_ours(evp, K, D * 24 + 1), p, r['shops'])
                acc[(p, D, 'own')] += (a - a0) / K
                acc[(p, D, 'el')] += (b - b0) / K
            for (t0, t1, lab) in [(288, 384, 'd12-15'), (384, 576, 'd16-23'), (576, 720, 'd24-29')]:
                a, b, _, _ = reprice(scale_ours(evp, 0.9, t0, t1), p, r['shops'])
                acc[(p, lab, 'cut10')] += (a - b) - (a0 - b0)
    n = len(rows)
    print(f"{n} seats. +{K} units of our supply at hour 1 of day D: margin value per unit = own revenue change - elite revenue change")
    print("   product     " + " ".join(f"   d{D:<3d}" for D in DAYS))
    for p in P:
        print(f"   {p:10s} " + " ".join(f"{(acc[(p,D,'own')]-acc[(p,D,'el')])/n:7.1f}" for D in DAYS)
              + "   (own " + " ".join(f"{acc[(p,D,'own')]/n:.0f}" for D in DAYS) + ")")
    print("\ncut 10% of our sales in a window (lots rounded): margin change per seat")
    for p in P:
        print(f"   {p:10s} " + " ".join(f"{lab} {acc[(p,lab,'cut10')]/n:+7.0f}" for lab in ('d12-15', 'd16-23', 'd24-29')))




def cross(rows):
    """Total cross-impact: our revenue change if the elite had sold nothing of the product before day D (and vice versa),
    and the curve of k extra units of ours at hour 1 of day D."""
    acc = collections.defaultdict(float)
    KS = [5, 10, 20, 40]
    DAYS = [10, 13, 16, 19, 22]
    for r in rows:
        ev = events(r)
        for p in P:
            evp = ev.get(p, {})
            a0, b0, _, _ = reprice(evp, p, r['shops'])
            no_el = {t: [e for e in es if e[0] == 0 or e[1] == 'B'] for t, es in evp.items()}
            no_us = {t: [e for e in es if e[0] == 1 or e[1] == 'B'] for t, es in evp.items()}
            a1, _, _, _ = reprice(no_el, p, r['shops']); _, b1, _, _ = reprice(no_us, p, r['shops'])
            acc[(p, 'el_on_us')] += a1 - a0; acc[(p, 'us_on_el')] += b1 - b0
            for D in DAYS:
                for k in KS:
                    a, b, _, _ = reprice(add_ours(evp, k, D * 24 + 1), p, r['shops'])
                    acc[(p, D, k)] += (a - a0) - (b - b0)
    n = len(rows)
    print(f"{n} seats. revenue each side loses to the other's whole supply of the product (per seat):")
    for p in P:
        print(f"   {p:10s} elite's supply costs us {acc[(p,'el_on_us')]/n:8.0f}   ours costs the elite {acc[(p,'us_on_el')]/n:8.0f}   net {(acc[(p,'us_on_el')]-acc[(p,'el_on_us')])/n:+8.0f}")
    print("\nmargin gain per seat of k extra units of ours at hour 1 of day D (total, not per unit)")
    for p in P:
        print(f"   {p:10s} " + "  ".join(f"d{D}:" + "/".join(f"{acc[(p,D,k)]/n:.0f}" for k in KS) for D in DAYS))


if __name__ == '__main__':
    rows = list(load(sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else None))
    {'validate': validate, 'supply': supply, 'cross': cross}[sys.argv[2]](rows)
