"""For each day: which jobs were still pending at hour 23, animals lost overnight, idle tiles by designation."""
import sys, collections, importlib.util
from harness import run_match
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 100
path = sys.argv[2] if len(sys.argv) > 2 else "main.py"
env, rew, st = run_match(path, "starter", seed)
spec = importlib.util.spec_from_file_location("probe", path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cfg = env.configuration
prev_anim = None
for day in range(30):
    s = day * 24 + 23
    if s >= len(env.steps): break
    o = env.steps[s][0].observation
    S = m.parse(o, cfg)
    M = m._MEM.setdefault(99, {"plan": {}, "zone": {}})
    m.set_policies(S, M)
    jobs = m.build_jobs(S, M)
    c = collections.Counter(j["op"][0] + ("!" if j["crit"] else "") for lst in jobs.values() for j in lst)
    anim = sum(1 for _, _, t in m.all_tiles(S) if m.is_animal(t))
    unfed = sum(1 for _, _, t in m.all_tiles(S) if m.is_animal(t) and not t["fed_today"])
    dying = sum(1 for _, _, t in m.all_tiles(S) if m.is_animal(t) and not t["fed_today"] and t["consecutive_unfed"] >= 1)
    pl_dying = sum(1 for _, _, t in m.all_tiles(S) if m.is_plant(t) and not t["watered_today"] and t["consecutive_unwatered"] >= 1)
    print(f"d{day:2d} h23: animals={anim:2d} unfed={unfed:2d} will_escape={dying:2d} plants_dying={pl_dying:2d} | undone: {dict(c)}")
print("FINAL", rew)
