"""Decode the chassis route library of lean_sf8.py and list each route's BUY_ANIMAL orders by day (days 0-15), plus which
2-shop patterns map to it (no-yarn patterns use _R108_SHOP_ROUTES, default 100; _V92_TABLE overrides).
usage: tape_herd.py [lean.py]"""
import sys, re, json, zlib, base64, collections, ast
src = open(sys.argv[1] if len(sys.argv) > 1 else 'gold/top10/lean_sf8.py', encoding='utf-8').read()
m = re.search(r"_R108_DATA = json\.loads\(zlib\.decompress\(base64\.b85decode\('([^']+)'\)\)\)", src)
D = json.loads(zlib.decompress(base64.b85decode(m.group(1))))
routes = {int(k): [D['actions'][i] for i in ids] for k, ids in D['routes'].items()}
shop_routes = {tuple(r['shops']): r['route'] for r in D['shops']}
v92 = ast.literal_eval(re.search(r"^_V92_TABLE = (\{.*\})$", src, re.M).group(1))
old = ast.literal_eval(re.search(r"^_R110_OLD_SHOPS = (\{.*\})$", src, re.M).group(1))
SH = ['BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PET_CAFE', 'PIZZA_SHOP', 'SMOOTHIE_SHOP', 'YARN_STORE']
use = collections.defaultdict(list)
for a in SH:
    for b in SH:
        k = (a, b)
        r = shop_routes.get(k, 100) if k.count('YARN_STORE') <= 0 else old.get(k, 0)
        r = v92.get(k, r)
        use[r].append(k)
print('routes used:', {r: len(v) for r, v in use.items()})
for r in sorted(use):
    tape = routes[r]
    buys = collections.defaultdict(collections.Counter); builds = collections.Counter()
    for t, a in enumerate(tape[:16 * 24]):
        if not isinstance(a, dict): continue
        for o in a.get('market') or []:
            if o and o[0] == 'BUY_ANIMAL': buys[t // 24][o[1]] += int(o[2])
        for c in [a.get('farmer')] + (a.get('hands') or []):
            if c and c[0] in ('BUILD_COOP', 'BUILD_PASTURE'): builds[(t // 24, c[0])] += 1
    no_yarn = [k for k in use[r] if 'YARN_STORE' not in k]
    print(f'\nroute {r}: {len(use[r])} patterns ({len(no_yarn)} without yarn), e.g. {use[r][:3]}')
    print('  buys by day: ' + ' '.join(f'd{d}:' + ','.join(f'{k[0]}{v}' for k, v in sorted(c.items())) for d, c in sorted(buys.items())))
    print('  builds: ' + ' '.join(f'd{d}:{k[6:9]}{v}' for (d, k), v in sorted(builds.items())))
