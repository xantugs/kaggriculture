import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diag import load, short, mean
X = load(sys.argv[1])
T = load(sys.argv[2]) if len(sys.argv) > 2 else None
Tm = {(x['gid'], x['seat']): x for x in T} if T else {}
def land(x, side):
    out = {}
    for D in x[side]:
        for q, h, c in D['land']:
            out[q] = D['d'] + h / 24.0
    return out
for team in ('ALL', 'FQ', 'Boey', 'TFC'):
    xs = [x for x in X if team == 'ALL' or short(x['team']) == team]
    if not xs: continue
    print('== %s (%d seats)' % (team, len(xs)))
    for side in ('ours', 'elite', 'T8'):
        src = xs if side != 'T8' else [Tm[(x['gid'], x['seat'])] for x in xs if (x['gid'], x['seat']) in Tm]
        sd = 'ours' if side in ('ours', 'T8') else 'elite'
        if not src: continue
        L = [land(x, sd) for x in src]
        ld = ' '.join('%s d%.2f(%d%%)' % (q, mean(l[q] for l in L if q in l), 100 * sum(1 for l in L if q in l) / len(L)) for q in ('NE', 'SW', 'SE') if any(q in l for l in L))
        row = []
        for d in (6, 10, 16):
            D = [x[sd][d] for x in src]
            row.append('d%d: $%.0f G%.1f C%.1f S%.1f str%.1f wht%.1f mel%.1f hires%.1f' % (d, mean(v['m0'] for v in D), mean(v['herd'].get('GOOSE', 0) for v in D),
                       mean(v['herd'].get('COW', 0) for v in D), mean(v['herd'].get('SHEEP', 0) for v in D), mean(v['crops'].get('STRAWBERRY', 0) for v in D),
                       mean(v['crops'].get('WHEAT', 0) for v in D), mean(v['crops'].get('MELON', 0) for v in D), mean(v['hires'] for v in D)))
        print('  %-5s land %s' % (side, ld))
        for r in row: print('        ' + r)
