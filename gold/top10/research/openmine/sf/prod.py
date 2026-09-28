"""Product revenue deltas (new - base) for us and the elite, split days 0-16 / 17-29, excluding elite-collapse games.
usage: prod.py base new [team] [collapse_threshold]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
base, new = sys.argv[1], sys.argv[2]
team = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != 'all' else None
thr = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
def gate(t): return {r['gid']: r for r in (json.loads(l) for l in open(os.path.join(HERE, 'out', t + '_gate.jsonl'), encoding='utf-8'))}
def early(t):
    E = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for l in open(os.path.join(HERE, 'out', t + '_days.jsonl'), encoding='utf-8'):
        r = json.loads(l)
        if r['d'] > 16: continue
        side = 'us' if r['role'] == 'ours' else 'el'
        for it, (n, v) in r['sell'].items(): E[r['gid']][side][it] += v
        for it, (n, v) in r['buy_prod'].items(): E[r['gid']][side][it] -= v
    return E
B, N = gate(base), gate(new); EB, EN = early(base), early(new)
keys = [g for g in N if g in B and (team is None or N[g]['team'] == team)]
ok = [g for g in keys if N[g]['tape'] >= thr * N[g]['rec_tape'] and B[g]['tape'] >= thr * B[g]['rec_tape']]
print('games', len(keys), 'non-collapse', len(ok), 'collapsed:', [g for g in keys if g not in ok])
n = len(ok)
print('dm %+.0f  dus %+.0f  del %+.0f  wins %d -> %d' % (sum(N[g]['m'] - B[g]['m'] for g in ok) / n, sum(N[g]['us'] - B[g]['us'] for g in ok) / n,
      sum(N[g]['tape'] - B[g]['tape'] for g in ok) / n, sum(B[g]['m'] > 0 for g in ok), sum(N[g]['m'] > 0 for g in ok)))
for side, lk in (('us', 'led_us'), ('el', 'led_elite')):
    tot = collections.Counter(); ea = collections.Counter()
    for g in ok:
        for it, v in (N[g][lk] or {}).items(): tot[it] += v / n
        for it, v in (B[g][lk] or {}).items(): tot[it] -= v / n
        for it, v in EN[g][side].items(): ea[it] += v / n
        for it, v in EB[g][side].items(): ea[it] -= v / n
    items = sorted(set(tot) | set(ea), key=lambda k: -abs(tot[k]))
    print(side, ' '.join('%s %+.0f(%+.0f/%+.0f)' % (k[:5], tot[k], ea[k], tot[k] - ea[k]) for k in items if abs(tot[k]) > 50))
