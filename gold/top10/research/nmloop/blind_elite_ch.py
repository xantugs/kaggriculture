"""blind_elite_ch.py GID SEAT LABEL OUT SEEDS : like blind_elite.py, but the top-team recording runs through our Chassis tape runner
(repair layers: hand_align, weed_repair, sell_lead, budget_guard, room_guard, clamp_sells, dead_stock, terminal_liquidation) - the
same machinery that plays our T8 tapes in any town. Row margin m is from CAND's side."""
import sys, os, json, gzip
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness'))
import lean
gid, seat, label, out, seeds = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
a_, b_ = seeds.split('-')
rec = None
with gzip.open('gold/top10/gates/fresh29_games.jsonl.gz', 'rt', encoding='utf-8') as fh:
    for l in fh:
        r = json.loads(l)
        if r['id'] == gid: rec = r; break
PASS = {"farmer": ["PASS"], "hands": [], "market": []}
tape = []
for t in range(720):
    a = rec['acts'][t + 1][seat] if t + 1 < len(rec['acts']) and isinstance(rec['acts'][t + 1], list) and len(rec['acts'][t + 1]) > seat else None
    tape.append(a if isinstance(a, dict) else dict(PASS))
with open(out, 'w', encoding='utf-8') as fo:
    for s in range(int(a_), int(b_) + 1):
        for cg in (0, 1):
            H = lean.load('gold/final/c2tr_final.py'); ch = H.__globals__['Chassis']({'elite': tape}, None, {'front_run': False})
            elite = lambda obs, cfg=None, ch=ch: ch.act(obs, cfg)
            me = lean.load(os.environ.get("CAND", "gold/final/CGt_final.py"))
            objs = [me, elite] if cg == 0 else [elite, me]
            r = lean.play(None, None, s, agent_objs=objs)
            fo.write(json.dumps(dict(label=label, gid=gid, seat=seat, seed=s, cgt_seat=cg, cgt=r['r'][cg], tape=r['r'][1 - cg], m=r['r'][cg] - r['r'][1 - cg], err=r['err'])) + '\n'); fo.flush()
