"""Build an elite base + controller hybrid and play one game vs a candidate in the recorded town.
usage: hybrid_smoke.py games.jsonl.gz gid seat start_step cand.py ['{gc overrides}']"""
import sys, json, subprocess, os
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
import lean
from eval_elite_routes import install_town, load_games
from transplant import reference_log
from build_elite import build
from kaggle_environments.envs.kaggriculture import kaggriculture as K
path, gid, seat, start, cand = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
over = json.loads(sys.argv[6]) if len(sys.argv) > 6 else {}
over['start'] = start
d = next(g for g in load_games(path) if g['id'] == gid)
base = f'/home/user/kaggriculture/gold/elite/bases/elite_{gid}_{seat}.py'
hyb = f'/home/user/kaggriculture/gold/elite/bases/hyb_{gid}_{seat}_s{start}.py'
ref = build(d, seat, base)
subprocess.run([sys.executable, '/home/user/kaggriculture/gold/build.py', hyb, json.dumps(over), base], check=True, capture_output=True)
orig = install_town(ref['shops'])
try:
    H = lean.load(hyb)
    ag = [None, None]; ag[seat] = H; ag[1 - seat] = lean.load(cand)
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
finally:
    K._end_of_day = orig
tel = dict(getattr(H, 'telemetry', {}) or {})
print(f"{d['info']['TeamNames'][seat]} gid {gid} s{seat} start {start}: hybrid {r['r'][seat]} vs cand {r['r'][1-seat]}  (recorded {d['rewards'][seat]}, plain-transplant see results)  err {r['err']} tmax {r['tmax']}")
print('telemetry:', json.dumps({k: v for k, v in tel.items() if v not in (0, None, '')}, ensure_ascii=False)[:1500])
