"""Analyse gapday_play rows: when is the us - elite margin gap created.
usage: gapday_ana.py rows.jsonl[,rows2.jsonl] [team|ALL] [--by-team]

Valuations of a farm at the start of day D (all in $):
  C  cash
  L  C + goods (shed, carried, units held by animals, harvestable units on plants) at the pooled future realized price
  B  L + capital at book value: land and animals at cost, straight-line to day 30 from their purchase day; growing plants at
     seed cost times the share of their output still to come; seeds held at cost
  E  L + capital at going-concern value: every animal at the pooled realized output rate per animal-day (both farms, all seats)
     times the days left times the pooled future price, net of one wheat a day; every plant at the pooled realized output of
     its crop still to come times the pooled future price; land not valued separately (it earns through what stands on it)
The pooled future price of a product from day D = mean realized price of all units sold by both farms on days D..29 in that game
(falls back to the quote at D).
"""
import sys, json, collections, math, statistics as st

CROPS = {"WHEAT": (10, 2, 4, False), "CARROT": (20, 2, 3, False), "TOMATO": (50, 8, 8, True), "STRAWBERRY": (100, 10, 10, True),
         "MELON": (80, 10, 12, False)}  # seed, first_yield_day, max_yield_day, ongoing
ONG_LIFE = {"TOMATO": (8, 1, 4), "STRAWBERRY": (10, 2, 4)}  # first, interval, productions
AN = {"GOOSE": (300, "EGG", 4), "COW": (400, "MILK", 8), "SHEEP": (500, "WOOL", 6)}
LAND = [1000, 2000, 4000]
PRODS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]


def load(paths, team='ALL'):
    rows = []
    for p in paths.split(','):
        for l in open(p, encoding='utf-8'):
            if l.strip():
                x = json.loads(l)
                if x.get('m') is None: continue
                if team != 'ALL' and x['team'] != team: continue
                rows.append(x)
    return rows


def fut_price(x, D, prod):
    u = s = 0
    for side in ('days_us', 'days_elite'):
        for dd in range(D, 30):
            f = x[side][dd]['f']
            u += f.get('Su' + prod, 0); s += f.get('S$' + prod, 0)
    if u >= 3: return s / u
    q = x['q'].get(str(D)) or x['q'].get('0')
    return q[prod]


def pooled_rates(rows):
    """animal output per animal-day (days >= 8), plant output per plant by crop (harvested units / plants planted)."""
    ad = collections.Counter(); au = collections.Counter(); pl = collections.Counter(); pu = collections.Counter()
    for x in rows:
        for side in ('days_us', 'days_elite'):
            for D in range(8, 29):
                s = x[side][D]['s']; f = x[side][D]['f']
                if not s: continue
                for k, (c, prod, fy) in AN.items():
                    ad[k] += s['an'].get(k, [0, 0])[0]; au[k] += f.get('hv_' + prod, 0)
            for D in range(0, 30):
                f = x[side][D]['f']
                for c in CROPS:
                    pl[c] += f.get('plant_' + c, 0); pu[c] += f.get('hv_' + c, 0)
    rate = {k: au[k] / max(1, ad[k]) for k in AN}
    per_plant = {c: pu[c] / max(1, pl[c]) for c in CROPS}
    return rate, per_plant


def purchases(x, side):
    """list of (day, kind) animal purchases and land purchase days."""
    an = []; land = []
    for D in range(30):
        f = x[side][D]['f']
        for k in AN:
            for _ in range(int(f.get('animu' + k, 0))): an.append((D, k))
        if f.get('land$', 0) > 0:
            v = f['land$']
            for c in LAND:
                pass
            land.append((D, v))
    return an, land


