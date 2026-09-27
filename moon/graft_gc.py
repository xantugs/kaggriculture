"""Graft the other session's GOLD controller section onto our chassis.
usage: graft_gc.py src.py out_name [base_name]
  src.py    a full submission file containing the '# GOLD controller' banner section at the end
  out_name  written to arena/cand/<out_name>.py
  base_name chassis in arena/cand (default omw_ad_a5 = v16e)
Copies src from the '# ====' line opening the GOLD banner to the end, appends it to the base, checks that the result
loads and chains GoldCtl over the base's last agent, and prints the GC_P.update line plus any GC_P keys that differ
from the current graft (adapt)."""
import sys, os, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); C = os.path.join(HERE, '..', 'arena', 'cand')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


src, out = sys.argv[1], sys.argv[2]
base = sys.argv[3] if len(sys.argv) > 3 else 'omw_ad_a5'
lines = open(src, encoding='utf-8').read().split('\n')
gold = next(i for i, l in enumerate(lines) if l.startswith('# GOLD controller'))
start = gold - 1 if lines[gold - 1].startswith('# ====') else gold
section = '\n'.join(lines[start:])
if re.search(r"configuration\s*\[\s*['\"]seed|\.seed\b", section):
    print('WARNING: section mentions the simulator seed - check the no-seed rule before using it')
body = open(os.path.join(C, base + '.py'), encoding='utf-8').read().rstrip('\n') + '\n\n\n'
path = os.path.join(C, out + '.py')
open(path, 'w', encoding='utf-8', newline='').write(body + section)
m = load(path, 'graft_new')
b = load(os.path.join(C, base + '.py'), 'graft_base')
assert m.kaggle_submission_agent.__name__ == 'agent' and m._GC_PARENT.telemetry in (m._AD_REPORT, getattr(m, '_SES_REPORT', None)), 'chain broken'
print('wrote', path, 'section lines', len(lines) - start, 'start step', m.GC_P['start'])
print([l for l in lines[start:] if l.startswith('GC_P.update')])
ref = os.path.join(C, 'adapt.py')
if os.path.exists(ref):
    r = load(ref, 'graft_ref').GC_P
    diff = {k: (r.get(k), v) for k, v in m.GC_P.items() if r.get(k) != v}
    diff.update({k: (v, None) for k, v in r.items() if k not in m.GC_P})
    print('GC_P changes vs adapt (old, new):', diff or 'none')
