"""Perfect-label reconstruction gate for the BC codec. For each recorded game, the teacher seat plays every action
passed through encode -> decode (bc_codec.roundtrip) while the opponent replays its recorded tape. A lossless codec
reproduces the recorded final rewards exactly. Reports per game: exact or not, reward deltas, and the first step where
the teacher's money diverges from the original replay.
usage: bc_gate.py games.jsonl "DSM|Vadim Vasilenko" [max_games]"""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean
import bc_codec

src, teams = sys.argv[1], sys.argv[2].split('|')
maxg = int(sys.argv[3]) if len(sys.argv) > 3 else 20
done = 0; exact = 0; rows = []
for line in open(src, encoding='utf-8'):
    d = json.loads(line)
    names = d['info']['TeamNames']
    seats = [i for i, n in enumerate(names) if n in teams]
    if not seats:
        continue
    done += 1
    if done > maxg:
        break
    acts = d['acts']
    money_ref = {}

    def tape(p, codec, log):
        def f(obs, cfg=None):
            t = obs['step']
            log[t] = obs['farms'][p]['money']
            a = acts[t + 1][p] if t + 1 < len(acts) else None
            a = a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
            if codec:
                invs = obs['private'].get('inventories') or []
                a = bc_codec.roundtrip(a, invs)
            return a
        return f
    ref = {}
    r0 = lean.play(None, None, d['info']['seed'], agent_objs=[tape(0, False, ref), tape(1, False, {})])
    for p in seats:
        log = {}
        ag = [tape(0, p == 0, log if p == 0 else {}), tape(1, p == 1, log if p == 1 else {})]
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        ok = [int(v) for v in r['r']] == [int(v) for v in d['rewards']]
        refm = {}
        lean.play(None, None, d['info']['seed'], agent_objs=[tape(0, False, refm if p == 0 else {}), tape(1, False, refm if p == 1 else {})])
        first = next((t for t in sorted(log) if abs(log[t] - refm.get(t, log[t])) > 0.5), None)
        exact += int(ok)
        rows.append((d['id'], names[p], ok, int(r['r'][p] - d['rewards'][p]), first))
        print(d['id'], names[p][:16], 'EXACT' if ok else 'DIFF', 'reward delta', int(r['r'][p] - d['rewards'][p]), 'first money divergence at step', first, flush=True)
print('teacher seasons', len(rows), 'exactly reproduced', exact)
