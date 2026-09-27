"""Build a full sf8 variant: sf8's knob set + overrides (div_over / rich_over merged key by key).
usage: mkcand.py name '{json overrides}' [ctl.py]    -> gold/top10/cands/full_<name>.py"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
FULL = os.path.join(HERE, '..', 'full')
SF8 = {"sells_first": True, "sells_first_chassis": True, "sells_first_slots": True, "sells_first_sort": True,
       "cash_guard_min": 5, "v233_wool_first": True,
       "div_over": {"mkt_dp_d29": True, "final_sell0": 0, "final_cap": 21, "mkt_dp_cap": 30}}
name, over = sys.argv[1], json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
ctl = sys.argv[3] if len(sys.argv) > 3 else os.path.join(FULL, 'ctl.py')
cfg = json.loads(json.dumps(SF8))
for k, v in over.items():
    if k in ('div_over', 'rich_over') and isinstance(v, dict):
        d = dict(cfg.get(k, {})); d.update(v); cfg[k] = d
    else:
        cfg[k] = v
out = os.path.abspath(os.path.join(HERE, '..', 'cands', 'full_%s.py' % name))
subprocess.run([sys.executable, os.path.join(FULL, 'bm5.py'), out, json.dumps(cfg), os.path.abspath(ctl)], check=True, cwd=FULL)
