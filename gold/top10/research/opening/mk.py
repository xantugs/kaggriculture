"""Build an opening-controller candidate: T8 knob set + {"start": 0, "open": cfg} on gold/top10/full/ctl_op.py.
usage: mk.py name base_cfg.json ['<json overrides>'] [extra top-level json]  -> gold/top10/cands/full_OP_<name>.py
Overrides merge into the base cfg; dict values (anim_cond, straw_hf, crew, over, ...) merge key by key one level down."""
import sys, json, subprocess, os
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
T8 = {"start": 480, "drop_refill": True, "trim_fix": True, "shed_skip": True, "eh_level": {"margin": 2, "min_units": 5, "last_day": 26, "frac": 0.5},
      "div_over": {"visit_watered": True}, "rich_over": {"visit_watered": True}, "s2t_ext": {"straw": 1, "tom": 1, "days": [11], "max_n": 4},
      "market_fix1": True, "market_fix2": True, "d28feed_fix": True, "mtrim_fix": True, "plant23_fix": True, "handover_fix1": True,
      "handover_fix3": True, "tie_blk": {"from": 6, "to": 19}, "vrp_pack": {"min_day": 16, "max_day": 28, "tries": 12, "rounds": 3, "w": 1.5},
      "d27_wheat": {"days": [27], "min_spare": 3, "keep": 0, "max_n": 12}}


def merge(base, over):
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            d = dict(out[k])
            for k2, v2 in v.items():
                if isinstance(v2, dict) and isinstance(d.get(k2), dict):
                    d2 = dict(d[k2]); d2.update(v2); d[k2] = d2
                else:
                    d[k2] = v2
            out[k] = d
        else:
            out[k] = v
    return out


if __name__ == '__main__':
    name = sys.argv[1]
    op = json.load(open(sys.argv[2], encoding='utf-8'))
    if len(sys.argv) > 3 and sys.argv[3]:
        op = merge(op, json.loads(sys.argv[3]))
    extra = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    cfg = dict(T8); cfg["start"] = 0; cfg["open"] = op; cfg.update(extra)
    json.dump(op, open(os.path.join(HERE, 'cfg_%s.json' % name), 'w', encoding='utf-8'))
    ctl = os.environ.get('CTL', os.path.join(KG, 'gold', 'top10', 'full', 'ctl_op.py'))
    subprocess.run([sys.executable, os.path.join(KG, 'gold', 'top10', 'tools', 'mkcand.py'), 'OP_' + name, json.dumps(cfg), ctl], check=True)
