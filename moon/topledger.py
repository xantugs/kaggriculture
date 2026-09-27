"""Full-game money flows (recorded replays) of us vs opponents in a rank band. usage: topledger.py maxrank"""
import sys, os, json, collections, urllib.request, zipfile, io, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(fn):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand')
    led = [collections.Counter(), collections.Counter()]; units = [collections.Counter(), collections.Counter()]; F = [None, None]
    oc, opm, ohire, oland = K._commit_unit, K._process_market, K._do_hire, K._do_buy_land
    def who(farm): return 0 if farm is F[P] else 1
    def commit(op, it, price, farm, private, market, cap=100):
        ok = oc(op, it, price, farm, private, market, cap)
        if ok:
            w = who(farm)
            if op == 'SELL': led[w][it] += price; units[w][it] += 1
            elif op == 'BUY_PRODUCT': led[w]['buy_' + it] -= price
            elif op == 'BUY_SEED': led[w]['seed_' + it] -= price; units[w]['seed_' + it] += 1
            elif op == 'BUY_ANIMAL': led[w]['anim_' + it] -= price; units[w]['anim_' + it] += 1
        return ok
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; r = ohire(farm, private, bs, mult); led[who(farm)]['hire'] += farm['money'] - m0; return r
    def land(farm, bs):
        m0 = farm['money']; r = oland(farm, bs); led[who(farm)]['land'] += farm['money'] - m0; return r
    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    K._commit_unit, K._process_market, K._do_hire, K._do_buy_land = commit, pm, hire, land
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._process_market, K._do_hire, K._do_buy_land = oc, opm, ohire, oland
    return d['info']['TeamNames'][1 - P], [dict(l) for l in led], [dict(u) for u in units], d['rewards'][P] - d['rewards'][1 - P]
if __name__ == '__main__':
    maxrank = int(sys.argv[1]); minrank = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
    req = urllib.request.Request('https://www.kaggle.com/api/v1/competitions/kaggriculture/leaderboard/download', headers={'Authorization': 'Bearer ' + tok})
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(req, timeout=120).read()))
    rows = list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8')))
    rank = {r['TeamName']: i + 1 for i, r in enumerate(rows)}
    files = []
    for f in json.load(open(os.path.join(HERE, 'g2800_list.json'))):
        d = json.load(open(f, encoding='utf-8'))[0]; n = d['info']['TeamNames']
        if minrank <= rank.get(n[1 - n.index('offhand')], 999) <= maxrank: files.append(f)
    L = [collections.Counter(), collections.Counter()]; U = [collections.Counter(), collections.Counter()]; M = []
    with ProcessPoolExecutor(12) as ex:
        for opp, led, un, m in ex.map(job, files):
            for w in (0, 1): L[w].update(led[w]); U[w].update(un[w])
            M.append(m)
    g = len(files)
    print(f'ranks {minrank}-{maxrank}: games {g}, mean recorded margin {sum(M)/g:+.0f}')
    for k in sorted(set(L[0]) | set(L[1]), key=lambda k: -abs(L[1][k] - L[0][k])):
        print(f'  {k:18s} us {L[0][k]/g:8.0f} ({U[0][k]/g:6.1f})   them {L[1][k]/g:8.0f} ({U[1][k]/g:6.1f})   them-us {(L[1][k]-L[0][k])/g:+7.0f}')
