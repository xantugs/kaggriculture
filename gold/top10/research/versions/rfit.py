"""rfit.py ROWS REFS [BANDS] : route oracle analysis + table re-fit with cross-validation.
ROWS: vgate rows of the forced-route variants (file cgt_rNNN.py) and optionally the baseline; REFS: the gate's refs (shops,
money/hands fingerprints, rating). For each game the CURRENT route is what CGt's router would pick (R108/V39/V92 tables,
reproduced here from the loaded module). Reports, per rating band: current wins, best-single-route wins, per-game oracle,
and K-fold cross-validated re-fits of the shop-pair table (and a (pair, rival class) table)."""
import sys, os, json, collections, io, contextlib, random
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'arena'); sys.path.insert(0, 'gold/harness')
rows_path, refs_path = sys.argv[1], sys.argv[2]
bands = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
with contextlib.redirect_stdout(io.StringIO()):
    import lean
    A = lean.load('gold/final/CGt_final.py')
G = A.__globals__
R108, R110, V92 = G['_R108_SHOP_ROUTES'], G['_R110_OLD_SHOPS'], G['_V92_TABLE']


def current_route(shops):
    pair = tuple(shops[:2]); use_new = pair.count('YARN_STORE') <= 0
    r = R108.get(pair, 100) if use_new else R110.get(pair, 0)
    return V92.get(pair, r)


def cls(m, h):
    if h == 0 and 940 <= m <= 980: return 'band'
    for lo, hi in ((540, 720), (2440, 2480)):
        if h == 0 and lo <= m <= hi: return 'C2S3'
    if h == 0 and m >= 2550: return 'chassis'
    if h >= 4 and m < 300: return 'hpoor'
    if (h == 5 and 2200 <= m <= 2500) or (3 <= h <= 5 and 300 <= m <= 1700): return 'hfirst'
    return 'other'


refs = {}
for l in (ln for rp in refs_path.split(',') for ln in open(rp, encoding='utf-8')):
    r = json.loads(l)
    if (r['gid'], r['seat']) in refs and refs[(r['gid'], r['seat'])].get('rating') is not None: continue
    m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
    refs[(r['gid'], r['seat'])] = dict(pair=tuple(r['shops'][:2]), upair=tuple(sorted(r['shops'][:2])), cls=cls(m, h), rating=r.get('rating'), band=r.get('band'), cur=current_route(r['shops']), team=r.get('team'), end=(r.get('end') or '')[:10])
M = collections.defaultdict(dict)   # (gid, seat) -> route -> margin
for l in open(rows_path, encoding='utf-8'):
    x = json.loads(l)
    if x.get('m') is None: continue
    f = os.path.basename(x['file'])
    if f.startswith('cgt_r'):
        M[(x['gid'], x['seat'])][int(f[5:8])] = x['m']
games = [k for k in M if k in refs and refs[k]['cur'] in M[k]]
print('games with the current route scored: %d (rows for %d games)' % (len(games), len(M)))
routes = sorted({r for k in games for r in M[k]})
print('routes:', routes)


def summarize(keys, label):
    if not keys: return
    cur = sum(M[k][refs[k]['cur']] > 0 for k in keys)
    single = max((sum(M[k].get(r, -1e9) > 0 for k in keys), r) for r in routes)
    oracle = sum(max(M[k].values()) > 0 for k in keys)
    print('%-28s n %4d | current route wins %3d (%.0f%%) | best single route %3d (route %d) | per-game oracle %3d' % (label, len(keys), cur, 100 * cur / len(keys), single[0], single[1], oracle))


def fit(train, key):
    """table: key(game) -> best route by (wins, margin) over the training games; None where fewer than MIN games."""
    by = collections.defaultdict(list)
    for k in train: by[key(k)].append(k)
    tab = {}
    for cell, ks in by.items():
        if len(ks) < MIN: continue
        best = max(routes, key=lambda r: (sum(M[k].get(r, -1e9) > 0 for k in ks), sum(max(-20000, min(20000, M[k].get(r, -1e9))) for k in ks)))
        tab[cell] = best
    return tab


def cv(keys, key, label, folds=5, seed=1):
    ks = list(keys)
    teams = sorted({refs[k]['team'] for k in ks}, key=str); random.Random(seed).shuffle(teams)
    fold_of = {t: i % folds for i, t in enumerate(teams)}   # team-grouped folds (a team's games never straddle train/test)
    won_new = won_cur = 0; changed = 0
    for f in range(folds):
        test = [k for k in ks if fold_of[refs[k]['team']] == f]; train = [k for k in ks if fold_of[refs[k]['team']] != f]
        tab = fit(train, key)
        for k in test:
            r = tab.get(key(k), refs[k]['cur'])
            if r not in M[k]: r = refs[k]['cur']
            changed += r != refs[k]['cur']
            won_new += M[k][r] > 0; won_cur += M[k][refs[k]['cur']] > 0
    print('   CV %-22s current %3d -> refit %3d wins of %d (route changed in %d games)' % (label, won_cur, won_new, len(ks), changed))


MIN = 3
allb = sorted({refs[k]['band'] for k in games if refs[k]['band'] is not None})
groups = [('all', games)] + [('band %d' % b, [k for k in games if refs[k]['band'] == b]) for b in (bands or allb)]
for label, keys in groups:
    summarize(keys, label)
    if len(keys) >= 30:
        cv(keys, lambda k: refs[k]['pair'], 'by shop pair')
        cv(keys, lambda k: refs[k]['upair'], 'by unordered pair')
        cv(keys, lambda k: ('yarn' if 'YARN_STORE' in refs[k]['pair'] else 'other'), 'yarn vs non-yarn')
        cv(keys, lambda k: (refs[k]['pair'], refs[k]['cls']), 'by pair + rival class')
        cv(keys, lambda k: refs[k]['cls'], 'by rival class only')
print('\nper-route wins over all games:', ' '.join('r%d:%d' % (r, sum(M[k].get(r, -1e9) > 0 for k in games)) for r in routes))
print('current-route usage:', dict(collections.Counter(refs[k]['cur'] for k in games)))
