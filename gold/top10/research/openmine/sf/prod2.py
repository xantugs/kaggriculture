"""Product ledger deltas vs T8 baseline rows file (whole game), per team, for us and elite.
usage: prod2.py base_rows new_tag team"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
B = {(r['gid'], r['seat']): r for r in (json.loads(l) for l in open(sys.argv[1], encoding='utf-8'))}
N = {(r['gid'], r['seat']): r for r in (json.loads(l) for l in open(os.path.join(HERE, 'out', sys.argv[2] + '_gate.jsonl'), encoding='utf-8'))}
team = sys.argv[3]
ks = [k for k in N if k in B and N[k]['team'] == team]
for side in ('led_us', 'led_elite'):
    c = collections.Counter()
    for k in ks:
        for it, v in (N[k][side] or {}).items():
            if it != 'land': c[it] += v / len(ks)
        for it, v in (B[k][side] or {}).items(): c[it] -= v / len(ks)
    print(team, side, ' '.join('%s %+.0f' % (it[:5], v) for it, v in sorted(c.items(), key=lambda x: -abs(x[1])) if abs(v) > 100))
