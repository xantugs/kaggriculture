"""T7 herd variants (days 1-11 purchase sequence) vs shops known on days 6 and 9."""
import collections
from lib import *
rows = load(role={'ours'})
V = collections.defaultdict(list)
for r in rows:
    s = []
    for d in range(1, 12):
        b = ''.join('%s%d' % (a[0], nbuy(r['days'][d], a)) for a in AN if nbuy(r['days'][d], a))
        if b:
            s.append('d%d:%s' % (d, b))
    V[' '.join(s)].append(r)
ab = {'YARN_STORE': 'Y', 'BAKERY': 'Bk', 'BRUNCH_SPOT': 'Br', 'PIZZA_SHOP': 'Pz', 'ICE_CREAM_SHOP': 'Ic', 'SMOOTHIE_SHOP': 'Sm', 'PET_CAFE': 'Pc', 'FARMERS_MARKET': 'Fm'}
for k, rs in sorted(V.items(), key=lambda kv: -len(kv[1])):
    print('%3d  %s' % (len(rs), k))
    c = collections.Counter(','.join(ab[s] for s in r['days'][9]['shops']) for r in rs)
    print('      shops@d9: ' + '  '.join('%s:%d' % kv for kv in c.most_common(12)))
