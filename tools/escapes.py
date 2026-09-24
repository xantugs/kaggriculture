import sys, json, statistics
from harness import run_match
params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
tot = []
for seed in range(200, 206):
    env, rew, st = run_match(("main.py", params), "starter", seed)
    esc = 0
    for d in range(1, 30):
        a = env.steps[d * 24 - 1][0].observation.farms[0]["tiles"]; b = env.steps[d * 24][0].observation.farms[0]["tiles"]
        esc += sum(1 for y in range(10) for x in range(10) if isinstance(a[y][x], dict) and a[y][x].get("animal") and isinstance(b[y][x], dict) and not b[y][x].get("animal"))
    tot.append((rew[0], esc)); print(f"  seed {seed}: ${rew[0]:9,.0f} escapes={esc}", flush=True)
print(f"mean ${statistics.mean(r for r,_ in tot):,.0f}  min ${min(r for r,_ in tot):,.0f} | escapes/game {statistics.mean(e for _,e in tot):.1f}")
