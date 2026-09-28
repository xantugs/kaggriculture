"""Per-day hires / wage / marginal hand wage, us vs rival, and the share of the flat-roster excess each day carries.
usage: roster_days.py file.jsonl [...]"""
import sys, json, statistics as st, collections
fib = [1, 1]
while len(fib) < 30: fib.append(fib[-1] + fib[-2])
wage = lambda n: sum(fib[:n])
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p, encoding='utf-8')]
rows = [x for x in rows if x['m'] is not None and len(x['days_us']) >= 29]
oth = 'elite'
print(len(rows), 'seats')
print('day  hires us/riv   $us/$riv   p(us>=12)  p(us>=13)  excess-vs-own-mean$  plantings us/riv  unit-acts us/riv')
for d in range(12, 30):
    hu = [x['days_us'][d]['mkt'].get('hires', 0) if d < 29 else None for x in rows] if d < 29 else None
    if d == 29: break
    he = [x['days_' + oth][d]['mkt'].get('hires', 0) for x in rows]
    cu = [x['days_us'][d]['mkt'].get('hire$', 0) for x in rows]
    ce = [x['days_' + oth][d]['mkt'].get('hire$', 0) for x in rows]
    # excess of this day vs the seat's own flat roster over days 16-28
    exc = []
    for x in rows:
        h = [x['days_us'][k]['mkt'].get('hires', 0) for k in range(16, 29)]
        mean = sum(h) / len(h)
        lo = int(mean); fr = mean - lo
        flat_w = (1 - fr) * wage(lo) + fr * wage(lo + 1)
        exc.append(x['days_us'][d]['mkt'].get('hire$', 0) - flat_w if d >= 16 else 0)
    pl_u = st.mean(sum(x['days_us'][d]['planted'].values()) for x in rows)
    pl_e = st.mean(sum(x['days_' + oth][d]['planted'].values()) for x in rows)
    va = st.mean(sum(v for k, v in x['verbs_us'].get(str(d), {}).items()) for x in rows) if 'verbs_us' in rows[0] else 0
    ve = st.mean(sum(v for k, v in x['verbs_' + oth].get(str(d), {}).items()) for x in rows) if 'verbs_us' in rows[0] else 0
    print(f"{d:3d}  {st.mean(hu):5.1f}/{st.mean(he):5.1f}  {st.mean(cu):5.0f}/{st.mean(ce):5.0f}   {sum(h>=12 for h in hu)/len(hu):5.2f}     {sum(h>=13 for h in hu)/len(hu):5.2f}     {st.mean(exc):+6.0f}            {pl_u:5.1f}/{pl_e:5.1f}      {va:5.0f}/{ve:5.0f}")
