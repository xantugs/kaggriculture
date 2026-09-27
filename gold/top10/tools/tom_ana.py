"""Summarise tom_sched.py traces: tomato plantings by day (us vs elite), revenue, price path, by takeover path / demand.
usage: tom_ana.py trace.jsonl [trace2.jsonl]   (second file: paired candidate, compares tomato plantings and m)"""
import sys, json, collections
TS = ('PIZZA_SHOP', 'FARMERS_MARKET')
def tdem(shops, day): return sum(6 for s in shops[:min(8, day // 3)] if s in TS)
R = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
C = {(r['gid'], r['seat']): r for r in map(json.loads, open(sys.argv[2], encoding='utf-8'))} if len(sys.argv) > 2 else {}
def cum(days, d): return sum(x[2] for x in days if x[0] <= d)
def grp(r):
    st = r['gc'].get('gc_start')
    return {288: 'd12', 384: 'd16', 576: 'd24'}.get(st, str(st))
rows = collections.defaultdict(list)
for r in R:
    rows[grp(r)].append(r); rows['ALL'].append(r)
    rows['dem18=%02d' % tdem(r['shops'], 18)].append(r)
print('%-9s %4s | %-35s | %-35s | %-17s | %s' % ('group', 'n', 'us plants cum d11/13/15/16/18/20', 'elite plants cum d11/13/15/16/18/20', 'tom$ us/elite', 'm  win'))
for g in sorted(rows):
    xs = rows[g]; n = len(xs)
    cu = [sum(cum(x['tdays_us'], d) for x in xs) / n for d in (11, 13, 15, 16, 18, 20)]
    ce = [sum(cum(x['tdays_el'], d) for x in xs) / n for d in (11, 13, 15, 16, 18, 20)]
    tu = sum(x['led_us'].get('TOMATO', 0) for x in xs) / n; te = sum(x['led_elite'].get('TOMATO', 0) for x in xs) / n
    print('%-9s %4d | %s | %s | %6.0f / %6.0f | %+6.0f %3.0f%%' % (g, n, ' '.join('%5.1f' % v for v in cu), ' '.join('%5.1f' % v for v in ce), tu, te,
          sum(x['m'] for x in xs) / n, 100 * sum(x['m'] > 0 for x in xs) / n))
# tomato price path (mean) by dem18
print('mean tomato quote at end of day (by dem18):')
for g in sorted(k for k in rows if k.startswith('dem')):
    xs = rows[g]
    px = collections.defaultdict(list)
    for x in xs:
        for dd in x['tdays_us']:
            for e in dd[11:]:
                if isinstance(e, list): px[dd[0]].append(e[0])
        for dd in x['tdays_el']:
            for e in dd[11:]:
                if isinstance(e, list): px[dd[0]].append(e[0])
    print('  %s n %3d  %s' % (g, len(xs), ' '.join('%d:%.0f' % (d, sum(v) / len(v)) for d, v in sorted(px.items()) if d >= 12)))
# per-day units sold
print('tomato units sold per day, us / elite (ALL):')
xs = rows['ALL']; n = len(xs)
print('  ' + ' '.join('%d:%.1f/%.1f' % (d, sum(x['tdays_us'][d][4] for x in xs if len(x['tdays_us']) > d) / n, sum(x['tdays_el'][d][4] for x in xs if len(x['tdays_el']) > d) / n) for d in range(14, 30)))
if C:
    print('paired vs', sys.argv[2])
    by = collections.defaultdict(list)
    for r in R:
        c = C.get((r['gid'], r['seat']))
        if not c: continue
        by[grp(r)].append((r, c)); by['ALL'].append((r, c))
    for g in sorted(by):
        ps = by[g]; n = len(ps)
        d = [c['m'] - r['m'] for r, c in ps]; md = sum(d) / n
        se = (sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) ** 0.5
        tp = sum(cum(c['tdays_us'], 29) - cum(r['tdays_us'], 29) for r, c in ps) / n
        dt = sum(c['led_us'].get('TOMATO', 0) - r['led_us'].get('TOMATO', 0) for r, c in ps) / n
        de = sum(c['led_elite'].get('TOMATO', 0) - r['led_elite'].get('TOMATO', 0) for r, c in ps) / n
        ch = sum(1 for x in d if abs(x) > 0.5)
        w0 = sum(r['m'] > 0 for r, c in ps); w1 = sum(c['m'] > 0 for r, c in ps)
        print('  %-6s n %3d  dm %+6.0f +- %4.0f  wins %d -> %d  changed %d  +tom plants %.1f  our tom$ %+.0f  elite tom$ %+.0f' % (g, n, md, se, w0, w1, ch, tp, dt, de))
        prod = collections.Counter()
        for r, c in ps:
            for k in set(r['led_us']) | set(c['led_us']): prod['us_' + k] += c['led_us'].get(k, 0) - r['led_us'].get(k, 0)
            for k in set(r['led_elite']) | set(c['led_elite']): prod['el_' + k] += c['led_elite'].get(k, 0) - r['led_elite'].get(k, 0)
        print('     ' + ' '.join('%s %+.0f' % (k, v / n) for k, v in sorted(prod.items(), key=lambda kv: -abs(kv[1])) if abs(v / n) >= 30))
