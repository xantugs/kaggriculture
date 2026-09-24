"""Show semantic teacher-vs-roundtrip differences with real inventories near a step. usage: gate_diff.py games.jsonl gid seat_team s0 s1"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, bc_codec
src, gid, team, s0, s1 = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
d = [json.loads(l) for l in open(src, encoding='utf-8') if json.loads(l)['id'] == gid][0]
p = d['info']['TeamNames'].index(team); acts = d['acts']
out = []
def tape(q):
    def f(obs, cfg=None):
        t = obs['step']
        a = acts[t + 1][q] if t + 1 < len(acts) else None
        a = a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        if q == p and s0 <= t <= s1:
            invs = obs['private'].get('inventories') or []
            rt = bc_codec.roundtrip(a, invs)
            ta = [a.get('farmer')] + list(a.get('hands') or [])
            ra = [rt['farmer']] + rt['hands']
            ud = [(k, x, y) for k, (x, y) in enumerate(zip(ta, ra)) if json.dumps(x) != json.dumps(y) and not (x and x[0] == 'PLACE' and x[1] in ('GOOSE', 'COW', 'SHEEP'))]
            if ud or json.dumps(a.get('market') or []) != json.dumps(rt['market']):
                out.append((t, ud, a.get('market'), rt['market'], [dict(i) for i in invs]))
        return a
    return f
lean.play(None, None, d['info']['seed'], agent_objs=[tape(0), tape(1)])
for t, ud, m1, m2, invs in out:
    print('step', t, 'unit diffs', ud)
    if json.dumps(m1) != json.dumps(m2): print('   market teacher', m1); print('   market decoded', m2)
