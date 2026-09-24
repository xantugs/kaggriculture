"""Mined-route experiment: each mined route (strong opponent that shares our opening) forced from day 6 in every
pinned strong-team world, on top of the full v12 chassis. usage: exp_mined.py mined.json out.jsonl [end_step]"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pinmulti

if __name__ == '__main__':
    mined = json.load(open(sys.argv[1], encoding='utf-8'))
    out = sys.argv[2]
    end = int(sys.argv[3]) if len(sys.argv) > 3 else 648
    routes = {int(k): v for k, v in mined['routes'].items()}
    games = pinmulti.load_games()
    variants = [('default', 'fr2.py', {})]
    for rid, tape in routes.items():
        variants.append(('m%d' % rid, 'fr2.py', {'_MINED': {rid: tape}, '_FR_ROUTE': rid, '_FR_END': end}))
    rs = pinmulti.run(games, 144, variants, out, chunk=6)
    pinmulti.summary(rs)
