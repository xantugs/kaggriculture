import json, collections, sys
fn = sys.argv[1]; base = sys.argv[2]
R = [json.loads(l) for l in open(fn)]
by = collections.defaultdict(dict)
for r in R: by[(r['opp'], r['seed'], r['seat'])][r['agent']] = r
agents = sorted({r['agent'] for r in R} - {base})
for a in agents:
    for opp in sorted({r['opp'] for r in R}) + ['ALL']:
        d = [(v[a]['m'], v[base]['m'], v[a]['us'] - v[base]['us']) for k, v in by.items() if (opp == 'ALL' or k[0] == opp) and a in v and base in v and v[a]['m'] is not None and v[base]['m'] is not None]
        if not d: continue
        n = len(d); dm = sum(x[0] - x[1] for x in d) / n; du = sum(x[2] for x in d) / n
        w = sum(1 for x in d if x[0] > 0); wb = sum(1 for x in d if x[1] > 0)
        fw = sum(1 for x in d if x[1] <= 0 < x[0]); fl = sum(1 for x in d if x[0] <= 0 < x[1])
        print('%-22s vs %-18s n %3d  margin %+6.0f  money %+6.0f  wins %2d (base %2d)  flips +%d -%d' % (a.split('/')[-1], opp.split('/')[-1], n, dm, du, w, wb, fw, fl))
