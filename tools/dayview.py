import collections, sys
from harness import run_match
seed = int(sys.argv[1]); day = int(sys.argv[2]); path = sys.argv[3] if len(sys.argv) > 3 else "main.py"
env, rew, st = run_match(path, "starter", seed)
for h in (0, 1, 2, 3, 5, 8, 12, 16, 20, 23):
    s = day * 24 + h
    o = env.steps[s][0].observation; a = env.steps[s + 1][0].action; f = o.farms[0]
    shed = {k: v for k, v in o.private["shed"].items() if v}; invs = o.private["inventories"]
    unfed = sum(1 for row in f["tiles"] for t in row if isinstance(t, dict) and t.get("animal") and not t["fed_today"])
    acts = collections.Counter((x[0] if x[0] not in ("NORTH","SOUTH","EAST","WEST") else "MOVE") for x in [a["farmer"]] + a["hands"])
    print(f"h{h:2d} ${f['money']:7.0f} units={1+len(f['hands']):2d} hire={sum(1 for od in a['market'] if od[0]=='HIRE')} unfed={unfed:2d} wheat shed={shed.get('WHEAT',0):3d} carried={sum(i.get('WHEAT',0) for i in invs):3d} cargo={sum(sum(i.values()) for i in invs):3d} shedtot={sum(shed.values()):3d} | {dict(acts)}")
    if h <= 1: print("     mkt:", a["market"])
