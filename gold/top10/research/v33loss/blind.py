"""blind.py GID SEAT LABEL OUT SEEDS : blind replay of one recorded ladder seat (its 720 recorded actions, no repairs) vs the
frozen CGt on fresh seeds, both seats; one row per game (tape cash, CGt cash, margin from CGt's side)."""
import sys, os, json
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness'))
import lean, pinned4
gid, seat, label, out, seeds = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
a_, b_ = seeds.split('-')
rec = None
for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8'):
    if l.startswith('{'):
        r = json.loads(l)
        if r['id'] == gid: rec = r; break
with open(out, 'w', encoding='utf-8') as fo:
    for s in range(int(a_), int(b_) + 1):
        for cg in (0, 1):
            tape = pinned4._tape(rec['acts'], seat); me = lean.load(os.environ.get("CAND", "gold/final/CGt_final.py"))
            objs = [me, tape] if cg == 0 else [tape, me]
            r = lean.play(None, None, s, agent_objs=objs)
            fo.write(json.dumps(dict(label=label, seed=s, cgt_seat=cg, cgt=r['r'][cg], tape=r['r'][1 - cg], m=r['r'][cg] - r['r'][1 - cg], shops=r.get('shops'), err=r['err'])) + '\n'); fo.flush()
