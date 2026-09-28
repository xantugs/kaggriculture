"""Goods left at the final snapshot (shed + carried + on animals/ongoing plants + one-time plants' units), us vs elite,
valued at the day-29 realized price of that product in the game. Also wheat balance d22-29.
usage: endstock.py rows.jsonl [...]"""
import sys, json, collections
AN = {'GOOSE': 'EGG', 'COW': 'MILK', 'SHEEP': 'WOOL'}
for p in sys.argv[1:]:
    rows = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    n = len(rows)
    left = {s: collections.Counter() for s in ('days_us', 'days_elite')}
    val = {s: 0.0 for s in left}
    bal = {s: collections.Counter() for s in left}
    for x in rows:
        for s in left:
            st = x[s][30]['s']
            if not st: continue
            c = collections.Counter()
            for k, v in st['shed'].items(): c[k] += v
            for k, v in st.get('inv', {}).items(): c[k] += v
            for k, (a, u) in st['an'].items(): c[AN[k]] += u
            for k, (a, u) in st['pl'].items(): c[k + '(pl)'] += u
            for k, v in c.items():
                left[s][k] += v
                pk = k.replace('(pl)', '')
                su = sum(x[ss][29]['f'].get('Su' + pk, 0) for ss in left); sd = sum(x[ss][29]['f'].get('S$' + pk, 0) for ss in left)
                val[s] += v * (sd / su if su else 0)
            for D in range(22, 30):
                f = x[s][D]['f']
                bal[s]['harvest'] += f.get('hv_WHEAT', 0); bal[s]['bought'] += f.get('BuWHEAT', 0)
                bal[s]['sold'] += f.get('SuWHEAT', 0); bal[s]['feed'] += f.get('op_FEED', 0)
                bal[s]['plant'] += f.get('plant_WHEAT', 0)
            s22 = x[s][22]['s']
            bal[s]['stock22'] += s22['shed'].get('WHEAT', 0) + s22.get('inv', {}).get('WHEAT', 0)
    print('==', p.split('/')[-1], n)
    for s in left:
        print('  %-10s left at end: %s   value ~$%.0f' % (s[5:], {k: round(v / n, 1) for k, v in left[s].most_common() if v / n >= 0.3}, val[s] / n))
        print('  %-10s wheat d22-29 per seat: %s' % (s[5:], {k: round(v / n, 1) for k, v in bal[s].items()}))