def value(x, side, D, rate, per_plant, P):
    s = x[side][D]['s'] if D < 30 else x[side][30]['s']
    if D == 30:
        fin = x['us'] if side == 'days_us' else x['elite']
        return dict(C=fin, L=fin, B=fin, E=fin)
    C = s['money']
    goods = collections.Counter()
    for k, v in s['shed'].items(): goods[k] += v
    for k, v in s.get('inv', {}).items(): goods[k] += v
    for k, (n, u) in s['an'].items(): goods[AN[k][1]] += u
    wip_book = 0.0; wip_econ = 0.0
    for crop, (n, u) in s['pl'].items():
        seed, fy, my, ong = CROPS[crop]
        ages = s['ages'].get(crop, {})
        if ong:
            goods[crop] += u   # produced, waiting on the plant
            first, iv, npr = ONG_LIFE[crop]
            tot = per_plant[crop]  # realized harvested units per planted plant
            for a, cnt in ages.items():
                a = int(a)
                # productions already made by age a (a production at the end of day planted+first-1+k*iv)
                done = 0 if a < first else min(npr, (a - first) // iv + 1)
                left = (npr - done) / npr
                wip_book += cnt * seed * left
                wip_econ += cnt * tot * left * P[crop]
        else:
            # one-time: units on the plant count as goods once harvestable, otherwise WIP
            avg = per_plant[crop]
            for a, cnt in ages.items():
                a = int(a)
                if a >= fy:
                    pass
                wip_book += cnt * seed
                wip_econ += cnt * avg * P[crop]
            # yield_units of one-time crops are inside the WIP estimate (avg realized units per plant); do not double count
    liquid = sum(v * P.get(k, 0) for k, v in goods.items() if k in P)
    seeds = sum(v * CROPS[k][0] for k, v in s.get('seeds', {}).items() if k in CROPS)
    # capital: animals alive now, assume the most recent purchases survive
    an_p, land_p = purchases(x, side)
    book_an = 0.0; econ_an = 0.0
    for k, (cost, prod, fy) in AN.items():
        n = s['an'].get(k, [0, 0])[0]
        bought = sorted([d for d, kk in an_p if kk == k and d < D], reverse=True)
        for i in range(n):
            d0 = bought[i] if i < len(bought) else 0
            book_an += cost * max(0, 30 - D) / max(1, 30 - d0)
            first_day = max(D, d0 + fy)
            days = max(0, 29 - first_day)
            econ_an += rate[k] * days * P[prod] - (29 - D) * P['WHEAT']
    book_land = 0.0
    for d0, v in land_p:
        if d0 < D: book_land += v * max(0, 30 - D) / max(1, 30 - d0)
    L = C + liquid
    return dict(C=C, L=L, B=L + book_an + book_land + wip_book + seeds, E=L + econ_an + wip_econ + seeds)


def main():
    paths = sys.argv[1]; team = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'ALL'
    rows = load(paths, team)
    rate, per_plant = pooled_rates(rows)
    print('%d seats; pooled animal output/day %s; realized units per planted plant %s' % (
        len(rows), {k: round(v, 2) for k, v in rate.items()}, {k: round(v, 2) for k, v in per_plant.items()}))
    DAYS = [1, 3, 6, 9, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    gap = {k: collections.defaultdict(list) for k in 'CLBE'}
    for x in rows:
        for D in DAYS:
            P = {p: fut_price(x, min(D, 29), p) for p in PRODS}
            vu = value(x, 'days_us', D, rate, per_plant, P); ve = value(x, 'days_elite', D, rate, per_plant, P)
            for k in 'CLBE': gap[k][D].append(vu[k] - ve[k])
    n = len(rows)
    fm = st.mean(x['m'] for x in rows)
    print('final margin us-elite: mean %+.0f  (wins %d/%d)' % (fm, sum(x['m'] > 0 for x in rows), n))
    print('day | cash gap | liquid gap | book gap | econ gap   (mean us - elite at the start of the day; share of the final gap)')
    for D in DAYS:
        g = {k: st.mean(gap[k][D]) for k in 'CLBE'}
        se = {k: st.pstdev(gap[k][D]) / math.sqrt(n) for k in 'CLBE'}
        print('%3d | %+7.0f (%3.0f%%) | %+7.0f (%3.0f%%) | %+7.0f (%3.0f%%) | %+7.0f +-%4.0f (%3.0f%%)' % (
            D, g['C'], 100 * g['C'] / fm, g['L'], 100 * g['L'] / fm, g['B'], 100 * g['B'] / fm, g['E'], se['E'], 100 * g['E'] / fm))


if __name__ == '__main__':
    main()


WIN = [(0, 6), (6, 12), (12, 16), (16, 22), (22, 30)]


def flows(rows, label=''):
    """mean per seat: cash flow by category and window, us, elite, gap."""
    cats = ['S$' + p for p in PRODS] + ['B$WHEAT', 'B$FERTILIZER', 'seed', 'anim', 'land$', 'hire$']
    tab = {side: {w: collections.Counter() for w in WIN} for side in ('days_us', 'days_elite')}
    for x in rows:
        for side in tab:
            for w in WIN:
                for D in range(*w):
                    f = x[side][D]['f']
                    for k, v in f.items():
                        if k.startswith('seed$'): tab[side][w]['seed'] -= v
                        elif k.startswith('anim$'): tab[side][w]['anim'] -= v
                        elif k.startswith('B$'): tab[side][w][k] -= v
                        elif k in ('land$', 'hire$'): tab[side][w][k] -= v
                        elif k.startswith('S$'): tab[side][w][k] += v
    n = len(rows)
    print('\n== cash flow gap us - elite per seat, by window %s' % label)
    print('%-14s' % 'category' + ''.join('%11s' % ('d%d-%d' % (a, b - 1)) for a, b in WIN) + '%11s' % 'total')
    tot = collections.Counter()
    for c in cats:
        vals = [(tab['days_us'][w][c] - tab['days_elite'][w][c]) / n for w in WIN]
        if max(abs(v) for v in vals) < 50: continue
        print('%-14s' % c.replace('S$', '') + ''.join('%+11.0f' % v for v in vals) + '%+11.0f' % sum(vals))
        for w, v in zip(WIN, vals): tot[w] += v
    allv = [sum((tab['days_us'][w][c] - tab['days_elite'][w][c]) for c in set(tab['days_us'][w]) | set(tab['days_elite'][w])) / n for w in WIN]
    print('%-14s' % 'NET (all)' + ''.join('%+11.0f' % v for v in allv) + '%+11.0f' % sum(allv))
    print('%-14s' % 'us revenue' + ''.join('%11.0f' % (sum(v for k, v in tab['days_us'][w].items() if k.startswith('S$')) / n) for w in WIN))
    print('%-14s' % 'elite revenue' + ''.join('%11.0f' % (sum(v for k, v in tab['days_elite'][w].items() if k.startswith('S$')) / n) for w in WIN))


def capacity(rows, days=(3, 6, 9, 12, 16, 20, 24, 28)):
    n = len(rows)
    print('\n== farm at the start of the day (mean per seat): us / elite')
    print('day  quads    cows       sheep      geese      | wheat     carrot    tomato    straw     melon    | empty+weed  hands(prev day) hires$(prev)')
    for D in days:
        out = []
        for side in ('days_us', 'days_elite'):
            c = collections.Counter()
            for x in rows:
                s = x[side][D]['s']; fprev = x[side][D - 1]['f']
                c['q'] += len(s['quads'])
                for k in AN: c[k] += s['an'].get(k, [0, 0])[0]
                for k in CROPS: c[k] += s['pl'].get(k, [0, 0])[0]
                tiles_used = sum(v[0] for v in s['an'].values()) + sum(v[0] for v in s['pl'].values())
                c['free'] += 25 * len(s['quads']) - tiles_used - 0
                c['hands'] += fprev.get('maxhands', 0); c['hire$'] += fprev.get('hire$', 0)
            out.append({k: v / n for k, v in c.items()})
        u, e = out
        print('%3d  %.2f/%.2f  %4.1f/%4.1f  %4.1f/%4.1f  %4.1f/%4.1f  | %4.1f/%4.1f %4.1f/%4.1f %4.1f/%4.1f %4.1f/%4.1f %4.1f/%4.1f | %5.1f/%5.1f  %4.1f/%4.1f  %5.0f/%5.0f' % (
            D, u['q'], e['q'], u['COW'], e['COW'], u['SHEEP'], e['SHEEP'], u['GOOSE'], e['GOOSE'], u['WHEAT'], e['WHEAT'],
            u['CARROT'], e['CARROT'], u['TOMATO'], e['TOMATO'], u['STRAWBERRY'], e['STRAWBERRY'], u['MELON'], e['MELON'],
            u['free'], e['free'], u['hands'], e['hands'], u['hire$'], e['hire$']))


def work(rows, wins=WIN):
    n = len(rows)
    keys = ['plant_WHEAT', 'plant_CARROT', 'plant_TOMATO', 'plant_STRAWBERRY', 'plant_MELON', 'water', 'op_FERTILIZE', 'op_FEED', 'op_CARE',
            'op_COLLECT_FERTILIZER', 'hv_WHEAT', 'hvn_WHEAT', 'hv_EGG', 'hv_MILK', 'hv_WOOL', 'hv_TOMATO', 'hv_STRAWBERRY', 'hv_CARROT',
            'hire_n', 'op_move', 'op_pass', 'op_fail', 'Bu' + 'WHEAT', 'Su' + 'WHEAT']
    print('\n== work and output per seat by window: us / elite')
    print('%-20s' % 'item' + ''.join('%16s' % ('d%d-%d' % (a, b - 1)) for a, b in wins))
    for k in keys:
        vals = []
        for w in wins:
            u = sum(x['days_us'][D]['f'].get(k, 0) for x in rows for D in range(*w)) / n
            e = sum(x['days_elite'][D]['f'].get(k, 0) for x in rows for D in range(*w)) / n
            vals.append('%7.1f/%-8.1f' % (u, e))
        print('%-20s' % k + ''.join('%16s' % v for v in vals))


if __name__ == '__main__' and '--more' in sys.argv:
    rows = load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'ALL')
    flows(rows); capacity(rows); work(rows)


def goods(rows, days=(12, 14, 16, 18, 22)):
    n = len(rows)
    print('\n== goods held at the start of the day (shed + carried + on animals + on ongoing plants), units per seat: us / elite')
    for D in days:
        cu = collections.Counter(); ce = collections.Counter()
        for x in rows:
            for side, c in (('days_us', cu), ('days_elite', ce)):
                s = x[side][D]['s']
                for k, v in s['shed'].items(): c[k] += v
                for k, v in s.get('inv', {}).items(): c[k] += v
                for k, (a, u) in s['an'].items(): c[AN[k][1]] += u
                for k, (a, u) in s['pl'].items():
                    if CROPS[k][3]: c[k] += u
        print('%3d ' % D + ' '.join('%s %.0f/%.0f' % (k[:5], cu[k] / n, ce[k] / n) for k in PRODS if cu[k] + ce[k] > 0.5 * n)
              + '   seeds us %s' % {k: round(v / n, 1) for k, v in sum((collections.Counter(x['days_us'][D]['s'].get('seeds', {})) for x in rows), collections.Counter()).items()}
              + ' elite %s' % {k: round(v / n, 1) for k, v in sum((collections.Counter(x['days_elite'][D]['s'].get('seeds', {})) for x in rows), collections.Counter()).items()})


if __name__ == '__main__' and '--goods' in sys.argv:
    goods(load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'ALL'))


