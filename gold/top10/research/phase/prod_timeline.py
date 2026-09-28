"""Per-day timeline of one product, us vs elite: units harvested, sold, realized price, units held (plants / shed+carried).
usage: prod_timeline.py rows.jsonl PRODUCT [d0 d1]"""
import sys, json
p, prod = sys.argv[1], sys.argv[2]
d0, d1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (10, 30)
rows = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
n = len(rows)
AN = {'EGG': 'GOOSE', 'MILK': 'COW', 'WOOL': 'SHEEP'}
print(p.split('/')[-1], prod, n, 'seats | per seat: harvested / sold @price / held on plants-animals / in shed+hands (start of day)')
for D in range(d0, d1):
    out = []
    for side in ('days_us', 'days_elite'):
        hv = su = sd = onp = sh = 0
        for x in rows:
            f = x[side][D]['f']; s = x[side][D]['s']
            hv += f.get('hv_' + prod, 0); su += f.get('Su' + prod, 0); sd += f.get('S$' + prod, 0)
            if prod in AN: onp += s['an'].get(AN[prod], [0, 0])[1]
            else: onp += s['pl'].get(prod, [0, 0])[1]
            sh += s['shed'].get(prod, 0) + s.get('inv', {}).get(prod, 0)
        out.append('%5.1f %5.1f@%3.0f %5.1f %5.1f' % (hv / n, su / n, sd / su if su else 0, onp / n, sh / n))
    print('d%2d  us %s  | elite %s' % (D, out[0], out[1]))
