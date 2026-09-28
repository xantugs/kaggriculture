"""gsum.py rows1.jsonl[,rows2.jsonl] : standard-gate summary vs T8 by subset (opening winners, herd-first, others), trimmed"""
import sys, os, json, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diag import t8rows, short
T = t8rows()
rows = [json.loads(l) for f in sys.argv[1].split(',') for l in open(f, encoding='utf-8')]
OW = ('FQ', 'Boey', 'TFC', 'CBF', 'Yiz')
HF = ('FQ', 'Boey', 'TFC')
subsets = [('all', lambda t: True), ('opening-winners', lambda t: t in OW), ('herd-first', lambda t: t in HF), ('strawberry-first CBF/Yiz', lambda t: t in ('CBF', 'Yiz')), ('other teams', lambda t: t not in OW)]
for nm, sel in subsets:
    xs = [(r, T[(r['gid'], r['seat'])]) for r in rows if sel(short(r['team']))]
    for tag, ys in (('', xs), (' trim', [(r, b) for r, b in xs if r['tape'] >= 0.6 * b['tape']])):
        if not ys: continue
        d = [r['m'] - b['m'] for r, b in ys]; n = len(d); mu = sum(d) / n
        se = (sum((x - mu) ** 2 for x in d) / max(1, n - 1)) ** 0.5 / n ** 0.5
        riv = collections.Counter()
        for r, b in ys:
            for k in set(r['led_elite']) | set(b['led_elite']):
                if k in ('land',): continue
                riv[k] += (r['led_elite'].get(k, 0) - b['led_elite'].get(k, 0)) / n
        print('%-26s%-5s n %3d  delta %+6.0f +- %5.0f  median %+6.0f  wins %3d -> %3d   rival %+.0f (%s)' % (nm, tag, n, mu, se, statistics.median(d),
              sum(b['m'] > 0 for r, b in ys), sum(r['m'] > 0 for r, b in ys), sum(riv.values()),
              ' '.join('%s %+.0f' % (k[:5], v) for k, v in sorted(riv.items(), key=lambda kv: -abs(kv[1]))[:4])))
