"""Most common day-0 herd and purchase sequences (days 1-11) per team; per-seat cash rule checks."""
import collections
from lib import *

rows = load(role={'rec', 'ours'})
G = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and late(r):
        G[SHORT[r['team']]].append(r)
    elif r['role'] == 'ours':
        G['T7'].append(r)
for g in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    rs = G[g]
    n = len(rs)
    c0 = collections.Counter('%dC%dS%dG' % (nbuy(r['days'][0], 'COW'), nbuy(r['days'][0], 'SHEEP'), nbuy(r['days'][0], 'GOOSE')) for r in rs)
    print('=====', g, n, 'day0 herd:', ', '.join('%s %.0f%%' % (k, 100 * v / n) for k, v in c0.most_common(4)))
    seqs = collections.Counter()
    for r in rs:
        s = []
        for d in range(1, 12):
            b = ''.join('%s%d' % (a[0], nbuy(r['days'][d], a)) for a in AN if nbuy(r['days'][d], a))
            if b:
                s.append('d%d:%s' % (d, b))
        seqs[' '.join(s)] += 1
    for k, v in seqs.most_common(6):
        print('  %4.0f%%  %s' % (100 * v / n, k))
    print('  distinct sequences: %d' % len(seqs))
