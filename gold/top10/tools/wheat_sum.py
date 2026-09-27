"""Summarise wheat_diag.py rows: per side, days d0..d1 (default 16-28), means per seat.
usage: wheat_sum.py rows.jsonl[,more] [d0] [d1] [by_team]"""
import sys, json, collections
files = sys.argv[1].split(','); d0 = int(sys.argv[2]) if len(sys.argv) > 2 else 16; d1 = int(sys.argv[3]) if len(sys.argv) > 3 else 28
by_team = len(sys.argv) > 4
rows = [json.loads(l) for f in files for l in open(f, encoding='utf-8')]


def side(days):
    o = collections.Counter(); ages = {c: collections.Counter() for c in ('WHEAT', 'CARROT')}
    for d in range(d0, d1 + 1):
        r = days[d]
        for k, v in r['plant'].items():
            c, q = k.split('@'); o['pl_' + c] += v; o['plq_%s_%s' % (c, q)] += v
        for c, hs in r['harv'].items():
            o['hv_' + c] += len(hs); o['hu_' + c] += sum(h[1] for h in hs); o['hf_' + c] += sum(h[2] for h in hs)
            if c in ages:
                for h in hs: ages[c][h[0]] += 1
        for c, n in r['water'].items(): o['wa_' + c] += n
        for c, n in r['fert'].items(): o['fe_' + c] += n
        o['hires'] += r['hires']; o['hire$'] += r['hire_cost']; o['acts'] += r['acts']; o['usteps'] += r['units']
        for c, n in r['sold'].items(): o['su_' + c] += n
        for c, n in r['sold_d'].items(): o['s$_' + c] += n
        for c, n in r['bought'].items(): o['bu_' + c] += n
        for c, n in r['tiles'].items(): o['ti_' + c] += n
    land = {}
    for d, r in enumerate(days):
        for q in r['land']: land[q] = d
    return o, ages, land


def report(label, R):
    n = len(R)
    if not n: return
    print('=== %s  (%d seats, days %d-%d, per seat)' % (label, n, d0, d1))
    nd = d1 - d0 + 1
    for who in ('elite', 'other'):
        tot = collections.Counter(); ag = {c: collections.Counter() for c in ('WHEAT', 'CARROT')}; lands = collections.defaultdict(list)
        for x in R:
            o, a, land = side(x[who])
            tot.update(o)
            for c in ag: ag[c].update(a[c])
            for q in ('NE', 'SW', 'SE'):
                lands[q].append(land.get(q))
        f = lambda k: tot[k] / n
        name = who if who == 'elite' else ('us' if 'cand' in R[0] else 'opp')
        print(' %-5s wheat: plant %5.1f harv %5.1f units/harv %.2f fert%% %3.0f  sold %5.0f u $%6.0f  bought %4.0f | tiles/day %4.1f' % (
            name, f('pl_WHEAT'), f('hv_WHEAT'), tot['hu_WHEAT'] / max(1, tot['hv_WHEAT']), 100 * tot['hf_WHEAT'] / max(1, tot['hv_WHEAT']),
            f('su_WHEAT'), f('s$_WHEAT'), f('bu_WHEAT'), f('ti_WHEAT') / nd))
        print('       carrot: plant %5.1f harv %5.1f units/harv %.2f fert%% %3.0f  sold %5.0f u $%6.0f | tiles/day %4.1f   tomato tiles %4.1f straw %4.1f' % (
            f('pl_CARROT'), f('hv_CARROT'), tot['hu_CARROT'] / max(1, tot['hv_CARROT']), 100 * tot['hf_CARROT'] / max(1, tot['hv_CARROT']),
            f('su_CARROT'), f('s$_CARROT'), f('ti_CARROT') / nd, f('ti_TOMATO') / nd, f('ti_STRAWBERRY') / nd))
        for c in ('WHEAT', 'CARROT'):
            s = sum(ag[c].values()) or 1
            print('       %-6s harvest ages: %s' % (c, '  '.join('%d:%.0f%%' % (k, 100 * v / s) for k, v in sorted(ag[c].items()))))
        print('       hands/day %.2f (hires %.1f/day, $%.0f/day)  acts/day %.0f  water/day W %.1f C %.1f  fert/day W %.1f C %.1f' % (
            f('usteps') / nd / 24, f('hires') / nd, f('hire$') / nd, f('acts') / nd, f('wa_WHEAT') / nd, f('wa_CARROT') / nd, f('fe_WHEAT') / nd, f('fe_CARROT') / nd))
        qs = collections.Counter()
        for k, v in tot.items():
            if k.startswith('plq_WHEAT'): qs[k[10:]] += v
        print('       wheat plantings by quadrant: %s' % ' '.join('%s %.1f' % (q, qs[q] / n) for q in ('NW', 'NE', 'SW', 'SE')))
        for q in ('NE', 'SW', 'SE'):
            ds = [d for d in lands[q] if d is not None]
            print('       land %s: %3.0f%% of seats, day mean %.1f  (%s)' % (q, 100 * len(ds) / n, sum(ds) / max(1, len(ds)),
                  ' '.join('%d:%d' % kv for kv in sorted(collections.Counter(ds).items()))))


report('ALL', rows)
if by_team:
    teams = collections.defaultdict(list)
    for x in rows: teams[x['team']].append(x)
    for t, R in sorted(teams.items(), key=lambda kv: -len(kv[1])): report(t, R)
