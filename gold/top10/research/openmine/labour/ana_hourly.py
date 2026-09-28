"""Hourly labour profile from hourly_elite.jsonl / hourly_ours.jsonl: effective actions per unit-turn by hour block,
when each hand's work starts and ends, and how many hand-turns are left after a hand's last effective action."""
import json, os, collections
from common import HERE, SHORT, TEAMS, mean, med

rows = []
for fn in ('hourly_elite.jsonl', 'hourly_ours.jsonl'):
    p = os.path.join(HERE, fn)
    if os.path.exists(p):
        rows += [json.loads(l) for l in open(p, encoding='utf-8')]
teams = TEAMS + ['T7']
BLK = [(0, 0), (1, 5), (6, 11), (12, 17), (18, 23)]
for lo, hi in ((2, 5), (6, 10), (11, 16)):
    print('\n== days %d-%d: effective actions per unit-turn (%%) by hour block; farmer share of E; hand first/last E hour (median); '
          'hand-turns after last E (%% of hand-turns)' % (lo, hi))
    print('team  n  ' + ''.join('%8s' % ('h%d-%d' % b) for b in BLK) + '   farmerE%  first  last  tail%  hands_with_0E%')
    for t in teams:
        R = [r for r in rows if SHORT.get(r['team'], r['team']) == t]
        if not R: continue
        E = collections.Counter(); U = collections.Counter(); EF = 0; ET = 0
        first = []; last = []; tail = 0; hturns = 0; zero = 0; nh = 0
        for r in R:
            for d in range(lo, hi + 1):
                nhand_h = []
                for h in range(24):
                    c = r['prof'].get('%d_%d' % (d, h), {})
                    for bi, (a, b) in enumerate(BLK):
                        if a <= h <= b:
                            E[bi] += c.get('E', 0); U[bi] += c.get('units', 0)
                    EF += c.get('EF', 0); ET += c.get('E', 0)
                    nhand_h.append(c.get('units', 1) - 1)
                maxh = max(nhand_h)
                for idx in range(1, maxh + 1):
                    # hours this hand existed
                    hrs = [h for h in range(24) if nhand_h[h] >= idx]
                    hturns += len(hrs); nh += 1
                    H = r['hands'].get('%d_%d' % (d, idx))
                    if not H:
                        zero += 1; tail += len(hrs); continue
                    first.append(H[0]); last.append(H[1])
                    tail += sum(1 for h in hrs if h > H[1])
        print('%5s %2d ' % (t, len(R)) + ''.join('%8.0f' % (100 * E[i] / max(1, U[i])) for i in range(len(BLK))) +
              '   %6.0f  %5.1f  %5.1f  %5.1f  %5.1f' % (100 * EF / max(1, ET), med(first), med(last), 100 * tail / max(1, hturns), 100 * zero / max(1, nh)))
