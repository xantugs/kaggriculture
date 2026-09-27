"""Market lens on fills_gate.py rows.
usage: ana_fills.py rows.jsonl[,more] [team_filter]
Prints per product: units / revenue / $ per unit for us and the elite by phase, the volume/price split of the revenue gap,
the cross-impact of each side's cumulative supply on the other's revenue (denial), floor sales, hour profile."""
import sys, json, math, collections

P = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
MP = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20), "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60), "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60), "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60), "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40)}


def _shape(f, x, T):
    x = max(0.0, x)
    if f == "linear": return x
    if f == "sq": return x * x
    if f == "sqrt": return math.sqrt(x)
    if f == "log": return math.log(1.0 + x)
    if f == "hinge":
        u = x / T
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    return x


def price(p, x):
    """x = inventory - I0."""
    base, T, bf, bt, af, at = MP[p]
    if x < 0:
        pr = base + bt * base / _shape(bf, T, T) * _shape(bf, -x, T)
    else:
        pr = base - at * base / _shape(af, T, T) * _shape(af, x, T)
    return max(1, int(round(pr)))


def phase(day):
    return 0 if day < 12 else 1 if day < 16 else 2 if day < 24 else 3
PH = ["d0-11", "d12-15", "d16-23", "d24-29"]


def load(paths, team=None):
    for path in paths.split(','):
        for l in open(path, encoding='utf-8'):
            r = json.loads(l)
            if r.get('m') is None: continue
            if team and team not in r['team']: continue
            yield r


def main():
    rows = list(load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
    n = len(rows)
    print(f"{n} seats, wins {sum(r['m'] > 0 for r in rows)}, margin {sum(r['m'] for r in rows)/n:+.0f}")
    # units / revenue by side, product, phase
    U = collections.defaultdict(float); R = collections.defaultdict(float)
    BU = collections.defaultdict(float); BR = collections.defaultdict(float)
    FL = collections.defaultdict(float)  # units sold at <= $2
    LOW = collections.defaultdict(float)  # units sold under 25% of base
    HR = collections.defaultdict(float)  # (side, prod, hour) units, days 12+
    DEN = collections.defaultdict(float)  # (victim side, prod) revenue lost to the other side's cumulative supply
    SELF = collections.defaultdict(float)
    for r in rows:
        inv = r['inv']
        # cumulative supply by side and product, step by step
        by_t = collections.defaultdict(list)
        for t, sd, op, it, k, d in r['fills']:
            by_t[t].append((sd, op, it, k, d))
        cum = [collections.Counter(), collections.Counter()]
        for t in sorted(by_t):
            day = t // 24; ph = phase(day)
            xs_pre = inv[t - 1] if t >= 1 else [0] * 9
            step_units = collections.Counter()
            for sd, op, it, k, d in by_t[t]:
                if op == 'S' and d > k: step_units[it] += k
            for sd, op, it, k, d in by_t[t]:
                if op == 'S':
                    U[(sd, it, ph)] += k; R[(sd, it, ph)] += d
                    if d <= 2 * k: FL[(sd, it, ph)] += k
                    if d < 0.25 * MP[it][0] * k: LOW[(sd, it, ph)] += k
                    if day >= 12: HR[(sd, it, t % 24)] += k
                    pi = P.index(it)
                    xm = xs_pre[pi] + step_units[it] / 2.0
                    est = price(it, xm)
                    other = cum[1 - sd][it]; mine = cum[sd][it]
                    DEN[(sd, it)] += k * (price(it, xm - other) - est)
                    SELF[(sd, it)] += k * (price(it, xm - mine) - est)
                else:
                    BU[(sd, it, ph)] += k; BR[(sd, it, ph)] += d
            for sd, op, it, k, d in by_t[t]:
                if op == 'S' and d > k: cum[sd][it] += k
                elif op == 'B': cum[sd][it] -= k
    print("\nper seat: units sold / $ per unit / revenue  (us | elite), gap split into volume and price (midpoint)")
    print(f"{'product':10s} {'phase':7s} {'u_us':>6} {'u_el':>6} {'$u_us':>6} {'$u_el':>6} {'R_us':>7} {'R_el':>7} {'gap':>7} {'vol':>7} {'price':>7}")
    tot = collections.Counter()
    for it in P:
        for ph in range(4):
            uu, ue = U[(0, it, ph)] / n, U[(1, it, ph)] / n
            ru, re_ = R[(0, it, ph)] / n, R[(1, it, ph)] / n
            if uu + ue < 0.5: continue
            pu = ru / uu if uu else 0; pe = re_ / ue if ue else 0
            pbar = (ru + re_) / (uu + ue)
            qbar = (uu + ue) / 2
            vol = (uu - ue) * pbar; prc = ru - re_ - vol
            tot[(it, 'vol')] += vol; tot[(it, 'prc')] += prc
            print(f"{it:10s} {PH[ph]:7s} {uu:6.1f} {ue:6.1f} {pu:6.1f} {pe:6.1f} {ru:7.0f} {re_:7.0f} {ru-re_:+7.0f} {vol:+7.0f} {prc:+7.0f}")
        gu = sum(R[(0, it, ph)] for ph in range(4)) / n; ge = sum(R[(1, it, ph)] for ph in range(4)) / n
        print(f"{it:10s} {'ALL':7s} {'':6s} {'':6s} {'':6s} {'':6s} {gu:7.0f} {ge:7.0f} {gu-ge:+7.0f} {tot[(it,'vol')]:+7.0f} {tot[(it,'prc')]:+7.0f}")
    print("\nproduct purchases per seat (units / $):")
    for it in ("WHEAT", "FERTILIZER"):
        print(f"  {it:10s} " + "  ".join(f"{PH[ph]} us {BU[(0,it,ph)]/n:5.1f}/{BR[(0,it,ph)]/n:6.0f} el {BU[(1,it,ph)]/n:5.1f}/{BR[(1,it,ph)]/n:6.0f}" for ph in range(4)))
    print("\nunits sold at <= $2 (floor) and under 25% of base, per seat (us | elite), all phases:")
    for it in P:
        f0 = sum(FL[(0, it, ph)] for ph in range(4)) / n; f1 = sum(FL[(1, it, ph)] for ph in range(4)) / n
        l0 = sum(LOW[(0, it, ph)] for ph in range(4)) / n; l1 = sum(LOW[(1, it, ph)] for ph in range(4)) / n
        print(f"  {it:10s} floor {f0:6.1f} | {f1:6.1f}   low {l0:6.1f} | {l1:6.1f}")
    print("\ncross-impact per seat: revenue each side lost to the OTHER side's cumulative supply (denial), and to its OWN earlier supply")
    print(f"{'product':10s} {'el->us':>8} {'us->el':>8} {'net(us)':>8} {'self_us':>8} {'self_el':>8}")
    for it in P:
        a = DEN[(0, it)] / n; b = DEN[(1, it)] / n
        print(f"{it:10s} {a:8.0f} {b:8.0f} {b-a:+8.0f} {SELF[(0,it)]/n:8.0f} {SELF[(1,it)]/n:8.0f}")
    print("\nhour profile of sales, days 12+ (units per seat), premium goods:")
    for it in ("STRAWBERRY", "MILK", "WOOL", "TOMATO", "EGG", "WHEAT", "CARROT"):
        for sd in (0, 1):
            print(f"  {it[:5]} {'us' if sd == 0 else 'el'}: " + " ".join(f"{HR[(sd,it,h)]/n:4.1f}" for h in range(24)))


if __name__ == '__main__':
    main()
