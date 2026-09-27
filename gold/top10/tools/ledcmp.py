"""Paired ledger deltas (us and elite, by product) of a candidate's rows vs base rows, keyed by (gid, seat).
usage: ledcmp.py base.jsonl cand.jsonl [team-split]"""
import sys, json, collections
B = {(r['gid'], r['seat']): r for r in map(json.loads, open(sys.argv[1], encoding='utf-8'))}
C = [json.loads(l) for l in open(sys.argv[2], encoding='utf-8')]
groups = collections.defaultdict(list)
for c in C:
    b = B.get((c['gid'], c['seat']))
    if not b or c.get('m') is None: continue
    groups['ALL'].append((b, c))
    if len(sys.argv) > 3: groups[c['team'][:14]].append((b, c))
for g, ps in sorted(groups.items(), key=lambda kv: (kv[0] != 'ALL', kv[0])):
    n = len(ps); d = [c['m'] - b['m'] for b, c in ps]; md = sum(d) / n
    se = (sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) ** 0.5
    fu = sum(1 for b, c in ps if b['m'] <= 0 < c['m']); fd = sum(1 for b, c in ps if c['m'] <= 0 < b['m'])
    prod = collections.Counter()
    for b, c in ps:
        for side in ('us', 'elite'):
            kb, kc = b['led_' + side], c['led_' + side]
            for k in set(kb) | set(kc): prod[side[:2] + '_' + k] += kc.get(k, 0) - kb.get(k, 0)
    print('%-14s n %3d  %+6.0f +- %4.0f  wins %d -> %d (+%d/-%d)' % (g, n, md, se, sum(b['m'] > 0 for b, c in ps), sum(c['m'] > 0 for b, c in ps), fu, fd))
    print('     ' + ' '.join('%s %+.0f' % (k, v / n) for k, v in sorted(prod.items(), key=lambda kv: -abs(kv[1])) if abs(v / n) >= 40))
