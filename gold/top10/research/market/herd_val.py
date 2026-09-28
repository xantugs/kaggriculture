"""Margin value (us - elite, exact re-pricing on recorded fill paths, both schedules fixed) of k extra animals placed on
day D, their product sold at hour 1 of each production day (cared daily: first lot min(held, fy) at D + fy, then
1 + interval every interval days), plus 1 fertilizer a day sold at hour 1. Costs are NOT subtracted: compare with
price + wheat feed (1 a day at the book) + labour.
usage: herd_val.py rows.jsonl[,more] [split]   split: yarn3 / egg3 (town class by the first 3 shops)"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import load, price, P
from reprice import events, reprice

AN = {"GOOSE": ("EGG", 4, 1, 4, 300), "COW": ("MILK", 8, 2, 6, 400), "SHEEP": ("WOOL", 6, 3, 6, 500)}


def sched(kind, D):
    prod, fy, iv, held, cost = AN[kind]
    out = {}
    d = D + fy
    if d <= 29:
        out[d] = min(held, fy)
        d += iv
        while d <= 29:
            out[d] = min(held, 1 + iv); d += iv
    return out


def main():
    rows = list(load(sys.argv[1]))
    split = sys.argv[2] if len(sys.argv) > 2 else None
    if split:
        key = {'yarn3': lambda r: sum(1 for s in r['shops'][:3] if s == 'YARN_STORE'),
               'egg3': lambda r: sum(1 for s in r['shops'][:3] if s in ('BAKERY', 'BRUNCH_SPOT')),
               'milk3': lambda r: sum(1 for s in r['shops'][:3] if s in ('PIZZA_SHOP', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'))}[split]
        groups = {}
        for r in rows: groups.setdefault(min(2, key(r)), []).append(r)
        for g in sorted(groups):
            print(f"=== {split} = {g}{'+' if g == 2 else ''}")
            run(groups[g], days=(10, 12))
        return
    run(rows)


def run(rows, days=(10, 12, 14, 16, 18)):
    n = len(rows)
    acc = collections.defaultdict(float)
    for r in rows:
        ev = events(r)
        base = {}
        for p in ("EGG", "MILK", "WOOL", "FERTILIZER"):
            a, b, _, _ = reprice(ev.get(p, {}), p, r['shops']); base[p] = a - b
        wi = P.index("WHEAT")
        for kind in AN:
            prod = AN[kind][0]
            for D in days:
                for k in (1, 2, 4):
                    e = {t: [list(x) for x in es] for t, es in ev.get(prod, {}).items()}
                    for d, u in sched(kind, D).items():
                        e.setdefault(d * 24 + 1, []).insert(0, [0, 'S', u * k, 0])
                    a, b, _, _ = reprice(e, prod, r['shops'])
                    f = {t: [list(x) for x in es] for t, es in ev.get("FERTILIZER", {}).items()}
                    for d in range(D + 1, 30):
                        f.setdefault(d * 24 + 1, []).insert(0, [0, 'S', k, 0])
                    fa, fb, _, _ = reprice(f, "FERTILIZER", r['shops'])
                    feed = sum(price("WHEAT", r['inv'][d * 24][wi]) for d in range(D, 29)) * k
                    acc[(kind, D, k, 'prod')] += (a - b) - base[prod]
                    acc[(kind, D, k, 'fert')] += (fa - fb) - base["FERTILIZER"]
                    acc[(kind, D, k, 'feed')] += feed
    print(f"{n} seats. k extra animals placed on day D: margin of their product + fertilizer, minus feed at the day's wheat quote,")
    print("minus the animal's price; per animal (labour not included: ~1 visit a day)")
    for kind in AN:
        for D in days:
            s = []
            for k in (1, 2, 4):
                pr_ = acc[(kind, D, k, 'prod')] / n / k; fe = acc[(kind, D, k, 'fert')] / n / k; fd = acc[(kind, D, k, 'feed')] / n / k
                s.append(f"k={k}: prod {pr_:5.0f} fert {fe:4.0f} feed -{fd:4.0f} net {pr_ + fe - fd - AN[kind][4]:+5.0f} ({(pr_ + fe - fd - AN[kind][4]) / max(1, 29 - D):+4.0f}/day)")
            print(f"  {kind:5s} d{D}: " + "   ".join(s))


if __name__ == '__main__':
    main()
