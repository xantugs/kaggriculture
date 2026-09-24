"""List steps where a mirror rival's market orders differ from ours (per game)."""
import json, sys
f, gi = sys.argv[1], int(sys.argv[2]); lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0; hi = int(sys.argv[4]) if len(sys.argv) > 4 else 720
d = json.load(open(f))[gi]; names = d['info']['TeamNames']; P = names.index('Khantugs Gantulga')
acts = d['acts']
def mk(a): return [tuple(o[:3]) for o in (a.get('market') or [])] if isinstance(a, dict) else []
same = diff = 0
for s in range(lo, min(hi, len(acts))):
    u = mk(acts[s][P]); t = mk(acts[s][1 - P])
    if u == t: same += 1; continue
    diff += 1
    print(s, 'd%d h%d' % ((s - 1) // 24, (s - 1) % 24), 'US', u, '| THEM', t)
print('same', same, 'diff', diff, names, d['rewards'])
