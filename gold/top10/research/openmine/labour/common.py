"""Shared loaders for the labour study (reads labour/rows.pkl built by compact.py)."""
import os, pickle, collections, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
SHORT = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', 'THIRD FARM CLUB': 'TFC', '吃白饭的大肥鱼': 'CBF', 'Yizhou': 'Yiz', 'T7': 'T7'}
TEAMS = ['FQ', 'Boey', 'TFC', 'CBF', 'Yiz']
LATE = ('2026-09-23', '2026-09-24', '2026-09-25', '2026-09-26')


def load(dates=LATE):
    with open(os.path.join(HERE, 'rows.pkl'), 'rb') as fh:
        D = pickle.load(fh)
    rec = [r for r in D['rec'] if (dates is None or r['date'] in dates)]
    return rec, D['ours'], D['rep']


def by_seat(rows):
    S = collections.defaultdict(dict)
    for r in rows:
        S[(r['gid'], r['seat'])][r['d']] = r
    return S


def team_of(r):
    if r['role'] == 'ours':
        return 'T7'
    return SHORT.get(r['team'], r['team'])


VCAT = {'WATER': 'water', 'HARVEST': 'harv', 'FEED': 'feed', 'CARE': 'care', 'COLLECT_FERTILIZER': 'cfert',
        'PLANT': 'plant', 'FERTILIZE': 'fertz', 'PICKUP': 'pick', 'DROP': 'drop', 'BUILD_COOP': 'build',
        'BUILD_PASTURE': 'build', 'DIG': 'dig'}


def verbcats(ops):
    c = collections.Counter()
    for k, v in (ops or {}).items():
        verb = k.split('@')[0].split(':')[0]
        if verb == 'PLACE':
            c['drop' if ':shed:' in k or k.startswith('PLACE:shed') else 'place'] += v
        else:
            c[VCAT.get(verb, verb)] += v
    return c


def labour(r):
    """unit-turns, effective, moves, idle (pass/noact/fail/unsent) for a day row (detail rows only)."""
    hh = r.get('hands_h') or [0] * 24
    ut = 24 + sum(hh)
    eff = sum((r.get('ops') or {}).values())
    fail = sum((r.get('fail') or {}).values())
    mv = r.get('move') or 0
    pas = (r.get('pas') or 0) + (r.get('noact') or 0)
    unsent = ut - eff - fail - mv - pas
    return dict(ut=ut, hturns=sum(hh), eff=eff, move=mv, pas=pas, fail=fail, unsent=unsent,
                idle=pas + fail + max(0, unsent))


def ntiles(r):
    return sum((r.get('crops') or {}).values())


def nanim(r):
    return sum((r.get('herd') or {}).values())


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float('nan')


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else float('nan')


def fib_sum(n):
    a, b, s = 1, 1, 0
    for _ in range(n):
        s += a; a, b = b, a + b
    return s


def lstsq(X, y):
    """Plain least squares via normal equations (no numpy in the venv)."""
    k = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(k)] for i in range(k)]
    b = [sum(r[i] * v for r, v in zip(X, y)) for i in range(k)]
    for i in range(k):
        A[i][i] += 1e-9
    for c in range(k):
        p = max(range(c, k), key=lambda i: abs(A[i][c]))
        A[c], A[p] = A[p], A[c]; b[c], b[p] = b[p], b[c]
        for i in range(k):
            if i != c and A[c][c]:
                f = A[i][c] / A[c][c]
                for j in range(c, k): A[i][j] -= f * A[c][j]
                b[i] -= f * b[c]
    return [b[i] / A[i][i] for i in range(k)]


def predict(X, beta):
    return [sum(a * c for a, c in zip(r, beta)) for r in X]


def r2(y, p):
    m = sum(y) / len(y)
    return 1 - sum((a - b) ** 2 for a, b in zip(y, p)) / sum((a - m) ** 2 for a in y)
