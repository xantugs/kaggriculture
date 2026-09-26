"""Build an m5 variant: base_m7_t4 + (local) ctl.py + cfg_m5 merged with overrides.
usage: bm5.py out.py '{"hire_compact": true}' [ctl_file]"""
import sys, json, os
HERE = os.path.dirname(os.path.abspath(__file__))   # put base_m7_t4.py, cfg_m5.json and the patched ctl.py here (see README)
out = sys.argv[1]
over = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
ctlf = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'ctl.py')
cfg = json.load(open(os.path.join(HERE, 'cfg_m5.json')))
for k, v in over.items():
    if k in ('div_over', 'rich_over') and isinstance(v, dict):
        d = dict(cfg.get(k, {})); d.update(v); cfg[k] = d
    else:
        cfg[k] = v
src = open(os.path.join(HERE, 'base_m7_t4.py'), encoding='utf-8').read()
ctl = open(ctlf, encoding='utf-8').read()
ctl = ctl.replace('_GC_CROPS = {', 'GC_P.update(%r)\n_GC_CROPS = {' % (cfg,), 1)
open(out, 'w', encoding='utf-8').write(src.rstrip('\n') + '\n\n' + ctl)
print('built', out, os.path.getsize(out), over)
