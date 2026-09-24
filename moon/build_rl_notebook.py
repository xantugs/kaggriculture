"""Assemble the RL Kaggle script (forked-state group rollouts + PPO/KL fine-tuning of the BC policy).
usage: build_rl_notebook.py out.py S_list(comma) [iters] [groups] [k_samples] [time_budget_s] [init_npz_name] [key=value ...]"""
import sys, os, json, zlib, base64
HERE = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
S_list = [int(x) for x in sys.argv[2].split(',')]
iters = int(sys.argv[3]) if len(sys.argv) > 3 else 200
groups = int(sys.argv[4]) if len(sys.argv) > 4 else 24
k = int(sys.argv[5]) if len(sys.argv) > 5 else 6
budget = int(sys.argv[6]) if len(sys.argv) > 6 else 11 * 3600
init = sys.argv[7] if len(sys.argv) > 7 else 'bc_model.npz'
P = dict(TAU=1.0, LR=1e-5, CLIP=0.2, KL_BETA=0.02, MARGIN_SCALE=5000.0, WIN_W=0.5, SIGMA_MIN=0.2, PPO_EPOCHS=2, MB=256)
for kv in sys.argv[8:]:
    key, v = kv.split('='); P[key] = float(v) if '.' in v or 'e' in v else int(v)
rd = lambda *p: open(os.path.join(HERE, *p), encoding='utf-8').read()
layer = rd('bc_layer.py')
legal_src = layer[layer.index('_BC_ACCESS = '):layer.index('def _bc_act')]
bcm_src = '\n\n'.join(rd(f) for f in ('feat.py', 'bc_codec.py', 'bc_core.py'))
files = dict(bcm=bcm_src, legal=legal_src, lean=rd('..', 'arena', 'lean.py'), v12=rd('..', 'arena', 'cand', 'omw_v12.py'))
blob = base64.b85encode(zlib.compress(json.dumps(files).encode(), 9)).decode()
head = '''# Kaggriculture RL: continuation fine-tuning of the cloned policy from forked v12 game states.
import os
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'; os.environ['MKL_NUM_THREADS'] = '1'
import subprocess, sys, json, glob, zlib, base64, time, random
import importlib.metadata as _md
if _md.version('kaggle-environments') != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
for _n, _s in json.loads(zlib.decompress(base64.b85decode(%r))).items():
    open('/kaggle/working/%%s.py' %% _n, 'w').write(_s)
S_LIST = %r
ITERS = %d
GROUPS = %d
K_SAMPLES = %d
TIME_BUDGET = %d
INIT_NAME = %r
''' % (blob, S_list, iters, groups, k, budget, init) + ''.join('%s = %r\n' % kv for kv in P.items())
src = head + rd('rl_body.py')
open(out, 'w', encoding='utf-8').write(src)
compile(src, out, 'exec')
print('built', out, len(src), P)
