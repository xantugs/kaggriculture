"""Per team x day (0-16): hires, wage, hire hours, hand-turns, effective actions, moves, idle, workload per hand.
usage: ana_days.py [T7pair]   (T7pair: restrict elite rows to the 96 games of the T7 run, recorded elite seat)"""
import sys, collections
from common import *

rec, ours, rep = load()
if len(sys.argv) > 1 and sys.argv[1] == 'T7pair':
    keys = {(r['gid'], r['opp']) for r in ours}
    rec = [r for r in rec if (r['gid'], r['team']) in keys]
rows = rec + ours
G = collections.defaultdict(list)
for r in rows:
    G[(team_of(r), r['d'])].append(r)
nseat = collections.Counter(team_of(r) for r in rows if r['d'] == 0)
print('seats', dict(nseat))
teams = TEAMS + ['T7']


def tab(title, fn, fmt='%6.1f'):
    print('\n' + title)
    print('day ' + ''.join('%7s' % t for t in teams))
    for d in range(17):
        line = '%3d ' % d
        for t in teams:
            rs = G.get((t, d), [])
            v = fn(rs) if rs else float('nan')
            line += ' ' + (fmt % v)
        print(line)


tab('hires (mean)', lambda rs: mean([r['hires'] for r in rs]))
tab('hires (median)', lambda rs: med([r['hires'] for r in rs]))
tab('wage $ (mean)', lambda rs: mean([r['wage'] for r in rs]))
tab('share of hires placed at hour 0 (%)', lambda rs: 100 * sum(h == 0 for r in rs for h in r['hire_h']) / max(1, sum(len(r['hire_h']) for r in rs)))
tab('share of hires placed after hour 2 (%)', lambda rs: 100 * sum(h > 2 for r in rs for h in r['hire_h']) / max(1, sum(len(r['hire_h']) for r in rs)))
tab('hand-turns (sum hands_h)', lambda rs: mean([labour(r)['hturns'] for r in rs]))
tab('effective actions per unit-turn (%)', lambda rs: 100 * sum(labour(r)['eff'] for r in rs) / sum(labour(r)['ut'] for r in rs))
tab('moves per unit-turn (%)', lambda rs: 100 * sum(labour(r)['move'] for r in rs) / sum(labour(r)['ut'] for r in rs))
tab('idle (pass+noop+unsent) per unit-turn (%)', lambda rs: 100 * sum(labour(r)['idle'] for r in rs) / sum(labour(r)['ut'] for r in rs))
tab('effective actions (mean)', lambda rs: mean([labour(r)['eff'] for r in rs]))
tab('crop tiles at h0', lambda rs: mean([ntiles(r) for r in rs]))
tab('animals placed at h0', lambda rs: mean([nanim(r) for r in rs]))
tab('crop tiles per hand (hires>0)', lambda rs: mean([ntiles(r) / r['hires'] for r in rs if r['hires']]))
tab('animals per hand (hires>0)', lambda rs: mean([nanim(r) / r['hires'] for r in rs if r['hires']]))
tab('(tiles + 3*animals) per unit (farmer+hands)', lambda rs: mean([(ntiles(r) + 3 * nanim(r)) / (1 + r['hires']) for r in rs]))
tab('hour-0 cash m0', lambda rs: mean([r['m0'] for r in rs]), '%6.0f')
tab('wage as % of day sells', lambda rs: 100 * sum(r['wage'] for r in rs) / max(1, sum(v[1] for r in rs for v in (r['sell'] or {}).values())))
