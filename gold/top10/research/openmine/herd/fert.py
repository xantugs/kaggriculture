"""Fertilizer balance per seat, days 0-9 and 10-15: collected (COLLECT ops), sold units/$, bought units/$, used (FERTILIZE ops)."""
import collections
from lib import *
rows = load(role={'rec', 'ours'})
G = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and late(r) and not boey_old(r):
        G[SHORT[r['team']]].append(r)
    elif r['role'] == 'ours':
        G['T7'].append(r)
for g in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    s = []
    for a0, a1 in ((0, 9), (10, 15)):
        rs = G[g]
        col = mean(sum(sum(r['days'][d]['coll'].values()) for d in range(a0, a1 + 1)) for r in rs)
        su = mean(sum((r['days'][d]['sell'].get('FERTILIZER') or [0, 0])[0] for d in range(a0, a1 + 1)) for r in rs)
        sd = mean(sum((r['days'][d]['sell'].get('FERTILIZER') or [0, 0])[1] for d in range(a0, a1 + 1)) for r in rs)
        bu = mean(sum((r['days'][d]['bp'].get('FERTILIZER') or [0, 0])[0] for d in range(a0, a1 + 1)) for r in rs)
        bd = mean(sum((r['days'][d]['bp'].get('FERTILIZER') or [0, 0])[1] for d in range(a0, a1 + 1)) for r in rs)
        fo = mean(sum(r['days'][d]['fert_ops'] for d in range(a0, a1 + 1)) for r in rs)
        s.append('d%d-%d collect %5.1f sold %5.1f ($%5.0f) bought %5.1f ($%5.0f) FERTILIZE %5.1f net $%5.0f' % (a0, a1, col, su, sd, bu, bd, fo, sd - bd))
    print('%-5s ' % g + ' | '.join(s))
