"""Per-day mean hires / wage / harvest units / plots for us vs elite (gate probe output)."""
import sys, json, collections
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p, encoding='utf-8')]
print(len(rows), 'seats')
print(f"{'day':>3} {'h_us':>5} {'h_el':>5} {'w_us':>6} {'w_el':>6} {'hv_us':>6} {'hv_el':>6} {'pl_us':>6} {'pl_el':>6} {'an_us':>5} {'an_el':>5} {'ow_us':>5} {'ow_el':>5}  h>=13 us/el  plant us/el")
for d in range(30):
    a = collections.defaultdict(float)
    for r in rows:
        for side in ('us', 'el'):
            c = r['days_us' if side == 'us' else 'days_elite'].get(str(d), {})
            a['h' + side] += c.get('hire', 0); a['w' + side] += c.get('wage', 0)
            a['hv' + side] += sum(v for k, v in c.items() if k.startswith('hv:'))
            a['pl' + side] += sum(v for k, v in c.items() if k.startswith('c:P:'))
            a['an' + side] += sum(v for k, v in c.items() if k.startswith('c:A:'))
            a['ow' + side] += c.get('c:owned', 0)
            a['big' + side] += c.get('hire', 0) >= 13
            a['pn' + side] += c.get('e:PLANT', 0)
    n = len(rows)
    print(f"{d:3d} {a['hus']/n:5.1f} {a['hel']/n:5.1f} {a['wus']/n:6.0f} {a['wel']/n:6.0f} {a['hvus']/n:6.1f} {a['hvel']/n:6.1f} {a['plus']/n:6.1f} {a['plel']/n:6.1f} {a['anus']/n:5.1f} {a['anel']/n:5.1f} {a['owus']/n:5.1f} {a['owel']/n:5.1f}  {a['bigus']/n:4.2f}/{a['bigel']/n:4.2f}  {a['pnus']/n:5.1f}/{a['pnel']/n:5.1f}")
