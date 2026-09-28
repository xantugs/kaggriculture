"""Build a CL_sf candidate: T8 knob set + {"start": 0, "open": <cfg>} (+ extra top-level overrides).
usage: mk.py name open_json_file_or_json [extra_json]  -> gold/top10/cands/full_CL_sf_<name>.py"""
import sys, os, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', '..'))
T8 = {"start": 480, "drop_refill": True, "trim_fix": True, "shed_skip": True, "eh_level": {"margin": 2, "min_units": 5, "last_day": 26, "frac": 0.5},
      "div_over": {"visit_watered": True}, "rich_over": {"visit_watered": True}, "s2t_ext": {"straw": 1, "tom": 1, "days": [11], "max_n": 4},
      "market_fix1": True, "market_fix2": True, "d28feed_fix": True, "mtrim_fix": True, "plant23_fix": True, "handover_fix1": True,
      "handover_fix3": True, "tie_blk": {"from": 6, "to": 19}, "vrp_pack": {"min_day": 16, "max_day": 28, "tries": 12, "rounds": 3, "w": 1.5},
      "d27_wheat": {"days": [27], "min_spare": 3, "keep": 0, "max_n": 12}}
name = sys.argv[1]
a = sys.argv[2]
opn = json.load(open(a, encoding='utf-8')) if os.path.exists(a) else json.loads(a)
extra = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
cfg = dict(T8); cfg["start"] = 0; cfg["open"] = opn
for k, v in extra.items():
    if k in ('div_over', 'rich_over') and isinstance(v, dict):
        d = dict(cfg.get(k, {})); d.update(v); cfg[k] = d
    else:
        cfg[k] = v
ctl = os.path.join(KG, 'gold', 'top10', 'full', os.environ.get('CTL', 'ctl_CL_sf.py'))
subprocess.run([sys.executable, os.path.join(KG, 'gold', 'top10', 'tools', 'mkcand.py'), 'CL_sf_' + name, json.dumps(cfg), ctl], check=True)
