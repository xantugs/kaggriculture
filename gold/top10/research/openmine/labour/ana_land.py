"""Labour around the land purchases (NE, SW): hires on the day before / of / after, land hour vs hire hours,
work done in the new quadrant that day (PLANT/BUILD/PLACE @Q) and the next day."""
import collections
from common import *

rec, ours, rep = load()
S = by_seat(rec + ours)
teams = TEAMS + ['T7']
for Q in ('NE', 'SW'):
    print('\n==== land %s' % Q)
    print('team   n  day   hour  cash_bef  hires[d-1,d,d+1]  hires_after_land_h  %%hired_after  plantQ_d buildQ_d placeQ_d  plantQ_d+1 buildQ_d+1 placeQ_d+1  eff_d  h_last_hire')
    for t in teams:
        acc = collections.defaultdict(list)
        for key, days in S.items():
            r0 = days.get(0)
            if r0 is None or team_of(r0) != t: continue
            ev = None
            for d in range(17):
                r = days.get(d)
                if r is None: continue
                for e in r['land'] or []:
                    if e['q'] == Q: ev = (d, e)
            if ev is None: continue
            d, e = ev
            if d + 1 > 16 or d < 1: continue
            r = days[d]; rn = days[d + 1]; rp = days[d - 1]
            acc['day'].append(d); acc['hour'].append(e['h']); acc['cash'].append(e['cash_before'])
            acc['hp'].append(rp['hires']); acc['hd'].append(r['hires']); acc['hn'].append(rn['hires'])
            ha = sum(1 for h in r['hire_h'] if h > e['h'])
            acc['ha'].append(ha); acc['pha'].append(1 if ha > 0 else 0)
            acc['hlast'].append(max(r['hire_h']) if r['hire_h'] else -1)
            for tag, rr in (('d', r), ('n', rn)):
                ops = rr['ops'] or {}
                acc['plant' + tag].append(sum(v for k, v in ops.items() if k.startswith('PLANT') and k.endswith('@' + Q)))
                acc['build' + tag].append(sum(v for k, v in ops.items() if k.startswith('BUILD') and k.endswith('@' + Q)))
                acc['place' + tag].append(sum(v for k, v in ops.items() if k.startswith('PLACE:') and not k.startswith('PLACE:shed') and k.endswith('@' + Q)))
            acc['eff'].append(labour(r)['eff'])
        if not acc['day']: continue
        n = len(acc['day'])
        print('%5s %4d %5.2f %5.1f  %7.0f   %4.1f %4.1f %4.1f      %4.2f              %4.0f%%        %5.1f  %5.1f  %5.1f      %5.1f  %5.1f  %5.1f   %6.1f  %4.1f' % (
            t, n, mean(acc['day']), mean(acc['hour']), mean(acc['cash']), mean(acc['hp']), mean(acc['hd']), mean(acc['hn']),
            mean(acc['ha']), 100 * mean(acc['pha']), mean(acc['plantd']), mean(acc['buildd']), mean(acc['placed']),
            mean(acc['plantn']), mean(acc['buildn']), mean(acc['placen']), mean(acc['eff']), mean(acc['hlast'])))