def decisions(rows):
    n = len(rows)
    print('\n== tape-phase decisions (per seat): us / elite')
    for side in ('days_us', 'days_elite'):
        ld = collections.defaultdict(list)
        for x in rows:
            k = 0
            for D in range(30):
                v = x[side][D]['f'].get('land$', 0)
                while v > 0 and k < 3:
                    ld[['NE', 'SW', 'SE'][k]].append(D); v -= LAND[k]; k += 1
            for q in ('NE', 'SW', 'SE'):
                if len(ld[q]) < len([1 for _ in ld[q]]): pass
        print(side, ' '.join('%s: %d%% bought, mean day %.1f (q25 %s, median %s)' % (
            q, 100 * len(v) / n, st.mean(v) if v else -1, sorted(v)[len(v) // 4] if v else '-', sorted(v)[len(v) // 2] if v else '-') for q, v in ld.items()))
    for w in WIN:
        cu = collections.Counter(); ce = collections.Counter()
        for x in rows:
            for side, c in (('days_us', cu), ('days_elite', ce)):
                for D in range(*w):
                    f = x[side][D]['f']
                    for k, v in f.items():
                        if k.startswith('animu'): c[k[5:]] += v
                        if k.startswith('seed$'): c['seed$'] += v
                        if k == 'hire$': c['hire$'] += v
                        if k == 'hire_n': c['hires'] += v
        print('days %2d-%2d animals bought: us %s elite %s | seeds $ %.0f/%.0f | hires %.1f/%.1f ($%.0f/$%.0f)' % (
            w[0], w[1] - 1, {k: round(cu[k] / n, 1) for k in AN}, {k: round(ce[k] / n, 1) for k in AN},
            cu['seed$'] / n, ce['seed$'] / n, cu['hires'] / n, ce['hires'] / n, cu['hire$'] / n, ce['hire$'] / n))


def predict(rows):
    """how well the state gap at day D predicts the final margin (OLS slope, R^2) and the mean remaining gap."""
    rate, per_plant = pooled_rates(rows)
    print('\n== final margin vs the gap at day D (per seat): slope, R^2, mean(final - gap(D)) = what happens after D')
    for D in (6, 12, 16, 18, 22, 26):
        for k in 'CLB':
            xs = []; ys = []
            for x in rows:
                P = {p: fut_price(x, D, p) for p in PRODS}
                g = value(x, 'days_us', D, rate, per_plant, P)[k] - value(x, 'days_elite', D, rate, per_plant, P)[k]
                xs.append(g); ys.append(x['m'])
            mx, my = st.mean(xs), st.mean(ys)
            sxx = sum((a - mx) ** 2 for a in xs); sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys)); syy = sum((b - my) ** 2 for b in ys)
            b = sxy / sxx if sxx else 0; r2 = sxy * sxy / (sxx * syy) if sxx and syy else 0
            after = [b_ - a for a, b_ in zip(xs, ys)]
            print('D %2d %s: gap %+6.0f  slope %.2f  R2 %.2f  after-D %+6.0f +- %4.0f' % (D, k, mx, b, r2, st.mean(after), st.pstdev(after) / math.sqrt(len(after))), end='   ')
        print()


if __name__ == '__main__' and '--dec' in sys.argv:
    rr = load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else 'ALL')
    decisions(rr); predict(rr)
