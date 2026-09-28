"""Cumulative cash statement from day 0 to the elite's SW purchase moment (recorded elite, the 96 T7 games), next to
T7 in the same town up to the same moment. Answers: which flows put $2,000 in the elite's hand at day ~8.3 and not in ours.
Moment = start of the elite's SW hour (fills of that hour counted only if they precede the land fill: approximated by
including same-hour sales and excluding same-hour purchases)."""
import collections
from common import load, SHORT, TEAMS, pairs
from sw_funding import land_event

S = load()
KEYS = ['start', 'fert_net', 'WOOL', 'MILK', 'EGG', 'wheat_net', 'other_sales', 'COW', 'SHEEP', 'GOOSE', 'seed_MELON',
        'seed_STRAW', 'seed_other', 'NE', 'wage', 'cash']


def cat(op, it):
    if op == 'S':
        if it == 'FERTILIZER':
            return 'fert_net'
        if it == 'WHEAT':
            return 'wheat_net'
        return it if it in ('WOOL', 'MILK', 'EGG') else 'other_sales'
    if op == 'BP':
        return 'fert_net' if it == 'FERTILIZER' else 'wheat_net'
    if op == 'BA':
        return it
    if op == 'BS':
        return {'MELON': 'seed_MELON', 'STRAWBERRY': 'seed_STRAW'}.get(it, 'seed_other')
    if op == 'H':
        return 'wage'
    return it  # land quadrant


def statement(s, d_end, h_end):
    c = collections.Counter(start=3000.0)
    for d in range(d_end + 1):
        for h, op, it, n, v in s['days'][d].get('fills') or []:
            if d == d_end and (h > h_end or (h == h_end and op != 'S')):
                continue
            c[cat(op, it)] += v if op == 'S' else -v
    c['cash'] = sum(v for k, v in c.items() if k != 'cash')
    return c


rows = collections.defaultdict(lambda: [collections.Counter(), collections.Counter(), 0])
for t7, e, rep in pairs(S):
    ev = land_event(e, 'SW')
    if not ev:
        continue
    d, h, cb = ev
    a = statement(e, d, h)
    b = statement(t7, d, h)
    R = rows[SHORT[e['team']]]
    R[0].update(a); R[1].update(b); R[2] += 1
    R = rows['ALL']
    R[0].update(a); R[1].update(b); R[2] += 1

print('%-12s' % 'flow' + ''.join('%17s' % ('%s n=%d' % (t, rows[t][2])) for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'ALL']))
print('%-12s' % '' + ''.join('%17s' % 'elite / T7 / diff' for _ in range(6)))
for k in KEYS:
    line = '%-12s' % k
    for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'ALL']:
        A, B, n = rows[t]
        line += '  %5.0f %5.0f %+5.0f' % (A[k] / n, B[k] / n, (A[k] - B[k]) / n)
    print(line)
