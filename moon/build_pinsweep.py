"""Assemble the pinned split-sweep kernel. usage: build_pinsweep.py out.py base_agent.py [S] [chunk]"""
import sys, os, json, zlib, base64, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tune
out, base_path = sys.argv[1], sys.argv[2]
S = int(sys.argv[3]) if len(sys.argv) > 3 else 96; chunk = int(sys.argv[4]) if len(sys.argv) > 4 else 12
rd = lambda p: open(p, encoding='utf-8').read()
base = rd(base_path)
files = dict(lean=rd(os.path.join(HERE, '..', 'arena', 'lean.py')), pinned=rd(os.path.join(HERE, 'pinned.py')),
             pinmulti=rd(os.path.join(HERE, 'pinmulti.py')), base=base)
blob = base64.b85encode(zlib.compress(json.dumps(files).encode(), 9)).decode()
knobs = dict(tune.KNOBS); knobs.update(tune.KNOBS2)
knobs.update({'_FD_FLUSH': [714, 717], '_PE_STEP': [680, 686, 692], '_V92_P_H': [24, 36, 72], '_R51_INPUT_CROPS': [
    {'WHEAT': (1, 4, 6), 'CARROT': (1, 3, 4)}, {'WHEAT': (2, 4, 6), 'CARROT': (2, 3, 4)}]})
knob_vars = []
for k, vals in knobs.items():
    if not re.search(r'^%s\s*=' % re.escape(k), base, flags=re.M):
        continue
    for v in vals:
        knob_vars.append((tune.label(k, v), {k: v}))
chain = re.findall(r"^(_[A-Za-z0-9_]*PARENT) *= *agent\s*$", base, flags=re.M)
skip_vars = [('skip' + l[:-7], {'__skip__': [l]}) for l in chain[1:]]
phases = [('knobs', knob_vars), ('skips', skip_vars)]
head = '''# Kaggriculture: pinned split sweep (copies vs divergent 2800+ opponents) for knob values and layer bypasses.
import os
os.environ['OMP_NUM_THREADS'] = '1'
import subprocess, sys, json, zlib, base64
import importlib.metadata as _md
try:
    _v = _md.version('kaggle-environments')
except Exception:
    _v = None
if _v != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
for _n, _s in json.loads(zlib.decompress(base64.b85decode(%r))).items():
    open('/kaggle/working/%%s.py' %% _n, 'w', encoding='utf-8').write(_s)
PHASES = %r
S_STEP = %d
CHUNK = %d
''' % (blob, phases, S, chunk)
src = head + open(os.path.join(HERE, 'pinsweep_body.py'), encoding='utf-8').read()
compile(src, out, 'exec'); open(out, 'w', encoding='utf-8').write(src)
print('built', out, len(src), 'knob variants', len(knob_vars), 'skip variants', len(skip_vars))
