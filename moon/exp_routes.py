"""Route-choice experiment: every chassis route forced from day 6, in every pinned strong-team world.
usage: exp_routes.py sanity | all [out.jsonl]"""
import sys, os, json, re, zlib, base64
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pinmulti


def route_ids():
    src = open(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
    m = re.search(r"_R108_DATA=json.loads\(zlib.decompress\(base64.b85decode\('([^']+)'", src)
    D = json.loads(zlib.decompress(base64.b85decode(m.group(1))))
    return sorted(int(k) for k in D['routes'])


if __name__ == '__main__':
    mode = sys.argv[1]
    games = pinmulti.load_games()
    if mode == 'sanity':
        rs = pinmulti.run(games[:16], 144, [('v12', '../arena/cand/omw_v12.py', {}), ('fr_none', 'fr.py', {'_FR_ROUTE': None}),
                                            ('fr_105', 'fr.py', {'_FR_ROUTE': 105})], 'rt_sanity.jsonl')
        pinmulti.summary(rs)
    else:
        out = sys.argv[2] if len(sys.argv) > 2 else 'rt_all.jsonl'
        variants = [('default', 'fr.py', {'_FR_ROUTE': None})] + [('r%d' % r, 'fr.py', {'_FR_ROUTE': r}) for r in route_ids()]
        rs = pinmulti.run(games, 144, variants, out, chunk=6)
        pinmulti.summary(rs)
