"""Build an isolated, private Kaggle continuation-learning experiment."""
from pathlib import Path
import ast
import base64
import hashlib
import json
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MOON = ROOT / 'moon'


def replace_once(text, old, new):
    assert text.count(old) == 1, (old[:100], text.count(old))
    return text.replace(old, new)


def build():
    original = (MOON / 'rl_body.py').read_text(encoding='utf-8')
    policy = original[original.index('def _pick('):original.index('def rollout_group(')]
    # Preserve float32 observations for behavior/training probability parity.
    policy = policy.replace('grid=grid.astype(np.float16)', 'grid=grid.astype(np.float32)')
    policy = 'import numpy as np\nimport bcm, legal\nUA, NQ, MARKET_HEADS = bcm.UA, bcm.NQ, bcm.MARKET_HEADS\nPASS_I = UA.index("PASS")\n\n' + policy
    layer = (MOON / 'bc_layer.py').read_text(encoding='utf-8')
    files = {
        'bcm': '\n\n'.join((MOON / f).read_text(encoding='utf-8') for f in ('feat.py', 'bc_codec.py', 'bc_core.py')),
        'legal': layer[layer.index('_BC_ACCESS = '):layer.index('def _bc_act')],
        'policy': policy,
        'lean': (ROOT / 'arena' / 'lean.py').read_text(encoding='utf-8'),
        'v12': (ROOT / 'arena' / 'cand' / 'omw_v13f.py').read_text(encoding='utf-8'),
    }
    snapshot = HERE / 'snapshot'
    snapshot.mkdir(exist_ok=True)
    for name, src in files.items():
        (snapshot / (name + '.py')).write_text(src, encoding='utf-8')
    manifest = {name: hashlib.sha256(src.encode()).hexdigest() for name, src in files.items()}
    (HERE / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))

    src = original[:original.index('def _pick(')] + 'from policy import policy_act\n\n' + original[original.index('def rollout_group('):]
    src = src.replace("mp.get_context('fork')", "mp.get_context('spawn')")
    src = src.replace("import torch.nn.functional as F\n", "import torch.nn.functional as F\n    torch.set_num_threads(1)\n")
    src = replace_once(src, "    dev = 'cuda' if torch.cuda.is_available() else 'cpu'", "    dev = 'cpu'  # bounded CPU pilot; workers never inherit a CUDA context")
    src = replace_once(src, '    history = []\n', (HERE / 'main_setup.inc').read_text())
    src = replace_once(src, 'np.random.RandomState(1000 + it)', 'np.random.RandomState(830_000_000 + it)')
    src = replace_once(src, "jobs = [(int(rs.randint(1, 2 ** 31 - 1)), int(rs.randint(2)), S_LIST, K_SAMPLES, TAU, wpath) for _ in range(GROUPS)]",
        "jobs = [(seed, p, S_LIST, K_SAMPLES, TAU, wpath) for seed in [int(rs.randint(830_000_000, 839_000_000)) for _ in range(GROUPS // 2)] for p in (0, 1)]")
    src = replace_once(src, "steps = []; diag =", "steps = []; diag =")  # assert source layout
    src = replace_once(src, "        # PPO update\n", "        assert not errs and not lost, ('rollout errors', errs, lost)\n        # PPO update\n")
    # Compute a single joint-action importance ratio, with conditional quantity factors.
    src = replace_once(src,
        "                    obj = clip_obj(la, oa, A_u).sum() + (clip_obj(lq, oq, A_u) * pick).sum() + clip_obj(lm, om, b['adv'][:, None]).sum()",
        "                    new_joint = joint(b, la, lq, lm)\n                    old_joint = joint(b, oa, oq, om)\n                    obj = clip_obj(new_joint, old_joint, b['adv']).sum()")
    src = replace_once(src, '                        r = torch.exp(new - old)', '                        r = torch.exp(torch.clamp(new - old, -20, 20))')
    # Exported logits and sampled action probabilities must match before any update.
    src = replace_once(src,
        "                    b = batch(steps[i:i + MB]); olds.append(taken(b, *dists(net, b)))",
        "                    b = batch(steps[i:i + MB]); olds.append(taken(b, *dists(net, b)))\n                    if it == 0 and i == 0:\n                        assert_export_parity(net, b)")
    src = replace_once(src,
        "        export('/kaggle/working/rl_model.npz')",
        "        export('/kaggle/working/rl_model.npz')\n        if (it + 1) % EVAL_EVERY == 0 or it + 1 == ITERS:\n            evaluate('rl_%03d' % (it + 1), '/kaggle/working/rl_model.npz', VAL_SEEDS, select=True)\n        if time.time() - t_start > TIME_BUDGET:\n            break")
    src = replace_once(src,
        '    ex.shutdown(wait=False, cancel_futures=True)',
        (HERE / 'main_finish.inc').read_text() + '\n    ex.shutdown(wait=True, cancel_futures=True)')
    helper = (HERE / 'helpers.py').read_text()
    src = replace_once(src, 'def main():', helper + '\n\ndef main():')
    blob = base64.b85encode(zlib.compress(json.dumps(files).encode(), 9)).decode()
    header = f'''# Private Kaggriculture continuation pilot. No competition submission.
import os
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
import sys, subprocess, json, glob, base64, zlib, time, random, hashlib
import importlib.metadata as metadata
if metadata.version('kaggle-environments') != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=True)
assert metadata.version('kaggle-environments') == '1.32.7'
if __name__ == '__main__':
    for name, content in json.loads(zlib.decompress(base64.b85decode({blob!r}))).items():
        open('/kaggle/working/%s.py' % name, 'w', encoding='utf-8').write(content)
    json.dump({manifest!r}, open('/kaggle/working/source_manifest.json', 'w'), indent=2)
S_LIST = [672, 696]
ITERS = 60
GROUPS = 8
K_SAMPLES = 3
TIME_BUDGET = 3600
INIT_NAME = 'bc_model.npz'
TAU = 1.0
LR = 1e-5
CLIP = 0.2
KL_BETA = 0.02
MARGIN_SCALE = 5000.0
WIN_W = 0.5
SIGMA_MIN = 0.2
PPO_EPOCHS = 2
MB = 64
EVAL_EVERY = 5
WARM_SEEDS = list(range(810000001, 810000033))
VAL_SEEDS = list(range(820000001, 820000005))
TEST_SEEDS = list(range(840100001, 840100017))
WARM_EPOCHS = 8
random.seed(20260923)
'''
    full = header + src
    compile(full, 'pilot.py', 'exec')
    (HERE / 'pilot.py').write_text(full, encoding='utf-8')
    print(json.dumps({'built': str(HERE / 'pilot.py'), 'bytes': len(full.encode()), 'incumbent_sha256': manifest['v12']}))


if __name__ == '__main__':
    build()
